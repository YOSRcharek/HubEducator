# 🤖 Machine Learning System Documentation

## Vue d'ensemble

Ce système ML fournit des analyses prédictives et des statistiques avancées pour les abonnements utilisateurs de HubEducator.

## 📊 Modèles Implémentés

### 1. Churn Prediction (Prédiction de Désabonnement)
- **Objectif**: Identifier les utilisateurs à risque de résilier leur abonnement
- **Algorithme**: Random Forest Classifier
- **Features**: 26 caractéristiques incluant l'engagement, l'historique de paiement, et les métriques temporelles
- **Output**: Probabilité de churn (0-100%) et niveau de risque (Low/Medium/High)

### 2. Revenue Forecasting (Prévision de Revenus)
- **Objectif**: Prédire les revenus futurs sur plusieurs périodes
- **Algorithme**: Random Forest Regressor avec features temporelles
- **Features**: Revenus historiques, tendances, lags, rolling statistics
- **Output**: Prévisions mensuelles pour les 6 prochains mois

### 3. LTV Calculator (Calculateur de Valeur Vie Client)
- **Objectif**: Estimer la valeur totale qu'un utilisateur générera
- **Algorithme**: Random Forest Regressor
- **Features**: Historique de transactions, engagement, comportement
- **Output**: LTV actuel, LTV prédit, et potentiel de croissance

## 🚀 Installation

### 1. Installer les dépendances ML

```bash
pip install -r requirements.txt
```

Les packages ML installés:
- `scikit-learn>=1.3.0` - Algorithmes ML
- `pandas>=2.0.0` - Manipulation de données
- `numpy>=1.24.0` - Calculs numériques
- `joblib>=1.3.0` - Sauvegarde de modèles
- `matplotlib>=3.7.0` - Visualisations
- `seaborn>=0.12.0` - Visualisations statistiques
- `imbalanced-learn>=0.11.0` - Gestion des données déséquilibrées

### 2. Structure des fichiers

```
core/
├── ml/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── churn_predictor.py
│   │   ├── revenue_forecaster.py
│   │   └── ltv_calculator.py
│   ├── features/
│   │   ├── __init__.py
│   │   └── feature_engineering.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_preprocessing.py
│   │   └── model_evaluator.py
│   └── trained_models/  (créé automatiquement)
│       ├── churn_predictor.pkl
│       ├── revenue_forecaster.pkl
│       └── ltv_calculator.pkl
```

## 📝 Utilisation

### Entraînement des Modèles

#### Entraîner tous les modèles
```bash
python manage.py train_ml_models
```

#### Entraîner un modèle spécifique
```bash
# Churn prediction
python manage.py train_ml_models --model churn

# Revenue forecasting
python manage.py train_ml_models --model revenue

# LTV calculator
python manage.py train_ml_models --model ltv
```

#### Options avancées
```bash
# Avec optimisation des hyperparamètres (plus lent mais meilleur)
python manage.py train_ml_models --model churn --optimize

# Revenue forecasting par semaine au lieu de mois
python manage.py train_ml_models --model revenue --period week
```

### Génération de Prédictions

#### Générer toutes les prédictions
```bash
python manage.py generate_predictions
```

#### Prédictions spécifiques
```bash
# Seulement churn
python manage.py generate_predictions --prediction-type churn

# Seulement utilisateurs à haut risque
python manage.py generate_predictions --prediction-type churn --high-risk-only

# Seulement LTV
python manage.py generate_predictions --prediction-type ltv
```

## 🌐 Interface Web

### Pages disponibles

1. **ML Insights Dashboard**: `/dashboard/ml-insights/`
   - Vue d'ensemble des modèles ML
   - Statistiques générales
   - Liens vers les analyses détaillées

2. **Churn Predictions**: `/dashboard/ml-insights/churn-predictions/`
   - Liste des utilisateurs à risque
   - Distribution des risques (High/Medium/Low)
   - Probabilités de churn détaillées

3. **Revenue Forecast**: `/dashboard/ml-insights/revenue-forecast/`
   - Graphique de prévision des revenus
   - Insights sur les tendances
   - Prévisions pour les 6 prochains mois

4. **LTV Analysis**: `/dashboard/ml-insights/ltv-analysis/`
   - Classement des utilisateurs par valeur
   - LTV actuel vs prédit
   - Segmentation des clients

### API Endpoints

#### Prédire le churn pour un abonnement
```
GET /dashboard/api/predict-churn/<subscription_id>/
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

#### Obtenir les prévisions de revenus
```
GET /dashboard/api/revenue-forecast/?periods=3
```

Réponse:
```json
{
    "forecasts": [1250.50, 1300.75, 1350.25],
    "insights": {
        "total_revenue": 15000.00,
        "avg_revenue_per_period": 1250.00,
        "revenue_trend": "increasing",
        "growth_rate": 5.2
    }
}
```

#### Prédire le LTV pour un abonnement
```
GET /dashboard/api/ltv-prediction/<subscription_id>/
```

Réponse:
```json
{
    "subscription_id": 123,
    "user_id": 456,
    "current_ltv": 150.00,
    "predicted_ltv": 450.00,
    "ltv_potential": 300.00,
    "predicted_at": "2025-10-23T05:45:00"
}
```

## 🔧 Configuration

### Paramètres des modèles

Les modèles peuvent être configurés dans leurs fichiers respectifs:

**ChurnPredictor** (`core/ml/models/churn_predictor.py`):
```python
ChurnPredictor(model_type='random_forest')  # ou 'gradient_boosting', 'logistic'
```

**RevenueForecaster** (`core/ml/models/revenue_forecaster.py`):
```python
RevenueForecaster(model_type='random_forest')  # ou 'gradient_boosting', 'linear'
```

### Ré-entraînement automatique

Pour automatiser le ré-entraînement mensuel, ajoutez un cron job:

```bash
# Ré-entraîner tous les modèles le 1er de chaque mois à 2h du matin
0 2 1 * * cd /path/to/HubEducator && python manage.py train_ml_models
```

Ou utilisez Celery pour des tâches périodiques dans Django.

## 📈 Métriques de Performance

### Churn Prediction
- **Accuracy**: Précision globale du modèle
- **ROC-AUC**: Aire sous la courbe ROC (0.5-1.0, plus c'est élevé mieux c'est)
- **Precision**: Proportion de vrais positifs parmi les prédictions positives
- **Recall**: Proportion de vrais positifs détectés
- **F1-Score**: Moyenne harmonique de Precision et Recall

### Revenue Forecasting
- **R² Score**: Coefficient de détermination (0-1, plus c'est élevé mieux c'est)
- **MAE**: Mean Absolute Error (erreur moyenne absolue en $)
- **RMSE**: Root Mean Squared Error (erreur quadratique moyenne en $)
- **MAPE**: Mean Absolute Percentage Error (erreur en %)

### LTV Calculator
- **R² Score**: Qualité de la prédiction
- **MAE**: Erreur moyenne en $
- **RMSE**: Erreur quadratique moyenne en $

## 🎯 Cas d'Usage

### 1. Réduire le Churn
```python
# Identifier les utilisateurs à haut risque
predictor = ChurnPredictor()
predictor.load()

high_risk_users = []
for subscription in active_subscriptions:
    pred = predictor.predict(subscription)
    if pred['risk_level'] == 'high':
        high_risk_users.append(subscription.user)

# Envoyer des emails de rétention
for user in high_risk_users:
    send_retention_email(user)
```

### 2. Planification Budgétaire
```python
# Obtenir les prévisions de revenus
forecaster = RevenueForecaster()
forecaster.load()

forecasts = forecaster.forecast(periods_ahead=6)
total_expected = sum(forecasts)

print(f"Revenus attendus sur 6 mois: ${total_expected:.2f}")
```

### 3. Segmentation Client
```python
# Identifier les clients premium
calculator = LTVCalculator()
calculator.load()

premium_users = []
for subscription in subscriptions:
    pred = calculator.predict_ltv(subscription)
    if pred['predicted_ltv'] > 500:
        premium_users.append(subscription.user)

# Offrir des avantages VIP
for user in premium_users:
    grant_vip_access(user)
```

## 🔍 Features Utilisées

### Features Utilisateur
- `account_age_days`: Âge du compte en jours
- `is_teacher`: Est un enseignant (0/1)
- `is_student`: Est un étudiant (0/1)

### Features Abonnement
- `subscription_age_days`: Durée de l'abonnement
- `days_until_end`: Jours restants
- `plan_type`: Type de plan (encodé)
- `amount`: Montant de l'abonnement
- `renewal_count`: Nombre de renouvellements

### Features Transaction
- `total_transactions`: Nombre total de transactions
- `total_spent`: Montant total dépensé
- `avg_transaction_amount`: Montant moyen par transaction
- `transaction_frequency`: Fréquence des transactions
- `days_since_last_payment`: Jours depuis le dernier paiement
- `transactions_last_7d/30d/90d`: Transactions récentes

### Features Engagement
- `courses_created`: Cours créés (teachers)
- `courses_enrolled`: Cours suivis (students)
- `courses_completed`: Cours complétés
- `completion_rate`: Taux de complétion
- `avg_course_students`: Moyenne d'étudiants par cours

### Features Temporelles
- `signup_month`: Mois d'inscription
- `signup_day_of_week`: Jour de la semaine
- `signup_quarter`: Trimestre d'inscription

## 🐛 Troubleshooting

### Erreur: "Model file not found"
**Solution**: Entraînez d'abord le modèle
```bash
python manage.py train_ml_models --model churn
```

### Erreur: "Insufficient data for training"
**Solution**: Assurez-vous d'avoir au moins 10 abonnements avec des transactions
- Créez plus d'abonnements de test
- Attendez d'avoir plus de données réelles

### Erreur: "No module named 'sklearn'"
**Solution**: Installez les dépendances ML
```bash
pip install -r requirements.txt
```

### Les prédictions semblent incorrectes
**Solutions**:
1. Ré-entraînez avec plus de données
2. Utilisez l'optimisation des hyperparamètres: `--optimize`
3. Vérifiez la qualité des données (transactions complètes, dates correctes)

## 📚 Ressources

- [Scikit-learn Documentation](https://scikit-learn.org/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [Random Forest Algorithm](https://scikit-learn.org/stable/modules/ensemble.html#forest)

## 🔄 Maintenance

### Ré-entraînement recommandé
- **Churn Model**: Tous les mois
- **Revenue Model**: Tous les mois
- **LTV Model**: Tous les 2-3 mois

### Monitoring
- Vérifiez régulièrement les métriques de performance
- Comparez les prédictions avec les résultats réels
- Ajustez les seuils de risque si nécessaire

## 📞 Support

Pour toute question ou problème:
1. Consultez cette documentation
2. Vérifiez les logs Django
3. Examinez les métriques de performance des modèles

---

**Version**: 1.0.0  
**Dernière mise à jour**: 23 Octobre 2025
