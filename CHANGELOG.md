# Changelog

## [1.1.0] – 2026-02-11

### Ajouté
- **Page Segmentation** (`/segmentation`) : choix d'une image (même source que la galerie), nombre de couleurs K (2–50), affichage image originale + image segmentée (K-means sur les couleurs RGB). Dépendances : Pillow, numpy, scikit-learn.
- **Carte d'accueil en Python** : l'URL d'embed OpenStreetMap est construite côté serveur (`_url_carte_embed`), plus de JavaScript Leaflet ; affichage en iframe.

### Modifié
- **README** : contenu (Segmentation, carte iframe), structure (templates, requirements).

## [1.0.0] – 2026-02-11

- Page d'accueil (présentation, carte ULCO Calais)
- Galerie d'images (scan des dossiers du PC)
- Dark mode (bouton dans la barre de navigation)
- Styles : charte blanc / noir / rouge
