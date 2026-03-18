from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Principle, Task
from .serializers import (
    PrincipleSerializer, PrincipleListSerializer,
    TaskSerializer, StatsSerializer
)


class PrincipleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['semester', 'is_archived']
    search_fields = ['name', 'description', 'semester']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Principle.objects.filter(
            user=self.request.user
        ).prefetch_related('tasks')

    def get_serializer_class(self):
        if self.action == 'list':
            return PrincipleListSerializer
        return PrincipleSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # FIX: archive toggle was not returning updated principle data
    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        principle = self.get_object()
        principle.is_archived = not principle.is_archived
        principle.save(update_fields=['is_archived'])
        return Response({
            'detail': f'Principle {"archived" if principle.is_archived else "unarchived"}.',
            'is_archived': principle.is_archived
        })

    # FIX: stats endpoint was crashing when principles had no tasks (division by zero edge case)
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        principles = list(
            Principle.objects.filter(user=request.user).prefetch_related('tasks')
        )
        total_tasks = sum(p.task_count for p in principles)
        completed_tasks = sum(p.completed_task_count for p in principles)
        completed_principles = sum(
            1 for p in principles
            if p.task_count > 0 and p.progress_percentage == 100
        )

        semesters = {}
        for p in principles:
            sem = p.semester or 'No Semester'
            if sem not in semesters:
                semesters[sem] = {'semester': sem, 'principles': 0, 'tasks': 0, 'completed': 0}
            semesters[sem]['principles'] += 1
            semesters[sem]['tasks'] += p.task_count
            semesters[sem]['completed'] += p.completed_task_count

        data = {
            'total_principles': len(principles),
            'active_principles': sum(1 for p in principles if not p.is_archived),
            'archived_principles': sum(1 for p in principles if p.is_archived),
            'completed_principles': completed_principles,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': total_tasks - completed_tasks,
            'overall_progress': round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
            'by_semester': list(semesters.values()),
        }
        serializer = StatsSerializer(data)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['principle', 'is_done', 'priority']
    search_fields = ['text', 'notes']
    ordering_fields = ['created_at', 'due_date', 'priority']

    def get_queryset(self):
        # FIX: only return tasks belonging to the logged-in user's principles
        return Task.objects.filter(
            principle__user=self.request.user
        ).select_related('principle')

    def perform_create(self, serializer):
        # FIX: validate that the principle belongs to the requesting user
        principle = serializer.validated_data.get('principle')
        if principle.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not own this principle.')
        serializer.save()

    # FIX: toggle was not using update_fields — caused full model save
    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        task = self.get_object()
        task.is_done = not task.is_done
        task.save()  # triggers done_at logic in model.save()
        return Response(TaskSerializer(task, context={'request': request}).data)
