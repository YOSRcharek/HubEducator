from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

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
        return self.nom
        # return f"{self.auteur.username}: {self.contenu[:30]}"
