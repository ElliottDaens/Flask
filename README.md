# Site perso Flask – Elliott Daens

Projet Flask : page d'accueil personnelle, galerie d'images et segmentation K-means.

## Contenu

- **Page d'accueil** : présentation, localisation (Calais / Côte d'Opale), carte (iframe OpenStreetMap générée en Python), technologies, centres d'intérêt.
- **Galerie** : explorateur de dossiers du PC (scan du disque), affichage des images par dossier.
- **Segmentation** : choix d'une image + nombre de couleurs K → affichage image originale et image segmentée (K-means sur les couleurs).
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

- `app.py` : routes (accueil, galerie, segmentation, service des images), logique K-means, URL carte (Python)
- `templates/` : base.html, index.html, galerie.html, segmentation.html
- `static/css/style.css` : styles (charte blanc / noir / rouge, dark mode)
- `static/images/` : photo de profil (`profil.jpg`) ; galerie et segmentation lisent les dossiers du disque
- `static/segmented/` : images segmentées générées (ignoré par git)

## Auteur

Elliott Daens
