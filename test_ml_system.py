"""
Script de test rapide pour le système ML.
Exécuter avec: python test_ml_system.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import UserSubscription, Transaction
from core.ml.models.churn_predictor import ChurnPredictor
from core.ml.models.revenue_forecaster import RevenueForecaster
from core.ml.models.ltv_calculator import LTVCalculator


def test_data_availability():
    """Test if we have enough data for ML."""
    print("=" * 60)
    print("Testing Data Availability")
    print("=" * 60)
    
    subscriptions_count = UserSubscription.objects.count()
    active_subscriptions = UserSubscription.objects.filter(status='active').count()
    transactions_count = Transaction.objects.filter(status='completed').count()
    
    print(f"Total Subscriptions: {subscriptions_count}")
    print(f"Active Subscriptions: {active_subscriptions}")
    print(f"Completed Transactions: {transactions_count}")
    
    if subscriptions_count < 10:
        print("\n⚠️  WARNING: Less than 10 subscriptions. ML models may not work well.")
        print("   Recommendation: Create more test data.")
    else:
        print("\n✅ Sufficient data for ML training!")
    
    if transactions_count < 5:
        print("⚠️  WARNING: Very few transactions. Revenue forecasting may be limited.")
    
    return subscriptions_count >= 10


def test_churn_model():
    """Test churn prediction model."""
    print("\n" + "=" * 60)
    print("Testing Churn Prediction Model")
    print("=" * 60)
    
    try:
        predictor = ChurnPredictor()
        
        # Try to load existing model
        try:
            predictor.load()
            print("✅ Churn model loaded successfully!")
            print(f"   Trained at: {predictor.metadata.get('trained_at')}")
            print(f"   Samples used: {predictor.metadata.get('n_samples')}")
            
            # Test prediction on first active subscription
            subscription = UserSubscription.objects.filter(status='active').first()
            if subscription:
                prediction = predictor.predict(subscription)
                print(f"\n📊 Sample Prediction:")
                print(f"   User: {subscription.user.username}")
                print(f"   Churn Probability: {prediction['churn_probability']:.1%}")
                print(f"   Risk Level: {prediction['risk_level']}")
            
        except FileNotFoundError:
            print("⚠️  Model not trained yet.")
            print("   Run: python manage.py train_ml_models --model churn")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing churn model: {e}")
        return False


def test_revenue_model():
    """Test revenue forecasting model."""
    print("\n" + "=" * 60)
    print("Testing Revenue Forecasting Model")
    print("=" * 60)
    
    try:
        forecaster = RevenueForecaster()
        
        try:
            forecaster.load()
            print("✅ Revenue model loaded successfully!")
            print(f"   Trained at: {forecaster.metadata.get('trained_at')}")
            
            # Get forecast
            forecasts = forecaster.forecast(periods_ahead=3)
            print(f"\n📈 Next 3 Periods Forecast:")
            for i, forecast in enumerate(forecasts, 1):
                print(f"   Period {i}: ${forecast:.2f}")
            
            # Get insights
            insights = forecaster.get_revenue_insights()
            print(f"\n💡 Revenue Insights:")
            print(f"   Total Revenue: ${insights['total_revenue']:.2f}")
            print(f"   Trend: {insights['revenue_trend']}")
            
        except FileNotFoundError:
            print("⚠️  Model not trained yet.")
            print("   Run: python manage.py train_ml_models --model revenue")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing revenue model: {e}")
        return False


def test_ltv_model():
    """Test LTV calculator model."""
    print("\n" + "=" * 60)
    print("Testing LTV Calculator Model")
    print("=" * 60)
    
    try:
        calculator = LTVCalculator()
        
        try:
            calculator.load()
            print("✅ LTV model loaded successfully!")
            print(f"   Trained at: {calculator.metadata.get('trained_at')}")
            
            # Test prediction on first active subscription
            subscription = UserSubscription.objects.filter(status='active').first()
            if subscription:
                prediction = calculator.predict_ltv(subscription)
                print(f"\n💎 Sample LTV Prediction:")
                print(f"   User: {subscription.user.username}")
                print(f"   Current LTV: ${prediction['current_ltv']:.2f}")
                print(f"   Predicted LTV: ${prediction['predicted_ltv']:.2f}")
                print(f"   Potential: ${prediction['ltv_potential']:.2f}")
            
        except FileNotFoundError:
            print("⚠️  Model not trained yet.")
            print("   Run: python manage.py train_ml_models --model ltv")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LTV model: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🤖 ML SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Test data
    has_data = test_data_availability()
    
    if not has_data:
        print("\n" + "=" * 60)
        print("⚠️  INSUFFICIENT DATA")
        print("=" * 60)
        print("Please create more subscriptions and transactions before training ML models.")
        return
    
    # Test models
    churn_ok = test_churn_model()
    revenue_ok = test_revenue_model()
    ltv_ok = test_ltv_model()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Data Availability: {'✅' if has_data else '❌'}")
    print(f"Churn Model: {'✅' if churn_ok else '❌'}")
    print(f"Revenue Model: {'✅' if revenue_ok else '❌'}")
    print(f"LTV Model: {'✅' if ltv_ok else '❌'}")
    
    if churn_ok and revenue_ok and ltv_ok:
        print("\n🎉 All ML models are working correctly!")
        print("\nNext steps:")
        print("1. Access the ML dashboard: http://localhost:8000/dashboard/ml-insights/")
        print("2. Generate predictions: python manage.py generate_predictions")
    else:
        print("\n⚠️  Some models need to be trained.")
        print("\nTo train all models, run:")
        print("   python manage.py train_ml_models")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
