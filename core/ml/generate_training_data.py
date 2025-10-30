"""
Generate synthetic training data for subscription recommendation model
"""

import numpy as np
import pandas as pd
import random


def generate_training_data(n_samples=1000):
    """Generate synthetic training data for subscription recommendations"""
    
    data = []
    
    for i in range(n_samples):
        # Randomly decide user type
        is_teacher = random.choice([0, 1])
        
        if is_teacher:
            # Teacher profile
            student_count = random.choice([
                random.randint(1, 15),      # Small class
                random.randint(15, 40),     # Medium class
                random.randint(40, 80),     # Large class
                random.randint(80, 150)     # Very large class
            ])
            course_count = random.randint(1, 20)
            budget = random.uniform(20, 150)
            
        else:
            # Student profile
            student_count = 0
            course_count = random.randint(1, 8)
            budget = random.uniform(5, 80)
        
        # Common features
        usage_frequency = random.randint(1, 7)
        experience_level = random.randint(1, 5)
        study_hours = random.uniform(0.5, 8)
        
        # Feature needs (correlated with budget and intensity)
        intensity = (usage_frequency * study_hours) / 10.0
        high_needs_prob = min(0.9, (budget / 100) * 0.5 + intensity * 0.5)
        
        needs_video = random.random() < high_needs_prob
        needs_quiz = random.random() < high_needs_prob
        needs_forum = random.random() < (high_needs_prob * 0.7)
        needs_analytics = random.random() < (high_needs_prob * 0.8) if is_teacher else random.random() < 0.3
        needs_certificates = random.random() < 0.6
        needs_offline = random.random() < (high_needs_prob * 0.6)
        needs_support = random.random() < (high_needs_prob * 0.7)
        
        # Calculate derived features
        intensity_score = intensity
        feature_demand = sum([needs_video, needs_quiz, needs_forum, needs_analytics, 
                            needs_certificates, needs_offline, needs_support]) / 7.0
        
        # Determine target label (subscription type) based on rules
        if is_teacher:
            if student_count > 50 or budget > 80:
                label = 'Premium'
            elif student_count > 20 or budget > 40:
                label = 'Standard'
            else:
                label = 'Basic'
        else:
            if budget > 50 and feature_demand > 0.6:
                label = 'Premium'
            elif budget > 25 or (feature_demand > 0.4 and intensity > 0.5):
                label = 'Standard'
            else:
                label = 'Basic'
        
        # Add some randomness (10% chance to change label)
        if random.random() < 0.1:
            label = random.choice(['Basic', 'Standard', 'Premium'])
        
        # Create sample
        sample = {
            'student_count': student_count,
            'budget': round(budget, 2),
            'usage_frequency': usage_frequency,
            'course_count': course_count,
            'experience_level': experience_level,
            'study_hours': round(study_hours, 1),
            'needs_video': int(needs_video),
            'needs_quiz': int(needs_quiz),
            'needs_forum': int(needs_forum),
            'needs_analytics': int(needs_analytics),
            'needs_certificates': int(needs_certificates),
            'needs_offline': int(needs_offline),
            'needs_support': int(needs_support),
            'intensity_score': round(intensity_score, 2),
            'feature_demand': round(feature_demand, 2),
            'is_teacher': is_teacher,
            'label': label
        }
        
        data.append(sample)
    
    return pd.DataFrame(data)


def save_training_data(filename='subscription_training_data.csv', n_samples=1000):
    """Generate and save training data to CSV"""
    df = generate_training_data(n_samples)
    df.to_csv(filename, index=False)
    print(f"Generated {n_samples} training samples")
    print(f"Saved to {filename}")
    print(f"\nLabel distribution:")
    print(df['label'].value_counts())
    print(f"\nUser type distribution:")
    print(f"Teachers: {df['is_teacher'].sum()}")
    print(f"Students: {(1 - df['is_teacher']).sum()}")
    return df


if __name__ == '__main__':
    import os
    from django.conf import settings
    
    # Save in ml folder
    output_path = os.path.join(settings.BASE_DIR, 'core', 'ml', 'data', 'subscription_training_data.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df = save_training_data(output_path, n_samples=1000)
    print(f"\nFirst few samples:")
    print(df.head())
