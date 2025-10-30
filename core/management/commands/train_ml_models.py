"""
Management command to train all ML models.
"""

from django.core.management.base import BaseCommand
from core.ml.models.churn_predictor import ChurnPredictor
from core.ml.models.revenue_forecaster import RevenueForecaster


class Command(BaseCommand):
    help = 'Train all ML models for subscription analytics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['churn', 'revenue', 'all'],
            default='all',
            help='Which model to train'
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='Optimize hyperparameters (slower)'
        )
        parser.add_argument(
            '--period',
            type=str,
            choices=['week', 'month'],
            default='month',
            help='Period for revenue forecasting'
        )
    
    def handle(self, *args, **options):
        model_type = options['model']
        optimize = options['optimize']
        period = options['period']
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('ML Model Training'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if model_type in ['churn', 'all']:
            self.train_churn_model(optimize)
        
        if model_type in ['revenue', 'all']:
            self.train_revenue_model(period)
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Training completed!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
    
    def train_churn_model(self, optimize):
        """Train churn prediction model."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.WARNING('Training Churn Prediction Model'))
        self.stdout.write('=' * 60 + '\n')
        
        try:
            predictor = ChurnPredictor(model_type='random_forest')
            metrics = predictor.train(
                optimize_hyperparameters=optimize,
                handle_imbalance=True
            )
            predictor.save()
            
            self.stdout.write(self.style.SUCCESS('\n✓ Churn model trained successfully!'))
            self.stdout.write(f"  - Accuracy: {metrics['accuracy']:.3f}")
            self.stdout.write(f"  - ROC-AUC: {metrics['roc_auc']:.3f}")
            self.stdout.write(f"  - F1-Score: {metrics['f1_score']:.3f}")
            self.stdout.write(f"  - Precision: {metrics['precision']:.3f}")
            self.stdout.write(f"  - Recall: {metrics['recall']:.3f}")
            
            if 'feature_importance' in metrics:
                self.stdout.write('\n  Top 5 Important Features:')
                for i, (feature, importance) in enumerate(
                    list(metrics['feature_importance'].items())[:5], 1
                ):
                    self.stdout.write(f"    {i}. {feature}: {importance:.4f}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error training churn model: {e}'))
    
    def train_revenue_model(self, period):
        """Train revenue forecasting model."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.WARNING('Training Revenue Forecasting Model'))
        self.stdout.write('=' * 60 + '\n')
        
        try:
            forecaster = RevenueForecaster(model_type='random_forest')
            metrics = forecaster.train(period=period)
            forecaster.save()
            
            self.stdout.write(self.style.SUCCESS('\n✓ Revenue model trained successfully!'))
            self.stdout.write(f"  - R² Score: {metrics['r2_score']:.3f}")
            self.stdout.write(f"  - MAE: ${metrics['mae']:.2f}")
            self.stdout.write(f"  - RMSE: ${metrics['rmse']:.2f}")
            self.stdout.write(f"  - MAPE: {metrics['mape']:.2f}%")
            
            # Get revenue insights
            insights = forecaster.get_revenue_insights()
            self.stdout.write('\n  Revenue Insights:')
            self.stdout.write(f"    - Total Revenue: ${insights['total_revenue']:.2f}")
            self.stdout.write(f"    - Avg per {period}: ${insights['avg_revenue_per_period']:.2f}")
            self.stdout.write(f"    - Trend: {insights['revenue_trend']}")
            
            # Forecast next 3 periods
            forecasts = forecaster.forecast(periods_ahead=3)
            self.stdout.write(f'\n  Next 3 {period}s forecast:')
            for i, forecast in enumerate(forecasts, 1):
                self.stdout.write(f"    {i}. ${forecast:.2f}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error training revenue model: {e}'))
