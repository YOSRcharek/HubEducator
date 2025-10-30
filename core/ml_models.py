from django.db import models
from django.contrib.auth import get_user_model
from .models import Subscription

User = get_user_model()


# --------------------------
# ML Recommendation Models
# --------------------------
class UserPreference(models.Model):
    """Store user preferences for ML recommendation"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ml_preference')
    
    # Numeric features
    student_count = models.IntegerField(default=0, help_text="Number of students (for teachers)")
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_frequency = models.IntegerField(default=1, help_text="Days per week (1-7)")
    course_count = models.IntegerField(default=0, help_text="Number of courses")
    experience_level = models.IntegerField(default=1, help_text="1=Beginner, 5=Expert")
    study_hours = models.DecimalField(max_digits=4, decimal_places=1, default=0, help_text="Hours per day")
    
    # Boolean features (needs)
    needs_video = models.BooleanField(default=False)
    needs_quiz = models.BooleanField(default=False)
    needs_forum = models.BooleanField(default=False)
    needs_analytics = models.BooleanField(default=False)
    needs_certificates = models.BooleanField(default=False)
    needs_offline = models.BooleanField(default=False)
    needs_support = models.BooleanField(default=False)
    
    # Categorical features
    GOAL_CHOICES = [
        ('professional', 'Professional Development'),
        ('academic', 'Academic Achievement'),
        ('personal', 'Personal Interest'),
    ]
    goal_type = models.CharField(max_length=20, choices=GOAL_CHOICES, default='academic')
    
    LEVEL_CHOICES = [
        ('high_school', 'High School'),
        ('university', 'University'),
        ('professional', 'Professional Training'),
    ]
    education_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='university')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
    
    @property
    def intensity_score(self):
        """Calculate usage intensity"""
        return float(self.usage_frequency * self.study_hours) / 10.0
    
    @property
    def feature_demand(self):
        """Calculate percentage of features needed"""
        total_features = 7
        needed = sum([
            self.needs_video, self.needs_quiz, self.needs_forum,
            self.needs_analytics, self.needs_certificates, 
            self.needs_offline, self.needs_support
        ])
        return needed / total_features


class RecommendationHistory(models.Model):
    """Track ML recommendations and their outcomes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    preference = models.ForeignKey(UserPreference, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Recommendation details
    recommended_subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='ml_recommendations')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="ML model confidence (0-100)")
    compatibility_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Overall compatibility (0-100)")
    
    # Alternative recommendations
    alternative_1 = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='alt1_recommendations')
    alternative_1_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    alternative_2 = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='alt2_recommendations')
    alternative_2_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # User action
    ACTION_CHOICES = [
        ('accepted', 'Accepted Recommendation'),
        ('alternative', 'Chose Alternative'),
        ('ignored', 'Ignored Recommendation'),
        ('pending', 'Pending Decision'),
    ]
    user_action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='pending')
    chosen_subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='chosen_recommendations')
    
    # Feedback
    satisfaction_rating = models.IntegerField(null=True, blank=True, help_text="1-5 stars")
    feedback_text = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    feedback_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Recommendation Histories'
    
    def __str__(self):
        return f"Recommendation for {self.user.email} - {self.recommended_subscription.name} ({self.compatibility_score}%)"
    
    @property
    def was_accurate(self):
        """Check if recommendation was accurate"""
        if self.user_action == 'accepted':
            return True
        elif self.user_action == 'alternative' and self.chosen_subscription in [self.alternative_1, self.alternative_2]:
            return True
        return False
