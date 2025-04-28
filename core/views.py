from rest_framework import viewsets
from .models import User, Group, GroupMembership, Post, Comment, DetectedObject, Quiz, Badge, UserBadge
from .serializers import UserSerializer, GroupSerializer, GroupMembershipSerializer, PostSerializer, CommentSerializer, DetectedObjectSerializer, QuizSerializer, BadgeSerializer, UserBadgeSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

class DetectedObjectViewSet(viewsets.ModelViewSet):
    queryset = DetectedObject.objects.all()
    serializer_class = DetectedObjectSerializer

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer

class UserBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserBadge.objects.all()
    serializer_class = UserBadgeSerializer
