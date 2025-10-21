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
    phone = models.CharField(max_length=20, blank=True, null=True)  # phone number
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
  
    def __str__(self):
        return self.username

class CourseCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
# --------------------------
# Course model
# --------------------------
class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('inprogress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    capacity = models.PositiveIntegerField(default=30)

    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )

    level = models.CharField(max_length=50, choices=LEVEL_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # ✅ Nouveau champ

    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    students = models.ManyToManyField(
        User,
        related_name='enrolled_courses',
        limit_choices_to={'role': 'student'},
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)  # Brève explication de la leçon
    order = models.PositiveIntegerField(default=0)  # Pour ordonner les leçons dans le cours
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Course: {self.course.title})"


class SubLesson(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='sub_lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)  # Texte explicatif ou cours écrit
    order = models.PositiveIntegerField(default=0)  # Pour garder l’ordre des sous-leçons
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Lesson: {self.lesson.title})"

class Resource(models.Model):
    RESOURCE_TYPES = (
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('audio', 'Audio'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)
    sub_lesson = models.ForeignKey(SubLesson, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)

    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to='lesson_resources/')
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)  # Pour définir l’ordre des fichiers dans la même section

    def __str__(self):
        return f"{self.title} ({self.resource_type})"


    
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
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises', null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.lesson.title}"

