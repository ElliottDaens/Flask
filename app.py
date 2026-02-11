# -*- coding: utf-8 -*-
"""
Application Flask : site perso + galerie type explorateur (scan du PC) + segmentation K-means.
Chaque utilisateur qui lance le site voit les dossiers et photos sur sa propre machine.
"""

import io
import os
import time
import uuid
from collections import deque
from flask import Flask, render_template, request, send_file, abort, url_for

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

app = Flask(__name__)

# Dossier uploads uniquement (les images segmentées ne sont plus enregistrées sur disque)
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
MAX_SIZE_SEGMENTATION = 800  # taille max (côté) pour accélérer le K-means

# Cache en mémoire des images segmentées (segment_id -> bytes PNG), max 10 entrées
_SEGMENT_CACHE = {}
_SEGMENT_CACHE_ORDER = []
_SEGMENT_CACHE_MAX = 10

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


def segmenter_image(chemin_absolu, k, max_size=MAX_SIZE_SEGMENTATION):
    """
    Segmente une image avec K-means sur les couleurs RGB.
    Ne sauvegarde rien sur disque : retourne (segment_id, bytes_png) pour affichage via cache.
    """
    global _SEGMENT_CACHE, _SEGMENT_CACHE_ORDER
    im = Image.open(chemin_absolu).convert('RGB')
    arr = np.array(im)
    h, w, _ = arr.shape
    if max(h, w) > max_size:
        im.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        arr = np.array(im)
        h, w, _ = arr.shape
    pixels = arr.reshape(-1, 3).astype(np.float64)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    kmeans.fit(pixels)
    centres = kmeans.cluster_centers_.round().astype(np.uint8)
    seg = centres[kmeans.labels_].reshape(h, w, 3)
    img_seg = Image.fromarray(seg)
    buf = io.BytesIO()
    img_seg.save(buf, format='PNG')
    buf.seek(0)
    png_bytes = buf.getvalue()
    segment_id = uuid.uuid4().hex[:16]
    while len(_SEGMENT_CACHE_ORDER) >= _SEGMENT_CACHE_MAX:
        old_id = _SEGMENT_CACHE_ORDER.pop(0)
        _SEGMENT_CACHE.pop(old_id, None)
    _SEGMENT_CACHE[segment_id] = png_bytes
    _SEGMENT_CACHE_ORDER.append(segment_id)
    return segment_id


def _url_carte_embed(lat, lon, zoom=17):
    """
    Construit l'URL d'intégration OpenStreetMap (iframe) à partir des coordonnées.
    Tout le calcul est fait en Python, pas de JavaScript côté page.
    """
    from urllib.parse import urlencode
    n = 2 ** zoom
    delta_lon = 360.0 / n
    delta_lat = 180.0 / n
    min_lon = lon - delta_lon / 2
    max_lon = lon + delta_lon / 2
    min_lat = lat - delta_lat / 2
    max_lat = lat + delta_lat / 2
    bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
    params = {"bbox": bbox, "layer": "mapnik", "marker": f"{lat},{lon}"}
    return "https://www.openstreetmap.org/export/embed.html?" + urlencode(params)


# ========== ROUTE 1 : Page d'accueil (site perso) ==========
@app.route('/')
def home():
    map_lat = 50.952644
    map_lon = 1.877985
    map_zoom = 17
    donnees_perso = {
        'prenom': 'Elliott',
        'nom': 'Daens',
        'sous_titre': 'Développeur en formation · Passionné tech',
        'localisation': 'Calais, Côte d\'Opale',
        'map_lat': map_lat,
        'map_lon': map_lon,
        'map_zoom': map_zoom,
        'map_label': 'ULCO Calais — 50 Rue Ferdinand Buisson, 62100 Calais, France',
        'map_embed_url': _url_carte_embed(map_lat, map_lon, map_zoom),
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


# ========== ROUTE 3 : Segmentation d'image (K-means couleurs) ==========
@app.route('/segmentation', methods=['GET', 'POST'])
def segmentation():
    global _CACHE_PAIRES, _CACHE_TIME
    if request.args.get('rafraichir'):
        _CACHE_PAIRES = None
    paires = get_dossiers_avec_photos(use_cache=True)
    dossiers = [p[0] for p in paires]
    dossier_choisi = request.values.get('dossier', '').strip().replace("\\", "/")
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

    result_original_url = None
    result_segmentee_url = None
    image_choisie = None
    k_utilise = 10
    erreur = None

    if request.method == 'POST':
        dossier_form = (request.form.get('dossier') or '').strip().replace("\\", "/")
        if dossier_form in dossiers:
            dossier_choisi = dossier_form
            images = next((imgs for rel, imgs in paires if rel == dossier_choisi), [])
        img_name = (request.form.get('image') or '').strip()
        try:
            k = int(request.form.get('k', 10))
            k = max(2, min(50, k))
        except (TypeError, ValueError):
            k = 10

        fichier_upload = request.files.get('fichier')
        utiliser_upload = fichier_upload and fichier_upload.filename and _fichier_image(fichier_upload.filename)

        if utiliser_upload:
            os.makedirs(UPLOADS_DIR, exist_ok=True)
            ext = os.path.splitext(fichier_upload.filename)[1].lower() or '.jpg'
            if ext not in EXTENSIONS_IMAGES:
                ext = '.jpg'
            nom_upload = f"up_{uuid.uuid4().hex[:12]}{ext}"
            chemin_upload = os.path.join(UPLOADS_DIR, nom_upload)
            try:
                fichier_upload.save(chemin_upload)
                segment_id = segmenter_image(chemin_upload, k)
                result_original_url = url_for('static', filename=f'uploads/{nom_upload}')
                result_segmentee_url = url_for('serve_segmented', segment_id=segment_id)
                k_utilise = k
            except Exception as e:
                erreur = f"Erreur lors de la segmentation : {e}"
                if os.path.isfile(chemin_upload):
                    try:
                        os.remove(chemin_upload)
                    except OSError:
                        pass
        elif img_name and dossier_choisi:
            chemin_relatif = f"{dossier_choisi}/{img_name}".replace("\\", "/")
            parties = [p for p in chemin_relatif.split("/") if p]
            chemin_absolu = os.path.join(RACINE_SCAN, *parties)
            if not _chemin_autorise(chemin_absolu) or not os.path.isfile(chemin_absolu) or not _fichier_image(img_name):
                erreur = "Image non autorisée ou introuvable."
            else:
                try:
                    segment_id = segmenter_image(chemin_absolu, k)
                    result_original_url = url_for('fichier_galerie', chemin_relatif=chemin_relatif)
                    result_segmentee_url = url_for('serve_segmented', segment_id=segment_id)
                    image_choisie = img_name
                    k_utilise = k
                except Exception as e:
                    erreur = f"Erreur lors de la segmentation : {e}"
        else:
            erreur = "Choisis un dossier et une image dans les listes, ou un fichier avec « Choisir un fichier »."

    return render_template(
        'segmentation.html',
        dossiers=dossiers,
        dossier_choisi=dossier_choisi,
        images=images,
        result_original_url=result_original_url,
        result_segmentee_url=result_segmentee_url,
        image_choisie=image_choisie,
        k_utilise=k_utilise,
        erreur=erreur,
    )


# ========== Service image segmentée (mémoire, pas de fichier sur disque) ==========
@app.route('/segmentation/serve/<segment_id>')
def serve_segmented(segment_id):
    """Sert l'image segmentée depuis le cache mémoire. Rien n'est enregistré sur disque."""
    if not segment_id or len(segment_id) > 32:
        abort(404)
    png_bytes = _SEGMENT_CACHE.get(segment_id)
    if not png_bytes:
        abort(404)
    return send_file(
        io.BytesIO(png_bytes),
        mimetype='image/png',
        as_attachment=False,
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
