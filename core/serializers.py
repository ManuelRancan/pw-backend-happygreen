# core/serializers.py - Aggiornato con contatori reali

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


# AGGIORNATO: GroupSerializer con contatori reali
class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_at', 'owner', 'owner_name', 'member_count', 'post_count']

    def get_member_count(self, obj):
        """Conta il numero reale di membri nel gruppo"""
        return GroupMembership.objects.filter(group=obj).count()

    def get_post_count(self, obj):
        """Conta il numero reale di post nel gruppo"""
        return Post.objects.filter(group=obj).count()

    def get_owner_name(self, obj):
        """Restituisce il nome del proprietario"""
        return f"{obj.owner.first_name} {obj.owner.last_name}".strip() or obj.owner.username


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

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Formatta la data in ISO format
        if instance.created_at:
            representation['created_at'] = instance.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return representation

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

    # Aggiungiamo metodi per formattare le date
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Formatta le date in ISO format con timezone
        if instance.created_at:
            representation['created_at'] = instance.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Formatta le date dei commenti
        if 'comments' in representation:
            for comment in representation['comments']:
                if 'created_at' in comment:
                    # Recupera l'oggetto comment per formattare la data
                    comment_obj = instance.comments.filter(id=comment['id']).first()
                    if comment_obj:
                        comment['created_at'] = comment_obj.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return representation

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
    member_count = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_at', 'owner', 'owner_details', 'members', 'member_count',
                  'post_count']

    def get_members(self, obj):
        memberships = GroupMembership.objects.filter(group=obj)
        return GroupMembershipDetailSerializer(memberships, many=True).data

    def get_member_count(self, obj):
        """Conta il numero reale di membri nel gruppo"""
        return GroupMembership.objects.filter(group=obj).count()

    def get_post_count(self, obj):
        """Conta il numero reale di post nel gruppo"""
        return Post.objects.filter(group=obj).count()