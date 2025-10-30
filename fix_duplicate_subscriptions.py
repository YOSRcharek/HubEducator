"""
Script pour corriger les abonnements en double
Désactive les anciens abonnements et garde uniquement le plus récent actif
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import UserSubscription, User

def fix_duplicate_subscriptions():
    """Désactive les anciens abonnements en double pour chaque utilisateur"""
    
    # Obtenir tous les utilisateurs qui ont plus d'un abonnement actif
    users_with_multiple = User.objects.filter(
        user_subscriptions__is_active=True
    ).distinct()
    
    fixed_count = 0
    
    for user in users_with_multiple:
        # Obtenir tous les abonnements actifs de cet utilisateur, triés par date de création
        active_subs = UserSubscription.objects.filter(
            user=user,
            is_active=True
        ).order_by('-created_at')
        
        if active_subs.count() > 1:
            print(f"\n👤 Utilisateur: {user.username} ({user.email})")
            print(f"   📊 Abonnements actifs trouvés: {active_subs.count()}")
            
            # Garder le plus récent actif, désactiver les autres
            for i, sub in enumerate(active_subs):
                if i == 0:
                    # Le plus récent reste actif
                    print(f"   ✅ Garde actif: {sub.subscription.name} (créé le {sub.created_at.strftime('%d/%m/%Y %H:%M')})")
                else:
                    # Désactiver les anciens
                    sub.is_active = False
                    sub.save()
                    print(f"   ❌ Désactivé: {sub.subscription.name} (créé le {sub.created_at.strftime('%d/%m/%Y %H:%M')})")
                    fixed_count += 1
    
    print(f"\n✨ Terminé! {fixed_count} abonnement(s) désactivé(s)")
    
    # Afficher un résumé
    print("\n📋 Résumé des abonnements actifs:")
    active_subscriptions = UserSubscription.objects.filter(is_active=True).select_related('user', 'subscription')
    for sub in active_subscriptions:
        print(f"   • {sub.user.username}: {sub.subscription.name} (expire le {sub.end_date.strftime('%d/%m/%Y')})")

if __name__ == '__main__':
    print("🔧 Correction des abonnements en double...\n")
    fix_duplicate_subscriptions()
