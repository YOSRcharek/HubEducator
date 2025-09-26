from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return self.username
