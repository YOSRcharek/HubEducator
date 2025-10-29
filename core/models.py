from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
# --------------------------
# User model
# --------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    phone = models.CharField(max_length=20, blank=True, null=True)  # phone number
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
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
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    students = models.ManyToManyField(User, related_name='enrolled_courses', limit_choices_to={'role': 'student'}, blank=True)
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
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
    visible = models.BooleanField(default=False)  # Nouveau champ
    publish_date = models.DateTimeField(null=True, blank=True)
    max_lessons = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

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
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=False)  # Nouveau champ
    max_sublessons = models.PositiveIntegerField(default=5) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Course: {self.course.title})"


class SubLesson(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='sub_lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=False)  # Nouveau champ
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Lesson: {self.lesson.title})"

class Resource(models.Model):
    RESOURCE_TYPES = (
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('external', 'External Link'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)
    sub_lesson = models.ForeignKey(SubLesson, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)

    # pour les fichiers internes
    file = models.FileField(upload_to='lesson_resources/', null=True, blank=True)

    # pour les ressources externes (YouTube, Google Docs, etc.)
    external_url = models.URLField(blank=True, null=True)

    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.resource_type})"

    def get_embed_url(self):
        """Retourne une version intégrable selon le type de lien."""
        if self.resource_type == 'external' and self.external_url:
            url = self.external_url
            if 'youtube.com/watch?v=' in url:
                video_id = url.split('watch?v=')[-1]
                return f"https://www.youtube.com/embed/{video_id}"
            elif 'docs.google.com' in url:
                return url.replace('/edit', '/preview')
        return self.external_url


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', limit_choices_to={'role': 'student'})
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(User, related_name='liked_reviews', blank=True)  # <- les utilisateurs qui ont liké

    def __str__(self):
        return f"{self.student.username} - {self.course.title} ({self.rating}★)"

    @property
    def helpful_count(self):
        return self.likes.count()
   
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
    title = models.CharField(max_length=200)
    description = models.TextField()
    speciality = models.ForeignKey('Speciality', on_delete=models.CASCADE)
    cover_image = models.URLField()  # Champ image ajouté
class CertificatExercise(models.Model):
    TYPE_CHOICES = [
        ('qcu', 'QCU'),  # Changed 'qcm' to 'qcu' here
        ('truefalse', 'True/False'),
        ('text', 'Text'),
    ]

    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='exercises')
    exercise_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    question = models.CharField(max_length=500, blank=True, null=True)
    correct_answer = models.CharField(max_length=200, blank=True, null=True)
    option1 = models.CharField(max_length=200, blank=True, null=True)
    option2 = models.CharField(max_length=200, blank=True, null=True)
    option3 = models.CharField(max_length=200, blank=True, null=True)
    option4 = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Exercise for {self.certificate.title} - {self.exercise_type}"


# --------------------------
# Certificate Attempt model
# --------------------------
class CertificateAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.certificate.title} - {self.score}/{self.total_questions}"


class CertificateAnswer(models.Model):
    attempt = models.ForeignKey(CertificateAttempt, on_delete=models.CASCADE, related_name='answers')
    exercise = models.ForeignKey(CertificatExercise, on_delete=models.CASCADE)
    answer = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer for {self.exercise.question} - Correct: {self.is_correct}"


# --------------------------
# Subscription model
# --------------------------
class Subscription(models.Model):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=100, help_text="e.g., 30 days, 3 months, 1 year")
    features = models.TextField(help_text="Enter features separated by new lines")
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student', help_text="Type of user this subscription is for")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - {self.get_user_type_display()} - {self.duration}"
    
    def get_features_list(self):
        """Return features as a list"""
        return [feature.strip() for feature in self.features.split('\n') if feature.strip()]


# --------------------------
# Transaction model (for payment tracking)
# --------------------------
class Transaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, related_name='transactions')
    
    # Stripe information
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Transaction details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription.name if self.subscription else 'N/A'} - ${self.amount} - {self.status}"


# --------------------------
# UserSubscription model (to track active subscriptions)
# --------------------------
class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_subscriptions')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='user_subscriptions')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'subscription', 'start_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription.name} - {'Active' if self.is_active else 'Inactive'}"
