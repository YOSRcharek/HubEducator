"""
Churn prediction model for user subscriptions.
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, GridSearchCV
from django.conf import settings

from core.ml.features.feature_engineering import FeatureEngineer
from core.ml.utils.data_preprocessing import DataPreprocessor
from core.ml.utils.model_evaluator import ModelEvaluator


class ChurnPredictor:
    """
    Predict subscription churn probability.
    
    Churn is defined as a subscription that has been cancelled or expired.
    """
    
    MODEL_DIR = os.path.join(settings.BASE_DIR, 'core', 'ml', 'trained_models')
    MODEL_FILE = 'churn_predictor.pkl'
    SCALER_FILE = 'churn_scaler.pkl'
    METADATA_FILE = 'churn_metadata.pkl'
    
    def __init__(self, model_type='random_forest'):
        """
        Initialize churn predictor.
        
        Args:
            model_type: 'random_forest', 'gradient_boosting', or 'logistic'
        """
        self.model_type = model_type
        self.model = self._create_model(model_type)
        self.preprocessor = DataPreprocessor(scaling_method='standard')
        self.feature_engineer = FeatureEngineer()
        self.is_trained = False
        self.metadata = {}
        
        # Create model directory if it doesn't exist
        os.makedirs(self.MODEL_DIR, exist_ok=True)
    
    def _create_model(self, model_type):
        """Create ML model based on type."""
        if model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        elif model_type == 'logistic':
            return LogisticRegression(
                max_iter=1000,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def train(self, optimize_hyperparameters=False, handle_imbalance=True):
        """
        Train the churn prediction model.
        
        Args:
            optimize_hyperparameters: Whether to perform grid search
            handle_imbalance: Whether to handle class imbalance
            
        Returns:
            dict: Training metrics
        """
        print("Creating training dataset...")
        df = self.feature_engineer.create_training_dataset(include_churned=True)
        
        if df.empty or len(df) < 5:
            raise ValueError("Insufficient data for training. Need at least 5 samples.")
        
        print(f"Dataset created: {len(df)} samples")
        print(f"Churn distribution:\n{df['churned'].value_counts()}")
        
        # Prepare features and target
        X = self.feature_engineer.prepare_features_for_prediction(df)
        y = df['churned'].values
        
        # Split data
        X_train, X_test, y_train, y_test = DataPreprocessor.split_data(
            X, y, test_size=0.2
        )
        
        # Handle class imbalance
        if handle_imbalance and len(np.unique(y_train)) > 1:
            print("Handling class imbalance...")
            X_train, y_train = DataPreprocessor.handle_imbalanced_data(
                X_train, y_train, method='oversample'
            )
        
        # Scale features
        print("Scaling features...")
        X_train_scaled = self.preprocessor.fit_transform(X_train)
        X_test_scaled = self.preprocessor.transform(X_test)
        
        # Hyperparameter optimization
        if optimize_hyperparameters:
            print("Optimizing hyperparameters...")
            self.model = self._optimize_hyperparameters(X_train_scaled, y_train)
        
        # Train model
        print("Training model...")
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        print("Evaluating model...")
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        metrics = ModelEvaluator.evaluate_classification(
            y_test, y_pred, y_pred_proba
        )
        
        # Cross-validation score
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=5, scoring='roc_auc'
        )
        metrics['cv_mean_auc'] = cv_scores.mean()
        metrics['cv_std_auc'] = cv_scores.std()
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            feature_names = self.feature_engineer.get_feature_importance_names()
            importances = self.model.feature_importances_
            
            # Sort by importance
            indices = np.argsort(importances)[::-1]
            metrics['feature_importance'] = {
                feature_names[i]: float(importances[i])
                for i in indices[:10]  # Top 10 features
            }
        
        # Save metadata
        self.metadata = {
            'trained_at': datetime.now().isoformat(),
            'model_type': self.model_type,
            'n_samples': len(df),
            'n_features': X.shape[1],
            'metrics': metrics,
            'feature_names': self.feature_engineer.get_feature_importance_names()
        }
        
        print(f"\nTraining completed!")
        print(f"Accuracy: {metrics['accuracy']:.3f}")
        print(f"ROC-AUC: {metrics['roc_auc']:.3f}")
        print(f"F1-Score: {metrics['f1_score']:.3f}")
        
        return metrics
    
    def _optimize_hyperparameters(self, X_train, y_train):
        """Optimize model hyperparameters using grid search."""
        if self.model_type == 'random_forest':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15],
                'min_samples_split': [2, 5, 10]
            }
        elif self.model_type == 'gradient_boosting':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            }
        else:
            param_grid = {
                'C': [0.1, 1, 10],
                'penalty': ['l2']
            }
        
        grid_search = GridSearchCV(
            self.model, param_grid, cv=3, scoring='roc_auc', n_jobs=-1
        )
        grid_search.fit(X_train, y_train)
        
        print(f"Best parameters: {grid_search.best_params_}")
        return grid_search.best_estimator_
    
    def predict(self, subscription):
        """
        Predict churn probability for a subscription.
        
        Args:
            subscription: UserSubscription instance
            
        Returns:
            dict: Prediction results
        """
        if not self.is_trained:
            self.load()
        
        # Extract features
        features = self.feature_engineer.extract_subscription_features(subscription)
        
        # Prepare for prediction
        feature_names = self.feature_engineer.get_feature_importance_names()
        X = pd.DataFrame([features])[feature_names].fillna(0)
        X = X.replace([np.inf, -np.inf], 0)
        
        # Scale features
        X_scaled = self.preprocessor.transform(X)
        
        # Predict
        churn_probability = self.model.predict_proba(X_scaled)[0, 1]
        will_churn = churn_probability > 0.5
        
        # Risk level
        if churn_probability < 0.3:
            risk_level = 'low'
        elif churn_probability < 0.7:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return {
            'subscription_id': subscription.id,
            'user_id': subscription.user.id,
            'churn_probability': float(churn_probability),
            'will_churn': bool(will_churn),
            'risk_level': risk_level,
            'predicted_at': datetime.now().isoformat()
        }
    
    def predict_batch(self, subscriptions):
        """
        Predict churn for multiple subscriptions.
        
        Args:
            subscriptions: List of UserSubscription instances
            
        Returns:
            list: List of prediction results
        """
        predictions = []
        for subscription in subscriptions:
            try:
                pred = self.predict(subscription)
                predictions.append(pred)
            except Exception as e:
                print(f"Error predicting for subscription {subscription.id}: {e}")
                continue
        
        return predictions
    
    def save(self):
        """Save trained model to disk."""
        if not self.is_trained:
            raise ValueError("Model not trained yet. Train before saving.")
        
        model_path = os.path.join(self.MODEL_DIR, self.MODEL_FILE)
        scaler_path = os.path.join(self.MODEL_DIR, self.SCALER_FILE)
        metadata_path = os.path.join(self.MODEL_DIR, self.METADATA_FILE)
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.preprocessor, scaler_path)
        joblib.dump(self.metadata, metadata_path)
        
        print(f"Model saved to {model_path}")
    
    def load(self):
        """Load trained model from disk."""
        model_path = os.path.join(self.MODEL_DIR, self.MODEL_FILE)
        scaler_path = os.path.join(self.MODEL_DIR, self.SCALER_FILE)
        metadata_path = os.path.join(self.MODEL_DIR, self.METADATA_FILE)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path}. Train the model first."
            )
        
        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(scaler_path)
        self.metadata = joblib.load(metadata_path)
        self.is_trained = True
        
        print(f"Model loaded from {model_path}")
        print(f"Trained at: {self.metadata.get('trained_at')}")
    
    def get_model_info(self):
        """Get information about the trained model."""
        if not self.is_trained:
            return {"status": "not_trained"}
        
        return {
            "status": "trained",
            "metadata": self.metadata
        }
