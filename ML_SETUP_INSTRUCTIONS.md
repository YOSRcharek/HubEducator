# 🚀 Instructions de Configuration ML - HubEducator

## 📦 Installation Complète

### Étape 1: Installer les Dépendances ML

```bash
# Activer votre environnement virtuel
.\venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Installer les packages ML
pip install -r requirements.txt
```

Les packages suivants seront installés:
- scikit-learn (algorithmes ML)
- pandas (manipulation de données)
- numpy (calculs numériques)
- joblib (sauvegarde de modèles)
- matplotlib & seaborn (visualisations)
- imbalanced-learn (gestion du déséquilibre)

### Étape 2: Vérifier les Données

```bash
# Lancer le script de test
python test_ml_system.py
```

Ce script vérifie:
- ✅ Nombre d'abonnements disponibles
- ✅ Nombre de transactions
- ✅ État des modèles ML

**Minimum requis:**
- 10+ abonnements (actifs ou expirés)
- 5+ transactions complétées

### Étape 3: Entraîner les Modèles

```bash
# Option 1: Entraîner tous les modèles (recommandé)
python manage.py train_ml_models

# Option 2: Entraîner individuellement
python manage.py train_ml_models --model churn
python manage.py train_ml_models --model revenue

# Option 3: Avec optimisation (plus lent mais meilleur)
python manage.py train_ml_models --optimize
```

**Temps d'entraînement estimé:**
- Sans optimisation: 30-60 secondes
- Avec optimisation: 2-5 minutes

### Étape 4: Générer les Prédictions

```bash
# Générer toutes les prédictions
python manage.py generate_predictions

# Ou spécifiquement
python manage.py generate_predictions --prediction-type churn
```

### Étape 5: Démarrer le Serveur

```bash
python manage.py runserver
```

### Étape 6: Accéder au Dashboard ML

Ouvrez votre navigateur:
```
http://127.0.0.1:8000/dashboard/ml-insights/
```

## 🎯 Navigation dans l'Interface

### Dashboard Principal
**URL**: `/dashboard/ml-insights/`

Vous y trouverez:
- 📊 Statistiques générales
- 🔴 Lien vers Churn Predictions
- 📈 Lien vers Revenue Forecast

### Churn Predictions
**URL**: `/dashboard/ml-insights/churn-predictions/`

Fonctionnalités:
- Liste des utilisateurs à risque
- Probabilité de churn (0-100%)
- Classification par niveau de risque
- Filtres et pagination

### Revenue Forecast
**URL**: `/dashboard/ml-insights/revenue-forecast/`

Fonctionnalités:
- Graphique de prévision interactif
- Prévisions sur 6 mois
- Insights sur les tendances
- Métriques de croissance

## 🔧 Configuration Avancée

### Ajouter un Lien dans la Navigation

Si vous voulez ajouter un lien ML dans votre navbar, modifiez:
`dashboard/templates/includes/navbar.html`

Ajoutez:
```html
<li class="nav-item">
    <a class="nav-link" href="{% url 'ml_insights' %}">
        <i class="fas fa-brain"></i> ML Analytics
    </a>
</li>
```

### Automatiser le Ré-entraînement

#### Option 1: Cron Job (Linux/Mac)
```bash
# Éditer crontab
crontab -e

# Ajouter cette ligne (ré-entraîner le 1er de chaque mois à 2h)
0 2 1 * * cd /path/to/HubEducator && /path/to/venv/bin/python manage.py train_ml_models
```

#### Option 2: Task Scheduler (Windows)
1. Ouvrir Task Scheduler
2. Créer une nouvelle tâche
3. Déclencher: Mensuel, 1er du mois, 2h00
4. Action: Lancer `python manage.py train_ml_models`

#### Option 3: Celery (Recommandé pour production)
```python
# Dans celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('HubEducator')

@app.task
def train_ml_models():
    from django.core.management import call_command
    call_command('train_ml_models')

# Schedule
app.conf.beat_schedule = {
    'train-ml-monthly': {
        'task': 'train_ml_models',
        'schedule': crontab(day_of_month='1', hour='2'),
    },
}
```

## 📊 Utilisation des APIs

### API Churn Prediction
```bash
# Prédire le churn pour un abonnement spécifique
curl http://localhost:8000/dashboard/api/predict-churn/123/
```

Réponse:
```json
{
    "subscription_id": 123,
    "user_id": 456,
    "churn_probability": 0.75,
    "will_churn": true,
    "risk_level": "high",
    "predicted_at": "2025-10-23T05:45:00"
}
```

### API Revenue Forecast
```bash
# Obtenir les prévisions pour 3 périodes
curl http://localhost:8000/dashboard/api/revenue-forecast/?periods=3
```

## 🐛 Troubleshooting

### Problème: "Model file not found"
**Cause**: Les modèles n'ont pas été entraînés

**Solution**:
```bash
python manage.py train_ml_models
```

### Problème: "Insufficient data for training"
**Cause**: Pas assez d'abonnements ou de transactions

**Solution**:
1. Créer plus d'abonnements de test
2. Créer des transactions de test
3. Attendre d'avoir plus de données réelles

**Script pour créer des données de test**:
```python
# Dans Django shell
python manage.py shell

from core.models import User, UserSubscription, Transaction
from django.utils import timezone
from datetime import timedelta
import random

# Créer des abonnements de test
for i in range(20):
    user = User.objects.create_user(
        username=f'testuser{i}',
        email=f'test{i}@example.com',
        password='testpass123'
    )
    
    subscription = UserSubscription.objects.create(
        user=user,
        plan='student',
        amount=10.00,
        status='active',
        start_date=timezone.now() - timedelta(days=random.randint(30, 365))
    )
    
    # Créer des transactions
    for j in range(random.randint(1, 5)):
        Transaction.objects.create(
            user=user,
            subscription=subscription,
            amount=10.00,
            status='completed',
            created_at=timezone.now() - timedelta(days=random.randint(1, 180))
        )
```

### Problème: Prédictions semblent incorrectes
**Solutions**:
1. Ré-entraîner avec plus de données
2. Utiliser l'optimisation: `--optimize`
3. Vérifier la qualité des données

### Problème: Erreur d'import scikit-learn
**Solution**:
```bash
pip uninstall scikit-learn
pip install scikit-learn>=1.3.0
```

### Problème: Graphiques ne s'affichent pas
**Cause**: Chart.js non chargé

**Solution**: Vérifier la connexion internet ou télécharger Chart.js localement

## 📈 Bonnes Pratiques

### 1. Ré-entraînement Régulier
- **Churn Model**: Tous les mois
- **Revenue Model**: Tous les mois

### 2. Monitoring des Performances
```bash
# Vérifier les métriques après entraînement
python manage.py train_ml_models --model churn
# Regarder les métriques affichées (Accuracy, ROC-AUC, etc.)
```

### 3. Backup des Modèles
```bash
# Sauvegarder les modèles entraînés
cp -r core/ml/trained_models/ backups/ml_models_$(date +%Y%m%d)/
```

### 4. Validation des Prédictions
- Comparer les prédictions avec les résultats réels
- Ajuster les seuils de risque si nécessaire
- Documenter les faux positifs/négatifs

## 🎓 Cas d'Usage Pratiques

### Cas 1: Campagne de Rétention
```bash
# 1. Identifier les utilisateurs à haut risque
python manage.py generate_predictions --prediction-type churn --high-risk-only

# 2. Dans le dashboard, filtrer par "High Risk"
# 3. Exporter la liste (ou utiliser l'API)
# 4. Envoyer des emails de rétention personnalisés
```

### Cas 2: Planification Budgétaire
```bash
# 1. Obtenir les prévisions de revenus
# Accéder à: /dashboard/ml-insights/revenue-forecast/

# 2. Utiliser les prévisions pour:
#    - Planifier les dépenses marketing
#    - Ajuster les objectifs de vente
#    - Prévoir les embauches
```

## 📚 Ressources Supplémentaires

### Documentation
- `ML_DOCUMENTATION.md` - Documentation technique complète
- `ML_QUICKSTART.md` - Guide de démarrage rapide
- `IMPLEMENTATION_SUMMARY.md` - Résumé de l'implémentation

### Scripts Utiles
- `test_ml_system.py` - Test du système ML
- `manage.py train_ml_models` - Entraînement des modèles
- `manage.py generate_predictions` - Génération des prédictions

### Liens Externes
- [Scikit-learn Docs](https://scikit-learn.org/)
- [Pandas Docs](https://pandas.pydata.org/)
- [Random Forest Explained](https://scikit-learn.org/stable/modules/ensemble.html#forest)

## ✅ Checklist de Déploiement

Avant de déployer en production:

- [ ] Installer toutes les dépendances ML
- [ ] Entraîner tous les modèles avec données réelles
- [ ] Tester les prédictions sur quelques utilisateurs
- [ ] Vérifier les métriques de performance
- [ ] Configurer le ré-entraînement automatique
- [ ] Mettre en place le monitoring
- [ ] Documenter les seuils de risque utilisés
- [ ] Former l'équipe à l'utilisation du dashboard
- [ ] Créer des alertes pour les modèles non entraînés
- [ ] Backup initial des modèles

## 🎉 Félicitations!

Votre système ML est maintenant configuré et prêt à l'emploi!

**Prochaines étapes:**
1. Accéder au dashboard: http://localhost:8000/dashboard/ml-insights/
2. Explorer les différentes analyses
3. Utiliser les insights pour améliorer votre business

**Questions?** Consultez la documentation complète dans `ML_DOCUMENTATION.md`

---

**Créé le**: 23 Octobre 2025  
**Version**: 1.0.0  
**Status**: ✅ Ready to Use
