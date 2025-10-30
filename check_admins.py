import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
django.setup()

from core.models import User

print("=" * 60)
print("VÉRIFICATION DES COMPTES ADMIN")
print("=" * 60)

# Chercher tous les utilisateurs avec role='admin'
admins = User.objects.filter(role='admin')
print(f"\n📊 Utilisateurs avec role='admin': {admins.count()}")

if admins.exists():
    for admin in admins:
        print(f"\n✅ Admin trouvé:")
        print(f"   - Username: {admin.username}")
        print(f"   - Email: {admin.email}")
        print(f"   - Role: {admin.role}")
        print(f"   - Staff: {admin.is_staff}")
        print(f"   - Superuser: {admin.is_superuser}")
        print(f"   - Email vérifié: {admin.email_verified}")
        print(f"   - Actif: {admin.is_active}")
else:
    print("   ❌ Aucun utilisateur avec role='admin'")

# Chercher les superusers
print(f"\n📊 Superusers (is_superuser=True): {User.objects.filter(is_superuser=True).count()}")
superusers = User.objects.filter(is_superuser=True)
if superusers.exists():
    for su in superusers:
        print(f"   - {su.username} ({su.email}) - Role: {su.role}")

# Afficher tous les utilisateurs
print(f"\n📊 Total d'utilisateurs dans la base: {User.objects.count()}")
all_users = User.objects.all()
if all_users.exists():
    print("\nTous les utilisateurs:")
    for user in all_users:
        print(f"   - {user.username} ({user.email}) - Role: {user.role} - Vérifié: {user.email_verified}")

print("\n" + "=" * 60)
