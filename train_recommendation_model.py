"""
Train the subscription recommendation ML model
Run this script to train the model with synthetic data
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.ml.generate_training_data import generate_training_data
from core.ml.recommendation_engine import recommender
import pandas as pd


def train_model():
    """Train the recommendation model"""
    print("=" * 60)
    print("SUBSCRIPTION RECOMMENDATION MODEL TRAINING")
    print("=" * 60)
    
    # Generate training data
    print("\n[1/4] Generating training data...")
    df = generate_training_data(n_samples=1000)
    
    print(f"\nDataset Info:")
    print(f"  Total samples: {len(df)}")
    print(f"  Features: {len(df.columns) - 1}")
    print(f"\nLabel Distribution:")
    print(df['label'].value_counts())
    
    # Prepare features and labels
    print("\n[2/4] Preparing features and labels...")
    feature_columns = [
        'student_count', 'budget', 'usage_frequency', 'course_count',
        'experience_level', 'study_hours', 'needs_video', 'needs_quiz',
        'needs_forum', 'needs_analytics', 'needs_certificates',
        'needs_offline', 'needs_support', 'intensity_score',
        'feature_demand', 'is_teacher'
    ]
    
    X = df[feature_columns]
    y = df['label']
    
    # Train model
    print("\n[3/4] Training Random Forest model...")
    results = recommender.train(X, y)
    
    print(f"\n[4/4] Training complete!")
    print(f"\nModel Performance:")
    print(f"  Training Accuracy: {results['train_accuracy']:.2%}")
    print(f"  Testing Accuracy: {results['test_accuracy']:.2%}")
    
    print(f"\nTop 5 Most Important Features:")
    feature_importance = sorted(
        results['feature_importance'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for i, (feature, importance) in enumerate(feature_importance[:5], 1):
        print(f"  {i}. {feature}: {importance:.4f}")
    
    print("\n" + "=" * 60)
    print("✅ Model trained and saved successfully!")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    train_model()
