# AI Horizon

Un projet de veille technologique automatisée en Intelligence Artificielle.

## Description

Ce projet a pour objectif de collecter, analyser et exposer des informations sur les dernières avancées en intelligence artificielle (articles, vidéos, études scientifiques).  
Il fournit une API rapide et sécurisée pour consulter ces données et intègre un système de monitoring et de gestion d'incidents pour assurer la fiabilité de la plateforme.

## Fonctionnalités principales

- Collecte automatisée via flux RSS et scraping ciblé
- Alimentation automatique de la base de données via `data_pipeline_runner.py`
- Initialisation rapide de la base avec `init_db.sql`
- API RESTful construite avec FastAPI
- Frontend léger développé avec Flask
- Extraction de mots-clés et détection de technologies
- Monitoring applicatif et alertes automatiques
- Tests unitaires, d'intégration et de bout en bout
- Pipeline de tests et monitoring via GitHub Actions
- Gestion sécurisée des utilisateurs et des accès API

## Installation locale

### Prérequis

- Python 3.10+
- MySQL (ou autre base de données compatible)
- Un environnement virtuel Python (recommandé)

### Étapes d'installation

1. Clonez le dépôt :

    ```bash
    git clone https://github.com/NoemieRondel/Projet-de-certification
    cd Projet-de-certification
    ```

2. Installez les dépendances :

    ```bash
    pip install -r requirements.txt
    ```

3. Configurez votre fichier `.env`.

4. Initialisez votre base de données :

    - Créez une base MySQL vide.
    - Exécutez le script `init_db.sql` pour créer les tables nécessaires :

    ```bash
    mysql -u votre_utilisateur -p votre_base < scripts/init_db.sql
    ```

5. Lancez l'API FastAPI :

    ```bash
    uvicorn app.main:app --reload
    ```

    L'API sera disponible sur [http://localhost:8000](http://localhost:8000).

6. Lancez le frontend Flask (dans le dossier `dashboard`) :

    ```bash
    python app/dashboard/run.py
    ```

    Le frontend sera disponible sur [http://localhost:5000](http://localhost:5000).

## Pipeline de collecte et alimentation de la base

Pour lancer le processus de collecte des données et alimenter automatiquement la base de données :

```bash
python scripts/data_pipeline_runner.py
```

Ce script récupère les dernières données (articles, vidéos, publications scientifiques) et les insère dans votre base.

### Lancer les tests

## Tests unitaires (à lancer localement)

```bash
pytest tests/unit
```
## Tests d'intégration et de monitoring (GitHub Actions)
Ils sont exécutés automatiquement lors de chaque push ou pull request sur GitHub.

Les tests automatisés incluent :

Tests d'intégration complet (register -> login -> accès protégé)

Tests end-to-end sur l'ensemble du flux

Les résultats des tests sont visibles dans l'onglet Actions de votre dépôt GitHub.

### Documentation API
Une documentation interactive est disponible après le démarrage du serveur :

Swagger UI : http://localhost:8000/docs


