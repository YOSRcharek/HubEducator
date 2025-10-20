# 📚 HubEducator

HubEducator est une plateforme éducative développée avec **Django**, permettant d’offrir un espace numérique d’apprentissage moderne, sécurisé et intelligent.  
Le projet inclut un **système d’authentification avancé**, une **gestion personnalisée des utilisateurs**, et une **architecure extensible pour intégrer à terme une IA éducative (assistant intelligent)**.

---

## 🚀 Fonctionnalités actuelles

✅ **Authentification avancée avec modèle utilisateur personnalisé** (`core.User`)  
✅ **Inscription utilisateur avec génération d’un code de vérification unique**  
✅ **Envoi automatique du code de vérification par email (SMTP configuré)**  
✅ **Vérification d’adresse email via saisie de code à 6 chiffres**  
✅ **Connexion / Déconnexion sécurisée**  
✅ **Gestion du statut utilisateur : email vérifié ou non**  
✅ **Gestion de session via Django Auth**  
✅ **Support des rôles utilisateurs (étudiant, enseignant, admin)**  
✅ **Interface utilisateur pour inscription / connexion / vérification**  
✅ **Connexion à une base de données PostgreSQL (hébergée sur Supabase)**  
✅ **Architecture évolutive prête pour l’ajout de cours, modules IA et chat intelligent**  

---

## 🤖 Fonctionnalités IA prévues (à venir)

🚧 Ces modules sont en phase d’étude et seront intégrés prochainement :

📌 Assistant virtuel intelligent pour répondre aux questions des étudiants  
📌 Génération automatique de quiz/exercices personnalisés  
📌 Analyse de progression et recommandations adaptées  
📌 Interaction multimodale (texte, voix, image)  
📌 Tableau de bord intelligent basé sur l’IA  

---

## 🏗️ Structure du projet (simplifiée)


HubEducator/
├── HubEducator/ # Répertoire principal du projet
│ ├── settings.py # Configuration globale (bd, AUTH_USER_MODEL, email)
│ ├── urls.py # URLs du projet
│ └── wsgi.py / asgi.py
│
├── core/ # App gérant le modèle utilisateur
│ ├── models.py # core.User avec email, code_verification, email_verified
│ └── forms.py
│
├── website/ # App principale (inscription, login, pages)
│ ├── views.py
│ ├── urls.py
│ └── templates/
│
├── venv/ # Environnement virtuel (non versionné sur GitHub)
├── manage.py
└── requirements.txt

---

---

## ⚙️ Technologies utilisées

| Technologie | Usage |
|-------------|--------|
| 🐍 Django (Python) | Backend & Auth |
| 🗄️ PostgreSQL (Supabase) | Base de données |
| 📧 SMTP (Gmail/Supabase) | Envoi des codes par email |
| 🎨 HTML/CSS (Templates Django) | Interface utilisateur |
| 🔐 Django Auth | Gestion sessions / sécurité |
| 🧠 (Prévu) IA - NLP | Assistant éducatif intelligent |

---

## 📦 Installation & exécution

```bash
# 1️⃣ Cloner le projet
git clone https://github.com/YOSRcharek/HubEducator
cd HubEducator

# 2️⃣ Créer un environnement virtuel
python -m venv venv
source venv/Scripts/activate  # Windows
# ou
source venv/bin/activate      # Linux/Mac

# 3️⃣ Installer les dépendances
pip install -r requirements.txt

# 4️⃣ Lancer la base de données et effectuer les migrations
python manage.py makemigrations
python manage.py migrate

# 5️⃣ Démarrer le serveur
python manage.py runserver

📍 Accès : http://127.0.0.1:8000/