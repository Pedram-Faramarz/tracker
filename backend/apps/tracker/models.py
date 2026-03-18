from django.db import models
from django.conf import settings


class Principle(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='principles')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    semester = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, default='#c8f55a')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user.email})'

    @property
    def task_count(self):
        # Use cached tasks if prefetched, else query
        if hasattr(self, '_prefetched_objects_cache') and 'tasks' in self._prefetched_objects_cache:
            return len(self._prefetched_objects_cache['tasks'])
        return self.tasks.count()

    @property
    def completed_task_count(self):
        if hasattr(self, '_prefetched_objects_cache') and 'tasks' in self._prefetched_objects_cache:
            return sum(1 for t in self._prefetched_objects_cache['tasks'] if t.is_done)
        return self.tasks.filter(is_done=True).count()

    @property
    def progress_percentage(self):
        total = self.task_count
        if total == 0:
            return 0
        return round(self.completed_task_count / total * 100)


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    principle = models.ForeignKey(Principle, on_delete=models.CASCADE, related_name='tasks')
    text = models.CharField(max_length=500)
    notes = models.TextField(blank=True)
    is_done = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    done_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['is_done', 'created_at']

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.is_done and not self.done_at:
            self.done_at = timezone.now()
        elif not self.is_done:
            self.done_at = None
        super().save(*args, **kwargs)
