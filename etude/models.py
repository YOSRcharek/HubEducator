from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import os
import uuid

def validate_resource_file(value):
    """Allow only common document types and limit size (optional)."""
    ext = os.path.splitext(value.name)[1].lower()
    allowed = {'.pdf', '.doc', '.docx', '.ppt', '.pptx'}
    if ext not in allowed:
        raise ValidationError("Unsupported file type. Allowed: pdf, doc, docx, ppt, pptx.")
    max_mb = 25
    if hasattr(value, 'size') and value.size > max_mb * 1024 * 1024:
        raise ValidationError(f"File too large (max {max_mb} MB).")
        
class GroupeEtude(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    membres = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="groupes_rejoints", blank=True)

User = get_user_model()

class Message(models.Model):
    groupe = models.ForeignKey(GroupeEtude, on_delete=models.CASCADE, related_name="messages")
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.auteur.username}: {self.contenu[:30]}"
class ResourceEtude(models.Model):
    groupe = models.ForeignKey(GroupeEtude, on_delete=models.CASCADE, related_name='resources_etude')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='resources_etude/etude/%Y/%m', validators=[validate_resource_file])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or (self.file.name.split('/')[-1])

class Meeting(models.Model):
    groupe = models.ForeignKey(GroupeEtude, related_name="meetings", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    meet_link = models.URLField(blank=True, null=True)
    event_id = models.CharField(max_length=255, blank=True, null=True)  # 🔹 make nullable

    def __str__(self):
        return self.title

