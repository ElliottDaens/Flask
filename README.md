# Site perso Flask – Elliott Daens

Projet Flask : page d'accueil personnelle et galerie d'images.

## Contenu

- **Page d'accueil** : présentation, localisation (Calais / Côte d'Opale), carte avec pin ULCO, technologies, centres d'intérêt.
- **Galerie** : explorateur de dossiers du PC (scan du disque), affichage des images par dossier.
- **Dark mode** : bascule clair/sombre avec préférence enregistrée.

## Installation

```bash
pip install -r requirements.txt
```

## Lancer le site

```bash
python app.py
```

Puis ouvrir **http://127.0.0.1:5001** dans le navigateur.

## Structure

- `app.py` : routes et logique (accueil, galerie, service des images)
- `templates/` : base.html, index.html, galerie.html
- `static/css/style.css` : styles (charte blanc / noir / rouge, dark mode)
- `static/images/` : photo de profil (`profil.jpg`) uniquement ; la galerie lit les dossiers du disque.

## Auteur

Elliott Daens
