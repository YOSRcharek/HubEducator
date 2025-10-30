"""
Management command to generate predictions for all active subscriptions.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import UserSubscription
from core.ml.models.churn_predictor import ChurnPredictor


class Command(BaseCommand):
    help = 'Generate ML predictions for all active subscriptions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--prediction-type',
            type=str,
            choices=['churn', 'all'],
            default='all',
            help='Type of prediction to generate'
        )
        parser.add_argument(
            '--high-risk-only',
            action='store_true',
            help='Show only high-risk churn predictions'
        )
    
    def handle(self, *args, **options):
        prediction_type = options['prediction_type']
        high_risk_only = options['high_risk_only']
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Generating ML Predictions'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Get active subscriptions
        subscriptions = UserSubscription.objects.filter(
            status='active'
        ).select_related('user')
        
        if not subscriptions.exists():
            self.stdout.write(self.style.WARNING('\nNo active subscriptions found.'))
            return
        
        self.stdout.write(f'\nFound {subscriptions.count()} active subscriptions.\n')
        
        if prediction_type in ['churn', 'all']:
            self.generate_churn_predictions(subscriptions, high_risk_only)
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Predictions completed!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
    
    def generate_churn_predictions(self, subscriptions, high_risk_only):
        """Generate churn predictions."""
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.WARNING('Churn Predictions'))
        self.stdout.write('=' * 60 + '\n')
        
        try:
            predictor = ChurnPredictor()
            predictor.load()
            
            predictions = predictor.predict_batch(subscriptions)
            
            # Filter high risk if requested
            if high_risk_only:
                predictions = [p for p in predictions if p['risk_level'] == 'high']
            
            # Sort by churn probability
            predictions.sort(key=lambda x: x['churn_probability'], reverse=True)
            
            # Display results
            self.stdout.write(f'Total predictions: {len(predictions)}\n')
            
            # Count by risk level
            risk_counts = {'high': 0, 'medium': 0, 'low': 0}
            for pred in predictions:
                risk_counts[pred['risk_level']] += 1
            
            self.stdout.write('Risk Distribution:')
            self.stdout.write(self.style.ERROR(f'  🔴 High Risk: {risk_counts["high"]}'))
            self.stdout.write(self.style.WARNING(f'  🟡 Medium Risk: {risk_counts["medium"]}'))
            self.stdout.write(self.style.SUCCESS(f'  🟢 Low Risk: {risk_counts["low"]}'))
            
            # Show top 10 at-risk subscriptions
            self.stdout.write('\nTop 10 At-Risk Subscriptions:')
            self.stdout.write('-' * 60)
            
            for i, pred in enumerate(predictions[:10], 1):
                subscription = UserSubscription.objects.get(id=pred['subscription_id'])
                risk_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[pred['risk_level']]
                
                self.stdout.write(
                    f"{i:2d}. {risk_emoji} User: {subscription.user.username:20s} | "
                    f"Churn Prob: {pred['churn_probability']:.1%} | "
                    f"Plan: {subscription.plan}"
                )
        
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                '\n✗ Churn model not found. Train it first with: '
                'python manage.py train_ml_models --model churn'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error generating churn predictions: {e}'))
