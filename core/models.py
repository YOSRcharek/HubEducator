from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
# --------------------------
# User model
# --------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    phone = models.CharField(max_length=20, blank=True, null=True)  # phone number
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


# --------------------------
# Speciality model
# --------------------------
class Speciality(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# --------------------------
# Certificate model
# --------------------------
class Certificate(models.Model):
    title = models.CharField(max_length=150)
    speciality = models.ForeignKey(Speciality, on_delete=models.SET_NULL, null=True, related_name='certificates')
    students = models.ManyToManyField(User, related_name='certificates', limit_choices_to={'role': 'student'}, blank=True)
    date_created = models.DateField(default=timezone.now)
    valid = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.speciality.name if self.speciality else 'No Speciality'}"


# --------------------------
# Certificate Block model
# --------------------------
class CertificateBlock(models.Model):
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='blocks')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} ({self.certificate.title})"


# --------------------------
# Question model (for Certificate)
# --------------------------
class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('mcq', 'Multiple Choice'),
        ('checkbox', 'Checkbox')
    ]
    block = models.ForeignKey(CertificateBlock, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, default='text')
    options = models.JSONField(blank=True, null=True)  # for MCQ or Checkbox

    def __str__(self):
        return f"{self.text} ({self.block.title})"


# --------------------------
# Answer model
# --------------------------
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers', limit_choices_to={'role': 'student'})
    answer = models.TextField()

    def __str__(self):
        return f"Answer by {self.student.username} to {self.question.text}"
