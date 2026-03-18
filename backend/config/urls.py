from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.tracker.urls')),
    # Catch all — serve Angular's index.html for client-side routing
    re_path(r'^(?!api/|admin/|media/).*$',
            TemplateView.as_view(template_name='index.html'),
            name='angular'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
