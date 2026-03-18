from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrincipleViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'principles', PrincipleViewSet, basename='principle')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]
