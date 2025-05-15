from rest_framework import viewsets, status
from .models import User, Group, GroupMembership, Post, Comment, DetectedObject, Quiz, Badge, UserBadge, GameScore
from .serializers import UserSerializer, GroupSerializer, GroupMembershipSerializer, PostSerializer, CommentSerializer, \
    DetectedObjectSerializer, QuizSerializer, BadgeSerializer, UserBadgeSerializer, GroupDetailSerializer, \
    GroupMembershipDetailSerializer
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Max, Sum


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


# Funzioni migliorate per gestire punteggi e leaderboard
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user_points(request):
    """
    Aggiorna i punti eco dell'utente quando guadagna punti in un gioco,
    registrando solo il miglior punteggio per ciascun gioco
    """
    points = request.data.get('points', 0)
    game_id = request.data.get('game_id', '')

    if points <= 0:
        return Response({'error': 'Punti non validi'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    # Verifica se esiste già un punteggio migliore per questo gioco/utente
    if game_id:
        # Cerca il punteggio migliore esistente
        best_score = GameScore.objects.filter(user=user, game_id=game_id).order_by('-score').first()

        if best_score is None:
            # Primo punteggio per questo gioco, lo creiamo
            GameScore.objects.create(
                user=user,
                game_id=game_id,
                score=points
            )
            # Aggiorna anche i punti totali dell'utente
            user.eco_points += points
            user.save()
        elif points > best_score.score:
            # Il nuovo punteggio è migliore, calcoliamo la differenza e aggiungiamo solo quella
            diff = points - best_score.score
            best_score.score = points
            best_score.save()

            # Aggiorna i punti totali dell'utente con la differenza
            user.eco_points += diff
            user.save()
        # Se il punteggio non è migliore, non facciamo nulla

    return Response({
        'success': True,
        'message': f'Punteggio aggiornato con successo',
        'total_points': user.eco_points
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_leaderboard(request):
    """
    Ottiene la classifica globale o per gioco specifico,
    mostrando solo il miglior punteggio per ciascun utente.
    Per la classifica globale, calcoliamo la somma dei migliori punteggi di ogni gioco.
    """
    game_id = request.query_params.get('game_id', None)

    if game_id:
        # Per un gioco specifico, otteniamo solo il miglior punteggio di ogni utente
        from django.db.models import Max
        user_best_scores = GameScore.objects.filter(game_id=game_id).values('user').annotate(
            best_score=Max('score')
        ).order_by('-best_score')[:50]

        # Costruiamo i dati della risposta
        leaderboard_data = []
        for entry in user_best_scores:
            user = User.objects.get(id=entry['user'])
            leaderboard_data.append({
                'userId': user.id,
                'username': user.username,
                'score': entry['best_score'],
                'avatar': user.avatar
            })

        return Response(leaderboard_data)
    else:
        # Per la classifica globale, calcoliamo la somma dei migliori punteggi per ogni gioco

        # 1. Per ogni utente e per ogni gioco, troviamo il miglior punteggio
        from django.db import connection

        # Questa query SQL trova il punteggio massimo per ogni utente per ogni gioco
        # e poi somma questi punteggi massimi per ogni utente
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    user_id, 
                    SUM(max_score) as total_score 
                FROM (
                    SELECT 
                        user_id, 
                        game_id, 
                        MAX(score) as max_score 
                    FROM 
                        core_gamescore 
                    GROUP BY 
                        user_id, game_id
                ) best_scores 
                GROUP BY 
                    user_id 
                ORDER BY 
                    total_score DESC
                LIMIT 50
            """)

            rows = cursor.fetchall()

        # Costruiamo i dati della risposta
        leaderboard_data = []
        for row in rows:
            user_id, total_score = row
            try:
                user = User.objects.get(id=user_id)
                leaderboard_data.append({
                    'userId': user.id,
                    'username': user.username,
                    'ecoPoints': int(total_score),  # Convertiamo in intero per sicurezza
                    'avatar': user.avatar
                })
            except User.DoesNotExist:
                # Ignoriamo utenti che potrebbero essere stati eliminati
                pass

        return Response(leaderboard_data)


# views.py - Nuove views per gestire i gruppi e i membri

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    authentication_classes = [TokenAuthentication]  # Add this line
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return GroupSerializer

    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        GroupMembership.objects.create(
            user=self.request.user,
            group=group,
            role='admin'
        )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        group = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'student')

        # Verifica che solo il proprietario o admin può aggiungere membri
        is_authorized = GroupMembership.objects.filter(
            group=group,
            user=request.user,
            role__in=['admin']
        ).exists() or group.owner == request.user

        if not is_authorized:
            return Response(
                {'error': 'Non hai il permesso di aggiungere membri'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(id=user_id)

            # Verifica se l'utente è già membro
            if GroupMembership.objects.filter(user=user, group=group).exists():
                return Response(
                    {'error': 'L\'utente è già membro di questo gruppo'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Aggiungi l'utente al gruppo
            membership = GroupMembership.objects.create(
                user=user,
                group=group,
                role=role
            )

            return Response(
                GroupMembershipDetailSerializer(membership).data,
                status=status.HTTP_201_CREATED
            )

        except User.DoesNotExist:
            return Response(
                {'error': 'Utente non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        group = self.get_object()
        user_id = request.data.get('user_id')

        # Verifica che solo il proprietario o admin può rimuovere membri
        is_authorized = GroupMembership.objects.filter(
            group=group,
            user=request.user,
            role__in=['admin']
        ).exists() or group.owner == request.user

        if not is_authorized:
            return Response(
                {'error': 'Non hai il permesso di rimuovere membri'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Non permettere la rimozione del proprietario
            target_user = User.objects.get(id=user_id)
            if target_user == group.owner:
                return Response(
                    {'error': 'Non puoi rimuovere il proprietario del gruppo'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            membership = GroupMembership.objects.get(user=target_user, group=group)
            membership.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except (User.DoesNotExist, GroupMembership.DoesNotExist):
            return Response(
                {'error': 'Membro non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        group = self.get_object()
        user_id = request.data.get('user_id')
        new_role = request.data.get('role')

        # Verifica che solo il proprietario o admin può cambiare ruoli
        is_authorized = GroupMembership.objects.filter(
            group=group,
            user=request.user,
            role__in=['admin']
        ).exists() or group.owner == request.user

        if not is_authorized:
            return Response(
                {'error': 'Non hai il permesso di cambiare ruoli'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            target_user = User.objects.get(id=user_id)
            membership = GroupMembership.objects.get(user=target_user, group=group)

            # Non permettere di cambiare il ruolo del proprietario
            if target_user == group.owner and new_role != 'admin':
                return Response(
                    {'error': 'Non puoi cambiare il ruolo del proprietario'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            membership.role = new_role
            membership.save()

            return Response(GroupMembershipDetailSerializer(membership).data)

        except (User.DoesNotExist, GroupMembership.DoesNotExist):
            return Response(
                {'error': 'Membro non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        # Ottieni tutti i gruppi di cui l'utente è membro
        memberships = GroupMembership.objects.filter(user=request.user)
        groups = [membership.group for membership in memberships]

        # Includi anche i gruppi di cui è proprietario ma non membro
        owned_groups = Group.objects.filter(owner=request.user)
        for group in owned_groups:
            if group not in groups:
                groups.append(group)

        return Response(GroupSerializer(groups, many=True).data)