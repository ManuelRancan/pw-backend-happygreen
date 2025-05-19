# serializers.py - Aggiornato con Like e Reactions

from rest_framework import serializers
from .models import User, Group, GroupMembership, Post, Comment, DetectedObject, Quiz, Badge, UserBadge, GameScore, \
    PostLike, PostReaction


class GameScoreSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username

    class Meta:
        model = GameScore
        fields = ['id', 'user', 'username', 'game_id', 'score', 'timestamp']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'eco_points', 'date_joined', 'email_verified'
        ]
        read_only_fields = ['email_verified']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class GroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembership
        fields = '__all__'


# NUOVO: Serializer per PostLike
class PostLikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = ['id', 'user', 'created_at']


# NUOVO: Serializer per PostReaction
class PostReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PostReaction
        fields = ['id', 'user', 'reaction', 'created_at']


# AGGIORNATO: Serializer per Comment con user details
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'content', 'created_at']


# AGGIORNATO: Serializer per Post con like, reactions e commenti
class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes = PostLikeSerializer(many=True, read_only=True)
    reactions = PostReactionSerializer(many=True, read_only=True)

    # Campi calcolati
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    user_liked = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_user_liked(self, obj):
        """Verifica se l'utente corrente ha messo like al post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_user_reaction(self, obj):
        """Ottiene la reaction dell'utente corrente al post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            return reaction.reaction if reaction else None
        return None

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'group', 'image_url', 'caption', 'latitude', 'longitude',
            'created_at', 'comments', 'likes', 'reactions', 'like_count',
            'comment_count', 'user_liked', 'user_reaction'
        ]


class DetectedObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectedObject
        fields = '__all__'


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = '__all__'


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'


class UserBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBadge
        fields = '__all__'


class LeaderboardUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'eco_points']


# serializers.py - Aggiungiamo nuovi serializers

class GroupMembershipDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupMembership
        fields = ['id', 'user', 'role', 'joined_at']


class GroupDetailSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    owner_details = UserSerializer(source='owner', read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_at', 'owner', 'owner_details', 'members']

    def get_members(self, obj):
        memberships = GroupMembership.objects.filter(group=obj)
        return GroupMembershipDetailSerializer(memberships, many=True).data