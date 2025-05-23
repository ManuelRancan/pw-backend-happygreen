# views.py - Correzione endpoint avatar

from rest_framework import viewsets, status
from .models import User, Group, GroupMembership, Post, Comment, DetectedObject, Quiz, Badge, UserBadge, GameScore, \
    PostLike, PostReaction
from .serializers import (
    UserSerializer, GroupSerializer, GroupMembershipSerializer, PostSerializer, CommentSerializer,
    DetectedObjectSerializer, QuizSerializer, BadgeSerializer, UserBadgeSerializer, GroupDetailSerializer,
    GroupMembershipDetailSerializer, PostLikeSerializer, PostReactionSerializer
)
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Max, Sum
import base64
import uuid
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Restituisce i dati dell'utente corrente
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# NUOVO: Endpoint separato per aggiornamento avatar - VERSIONE CORRETTA
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user_avatar(request):
    """
    Aggiorna l'avatar dell'utente corrente
    """
    user = request.user
    avatar_data = request.data.get('avatar')

    if not avatar_data:
        return Response(
            {'error': 'Immagine avatar richiesta'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        logger.info(f"Received avatar update request for user {user.username}")
        logger.info(f"Avatar data length: {len(avatar_data)}")

        # Validazione del formato base64
        if not avatar_data.startswith('data:image'):
            return Response(
                {'error': 'Formato immagine non valido. Richiesto formato base64 con prefisso data:image'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validazione dimensione (max 5MB per sicurezza)
        if len(avatar_data) > 5 * 1024 * 1024:  # 5MB
            return Response(
                {'error': 'Immagine troppo grande. Dimensione massima: 5MB'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Salva direttamente i dati base64 nel database
        user.avatar = avatar_data
        user.save()

        logger.info(f"Avatar updated successfully for user {user.username}")
        logger.info(f"New avatar data length: {len(user.avatar) if user.avatar else 0}")

        return Response({
            'success': True,
            'avatar': user.avatar,
            'message': 'Avatar aggiornato con successo'
        })

    except Exception as e:
        logger.error(f"Error updating avatar for user {user.username}: {str(e)}")
        return Response(
            {'error': f'Errore nell\'aggiornamento dell\'avatar: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# NUOVO: Endpoint separato per aggiornamento profilo
@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Aggiorna il profilo dell'utente corrente
    """
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'user': serializer.data,
            'message': 'Profilo aggiornato con successo'
        })
    else:
        return Response(
            {'error': 'Dati non validi', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


# Le altre classi viewset rimangono invariate...
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    authentication_classes = [TokenAuthentication]
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
    def join(self, request, pk=None):
        """
        Permette all'utente corrente di unirsi al gruppo
        """
        group = self.get_object()
        user = request.user

        if GroupMembership.objects.filter(user=user, group=group).exists():
            return Response(
                {'error': 'Sei già membro di questo gruppo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            membership = GroupMembership.objects.create(
                user=user,
                group=group,
                role='student'
            )

            return Response(
                GroupMembershipDetailSerializer(membership).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': f'Errore nell\'unirsi al gruppo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """
        Permette agli admin di aggiungere altri membri
        """
        group = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'student')

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

            if GroupMembership.objects.filter(user=user, group=group).exists():
                return Response(
                    {'error': 'L\'utente è già membro di questo gruppo'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer


# Il resto delle classi viewset aggiornato per gestire gli avatar...
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        IMPORTANTE: Filtra i post in base al gruppo specificato nel query parameter
        """
        queryset = Post.objects.all()
        group_id = self.request.query_params.get('group', None)

        if group_id is not None:
            try:
                group_id = int(group_id)
                # Verifica che l'utente sia membro del gruppo
                is_member = GroupMembership.objects.filter(
                    user=self.request.user,
                    group_id=group_id
                ).exists()

                # Verifica che l'utente sia il proprietario del gruppo
                is_owner = Group.objects.filter(
                    id=group_id,
                    owner=self.request.user
                ).exists()

                if is_member or is_owner:
                    # Filtra solo i post di questo gruppo
                    queryset = queryset.filter(group_id=group_id)
                else:
                    # Se non è membro né proprietario, restituisci queryset vuoto
                    queryset = Post.objects.none()
            except (ValueError, TypeError):
                # Se group_id non è un intero valido, restituisci queryset vuoto
                queryset = Post.objects.none()
        else:
            # Se non è specificato un gruppo, restituisci solo i post dei gruppi dell'utente
            user_groups = GroupMembership.objects.filter(user=self.request.user).values_list('group_id', flat=True)
            owned_groups = Group.objects.filter(owner=self.request.user).values_list('id', flat=True)
            all_user_groups = list(user_groups) + list(owned_groups)
            queryset = queryset.filter(group_id__in=all_user_groups)

        # FIX: Ordina i post dal più recente al più vecchio e prefetch le relazioni
        return queryset.select_related('user', 'group').prefetch_related(
            'comments__user', 'likes__user', 'reactions__user'
        ).order_by('-created_at')

    def get_serializer_context(self):
        """Passa il context al serializer per calcolare i campi user-specific"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        """
        Verifica che l'utente possa creare post nel gruppo specificato
        """
        group_id = serializer.validated_data.get('group').id

        # Verifica che l'utente sia membro del gruppo o proprietario
        is_member = GroupMembership.objects.filter(
            user=self.request.user,
            group_id=group_id
        ).exists()

        is_owner = Group.objects.filter(
            id=group_id,
            owner=self.request.user
        ).exists()

        if not (is_member or is_owner):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Non hai il permesso di creare post in questo gruppo")

        # Log dell'immagine ricevuta
        image_url = serializer.validated_data.get('image_url', '')
        logger.info(f"Creating post with image_url length: {len(image_url)}")
        if image_url and image_url.startswith('data:image'):
            logger.info("Received base64 image for post")
        elif image_url:
            logger.info(f"Received image URL: {image_url[:50]}...")

        # Salva il post con l'utente corrente
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_like(self, request, pk=None):
        post = self.get_object()

        try:
            # Cerca se l'utente ha già messo like
            like = PostLike.objects.get(post=post, user=request.user)
            # Se esiste, rimuovi il like
            like.delete()
            liked = False
        except PostLike.DoesNotExist:
            # Se non esiste, crea il like
            PostLike.objects.create(post=post, user=request.user)
            liked = True

        # Restituisci lo stato aggiornato
        return Response({
            'liked': liked,
            'like_count': post.likes.count()
        })

    @action(detail=True, methods=['post'])
    def add_reaction(self, request, pk=None):
        """
        Aggiungi o cambia reaction per un post
        """
        post = self.get_object()
        reaction_emoji = request.data.get('reaction')

        if not reaction_emoji:
            return Response(
                {'error': 'Reaction emoji richiesta'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valida che la reaction sia tra quelle supportate
        valid_reactions = [choice[0] for choice in PostReaction.REACTION_CHOICES]
        if reaction_emoji not in valid_reactions:
            return Response(
                {'error': 'Reaction non valida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Cerca se l'utente ha già una reaction
            reaction = PostReaction.objects.get(post=post, user=request.user)
            if reaction.reaction == reaction_emoji:
                # Se è la stessa reaction, rimuovila
                reaction.delete()
                removed = True
                user_reaction = None
            else:
                # Se è diversa, aggiornala
                reaction.reaction = reaction_emoji
                reaction.save()
                removed = False
                user_reaction = reaction_emoji
        except PostReaction.DoesNotExist:
            # Se non esiste, crea la reaction
            PostReaction.objects.create(post=post, user=request.user, reaction=reaction_emoji)
            removed = False
            user_reaction = reaction_emoji

        # Conta tutte le reactions per questo post raggruppate per emoji
        from django.db.models import Count
        reactions_count = {}
        reactions_data = post.reactions.values('reaction').annotate(count=Count('reaction'))

        for reaction_data in reactions_data:
            reactions_count[reaction_data['reaction']] = reaction_data['count']

        return Response({
            'removed': removed,
            'user_reaction': user_reaction,
            'reactions_count': reactions_count
        })

    @action(detail=True, methods=['get'])
    def reactions(self, request, pk=None):
        """
        NUOVO: Ottieni tutte le reactions di un post con utenti che le hanno messe
        """
        post = self.get_object()
        reactions = post.reactions.all()

        # Raggruppa per emoji
        reactions_by_emoji = {}
        for reaction in reactions:
            emoji = reaction.reaction
            if emoji not in reactions_by_emoji:
                reactions_by_emoji[emoji] = []
            reactions_by_emoji[emoji].append({
                'user_id': reaction.user.id,
                'username': reaction.user.username,
                'created_at': reaction.created_at
            })

        return Response(reactions_by_emoji)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Verifica che l'utente possa commentare sul post
        """
        post = serializer.validated_data.get('post')
        group_id = post.group.id

        # Verifica che l'utente sia membro del gruppo
        is_member = GroupMembership.objects.filter(
            user=self.request.user,
            group_id=group_id
        ).exists()

        is_owner = Group.objects.filter(
            id=group_id,
            owner=self.request.user
        ).exists()

        if not (is_member or is_owner):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Non hai il permesso di commentare in questo gruppo")

        serializer.save(user=self.request.user)


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


# Funzioni per gestire punteggi e leaderboard (invariate)
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

    if game_id:
        best_score = GameScore.objects.filter(user=user, game_id=game_id).order_by('-score').first()

        if best_score is None:
            GameScore.objects.create(
                user=user,
                game_id=game_id,
                score=points
            )
            user.eco_points += points
            user.save()
        elif points > best_score.score:
            diff = points - best_score.score
            best_score.score = points
            best_score.save()
            user.eco_points += diff
            user.save()

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
    Ottiene la classifica globale o per gioco specifico
    """
    game_id = request.query_params.get('game_id', None)

    if game_id:
        from django.db.models import Max
        user_best_scores = GameScore.objects.filter(game_id=game_id).values('user').annotate(
            best_score=Max('score')
        ).order_by('-best_score')[:50]

        leaderboard_data = []
        for entry in user_best_scores:
            user = User.objects.get(id=entry['user'])
            leaderboard_data.append({
                'userId': user.id,
                'username': user.username,
                'score': entry['best_score'],
                'avatar': user.avatar  # Include avatar nella classifica
            })

        return Response(leaderboard_data)
    else:
        from django.db import connection

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

        leaderboard_data = []
        for row in rows:
            user_id, total_score = row
            try:
                user = User.objects.get(id=user_id)
                leaderboard_data.append({
                    'userId': user.id,
                    'username': user.username,
                    'ecoPoints': int(total_score),
                    'avatar': user.avatar  # Include avatar nella classifica
                })
            except User.DoesNotExist:
                pass

        return Response(leaderboard_data)