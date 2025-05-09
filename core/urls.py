# urls.py (principale)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core import views

router = DefaultRouter()
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
    # Nota: rimuoviamo 'api/' dal prefisso poiché è già incluso nel file urls.py principale
    path('user/update-points/', views.update_user_points, name='update-user-points'),
    path('leaderboard/', views.get_leaderboard, name='get-leaderboard'),
    path('users/me/', views.current_user, name='current-user'),
    path('', include(router.urls)),
    path('auth/', include('core.auth_urls')),  # Auth routes
]