"""
Data preprocessing utilities for ML models.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split


class DataPreprocessor:
    """Handle data preprocessing for ML models."""
    
    def __init__(self, scaling_method='standard'):
        """
        Initialize preprocessor.
        
        Args:
            scaling_method: 'standard' or 'minmax'
        """
        self.scaling_method = scaling_method
        self.scaler = StandardScaler() if scaling_method == 'standard' else MinMaxScaler()
        self.is_fitted = False
    
    def fit_transform(self, X):
        """
        Fit scaler and transform data.
        
        Args:
            X: Feature matrix
            
        Returns:
            Scaled feature matrix
        """
        X_scaled = self.scaler.fit_transform(X)
        self.is_fitted = True
        return X_scaled
    
    def transform(self, X):
        """
        Transform data using fitted scaler.
        
        Args:
            X: Feature matrix
            
        Returns:
            Scaled feature matrix
        """
        if not self.is_fitted:
            raise ValueError("Scaler not fitted. Call fit_transform first.")
        return self.scaler.transform(X)
    
    @staticmethod
    def split_data(X, y, test_size=0.2, random_state=42):
        """
        Split data into train and test sets.
        
        Args:
            X: Features
            y: Target
            test_size: Proportion of test set
            random_state: Random seed
            
        Returns:
            X_train, X_test, y_train, y_test
        """
        import numpy as np
        
        # Check if we have enough samples for stratified split
        unique, counts = np.unique(y, return_counts=True)
        min_samples = counts.min()
        
        # Need at least 2 samples per class for stratified split
        if min_samples < 2:
            print(f"⚠️  Not enough samples for stratified split (min class has {min_samples} sample)")
            print("   Using regular split without stratification")
            return train_test_split(X, y, test_size=test_size, random_state=random_state)
        
        try:
            return train_test_split(X, y, test_size=test_size, 
                                    random_state=random_state, stratify=y)
        except ValueError as e:
            print(f"⚠️  Stratified split failed: {e}")
            print("   Using regular split without stratification")
            return train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    @staticmethod
    def handle_imbalanced_data(X, y, method='oversample'):
        """
        Handle imbalanced datasets.
        
        Args:
            X: Features
            y: Target
            method: 'oversample' or 'undersample'
            
        Returns:
            X_resampled, y_resampled
        """
        try:
            from imblearn.over_sampling import SMOTE
            from imblearn.under_sampling import RandomUnderSampler
            import numpy as np
            
            # Check if we have enough samples for SMOTE
            unique, counts = np.unique(y, return_counts=True)
            min_samples = counts.min()
            
            # SMOTE requires at least 6 samples in minority class (default k_neighbors=5)
            if min_samples < 6:
                print(f"⚠️  Not enough samples for SMOTE (min class has {min_samples} samples, need 6+)")
                print("   Skipping class balancing - using original data")
                return X, y
            
            if method == 'oversample':
                sampler = SMOTE(random_state=42, k_neighbors=min(5, min_samples-1))
            else:
                sampler = RandomUnderSampler(random_state=42)
            
            X_resampled, y_resampled = sampler.fit_resample(X, y)
            return X_resampled, y_resampled
        except ImportError:
            print("imbalanced-learn not installed. Returning original data.")
            return X, y
        except Exception as e:
            print(f"Error in class balancing: {e}")
            print("Returning original data.")
            return X, y
    
    @staticmethod
    def remove_outliers(df, columns, n_std=3):
        """
        Remove outliers using standard deviation method.
        
        Args:
            df: DataFrame
            columns: Columns to check for outliers
            n_std: Number of standard deviations
            
        Returns:
            DataFrame without outliers
        """
        df_clean = df.copy()
        for col in columns:
            mean = df_clean[col].mean()
            std = df_clean[col].std()
            df_clean = df_clean[
                (df_clean[col] >= mean - n_std * std) &
                (df_clean[col] <= mean + n_std * std)
            ]
        return df_clean
