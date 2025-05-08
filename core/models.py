import random

from django.db import models
from django.contrib.auth.models import AbstractUser

# core/models.py - Update the User model
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    avatar = models.TextField(blank=True, null=True)
    eco_points = models.IntegerField(default=0)
    date_joined = models.DateTimeField(auto_now_add=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    verification_token_expires = models.DateTimeField(blank=True, null=True)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    verification_code_expires = models.DateTimeField(null=True, blank=True)
    def set_verification_token(self):
        """Genera un nuovo token di verifica e imposta la scadenza (24 ore)"""
        self.verification_token = uuid.uuid4()
        self.verification_token_expires = timezone.now() + timedelta(hours=24)
        self.save()

    def verify_email(self):
        """Segna l'email dell'utente come verificata"""
        self.email_verified = True
        self.verification_token = None
        self.verification_token_expires = None
        self.save()

    def is_token_valid(self):
        """Controlla se il token di verifica è ancora valido"""
        if not self.verification_token_expires:
            return False
        return timezone.now() <= self.verification_token_expires

    def set_verification_code(self):
        """Genera un nuovo codice di verifica"""
        self.verification_code = ''.join(random.choices('0123456789', k=6))
        self.verification_code_expires = timezone.now() + timedelta(minutes=10)
        self.save()

    def verify_with_code(self, code):
        """Verifica l'utente con il codice OTP"""
        if (self.verification_code == code and
                self.verification_code_expires and
                timezone.now() <= self.verification_code_expires):
            self.email_verified = True
            self.is_active = True  # Attiva l'utente dopo la verifica
            self.verification_code = None
            self.verification_code_expires = None
            self.save()
            return True
        return False

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