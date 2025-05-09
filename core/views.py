from rest_framework import viewsets, status
from .models import User, Group, GroupMembership, Post, Comment, DetectedObject, Quiz, Badge, UserBadge, GameScore
from .serializers import UserSerializer, GroupSerializer, GroupMembershipSerializer, PostSerializer, CommentSerializer, \
    DetectedObjectSerializer, QuizSerializer, BadgeSerializer, UserBadgeSerializer, GameScoreSerializer
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Restituisce i dati dell'utente corrente
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

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


# views.py - Aggiungiamo le view per gestire punteggi e leaderboard
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user_points(request):
    """
    Aggiorna i punti eco dell'utente quando guadagna punti in un gioco
    """
    points = request.data.get('points', 0)
    game_id = request.data.get('game_id', '')

    if points <= 0:
        return Response({'error': 'Punti non validi'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    user.eco_points += points
    user.save()

    # Salva anche il punteggio nel leaderboard
    if game_id:
        GameScore.objects.create(
            user=user,
            game_id=game_id,
            score=points
        )

    return Response({
        'success': True,
        'message': f'Aggiunti {points} punti eco',
        'total_points': user.eco_points
    })

@api_view(['GET'])
def get_leaderboard(request):
    """
    Ottiene la classifica globale e per gioco specifico
    """
    game_id = request.query_params.get('game_id', None)

    if game_id:
        scores = GameScore.objects.filter(game_id=game_id).order_by('-score')[:50]
        serializer = GameScoreSerializer(scores, many=True)
    else:
        from django.db.models import Sum
        scores = User.objects.annotate(
            total_score=Sum('gamescore__score')
        ).order_by('-total_score')[:50]
        from .serializers import LeaderboardUserSerializer
        serializer = LeaderboardUserSerializer(scores, many=True)

    return Response(serializer.data)
