"""
Script pour générer des données de revenus historiques de test
⚠️ POUR DÉMONSTRATION UNIQUEMENT 
"""
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import User, Subscription, Transaction
import random

def generate_test_revenue_data(months=12):
    """
    Génère des transactions historiques pour tester Revenue Forecasting
    """
    print(f"\n{'='*60}")
    print(f"Génération de {months} mois de données de test")
    print(f"{'='*60}\n")
    
    # Récupérer un utilisateur et un abonnement existants
    try:
        user = User.objects.first()
        subscription = Subscription.objects.first()
        
        if not user or not subscription:
            print("❌ Erreur: Aucun utilisateur ou abonnement trouvé")
            return
        
        print(f"Utilisateur: {user.username}")
        print(f"Abonnement: {subscription.name}\n")
        
        # Date de départ (il y a X mois) - avec timezone
        now = timezone.now()
        
        # Générer des transactions mensuelles avec croissance
        base_amount = 50
        growth_rate = 1.05  # 5% de croissance par mois
        
        created_count = 0
        
        for i in range(months):
            # Date de la transaction - 1er jour de chaque mois
            # Remonter de (months - i) mois depuis maintenant
            months_ago = months - i - 1
            year = now.year
            month = now.month - months_ago
            
            # Ajuster l'année si nécessaire
            while month <= 0:
                month += 12
                year -= 1
            while month > 12:
                month -= 12
                year += 1
            
            # Créer la date au 1er du mois à midi
            transaction_date = timezone.make_aware(
                datetime(year, month, 1, 12, 0, 0)
            )
            
            # Montant avec croissance et variation aléatoire
            amount = base_amount * (growth_rate ** i) * random.uniform(0.9, 1.1)
            amount = round(amount, 2)
            
            # Créer la transaction
            try:
                # Créer d'abord sans created_at
                transaction = Transaction(
                    user=user,
                    subscription=subscription,
                    stripe_payment_intent_id=f"test_pi_{i}_{timezone.now().timestamp()}",
                    amount=Decimal(str(amount)),
                    currency='usd',
                    status='completed',
                    description=f"Test transaction - Month {i+1}",
                    completed_at=transaction_date
                )
                # Sauvegarder sans auto_now_add
                transaction.save()
                
                # Forcer la mise à jour de created_at
                Transaction.objects.filter(id=transaction.id).update(
                    created_at=transaction_date
                )
                
                created_count += 1
                print(f"✓ {transaction_date.strftime('%Y-%m')}: ${amount:.2f}")
            except Exception as e:
                print(f"✗ Erreur mois {i+1}: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ {created_count}/{months} transactions créées avec succès!")
        print(f"{'='*60}\n")
        print("Vous pouvez maintenant entraîner le modèle Revenue Forecasting:")
        print("  python manage.py train_ml_models --model revenue\n")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")

if __name__ == "__main__":
    # Générer 12 mois de données
    generate_test_revenue_data(months=12)
