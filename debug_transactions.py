"""
Script pour déboguer les dates des transactions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import Transaction

print(f"\n{'='*60}")
print("Debug: Dates des Transactions")
print(f"{'='*60}\n")

# Toutes les transactions de test
test_transactions = Transaction.objects.filter(
    description__startswith='Test transaction'
).order_by('created_at')

print(f"📊 Total: {test_transactions.count()} transactions de test\n")

for trans in test_transactions:
    print(f"ID: {trans.id}")
    print(f"  Amount: ${trans.amount}")
    print(f"  Description: {trans.description}")
    print(f"  created_at: {trans.created_at}")
    print(f"  completed_at: {trans.completed_at}")
    print(f"  Month (created_at): {trans.created_at.strftime('%Y-%m')}")
    print()

print(f"{'='*60}\n")
