# Explications pédagogiques – Projet Flask (site perso + galerie)

Ce document t’accompagne pour comprendre tout le projet et pouvoir l’expliquer à ton professeur. Il suit le plan demandé : structure, installation, code, templates, CSS, gestion des images, rappels de cours, et résumé final.

---

## 1. Structure du projet

Voici l’arborescence du projet telle qu’elle est organisée :

```
flask/
  app.py                    # Point d'entrée : routes et logique Flask
  requirements.txt          # Dépendances (Flask)
  EXPLICATIONS_PEDAGOGIQUES.md   # Ce fichier
  templates/                # Templates HTML (Jinja2)
    base.html               # Modèle commun : head, nav, footer
    index.html              # Page d'accueil (site perso + carte de localisation)
    galerie.html            # Page galerie d'images
  static/                   # Fichiers statiques servis par Flask
    css/
      style.css             # Feuille de style (charte blanc / noir / rouge)
    images/                 # Images du site
      profil.jpg            # Photo de profil pour la page perso
      # La galerie charge les images depuis les dossiers du PC (scan disque)
```

### Rôle de chaque élément

| Fichier / Dossier | Rôle |
|-------------------|------|
| **app.py** | Cœur de l’application : définit les routes (URL → fonction Python) et envoie les données aux templates. |
| **templates/** | Fichiers HTML avec la syntaxe Jinja2 (`{{ variable }}`, `{% block %}`, etc.). Flask y injecte les variables et génère le HTML final. |
| **base.html** | Template de base : structure commune (head, menu, zone de contenu, footer). Les autres pages « héritent » de ce template et ne remplissent que les blocs (title, content). |
| **index.html** | Page d’accueil : présentation (prénom, nom, texte, centres d’intérêt, photo de profil). |
| **galerie.html** | Page galerie : liste déroulante des catégories, miniatures, et grande image au clic. |
| **static/** | Tout ce qui est « statique » (CSS, images, JS) : Flask sert ces fichiers tels quels à l’URL `/static/...`. |
| **static/css/style.css** | Mise en forme du site (charte blanc / noir / accents rouges, menu, profil, carte de localisation, galerie). |
| **static/images/** | Photo de profil (`profil.jpg`) à la racine. La galerie affiche les images des dossiers du PC (scan disque). |

---

## 2. Installation et lancement

### Créer un environnement virtuel (recommandé pour le cours)

Cela évite de mélanger les paquets du projet avec le reste de ton Python.

```bash
# Dans le dossier flask (ou à la racine du projet)
python -m venv venv
```

- **python -m venv venv** : crée un dossier `venv` contenant un Python isolé et un `pip` dédié au projet.

Activer l’environnement :

- **Windows (PowerShell)** : `.\venv\Scripts\Activate.ps1`
- **Windows (cmd)** : `venv\Scripts\activate.bat`
- **Linux / macOS** : `source venv/bin/activate`

Une fois activé, le préfixe `(venv)` apparaît dans le terminal.

### Installer Flask

```bash
pip install -r requirements.txt
```

- **pip install -r requirements.txt** : installe les versions indiquées dans `requirements.txt` (ici Flask). Tu peux aussi faire `pip install Flask` si tu n’utilises pas le fichier.

### Lancer l’application

```bash
# Méthode 1 (recommandée)
flask run --port 5001

# Méthode 2 (si tu as if __name__ == '__main__' dans app.py)
python app.py
```

- **flask run** : lance le serveur de développement Flask. Par défaut l’URL est `http://127.0.0.1:5000` ; avec `--port 5001` ce sera `http://127.0.0.1:5001`.
- **python app.py** : exécute `app.py` ; le `if __name__ == '__main__': app.run(...)` lance alors le serveur (ici en port 5001).

Ouvre un navigateur et va sur `http://127.0.0.1:5001` pour voir le site.

---

## 3. Code Flask principal (app.py)

Le code complet est dans le fichier `app.py`. Voici ce que fait chaque partie.

### Imports et configuration

```python
import os
from flask import Flask, render_template, request

app = Flask(__name__)
DOSSIER_IMAGES = os.path.join(app.static_folder, 'images')
```

- **Flask** : classe qui représente l’application.
- **render_template** : permet de renvoyer une page HTML générée à partir d’un fichier du dossier `templates/` et de variables.
- **request** : accès aux paramètres de la requête (ex. `?categorie=paysages`).
- **app.static_folder** : chemin du dossier `static/`. On en déduit le chemin de `static/images/` pour lister les sous-dossiers et les images.

### Fonction `get_categories()`

- **Rôle** : retourner la liste des noms des sous-dossiers de `static/images/` (paysages, animaux, dessins, etc.).
- **Méthode** : `os.listdir(DOSSIER_IMAGES)` donne tous les noms ; on garde seulement ceux qui sont des dossiers avec `os.path.isdir(...)`.
- Ces noms serviront à remplir la liste déroulante de la galerie.

### Fonction `get_images(categorie)`

- **Rôle** : retourner la liste des noms de fichiers image d’un sous-dossier donné (ex. `paysages`).
- **Méthode** : on parcourt le contenu du dossier `static/images/<categorie>/` et on ne garde que les fichiers dont l’extension est `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`.

### Route `/` (page d’accueil)

```python
@app.route('/')
def home():
    donnees_perso = {
        'prenom': 'Elliott', 'nom': 'Daens',
        'localisation': 'Calais, Côte d\'Opale',
        'map_lat': 50.9492, 'map_lon': 1.8618, 'map_zoom': 18,
        'map_label': '50 Rue Ferdinand Buisson, 62100 Calais, France',
        # ... présentation, technologies, centres d'intérêt, liens, photo_profil
    }
    return render_template('index.html', **donnees_perso)
```

- **@app.route('/')** : associe l’URL « / » à la fonction `home()`. Quand un visiteur ouvre la page d’accueil, c’est cette fonction qui est exécutée.
- **render_template('index.html', **donnees_perso)** : Flask génère le HTML à partir de `templates/index.html` et passe toutes les clés de `donnees_perso` comme variables au template (dans le template tu pourras utiliser `{{ prenom }}`, `{{ nom }}`, `{{ map_lat }}`, etc.).
- **Carte** : les champs `map_lat`, `map_lon`, `map_zoom` et `map_label` dans `donnees_perso` servent à afficher une carte (Leaflet + OpenStreetMap) avec un pin à l'adresse indiquée (ex. 50 Rue Ferdinand Buisson, 62100 Calais). Pour changer d'adresse, modifie ces quatre valeurs dans `app.py`.

### Route `/galerie`

```python
@app.route('/galerie', methods=['GET'])
def galerie():
    categories = get_categories()
    categorie_choisie = request.args.get('categorie', '').strip()
    # Si la catégorie n'est pas dans la liste, on prend la première
    if categorie_choisie not in categories and categories:
        categorie_choisie = categories[0]
    images = get_images(categorie_choisie) if categorie_choisie else []
    return render_template('galerie.html', categories=categories,
                           categorie_choisie=categorie_choisie, images=images)
```

- **request.args.get('categorie', '')** : récupère le paramètre d’URL `?categorie=paysages`. S’il est absent, on utilise la première catégorie (ou aucune si la liste est vide).
- On calcule **categories**, **categorie_choisie** et **images**, puis on les envoie au template **galerie.html**.

### Lancement du serveur

```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)
```

- **if __name__ == '__main__'** : ce bloc ne s’exécute que lorsque tu lances le fichier avec `python app.py` (pas quand un autre module importe `app`).
- **debug=True** : rechargement automatique quand tu modifies le code et messages d’erreur détaillés dans le navigateur (à désactiver en production).

---

## 4. Templates HTML (Jinja2)

### base.html

- Contient la structure commune : `<!DOCTYPE html>`, `<head>`, lien vers le CSS, `<nav>`, `<main>` avec `{% block content %}`, `<footer>`.
- **{% block title %}** et **{% block content %}** : des « emplacements » que les autres templates remplissent avec **{% block title %}...{% endblock %}** et **{% block content %}...{% endblock %}`.
- **{{ url_for('static', filename='css/style.css') }}** : Jinja2 appelle la fonction Flask `url_for` pour générer l’URL du fichier CSS (ex. `/static/css/style.css`). Ainsi, si tu déplaces l’app, les URLs restent correctes.
- **Dark mode** : un script dans le `<head>` lit au chargement la clé `theme` dans `localStorage` et pose `data-theme="light"` ou `data-theme="dark"` sur `<html>`, ce qui évite un flash de thème incorrect. Un **bouton** (`.theme-toggle`) dans la barre de navigation permet de basculer entre mode clair et mode sombre ; au clic, un second script met à jour `data-theme`, enregistre le choix dans `localStorage` et adapte le libellé du bouton (« Sombre » / « Clair ») et l’icône (lune / soleil). Toute la mise en forme dépend des variables CSS, donc le dark mode repose sur les règles `[data-theme="dark"]` dans le CSS.

### index.html (page perso)

- **{% extends "base.html" %}** : ce template hérite de `base.html`. Il ne définit que les blocs qu’il remplit (title, content).
- **{{ prenom }}**, **{{ nom }}**, **{{ localisation }}**, **{{ presentation }}** : variables passées depuis `app.py` (donnees_perso).
- **Carte de localisation** : si `map_lat` et `map_lon` sont définis, un bloc « Où me trouver » affiche une carte. Le template insère une `<div id="map">` avec des attributs `data-lat`, `data-lon`, `data-zoom`, `data-label` remplis par les variables Flask. Un script (Leaflet) lit ces attributs au chargement et affiche la carte OpenStreetMap avec un marqueur (pin) ; au clic sur le pin, une bulle affiche `map_label` (ex. « 50 Rue Ferdinand Buisson, 62100 Calais, France »).
- **{% for interet in centres_interet %}** … **{% endfor %}** : boucle pour afficher chaque centre d’intérêt.
- **url_for('static', filename='images/' ~ photo_profil)** : URL de la photo de profil. Le `~` en Jinja2 concatène les chaînes.

### galerie.html

- **{% if categories %}** … **{% endif %}** : n’affiche le formulaire et la galerie que s’il existe au moins une catégorie.
- **{% for cat in categories %}** : remplit la liste déroulante avec chaque sous-dossier de `static/images/`.
- **{% if cat == categorie_choisie %}selected{% endif %}** : l’option correspondant à la catégorie choisie est marquée comme sélectionnée.
- Pour chaque image : **url_for('static', filename='images/' ~ categorie_choisie ~ '/' ~ img)** produit l’URL complète (ex. `/static/images/paysages/montagne.jpg`).
- Le petit script JavaScript permet de changer de catégorie en redirigeant vers `/galerie?categorie=...` et d’afficher l’image cliquée dans le grand cadre.

---

## 5. Fichiers statiques (CSS)

Le fichier **static/css/style.css** contient la mise en forme (charte blanc / noir / accents rouges) :

- **Variables CSS** : en plus des couleurs, le fichier définit des variables pour les rayons (`--radius-sm`, `--radius-md`, `--radius-lg`), les ombres (`--shadow-sm`, `--shadow-md`, `--shadow-lg`), la transition (`--transition`) et un rouge atténué pour les effets de focus/hover (`--rouge-light`). En dark mode, ces variables sont redéfinies dans `[data-theme="dark"]`.
- Mise en page générale (police, fond, conteneur, `scroll-behavior: smooth`).
- **Navigation** : barre **sticky** en haut au scroll, liens avec soulignement animé au survol, **bouton dark mode** (`.theme-toggle`). La nav a un **z-index: 1100** pour rester au-dessus de la carte Leaflet (qui utilise des z-index élevés) lors du défilement.
- **Mode sombre (dark mode)** : le sélecteur **`[data-theme="dark"]`** redéfinit les variables CSS (fond sombre, texte clair, bordures, rouge plus vif, ombres adaptées). La nav et le footer restent en fond sombre. En galerie, le **select** (liste déroulante des catégories) a un fond et un texte explicites en dark mode (`background: #2a2a2a`, `color: #e8e8e8`) pour rester lisibles.
- Page perso : carte de profil (photo, blocs technologies en encadrés, centres d’intérêt en pastilles avec hover), **carte de localisation** (Leaflet avec bordure, popup du pin en rouge).
- Galerie : select stylisé avec flèche personnalisée, zone de miniatures, cadre pour la grande image, effets hover sur les miniatures.

### Comment Flask sert les fichiers statiques

- Tout fichier placé dans **static/** est accessible à l’URL **/static/...**.
- Exemple : `static/css/style.css` → `http://127.0.0.1:5001/static/css/style.css`.
- Dans les templates, on n’écrit pas cette URL en dur : on utilise **url_for('static', filename='css/style.css')** pour que Flask génère le bon chemin. C’est la bonne pratique.

---

## 6. Gestion des images

### Où mettre les fichiers

- **Photo de profil (page d’accueil)** : un seul fichier, directement dans **static/images/**, par exemple :
  - **profil.jpg** ou **profil.png**
  - Chemin complet côté projet : `flask/static/images/profil.jpg`
- **Galerie** : une catégorie = un sous-dossier de **static/images/**.
  - Exemples :
    - `static/images/paysages/montagne.jpg`, `static/images/paysages/lac.png`
    - `static/images/animaux/chien.jpg`, `static/images/animaux/chat.png`
    - `static/images/dessins/croquis.png`

### Comment le code retrouve les dossiers et les images

1. **get_categories()** : lit le contenu de `static/images/` avec `os.listdir` et ne garde que les noms qui sont des dossiers → ce sont les options de la liste déroulante.
2. **get_images(categorie)** : lit le contenu de `static/images/<categorie>/` et ne garde que les fichiers dont l’extension est une extension d’image connue.
3. Dans le template, l’URL d’une image est construite avec **url_for('static', filename='images/' ~ categorie_choisie ~ '/' ~ img)**. Par exemple pour `categorie_choisie = "paysages"` et `img = "montagne.jpg"`, on obtient `/static/images/paysages/montagne.jpg`.

### Exemples concrets de noms de fichiers

- Page perso : **static/images/profil.jpg**
- Galerie :
  - **static/images/paysages/montagne.jpg**
  - **static/images/animaux/chien.png**

Tu peux en ajouter d’autres dans les mêmes dossiers ; ils apparaîtront automatiquement dans la galerie.

---

## 7. Rappels et points à retenir

### Route Flask

- Une **route** associe une URL à une fonction Python.
- Exemple : `@app.route('/galerie')` signifie que lorsque quelqu’un demande `/galerie`, Flask appelle la fonction `galerie()` et renvoie ce qu’elle retourne (ici le résultat de `render_template(...)`).

### Template

- Un **template** est un fichier HTML contenant des « trous » (variables et blocs) remplis par Flask/Jinja2.
- On utilise **render_template('nom.html', variable=value)** pour générer le HTML final en passant des variables au template.

### Variable de contexte

- Les noms passés à **render_template** (par ex. `prenom`, `nom`, `categories`, `images`) sont les **variables de contexte**.
- Dans le template, on les affiche avec **{{ nom }}** et on peut faire des boucles ou des conditions avec **{% for %}**, **{% if %}**, etc.

### Jinja2 en bref

- **{{ expression }}** : affiche le résultat de l’expression (texte inséré dans le HTML).
- **{% ... %}** : instruction (bloc, boucle, condition) sans affichage direct.
- **{% extends "base.html" %}** : héritage du template de base.
- **{% block content %}** … **{% endblock %}** : définition du contenu d’un bloc.

### Où modifier quoi

- **Présentation, prénom, nom, localisation, centres d’intérêt, technologies, liens** : dans **app.py**, dans le dictionnaire **donnees_perso** de la fonction **home()**.
- **Carte (localisation)** : dans **app.py**, toujours dans **donnees_perso** : `map_lat`, `map_lon` (coordonnées GPS), `map_zoom` (niveau de zoom, ex. 18 pour une rue), `map_label` (texte affiché dans la bulle au clic sur le pin). Exemple : pour une autre adresse, change ces quatre valeurs (tu peux récupérer lat/lon sur [OpenStreetMap](https://www.openstreetmap.org) en cliquant sur la carte).
- **Catégories d’images** : en créant ou supprimant des sous-dossiers dans **static/images/** (pas besoin de toucher au code).
- **Style (couleurs, polices, mise en page)** : dans **static/css/style.css**.
- **Dark mode** : le bouton dans la nav est dans **base.html** (HTML + deux petits scripts). Les couleurs du mode sombre sont dans **static/css/style.css** sous `[data-theme="dark"]`. Le choix de l’utilisateur est stocké dans **localStorage** (clé `theme`) pour être conservé entre les visites.

---

## 8. Vérification finale – Résumé pour le professeur

### Fonctionnement global

1. **Lancement** : dans le dossier du projet, activer l’environnement virtuel puis lancer `flask run --port 5001` ou `python app.py`. Ouvrir `http://127.0.0.1:5001`.
2. **Page d’accueil** : présente le prénom, le nom, la localisation (ex. Calais, Côte d’Opale), un texte de présentation, les technologies, les centres d’intérêt, les liens et une photo de profil. Une **carte interactive** (Leaflet + OpenStreetMap) affiche un pin à l’adresse configurée (ex. 50 Rue Ferdinand Buisson, 62100 Calais, France) ; au clic sur le pin, une bulle affiche l’adresse complète. Les données viennent de `app.py` et sont affichées via le template `index.html`.
3. **Page galerie** : une liste déroulante permet de choisir un sous-dossier de `static/images/` (paysages, animaux, dessins…). Les images de ce dossier sont affichées en miniatures ; un clic sur une miniature l’affiche en grand dans le cadre prévu. Les URLs des images passent par le dossier **static/** (servi par Flask).
4. **Dark mode** : un bouton dans la barre de navigation permet de basculer entre thème clair et thème sombre. Le choix est enregistré dans le navigateur (`localStorage`) et réappliqué à chaque visite.
5. **Technologies** : Flask (routes et logique), Jinja2 (templates HTML), CSS (variables + thème clair/sombre), JavaScript (carte Leaflet, bascule dark mode), fichiers statiques pour les images et le CSS.

### Phrases types pour l’oral

- « J’ai fait un site avec Flask : une page d’accueil perso et une page galerie qui affiche les images selon le dossier choisi. »
- « Les routes sont dans app.py : “/” pour l’accueil et “/galerie” pour la galerie. Les données sont passées aux templates avec render_template. »
- « Les images sont dans static/images/, avec un sous-dossier par catégorie. Le code liste ces dossiers et les fichiers image avec os.listdir, puis envoie les listes au template. »
- « Les templates héritent de base.html pour le menu et la structure. La page perso inclut une carte (Leaflet) avec un pin sur mon adresse ; les coordonnées et le texte du pin viennent de app.py. La galerie utilise une liste déroulante et des miniatures ; un peu de JavaScript permet de changer de catégorie et d’afficher l’image cliquée en grand. »
- « Le dark mode est géré en JavaScript : au clic sur le bouton, on change l’attribut `data-theme` sur la balise html et on enregistre le choix dans localStorage. Le CSS utilise des variables ; en mode dark on les redéfinit avec `[data-theme="dark"]`, donc tout le site suit sans dupliquer les règles. »

Tu peux utiliser ce fichier comme support pour réviser et pour présenter le projet à ton professeur. Bon courage pour ta présentation.
