from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core import views  # Assicurati che il percorso al modulo sia corretto

# Crea un router
router = DefaultRouter()

# Aggiungi i tuoi viewset al router
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'group-memberships', views.GroupMembershipViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'detected-objects', views.DetectedObjectViewSet)
router.register(r'quizzes', views.QuizViewSet)
router.register(r'badges', views.BadgeViewSet)
router.register(r'user-badges', views.UserBadgeViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # Includi il router per le API
]
