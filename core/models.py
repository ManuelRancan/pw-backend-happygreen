from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    avatar = models.TextField(blank=True, null=True)
    eco_points = models.IntegerField(default=0)
    date_joined = models.DateTimeField(auto_now_add=True)

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')

    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    image_url = models.TextField()
    caption = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class DetectedObject(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    label = models.CharField(max_length=100)
    description = models.TextField()
    recycle_tips = models.TextField()

class Quiz(models.Model):
    question = models.TextField()
    correct_answer = models.TextField()
    options = models.JSONField()

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_url = models.TextField()

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)