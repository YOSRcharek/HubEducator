# 🚀 ML Quick Start Guide

## Installation Rapide

### 1. Installer les dépendances ML
```bash
pip install -r requirements.txt
```

### 2. Entraîner les modèles
```bash
# Entraîner tous les modèles (recommandé pour la première fois)
python manage.py train_ml_models

# Ou entraîner individuellement
python manage.py train_ml_models --model churn
python manage.py train_ml_models --model revenue
python manage.py train_ml_models --model ltv
```

### 3. Générer des prédictions
```bash
python manage.py generate_predictions
```

### 4. Accéder au Dashboard ML
Ouvrez votre navigateur et allez à:
```
http://127.0.0.1:8000/dashboard/ml-insights/
```

## 📊 Pages Disponibles

- **ML Dashboard**: `/dashboard/ml-insights/`
- **Churn Predictions**: `/dashboard/ml-insights/churn-predictions/`
- **Revenue Forecast**: `/dashboard/ml-insights/revenue-forecast/`
- **LTV Analysis**: `/dashboard/ml-insights/ltv-analysis/`

## ⚠️ Prérequis

Pour que les modèles fonctionnent correctement, vous devez avoir:
- Au moins 10 abonnements actifs
- Des transactions complétées
- Des données historiques (plus il y en a, mieux c'est)

## 🔄 Ré-entraînement

Il est recommandé de ré-entraîner les modèles:
- **Churn**: Tous les mois
- **Revenue**: Tous les mois
- **LTV**: Tous les 2-3 mois

```bash
# Ré-entraîner tous les modèles
python manage.py train_ml_models
```

## 📈 Métriques Clés

### Churn Prediction
- **ROC-AUC > 0.7**: Bon modèle
- **ROC-AUC > 0.8**: Excellent modèle

### Revenue Forecast
- **R² > 0.7**: Bonnes prédictions
- **MAPE < 20%**: Erreur acceptable

### LTV Calculator
- **R² > 0.6**: Prédictions utilisables
- **MAE**: Erreur moyenne en dollars

## 🎯 Cas d'Usage Rapides

### Identifier les utilisateurs à risque
```bash
python manage.py generate_predictions --prediction-type churn --high-risk-only
```

### Prévoir les revenus des 3 prochains mois
Accédez à: `/dashboard/ml-insights/revenue-forecast/`

### Trouver vos clients les plus précieux
Accédez à: `/dashboard/ml-insights/ltv-analysis/`

## 🐛 Problèmes Courants

### "Model file not found"
➡️ Entraînez d'abord: `python manage.py train_ml_models`

### "Insufficient data"
➡️ Créez plus d'abonnements et de transactions de test

### Prédictions incorrectes
➡️ Ré-entraînez avec `--optimize`: `python manage.py train_ml_models --optimize`

## 📚 Documentation Complète

Pour plus de détails, consultez: `ML_DOCUMENTATION.md`

---

**Besoin d'aide?** Consultez la documentation complète ou les logs Django.
