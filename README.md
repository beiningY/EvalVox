
# Guide d'installation d'EvalVox

Ce guide vous aidera à configurer l'application EvalVox sur votre serveur local pour le développement et les tests. Suivez les étapes ci-dessous pour commencer.

## Cloner le dépôt

Tout d'abord, clonez le dépôt EvalVox sur votre machine locale en utilisant Git :

```
git clone https://github.com/beiningY/EvalVox.git
```

## Naviguer vers le répertoire du projet

Après le clonage, déplacez-vous dans le répertoire du projet :

```
cd EvalVox
```

## Configuration d'un environnement virtuel (Optionnel mais recommandé)

Créer un environnement virtuel n'est pas obligatoire mais fortement recommandé pour éviter les conflits avec d'autres paquets Python sur votre système :

```
python -m venv venv
source venv/bin/activate # Sous Windows, utilisez venv\Scripts\activate
```

## Installation des dépendances du projet

Installez toutes les dépendances nécessaires pour le projet en exécutant :

```
pip install -r requirements.txt
```

Alternativement, vous pouvez installer manuellement les bibliothèques requises :

```
pip install os
pip install json
pip install unicodedata
pip install praatio
pip install beautifulsoup4
pip install spacy
pip install string
pip install unidecode
pip install pyannote.core
pip install pyannote.metrics
pip install io
pip install sys
pip install numpy
pip install jiwer
pip install django
pip install uuid
```

## Démarrer le serveur de développement

Pour démarrer le serveur de développement, exécutez :

```
python manage.py runserver
```

## Accéder à l'application Web

Enfin, ouvrez votre navigateur web et rendez-vous à l'URL suivante pour accéder à l'application EvalVox :

```
http://127.0.0.1:8000/
```

Vous devriez maintenant avoir l'application EvalVox fonctionnant sur votre serveur local. Profitez des tests et du développement !

