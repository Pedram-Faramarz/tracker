from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection

def db_check(request):
    try:
        vendor = connection.vendor
        db_name = connection.settings_dict.get('NAME', 'unknown')
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users_user")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tracker_principle")
        principle_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tracker_task")
        task_count = cursor.fetchone()[0]
        return JsonResponse({
            'database': vendor,
            'name': str(db_name),
            'users': user_count,
            'principles': principle_count,
            'tasks': task_count,
            'status': 'ok'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.tracker.urls')),
    path('db-check/', db_check),
    re_path(r'^(?!api/|admin/|media/).*$',
            TemplateView.as_view(template_name='index.html'),
            name='angular'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
