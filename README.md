# SARN - Système d'Archivage et de Référencement Numérique

## Structure du projet

```
archive_project/
│
├── .env
├── db.sqlite3
├── manage.py
├── archive_masm/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
├── core/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── auth.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── base_2.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── add_archive.html
│   │   ├── add_archive_folder.html
│   │   ├── add_archive_secretariat.html
│   │   ├── archives_list.html
│   │   ├── permissions_folder.html
│   │   ├── permissions_piece.html
│   │   ├── profiles.html
│   │   ├── users.html
│   │   ├── trash.html
│   │   └── ...
│   ├── utils/
│   │   └── crypto.py
│
├── media/
│   └── pieces/
```

---

## Description des dossiers et fichiers

### Racine du projet

- **.env**  
  Fichier de configuration des variables d’environnement (ex : clés secrètes, paramètres DB).

- **db.sqlite3**  
  Base de données SQLite utilisée par Django.

- **manage.py**  
  Script principal pour lancer les commandes Django (runserver, migrate, createsuperuser, etc.).

---

### Dossier `archive_masm/`  
Configuration principale du projet Django.

- **__init__.py**  
  Indique que ce dossier est un package Python.

- **asgi.py**  
  Point d’entrée ASGI pour le déploiement asynchrone.

- **settings.py**  
  Paramètres globaux du projet (DB, apps, sécurité, etc.).

- **urls.py**  
  Définition des routes principales du projet.

- **wsgi.py**  
  Point d’entrée WSGI pour le déploiement classique.

---

### Dossier `core/`  
Application principale contenant la logique métier.

- **__init__.py**  
  Indique que ce dossier est un package Python.

- **admin.py**  
  Configuration de l’interface d’administration Django.

- **apps.py**  
  Configuration de l’application Django.

- **auth.py**  
  Backend d’authentification personnalisé (connexion par email ou matricule).

- **forms.py**  
  Définition des formulaires Django (inscription, login, création d’archives, etc.).

- **models.py**  
  Définition des modèles de données (utilisateurs, dossiers, pièces, permissions, historique…).

- **tests.py**  
  Tests unitaires de l’application.

- **views.py**  
  Logique des vues (fonctions qui traitent les requêtes et renvoient les templates).

- **migrations/**  
  Scripts de migration de la base de données (création/modification des tables).

- **templates/**  
  Fichiers HTML des pages de l’application (voir détails ci-dessous).

- **utils/**  
  Fonctions utilitaires, par exemple :  
  - **crypto.py** : chiffrement/déchiffrement des fichiers.

---

### Dossier `core/templates/`  
Templates HTML pour le rendu des pages.

- **base.html / base_2.html**  
  Templates de base hérités par toutes les pages.

- **dashboard.html**  
  Tableau de bord avec statistiques et graphiques.

- **login.html / register.html**  
  Pages de connexion et d’inscription.

- **add_archive.html**  
  Choix du type d’archive à créer.

- **add_archive_folder.html**  
  Formulaire de création de dossier avec pièces.

- **add_archive_secretariat.html**  
  Formulaire de création de documents indépendants (secrétariat).

- **archives_list.html**  
  Liste et recherche des archives (dossiers et pièces).

- **permissions_folder.html / permissions_piece.html**  
  Gestion des droits d’accès sur dossiers/pièces.

- **profiles.html**  
  Page de profil utilisateur.

- **users.html**  
  Gestion des utilisateurs (admin/chef).

- **trash.html**  
  Corbeille : gestion des éléments supprimés.

- **...**  
  D’autres templates pour les types, l’organisation, etc.

---

### Dossier `media/pieces/`  
Stockage des fichiers archivés (pièces jointes, documents…).

---

## Démarrage rapide

1. Installer les dépendances Python (voir requirements.txt si disponible).
2. Configurer `.env` si besoin.
3. Appliquer les migrations :  
   ```sh
   python manage.py migrate
   ```
4. Créer un superutilisateur :  
   ```sh
   python manage.py createsuperuser
   ```
5. Lancer le serveur :  
   ```sh
   python manage.py runserver
   ```

---

## Contact

Pour toute question, contactez l’équipe de développement.0