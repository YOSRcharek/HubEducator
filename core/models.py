from django.db import models
from django.contrib.auth.models import AbstractUser

# --------------------------
# User model
# --------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    def __str__(self):
        return self.username


# --------------------------
# Course model
# --------------------------
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    students = models.ManyToManyField(User, related_name='enrolled_courses', limit_choices_to={'role': 'student'}, blank=True)

    def __str__(self):
        return self.title



# --------------------------
# Chapter model
# --------------------------
class Chapter(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)  # text content
    video = models.FileField(upload_to='chapter_videos/', null=True, blank=True)
    document = models.FileField(upload_to='chapter_docs/', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters')

    def __str__(self):
        return f"{self.title} - {self.course.title}"


# --------------------------
# Exercise model
# --------------------------
class Exercise(models.Model):
    EXERCISE_TYPE_CHOICES = (
        ('mcq', 'Multiple Choice Question'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('open', 'Open Problem'),
    )
    title = models.CharField(max_length=200)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES)
    statement = models.TextField()
    correction = models.TextField()
    generated_by = models.CharField(max_length=20, choices=(('AI', 'AI'), ('Teacher', 'Teacher')), default='Teacher')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='exercises')

    def __str__(self):
        return f"{self.title} - {self.chapter.title}"
