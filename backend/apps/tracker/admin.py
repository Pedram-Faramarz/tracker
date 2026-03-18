from django.contrib import admin
from .models import Principle, Task


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ('text', 'is_done', 'priority', 'due_date')


@admin.register(Principle)
class PrincipleAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'semester', 'task_count', 'progress_percentage', 'is_archived', 'created_at')
    list_filter = ('is_archived', 'semester')
    search_fields = ('name', 'user__email')
    inlines = [TaskInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('text', 'principle', 'is_done', 'priority', 'due_date', 'created_at')
    list_filter = ('is_done', 'priority')
    search_fields = ('text', 'principle__name')
    readonly_fields = ('created_at', 'updated_at', 'done_at')
