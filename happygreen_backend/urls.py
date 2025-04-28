from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from core import views

router = routers.DefaultRouter()

router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'groupmemberships', views.GroupMembershipViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'detectedobjects', views.DetectedObjectViewSet)
router.register(r'quizzes', views.QuizViewSet)
router.register(r'badges', views.BadgeViewSet)
router.register(r'userbadges', views.UserBadgeViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]
