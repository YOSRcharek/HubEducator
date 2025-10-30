"""
ML Recommendation Engine for Subscription Plans
Uses Random Forest Classifier to recommend the best subscription plan
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from django.conf import settings


class SubscriptionRecommender:
    """ML-based subscription recommendation system"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'student_count', 'budget', 'usage_frequency', 'course_count',
            'experience_level', 'study_hours', 'needs_video', 'needs_quiz',
            'needs_forum', 'needs_analytics', 'needs_certificates',
            'needs_offline', 'needs_support', 'intensity_score',
            'feature_demand', 'is_teacher'
        ]
        self.model_path = os.path.join(settings.BASE_DIR, 'core', 'ml', 'trained_models', 'subscription_recommender.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'core', 'ml', 'trained_models', 'scaler.pkl')
        
    def prepare_features(self, preference, user_type='student'):
        """Convert UserPreference object to feature vector"""
        features = {
            'student_count': float(preference.student_count),
            'budget': float(preference.budget),
            'usage_frequency': float(preference.usage_frequency),
            'course_count': float(preference.course_count),
            'experience_level': float(preference.experience_level),
            'study_hours': float(preference.study_hours),
            'needs_video': int(preference.needs_video),
            'needs_quiz': int(preference.needs_quiz),
            'needs_forum': int(preference.needs_forum),
            'needs_analytics': int(preference.needs_analytics),
            'needs_certificates': int(preference.needs_certificates),
            'needs_offline': int(preference.needs_offline),
            'needs_support': int(preference.needs_support),
            'intensity_score': preference.intensity_score,
            'feature_demand': preference.feature_demand,
            'is_teacher': 1 if user_type == 'teacher' else 0
        }
        return pd.DataFrame([features])[self.feature_names]
    
    def train(self, X, y):
        """Train the Random Forest model"""
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        print(f"Training Accuracy: {train_score:.2%}")
        print(f"Testing Accuracy: {test_score:.2%}")
        
        # Save model
        self.save_model()
        
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
        }
    
    def predict(self, preference, user_type='student'):
        """Predict best subscription for given preferences"""
        if self.model is None:
            self.load_model()
        
        # Prepare features
        X = self.prepare_features(preference, user_type)
        X_scaled = self.scaler.transform(X)
        
        # Get prediction and probabilities
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        # Get class labels
        classes = self.model.classes_
        
        # Create results with probabilities
        results = []
        for cls, prob in zip(classes, probabilities):
            results.append({
                'subscription_name': cls,
                'probability': float(prob),
                'confidence': float(prob * 100)
            })
        
        # Sort by probability
        results = sorted(results, key=lambda x: x['probability'], reverse=True)
        
        return {
            'recommended': results[0]['subscription_name'],
            'confidence': results[0]['confidence'],
            'all_predictions': results
        }
    
    def calculate_compatibility_score(self, preference, subscription, user_type='student'):
        """Calculate detailed compatibility score between preference and subscription"""
        score = 0
        max_score = 100
        
        # Budget fit (30 points)
        subscription_price = float(subscription.price)
        budget = float(preference.budget)
        if budget >= subscription_price:
            budget_score = 30
        elif budget >= subscription_price * 0.8:
            budget_score = 25
        elif budget >= subscription_price * 0.6:
            budget_score = 15
        else:
            budget_score = 5
        score += budget_score
        
        # Feature match (40 points)
        # This is simplified - in production, you'd match against actual subscription features
        feature_demand = preference.feature_demand
        if 'premium' in subscription.name.lower():
            feature_match = feature_demand * 40
        elif 'standard' in subscription.name.lower():
            feature_match = min(feature_demand * 40, 35) if feature_demand <= 0.7 else feature_demand * 30
        else:  # basic
            feature_match = (1 - feature_demand) * 40
        score += feature_match
        
        # Usage intensity fit (20 points)
        intensity = preference.intensity_score
        if 'premium' in subscription.name.lower():
            intensity_score = min(intensity * 4, 20)
        elif 'standard' in subscription.name.lower():
            intensity_score = 15 if 0.3 <= intensity <= 0.7 else 10
        else:
            intensity_score = 20 if intensity < 0.3 else 5
        score += intensity_score
        
        # User type match (10 points)
        if subscription.user_type == user_type:
            score += 10
        
        return min(score, max_score)
    
    def get_recommendations(self, preference, user_type='student', subscriptions=None):
        """Get full recommendations with alternatives"""
        from core.models import Subscription
        
        if subscriptions is None:
            subscriptions = Subscription.objects.filter(
                user_type=user_type,
                is_active=True
            ).order_by('price')
        
        # Get ML prediction
        ml_result = self.predict(preference, user_type)
        
        # Calculate compatibility for all subscriptions
        recommendations = []
        for sub in subscriptions:
            compatibility = self.calculate_compatibility_score(preference, sub, user_type)
            
            # Boost score if it matches ML prediction
            if sub.name == ml_result['recommended']:
                ml_boost = ml_result['confidence'] * 0.3
                final_score = min(compatibility + ml_boost, 100)
            else:
                final_score = compatibility
            
            recommendations.append({
                'subscription': sub,
                'compatibility_score': round(final_score, 2),
                'ml_confidence': ml_result['confidence'] if sub.name == ml_result['recommended'] else 0,
                'is_recommended': sub.name == ml_result['recommended']
            })
        
        # Sort by compatibility score
        recommendations = sorted(recommendations, key=lambda x: x['compatibility_score'], reverse=True)
        
        return {
            'primary': recommendations[0] if recommendations else None,
            'alternatives': recommendations[1:3] if len(recommendations) > 1 else [],
            'all': recommendations,
            'ml_prediction': ml_result
        }
    
    def save_model(self):
        """Save trained model and scaler"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model and scaler"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            print("Model loaded successfully")
        else:
            raise FileNotFoundError("Trained model not found. Please train the model first.")
    
    def get_feature_importance(self):
        """Get feature importance from trained model"""
        if self.model is None:
            self.load_model()
        
        importance = dict(zip(self.feature_names, self.model.feature_importances_))
        return sorted(importance.items(), key=lambda x: x[1], reverse=True)


# Global instance
recommender = SubscriptionRecommender()
