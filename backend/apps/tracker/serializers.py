from rest_framework import serializers
from .models import Principle, Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'principle', 'text', 'notes', 'is_done',
                  'priority', 'due_date', 'done_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'done_at', 'created_at', 'updated_at')

    def validate_principle(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and value.user != request.user:
            raise serializers.ValidationError('You do not own this principle.')
        return value

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Task text cannot be empty.')
        return value.strip()


class TaskInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'text', 'notes', 'is_done', 'priority',
                  'due_date', 'done_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'done_at', 'created_at', 'updated_at')


class PrincipleSerializer(serializers.ModelSerializer):
    # Use SerializerMethodField so they always return safe defaults even on new objects
    tasks = TaskInlineSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    completed_task_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Principle
        fields = (
            'id', 'name', 'description', 'semester', 'color',
            'is_archived', 'tasks', 'task_count', 'completed_task_count',
            'progress_percentage', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_task_count(self, obj):
        try:
            return obj.task_count
        except Exception:
            return 0

    def get_completed_task_count(self, obj):
        try:
            return obj.completed_task_count
        except Exception:
            return 0

    def get_progress_percentage(self, obj):
        try:
            return obj.progress_percentage
        except Exception:
            return 0

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Principle name cannot be empty.')
        return value.strip()


class PrincipleListSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()
    completed_task_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Principle
        fields = (
            'id', 'name', 'description', 'semester', 'color',
            'is_archived', 'task_count', 'completed_task_count',
            'progress_percentage', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_task_count(self, obj):
        try:
            return obj.task_count
        except Exception:
            return 0

    def get_completed_task_count(self, obj):
        try:
            return obj.completed_task_count
        except Exception:
            return 0

    def get_progress_percentage(self, obj):
        try:
            return obj.progress_percentage
        except Exception:
            return 0


class StatsSerializer(serializers.Serializer):
    total_principles = serializers.IntegerField()
    active_principles = serializers.IntegerField()
    archived_principles = serializers.IntegerField()
    completed_principles = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    overall_progress = serializers.FloatField()
    by_semester = serializers.ListField()
