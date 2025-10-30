"""
Script pour générer des abonnements utilisateurs de test
⚠️ POUR DÉMONSTRATION UNIQUEMENT 
"""
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import User, Subscription, Transaction, UserSubscription

def generate_test_subscriptions(num_users=20):
    """
    Génère des utilisateurs et abonnements de test pour ML
    """
    print(f"\n{'='*60}")
    print(f"Génération de {num_users} abonnements de test")
    print(f"{'='*60}\n")
    
    # Récupérer les abonnements disponibles
    subscriptions = list(Subscription.objects.all())
    
    if not subscriptions:
        print("❌ Erreur: Aucun abonnement trouvé dans la base de données")
        return
    
    print(f"📦 {len(subscriptions)} types d'abonnements disponibles\n")
    
    created_users = 0
    created_subscriptions = 0
    created_transactions = 0
    
    for i in range(num_users):
        try:
            # Créer un utilisateur de test
            username = f"testuser{i+1}"
            email = f"test{i+1}@example.com"
            
            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                print(f"ℹ️  Utilisateur existant: {username}")
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password="testpass123",
                    role=random.choice(['student', 'teacher']),
                    email_verified=True
                )
                created_users += 1
                print(f"✓ Utilisateur créé: {username} ({user.role})")
            
            # Choisir un abonnement aléatoire
            subscription = random.choice(subscriptions)
            
            # Date de début (entre 1 et 12 mois en arrière)
            months_ago = random.randint(1, 12)
            start_date = timezone.now() - timedelta(days=30 * months_ago)
            
            # Durée de l'abonnement (30, 90, ou 365 jours)
            duration_days = random.choice([30, 90, 365])
            end_date = start_date + timedelta(days=duration_days)
            
            # Déterminer si l'abonnement est toujours actif
            is_active = end_date > timezone.now() and random.random() > 0.2  # 80% actifs
            
            # Créer la transaction
            payment_intent_id = f"pi_test_{user.id}_{i}_{int(timezone.now().timestamp())}"
            
            transaction = Transaction.objects.create(
                user=user,
                subscription=subscription,
                stripe_payment_intent_id=payment_intent_id,
                amount=subscription.price,
                currency='usd',
                status='completed',
                description=f"Test subscription - {subscription.name}",
                completed_at=start_date
            )
            
            # Forcer la date de création
            Transaction.objects.filter(id=transaction.id).update(
                created_at=start_date
            )
            created_transactions += 1
            
            # Créer l'abonnement utilisateur
            user_sub = UserSubscription.objects.create(
                user=user,
                subscription=subscription,
                transaction=transaction,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                auto_renew=random.choice([True, False])
            )
            
            # Forcer la date de création
            UserSubscription.objects.filter(id=user_sub.id).update(
                created_at=start_date
            )
            created_subscriptions += 1
            
            status = "✅ Actif" if is_active else "❌ Expiré"
            print(f"  → {subscription.name} (${subscription.price}) - {status}")
            
        except Exception as e:
            print(f"✗ Erreur utilisateur {i+1}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Résumé:")
    print(f"   • {created_users} nouveaux utilisateurs créés")
    print(f"   • {created_subscriptions} abonnements créés")
    print(f"   • {created_transactions} transactions créées")
    print(f"{'='*60}\n")
    
    # Afficher les statistiques
    total_active = UserSubscription.objects.filter(is_active=True).count()
    total_inactive = UserSubscription.objects.filter(is_active=False).count()
    
    try:
        import django.db.models
        total_revenue = Transaction.objects.filter(status='completed').aggregate(
            total=django.db.models.Sum('amount')
        )['total'] or 0
    except:
        total_revenue = 0
    
    print(f"📊 Statistiques globales:")
    print(f"   • Abonnements actifs: {total_active}")
    print(f"   • Abonnements expirés: {total_inactive}")
    print(f"   • Revenu total: ${total_revenue:.2f}")
    print(f"\n🎯 Vous pouvez maintenant entraîner les modèles ML:")
    print(f"   python manage.py train_ml_models --model all\n")

if __name__ == "__main__":
    # Générer 20 abonnements de test
    generate_test_subscriptions(num_users=20)
