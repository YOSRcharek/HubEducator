"""
Revenue forecasting model for subscription predictions.
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from django.conf import settings
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from core.models import Transaction, UserSubscription
from core.ml.utils.data_preprocessing import DataPreprocessor
from core.ml.utils.model_evaluator import ModelEvaluator


class RevenueForecaster:
    """
    Forecast future revenue based on historical subscription data.
    """
    
    MODEL_DIR = os.path.join(settings.BASE_DIR, 'core', 'ml', 'trained_models')
    MODEL_FILE = 'revenue_forecaster.pkl'
    SCALER_FILE = 'revenue_scaler.pkl'
    METADATA_FILE = 'revenue_metadata.pkl'
    
    def __init__(self, model_type='random_forest'):
        """
        Initialize revenue forecaster.
        
        Args:
            model_type: 'random_forest', 'gradient_boosting', or 'linear'
        """
        self.model_type = model_type
        self.model = self._create_model(model_type)
        self.preprocessor = DataPreprocessor(scaling_method='standard')
        self.is_trained = False
        self.metadata = {}
        
        os.makedirs(self.MODEL_DIR, exist_ok=True)
    
    def _create_model(self, model_type):
        """Create ML model based on type."""
        if model_type == 'random_forest':
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            return GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        elif model_type == 'linear':
            return LinearRegression()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_time_series_features(self, df):
        """
        Create time series features from revenue data.
        
        Args:
            df: DataFrame with date and revenue columns
            
        Returns:
            DataFrame with features
        """
        df = df.copy()
        
        # Temporal features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['day_of_year'] = df['date'].dt.dayofyear
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        # Lag features (previous periods)
        df['revenue_lag_1'] = df['revenue'].shift(1)
        df['revenue_lag_2'] = df['revenue'].shift(2)
        df['revenue_lag_3'] = df['revenue'].shift(3)
        df['revenue_lag_4'] = df['revenue'].shift(4)
        
        # Rolling statistics
        df['revenue_rolling_mean_3'] = df['revenue'].rolling(window=3).mean()
        df['revenue_rolling_std_3'] = df['revenue'].rolling(window=3).std()
        df['revenue_rolling_mean_6'] = df['revenue'].rolling(window=6).mean()
        
        # Growth rate
        df['revenue_growth'] = df['revenue'].pct_change()
        
        # Subscription count features
        if 'subscription_count' in df.columns:
            df['subs_lag_1'] = df['subscription_count'].shift(1)
            df['subs_rolling_mean_3'] = df['subscription_count'].rolling(window=3).mean()
        
        return df
    
    def _get_historical_revenue_data(self, period='month'):
        """
        Get historical revenue data aggregated by period.
        
        Args:
            period: 'week' or 'month'
            
        Returns:
            DataFrame with historical revenue
        """
        # Get all transactions
        transactions = Transaction.objects.filter(
            status='completed'
        ).order_by('created_at')
        
        if not transactions.exists():
            raise ValueError("No transaction data available for training.")
        
        # Aggregate by period
        if period == 'month':
            aggregated = transactions.annotate(
                period=TruncMonth('created_at')
            ).values('period').annotate(
                revenue=Sum('amount'),
                transaction_count=Count('id')
            ).order_by('period')
        else:  # week
            aggregated = transactions.annotate(
                period=TruncWeek('created_at')
            ).values('period').annotate(
                revenue=Sum('amount'),
                transaction_count=Count('id')
            ).order_by('period')
        
        # Convert to DataFrame
        df = pd.DataFrame(list(aggregated))
        df.rename(columns={'period': 'date'}, inplace=True)
        df['revenue'] = df['revenue'].astype(float)
        
        # Get subscription counts
        subscriptions = UserSubscription.objects.filter(
            is_active=True
        )
        
        if period == 'month':
            sub_counts = subscriptions.annotate(
                period=TruncMonth('start_date')
            ).values('period').annotate(
                subscription_count=Count('id')
            ).order_by('period')
        else:
            sub_counts = subscriptions.annotate(
                period=TruncWeek('start_date')
            ).values('period').annotate(
                subscription_count=Count('id')
            ).order_by('period')
        
        sub_df = pd.DataFrame(list(sub_counts))
        if not sub_df.empty:
            sub_df.rename(columns={'period': 'date'}, inplace=True)
            df = df.merge(sub_df, on='date', how='left')
            df['subscription_count'] = df['subscription_count'].fillna(0)
        
        return df
    
    def train(self, period='month'):
        """
        Train the revenue forecasting model.
        
        Args:
            period: 'week' or 'month'
            
        Returns:
            dict: Training metrics
        """
        print(f"Creating {period}ly revenue dataset...")
        df = self._get_historical_revenue_data(period=period)
        
        if len(df) < 6:
            raise ValueError(f"Insufficient data for training. Need at least 6 {period}s.")
        
        print(f"Dataset created: {len(df)} periods")
        
        # Create time series features
        df = self._create_time_series_features(df)
        
        # Remove rows with NaN (from lag features)
        df = df.dropna()
        
        if len(df) < 6:
            raise ValueError("Insufficient data after feature engineering.")
        
        # Prepare features and target
        feature_columns = [
            'year', 'month', 'quarter', 'day_of_year', 'week_of_year',
            'revenue_lag_1', 'revenue_lag_2', 'revenue_lag_3', 'revenue_lag_4',
            'revenue_rolling_mean_3', 'revenue_rolling_std_3',
            'revenue_rolling_mean_6', 'revenue_growth', 'transaction_count'
        ]
        
        if 'subscription_count' in df.columns:
            feature_columns.extend(['subscription_count', 'subs_lag_1', 'subs_rolling_mean_3'])
        
        X = df[feature_columns].fillna(0)
        y = df['revenue'].values
        
        # Split data (use last 20% as test)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Scale features
        print("Scaling features...")
        X_train_scaled = self.preprocessor.fit_transform(X_train)
        X_test_scaled = self.preprocessor.transform(X_test)
        
        # Train model
        print("Training model...")
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        print("Evaluating model...")
        y_pred = self.model.predict(X_test_scaled)
        
        metrics = ModelEvaluator.evaluate_regression(y_test, y_pred)
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            indices = np.argsort(importances)[::-1]
            metrics['feature_importance'] = {
                feature_columns[i]: float(importances[i])
                for i in indices[:10]
            }
        
        # Save metadata
        self.metadata = {
            'trained_at': datetime.now().isoformat(),
            'model_type': self.model_type,
            'period': period,
            'n_samples': len(df),
            'n_features': X.shape[1],
            'metrics': metrics,
            'feature_names': feature_columns
        }
        
        print(f"\nTraining completed!")
        print(f"R² Score: {metrics['r2_score']:.3f}")
        print(f"MAE: ${metrics['mae']:.2f}")
        print(f"RMSE: ${metrics['rmse']:.2f}")
        
        return metrics
    
    def forecast(self, periods_ahead=3):
        """
        Forecast revenue for future periods.
        
        Args:
            periods_ahead: Number of periods to forecast
            
        Returns:
            list: Forecasted revenue values
        """
        if not self.is_trained:
            self.load()
        
        # Get recent data
        period = self.metadata.get('period', 'month')
        df = self._get_historical_revenue_data(period=period)
        df = self._create_time_series_features(df)
        df = df.dropna()
        
        if df.empty:
            raise ValueError("No data available for forecasting.")
        
        feature_columns = self.metadata['feature_names']
        forecasts = []
        
        # Iteratively forecast
        for i in range(periods_ahead):
            # Get last row features
            last_row = df.iloc[-1:][feature_columns].fillna(0)
            X_scaled = self.preprocessor.transform(last_row)
            
            # Predict
            predicted_revenue = self.model.predict(X_scaled)[0]
            forecasts.append(float(predicted_revenue))
            
            # Create next period row for iterative forecasting
            next_date = df.iloc[-1]['date'] + timedelta(days=30 if period == 'month' else 7)
            next_row = {
                'date': next_date,
                'revenue': predicted_revenue,
                'transaction_count': df.iloc[-1]['transaction_count'],
                'subscription_count': df.iloc[-1].get('subscription_count', 0)
            }
            
            next_df = pd.DataFrame([next_row])
            next_df = self._create_time_series_features(
                pd.concat([df, next_df], ignore_index=True)
            ).iloc[-1:]
            
            df = pd.concat([df, next_df], ignore_index=True)
        
        return forecasts
    
    def get_revenue_insights(self):
        """
        Get revenue insights and statistics.
        
        Returns:
            dict: Revenue insights
        """
        period = self.metadata.get('period', 'month')
        df = self._get_historical_revenue_data(period=period)
        
        insights = {
            'total_revenue': float(df['revenue'].sum()),
            'avg_revenue_per_period': float(df['revenue'].mean()),
            'revenue_std': float(df['revenue'].std()),
            'revenue_trend': 'increasing' if df['revenue'].iloc[-1] > df['revenue'].iloc[0] else 'decreasing',
            'best_period': df.loc[df['revenue'].idxmax(), 'date'].isoformat(),
            'best_period_revenue': float(df['revenue'].max()),
            'worst_period': df.loc[df['revenue'].idxmin(), 'date'].isoformat(),
            'worst_period_revenue': float(df['revenue'].min()),
        }
        
        # Growth rate
        if len(df) > 1:
            insights['growth_rate'] = float(
                (df['revenue'].iloc[-1] - df['revenue'].iloc[0]) / df['revenue'].iloc[0] * 100
            )
        
        return insights
    
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
