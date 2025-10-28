"""
Script pour vérifier les données de revenus disponibles
"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import Transaction
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
import pandas as pd

print(f"\n{'='*60}")
print("Vérification des Données de Revenus")
print(f"{'='*60}\n")

# Toutes les transactions
all_transactions = Transaction.objects.filter(status='completed')
print(f"📊 Total transactions: {all_transactions.count()}")
print(f"💰 Revenu total: ${all_transactions.aggregate(total=Sum('amount'))['total'] or 0:.2f}\n")

# Agrégation par mois
monthly_revenue = Transaction.objects.filter(
    status='completed'
).annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    revenue=Sum('amount'),
    transaction_count=Count('id')
).order_by('month')

print(f"📅 Revenus par mois ({monthly_revenue.count()} périodes):")
print(f"{'-'*60}")

if monthly_revenue:
    for item in monthly_revenue:
        month_str = item['month'].strftime('%Y-%m') if item['month'] else 'Unknown'
        print(f"  {month_str}: ${item['revenue']:.2f} ({item['transaction_count']} transactions)")
else:
    print("  ❌ Aucune donnée trouvée")

print(f"{'-'*60}\n")

# Diagnostic
periods_count = monthly_revenue.count()
if periods_count >= 12:
    print(f"✅ SUFFISANT: {periods_count} mois de données")
    print("   → Revenue Forecasting peut être entraîné!")
elif periods_count >= 6:
    print(f"⚠️ LIMITE: {periods_count} mois de données")
    print("   → Revenue Forecasting peut être entraîné (mode réduit)")
else:
    print(f"❌ INSUFFISANT: {periods_count} mois de données")
    print(f"   → Besoin de {6 - periods_count} mois supplémentaires")

print(f"\n{'='*60}\n")
