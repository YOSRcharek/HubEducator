"""
Script pour nettoyer les transactions de test
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import Transaction

print(f"\n{'='*60}")
print("Nettoyage des Transactions de Test")
print(f"{'='*60}\n")

# Supprimer les transactions de test
test_transactions = Transaction.objects.filter(
    description__startswith='Test transaction'
)

count = test_transactions.count()
if count > 0:
    print(f"🗑️  Suppression de {count} transactions de test...")
    test_transactions.delete()
    print(f"✅ {count} transactions supprimées\n")
else:
    print("ℹ️  Aucune transaction de test trouvée\n")

print(f"{'='*60}\n")
print("Vous pouvez maintenant régénérer les données:")
print("  python generate_test_revenue_data.py\n")
