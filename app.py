# -*- coding: utf-8 -*-
"""
Application Flask : site perso + galerie type explorateur (scan du PC)
Chaque utilisateur qui lance le site voit les dossiers et photos sur sa propre machine.
"""

import os
import time
from collections import deque
from flask import Flask, render_template, request, send_file, abort

app = Flask(__name__)

# Racine du scan : dossier utilisateur par défaut.
RACINE_SCAN = os.path.expanduser("~")
PROFONDEUR_MAX = 8
MAX_DOSSIERS_GALERIE = 120
EXTENSIONS_IMAGES = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

# Dossiers à ignorer (système, cache) pour ne pas remplir la galerie avec AppData etc.
DOSSIERS_IGNORES = frozenset({
    'appdata', 'application data', 'local', 'roaming', 'locallow',
    'cache', 'caches', '.cache', 'temp', 'tmp', '.tmp',
    'program data', 'program files', 'program files (x86)',
    'windows', 'system volume information', '$recycle.bin',
    'node_modules', '.git', '.svn', '__pycache__',
})

# Cache du scan
_CACHE_PAIRES = None
_CACHE_TIME = 0
CACHE_DURATION_SEC = 300


def _chemin_autorise(chemin_absolu):
    racine = os.path.realpath(RACINE_SCAN)
    cible = os.path.realpath(chemin_absolu)
    return cible == racine or cible.startswith(racine + os.sep)


def _fichier_image(nom):
    return nom.lower().endswith(EXTENSIONS_IMAGES)


def _images_dans_dossier(chemin):
    if not os.path.isdir(chemin):
        return []
    try:
        return sorted(
            f for f in os.listdir(chemin)
            if _fichier_image(f)
        )
    except (PermissionError, OSError):
        return []


def _ignorer_dossier(nom):
    """True si le dossier doit être ignoré (AppData, caches, etc.)."""
    n = nom.lower().strip()
    if n.startswith('.'):
        return True
    return n in DOSSIERS_IGNORES


def _priorite_dossier(nom):
    """Priorité pour le tri : dossiers photos en premier."""
    n = nom.lower()
    if n in ('pictures', 'photos', 'images', 'mes images', 'photo', 'image'):
        return 0
    if n in ('desktop', 'bureau', 'documents', 'downloads', 'téléchargements'):
        return 1
    if n.startswith('pic') or n.startswith('photo') or n.startswith('image'):
        return 0
    return 2


def _scan_bfs():
    """
    Scan en largeur (BFS) : on traite d'abord tous les dossiers de niveau 1 (Pictures, Bureau, etc.),
    puis niveau 2, etc. On ignore AppData et dossiers système. Tri par priorité à chaque niveau.
    """
    resultat = []
    file_attente = deque([(RACINE_SCAN, "", 0)])
    while file_attente and len(resultat) < MAX_DOSSIERS_GALERIE:
        racine, prefixe, profondeur = file_attente.popleft()
        if profondeur >= PROFONDEUR_MAX:
            continue
        try:
            noms = os.listdir(racine)
        except (PermissionError, OSError):
            continue
        sous_dossiers = []
        for nom in noms:
            if _ignorer_dossier(nom):
                continue
            chemin = os.path.join(racine, nom)
            if not os.path.isdir(chemin):
                continue
            rel = os.path.join(prefixe, nom) if prefixe else nom
            rel_slash = rel.replace(os.sep, "/")
            images = _images_dans_dossier(chemin)
            if images:
                resultat.append((rel_slash, images))
                if len(resultat) >= MAX_DOSSIERS_GALERIE:
                    break
            sous_dossiers.append((chemin, rel, profondeur + 1))
        sous_dossiers.sort(key=lambda x: _priorite_dossier(os.path.basename(x[0])))
        for chemin, rel, p in sous_dossiers:
            if len(resultat) >= MAX_DOSSIERS_GALERIE:
                break
            file_attente.append((chemin, rel, p))
    return sorted(resultat, key=lambda x: x[0].lower())


def get_dossiers_avec_photos(use_cache=True):
    """
    Retourne la liste des dossiers avec au moins une image.
    AppData et dossiers système sont exclus. Scan en largeur pour privilégier Pictures, Bureau, etc.
    """
    global _CACHE_PAIRES, _CACHE_TIME
    if use_cache and _CACHE_PAIRES is not None and (time.time() - _CACHE_TIME) < CACHE_DURATION_SEC:
        return _CACHE_PAIRES
    if not os.path.isdir(RACINE_SCAN):
        _CACHE_PAIRES = []
        return []
    paires = _scan_bfs()
    _CACHE_PAIRES = paires
    _CACHE_TIME = time.time()
    return paires


# ========== ROUTE 1 : Page d'accueil (site perso) ==========
@app.route('/')
def home():
    donnees_perso = {
        'prenom': 'Elliott',
        'nom': 'Daens',
        'sous_titre': 'Développeur en formation · Passionné tech',
        'localisation': 'Calais, Côte d\'Opale',
        'map_lat': 50.952644,
        'map_lon': 1.877985,
        'map_zoom': 17,
        'map_label': 'ULCO Calais — 50 Rue Ferdinand Buisson, 62100 Calais, France',
        'presentation': (
            "Je maîtrise les technologies frontend et backend et j'ai un intérêt particulier "
            "pour Docker et la création / maintenance de serveur (NAS, etc.). "
            "Développement full-stack, infrastructures et monitoring font partie de mon quotidien."
        ),
        'technologies': {
            'Frontend': ['HTML5', 'CSS3', 'JavaScript', 'UI/UX Design'],
            'Backend': ['PHP', 'Node.js', 'MySQL', 'BDD'],
            'Infrastructure': ['Docker & Compose', 'Linux', 'Monitoring & Logs', 'Configuration Réseaux'],
        },
        'centres_interet': [
            'Jiu-Jitsu Brésilien',
            'Musculation',
            'Gaming',
            'Formule 1',
            'Cinéma',
            'Tinkering (Vinted, eBay via Bot Python)',
        ],
        'en_apprentissage': [
            'Frameworks Web Avancés & Architecture MVC',
            'Automatisation Serveur',
        ],
        'liens': {
            'GitHub': 'https://github.com/ElliottDaens',
            'LinkedIn': '#',
            'Email': 'mailto:#',
        },
        'photo_profil': 'profil.jpg',
    }
    return render_template('index.html', **donnees_perso)


# ========== ROUTE 2 : Galerie (scan PC) ==========
@app.route('/galerie', methods=['GET'])
def galerie():
    global _CACHE_PAIRES, _CACHE_TIME
    if request.args.get('rafraichir'):
        _CACHE_PAIRES = None
    paires = get_dossiers_avec_photos(use_cache=True)
    dossiers = [p[0] for p in paires]
    dossier_choisi = request.args.get('dossier', '').strip().replace("\\", "/")
    if dossier_choisi not in dossiers and dossiers:
        dossier_choisi = dossiers[0]
    elif not dossiers:
        dossier_choisi = None

    images = []
    if dossier_choisi:
        for rel, imgs in paires:
            if rel == dossier_choisi:
                images = imgs
                break

    return render_template(
        'galerie.html',
        dossiers=dossiers,
        dossier_choisi=dossier_choisi,
        images=images,
    )


# ========== Service des images (fichiers sur le disque) ==========
@app.route('/galerie/fichier/<path:chemin_relatif>')
def fichier_galerie(chemin_relatif):
    """
    Envoie une image située sous RACINE_SCAN.
    chemin_relatif = dossier/relatif/fichier.jpg (avec /). Sécurisé contre path traversal.
    """
    chemin_relatif = chemin_relatif.replace("\\", "/").strip("/")
    if ".." in chemin_relatif:
        abort(403)
    parties = [p for p in chemin_relatif.split("/") if p]
    chemin_absolu = os.path.join(RACINE_SCAN, *parties)
    if not _chemin_autorise(chemin_absolu):
        abort(403)
    if not os.path.isfile(chemin_absolu):
        abort(404)
    if not _fichier_image(os.path.basename(chemin_absolu)):
        abort(403)
    return send_file(chemin_absolu, mimetype=None, as_attachment=False)


# ========== Lancement ==========
if __name__ == '__main__':
    app.run(debug=True, port=5001)
