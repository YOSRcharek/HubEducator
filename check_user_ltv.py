"""
Script pour vérifier le LTV d'un utilisateur spécifique
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import User, Transaction, UserSubscription
from django.db.models import Sum

# Email à vérifier
email = "douabaghdadi89@gmail.com"

try:
    user = User.objects.get(email=email)
    print(f"\n{'='*60}")
    print(f"Analyse LTV pour: {user.username} ({user.email})")
    print(f"{'='*60}\n")
    
    # Transactions
    transactions = Transaction.objects.filter(user=user, status='completed')
    print(f"📊 TRANSACTIONS ({transactions.count()} total):")
    print(f"{'-'*60}")
    
    total = 0
    for i, trans in enumerate(transactions, 1):
        print(f"{i}. ${trans.amount} - {trans.created_at.strftime('%Y-%m-%d')} - {trans.description or 'No description'}")
        total += float(trans.amount)
    
    print(f"{'-'*60}")
    print(f"💰 TOTAL (Current LTV): ${total}\n")
    
    # Abonnements
    subscriptions = UserSubscription.objects.filter(user=user)
    print(f"📋 ABONNEMENTS ({subscriptions.count()} total):")
    print(f"{'-'*60}")
    
    for i, sub in enumerate(subscriptions, 1):
        status = "✅ Actif" if sub.is_active else "❌ Inactif"
        print(f"{i}. {sub.subscription.name} - ${sub.subscription.price} - {status}")
        print(f"   Période: {sub.start_date.strftime('%Y-%m-%d')} → {sub.end_date.strftime('%Y-%m-%d')}")
    
    print(f"{'-'*60}\n")
    
    # Calcul ML
    total_calculated = transactions.aggregate(total=Sum('amount'))['total'] or 0
    print(f"🤖 CALCUL ML:")
    print(f"   Current LTV (somme des transactions) = ${total_calculated}")
    print(f"\n{'='*60}\n")
    
except User.DoesNotExist:
    print(f"\n❌ Utilisateur avec email '{email}' non trouvé.\n")
except Exception as e:
    print(f"\n❌ Erreur: {e}\n")
