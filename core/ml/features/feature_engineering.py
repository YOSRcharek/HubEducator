"""
Feature engineering for subscription ML models.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from core.models import UserSubscription, Transaction, Course


class FeatureEngineer:
    """Extract and engineer features for ML models."""
    
    @staticmethod
    def extract_subscription_features(subscription):
        """
        Extract features for a single subscription.
        
        Args:
            subscription: UserSubscription instance
            
        Returns:
            dict: Feature dictionary
        """
        now = timezone.now()
        user = subscription.user
        
        # Basic subscription features
        features = {
            'subscription_id': subscription.id,
            'user_id': user.id,
            'plan_type': 1 if subscription.subscription.user_type == 'student' else 2,  # Encoded
            'subscription_age_days': (now - subscription.start_date).days,
            'days_until_end': (subscription.end_date - now).days if subscription.end_date else 365,
            'is_active': 1 if subscription.is_active else 0,
            'amount': float(subscription.subscription.price),
        }
        
        # User account features
        features['account_age_days'] = (now - user.date_joined).days
        features['is_teacher'] = 1 if user.role == 'teacher' else 0
        features['is_student'] = 1 if user.role == 'student' else 0
        
        # Transaction history features
        transactions = Transaction.objects.filter(user=user)
        features['total_transactions'] = transactions.count()
        features['total_spent'] = float(transactions.aggregate(
            total=Sum('amount'))['total'] or 0)
        features['avg_transaction_amount'] = float(transactions.aggregate(
            avg=Avg('amount'))['avg'] or 0)
        
        # Calculate transaction frequency
        if transactions.exists():
            first_transaction = transactions.order_by('created_at').first()
            transaction_days = (now - first_transaction.created_at).days
            features['transaction_frequency'] = (
                features['total_transactions'] / max(transaction_days, 1)
            )
            
            # Days since last transaction
            last_transaction = transactions.order_by('-created_at').first()
            features['days_since_last_payment'] = (
                now - last_transaction.created_at
            ).days
        else:
            features['transaction_frequency'] = 0
            features['days_since_last_payment'] = 9999
        
        # Course engagement features
        # Note: Simplified version - can be enhanced when enrollment tracking is added
        if features['is_teacher']:
            # Count courses created by this teacher
            try:
                courses_created = Course.objects.filter(teacher=user).count()
                features['courses_created'] = courses_created
                features['avg_course_students'] = 0  # Placeholder - needs enrollment model
            except:
                features['courses_created'] = 0
                features['avg_course_students'] = 0
        else:
            features['courses_created'] = 0
            features['avg_course_students'] = 0
        
        # Student engagement features - placeholder for now
        # These can be enhanced when enrollment tracking is implemented
        features['courses_enrolled'] = 0
        features['courses_completed'] = 0
        features['completion_rate'] = 0
        
        # Temporal features
        features['signup_month'] = subscription.start_date.month
        features['signup_day_of_week'] = subscription.start_date.weekday()
        features['signup_quarter'] = (subscription.start_date.month - 1) // 3 + 1
        
        # Renewal features
        user_subscriptions = UserSubscription.objects.filter(user=user)
        features['total_subscriptions'] = user_subscriptions.count()
        features['renewal_count'] = max(features['total_subscriptions'] - 1, 0)
        
        # Activity recency features (last 7, 30, 90 days)
        features['transactions_last_7d'] = transactions.filter(
            created_at__gte=now - timedelta(days=7)
        ).count()
        features['transactions_last_30d'] = transactions.filter(
            created_at__gte=now - timedelta(days=30)
        ).count()
        features['transactions_last_90d'] = transactions.filter(
            created_at__gte=now - timedelta(days=90)
        ).count()
        
        return features
    
    @staticmethod
    def create_training_dataset(include_churned=True):
        """
        Create a complete training dataset from all subscriptions.
        
        Args:
            include_churned: Include expired/cancelled subscriptions
            
        Returns:
            pd.DataFrame: Training dataset
        """
        subscriptions = UserSubscription.objects.select_related('user', 'subscription').all()
        
        if not include_churned:
            subscriptions = subscriptions.filter(is_active=True)
        
        data = []
        for subscription in subscriptions:
            try:
                features = FeatureEngineer.extract_subscription_features(subscription)
                
                # Add target variable for churn prediction
                # Churned = subscription is not active or end_date has passed
                now = timezone.now()
                is_expired = subscription.end_date < now if subscription.end_date else False
                features['churned'] = 1 if (not subscription.is_active or is_expired) else 0
                
                data.append(features)
            except Exception as e:
                print(f"Error processing subscription {subscription.id}: {e}")
                continue
        
        df = pd.DataFrame(data)
        return df
    
    @staticmethod
    def prepare_features_for_prediction(df):
        """
        Prepare features for model prediction.
        
        Args:
            df: DataFrame with raw features
            
        Returns:
            pd.DataFrame: Processed features ready for prediction
        """
        # Select feature columns (exclude IDs and target)
        feature_columns = [
            'plan_type', 'subscription_age_days', 'days_until_end',
            'is_active', 'amount', 'account_age_days', 'is_teacher',
            'is_student', 'total_transactions', 'total_spent',
            'avg_transaction_amount', 'transaction_frequency',
            'days_since_last_payment', 'courses_created',
            'avg_course_students', 'courses_enrolled', 'courses_completed',
            'completion_rate', 'signup_month', 'signup_day_of_week',
            'signup_quarter', 'total_subscriptions', 'renewal_count',
            'transactions_last_7d', 'transactions_last_30d',
            'transactions_last_90d'
        ]
        
        # Handle missing values
        X = df[feature_columns].fillna(0)
        
        # Handle infinite values
        X = X.replace([np.inf, -np.inf], 0)
        
        return X
    
    @staticmethod
    def get_feature_importance_names():
        """Return list of feature names in order."""
        return [
            'plan_type', 'subscription_age_days', 'days_until_end',
            'is_active', 'amount', 'account_age_days', 'is_teacher',
            'is_student', 'total_transactions', 'total_spent',
            'avg_transaction_amount', 'transaction_frequency',
            'days_since_last_payment', 'courses_created',
            'avg_course_students', 'courses_enrolled', 'courses_completed',
            'completion_rate', 'signup_month', 'signup_day_of_week',
            'signup_quarter', 'total_subscriptions', 'renewal_count',
            'transactions_last_7d', 'transactions_last_30d',
            'transactions_last_90d'
        ]
