# Radar Vision Control

Application Python de visualisation et de detection autour d'un flux LiDAR/CSV, avec interface graphique PySide6, vues radar 2D/3D, clustering DBSCAN, suivi d'objets, alertes de proximite et detection image/video avec YOLOv8.

Le projet peut fonctionner sans capteur physique grace au mode demo et au fichier `fake_scan.csv`.

## Sommaire

- [Fonctionnalites](#fonctionnalites)
- [Architecture generale](#architecture-generale)
- [Installation](#installation)
- [Lancement](#lancement)
- [Utilisation](#utilisation)
- [Format CSV attendu](#format-csv-attendu)
- [Configuration](#configuration)
- [Role de chaque fichier](#role-de-chaque-fichier)
- [Dossiers du projet](#dossiers-du-projet)
- [Exports](#exports)
- [Depannage](#depannage)
- [Limites actuelles](#limites-actuelles)

## Fonctionnalites

- Interface graphique moderne en dark mode.
- Mode demo complet avec scene LiDAR simulee, vehicules, pieton, velo, camion et obstacle.
- Import d'un fichier CSV representant un scan LiDAR.
- Conversion polaire vers cartesien.
- Detection d'objets par clustering DBSCAN.
- Tracking d'objets avec identifiants persistants.
- Vue Bird Eye View, aussi appelee BEV.
- Vue 3D OpenGL du nuage de points.
- Vue polaire angle/distance.
- Tableau des detections avec ID, classe, confiance, distance, position et couleur.
- Alertes de proximite selon un rayon configurable.
- Detection d'objets dans des images avec YOLOv8.
- Detection d'objets dans des videos avec YOLOv8, lecture/pause et radar de distance estimee.
- Export CSV des detections.
- Export PNG des images ou frames annotees.
- Journalisation dans `logs/app.log`.

## Architecture generale

Le point d'entree est `main.py`. Il initialise l'application PySide6, applique le theme sombre, configure les logs, puis ouvre `MainWindow`.

`MainWindow` orchestre ensuite les composants :

1. Recuperation des points depuis le mode demo ou depuis un CSV.
2. Conversion des donnees LiDAR en coordonnees exploitables.
3. Detection par DBSCAN pour les points LiDAR.
4. Normalisation des detections dans un format commun.
5. Tracking via `ObjectTracker`.
6. Verification des alertes avec `AlertManager`.
7. Mise a jour des vues BEV, 3D, polaire, tableau et metriques.

La detection camera/image/video est separee dans des fenetres dediees :

- `ImageDetectorWindow` pour les images.
- `VideoDetectorWindow` pour les videos.
- `YOLODetector` pour charger YOLOv8 et convertir les bounding boxes en detections compatibles avec le reste du projet.

## Installation

### Prerequis

- Python 3.10 ou plus recent.
- Windows 10/11 recommande pour ce depot local.
- Une carte graphique compatible OpenGL pour la vue 3D.
- Connexion internet seulement si les dependances ou le modele YOLO doivent etre telecharges.

### Creation de l'environnement virtuel

```bash
python -m venv venv
```

Activation sous Windows PowerShell :

```powershell
.\venv\Scripts\Activate.ps1
```

Activation sous Windows CMD :

```cmd
venv\Scripts\activate
```

Activation sous Linux/macOS :

```bash
source venv/bin/activate
```

### Installation des dependances

```bash
pip install -r requirements.txt
```

Les dependances principales sont :

- `PySide6` pour l'interface graphique.
- `pyqtgraph` pour les graphes 2D et la vue OpenGL.
- `PyOpenGL` pour la vue 3D.
- `ultralytics` pour YOLOv8.
- `numpy` pour les calculs numeriques.
- `pandas` pour la lecture/export CSV.
- `scikit-learn` pour DBSCAN.

## Lancement

Depuis le dossier du projet :

```bash
python main.py
```

Au lancement, l'application ouvre la fenetre principale `Radar Vision Control`.

## Utilisation

### Mode demo

Le mode demo est le mode par defaut. Il genere une scene LiDAR simulee avec plusieurs objets et un environnement routier.

Boutons utiles :

- `Mode demo` : reactive la simulation.
- `Demarrer scan` : lance ou relance le rafraichissement.
- `Arreter` : stoppe le timer d'acquisition.
- `Exporter CSV` : exporte les detections courantes si elles existent.

### Mode CSV LiDAR

1. Cliquer sur `Importer CSV`.
2. Selectionner un fichier compatible, par exemple `fake_scan.csv`.
3. Cliquer sur `Demarrer scan`.

Le fichier est lu par tranches de 360 lignes, ce qui correspond a un tour de scan dans la logique actuelle.

### Analyse d'image

1. Cliquer sur `Analyser image`.
2. Dans la nouvelle fenetre, cliquer sur `Load Image`.
3. Selectionner une image `.png`, `.jpg`, `.jpeg` ou `.bmp`.
4. Les objets detectes sont affiches avec leurs bounding boxes.

Exports disponibles :

- `Export CSV` pour les detections.
- `Export Annotated PNG` pour l'image annotee.

### Analyse video

1. Cliquer sur `Analyser video`.
2. Dans la nouvelle fenetre, cliquer sur `Importer video`.
3. Selectionner une video `.mp4`, `.avi` ou `.mov`.
4. Cliquer sur `Lecture` pour lire ou `Pause` pour suspendre.

La detection YOLO est lancee toutes les `10` frames par defaut pour limiter la charge CPU/GPU.

Exports disponibles :

- `Export CSV` pour les detections de la frame courante.
- `Export PNG` pour exporter la frame annotee affichee.

### Connexion capteur

Le bouton `Connecter capteur` affiche actuellement un message d'information. L'architecture prevoit l'ajout futur d'un vrai capteur, mais cette version fonctionne principalement avec demo, CSV, image et video.

## Format CSV attendu

Le lecteur CSV attend au minimum les colonnes suivantes :

```csv
timestamp,angle,distance,quality
0,0,8.0,15
0,1,8.0,15
0,2,8.0,15
```

Colonnes utilisees directement :

- `angle` : angle en degres.
- `distance` : distance mesuree.

Colonnes utiles mais pas indispensables dans le traitement actuel :

- `timestamp` : index temporel ou numero de frame.
- `quality` : qualite du point ou intensite du scan.

Pour regenerer un fichier de test :

```bash
python generate_fake_scan.py
```

Cela ecrit un nouveau `fake_scan.csv`.

## Configuration

La configuration principale est dans `config.json`.

```json
{
  "serial_port": "COM3",
  "baudrate": 115200,
  "display_refresh_hz": 10,
  "min_distance": 0.15,
  "max_distance": 12.0,
  "dbscan_eps": 0.30,
  "dbscan_min_samples": 4,
  "safety_radius": 2.0,
  "tracking_distance_threshold": 0.5
}
```

Parametres importants :

- `display_refresh_hz` : frequence de rafraichissement de l'interface.
- `dbscan_eps` : distance maximale entre points voisins pour DBSCAN.
- `dbscan_min_samples` : nombre minimum de points pour former un cluster.
- `safety_radius` : distance en metres sous laquelle une alerte est affichee.
- `tracking_distance_threshold` : distance maximale pour associer une detection a une piste existante.
- `serial_port` et `baudrate` : prevus pour une integration capteur future.
- `min_distance` et `max_distance` : parametres de scan disponibles dans la configuration, mais peu exploites dans le code actuel.

## Role de chaque fichier

| Fichier | Role |
| --- | --- |
| `main.py` | Point d'entree de l'application. Configure les logs, cree `QApplication`, applique le theme et affiche la fenetre principale. |
| `main_window.py` | Fenetre principale. Gere les modes demo/CSV, les boutons, le timer, la detection LiDAR, le tracking, les alertes, les exports et la mise a jour de toutes les vues. |
| `config.json` | Fichier de configuration principal : frequence, DBSCAN, rayon de securite, tracking, port serie prevu. |
| `config_loader.py` | Petit chargeur JSON reutilisable. Il cherche d'abord le chemin donne, puis `config.json` a la racine si besoin. |
| `theme.py` | Feuille de style globale Qt en dark mode. Definit les couleurs et styles generaux des widgets. |
| `controls_panel.py` | Panneau lateral avec les boutons de commande : connexion, start/stop, import CSV, analyse image/video, demo, export. |
| `metrics_widget.py` | Cartes de metriques affichant le nombre de points, le nombre d'objets et les FPS. |
| `bev_widget.py` | Vue Bird Eye View en 2D. Affiche les points, le capteur, les cercles de distance, les boites et labels des detections. |
| `bev_overlay.py` | Ancien module d'overlay BEV. Dessine des rectangles et labels sur un `PlotWidget`, mais la logique actuelle est surtout dans `bev_widget.py`. |
| `lidar_3d_widget.py` | Vue 3D OpenGL du nuage de points et des objets. Utilise `pyqtgraph.opengl` et bascule vers un message d'erreur si OpenGL n'est pas disponible. |
| `polar_widget.py` | Vue polaire angle/distance. Sert a visualiser le scan comme un radar classique. |
| `detections_table.py` | Tableau Qt affichant les detections suivies : ID, nom, classe, confiance, distance, position et couleur. |
| `alert_manager.py` | Verifie si une detection est dans le rayon de securite et produit les messages d'alerte. |
| `csv_player.py` | Charge un CSV, lit les donnees par blocs de 360 lignes et convertit angle/distance en coordonnees cartesiennes. |
| `csv_recorder.py` | Utilitaire simple pour sauvegarder un DataFrame en CSV. Peu utilise dans l'interface actuelle. |
| `dbscan_detector.py` | Detection LiDAR par clustering DBSCAN. Transforme les clusters en objets `ObjectDetection`. |
| `object_detection.py` | Dataclass simple representant une detection issue du clustering LiDAR. |
| `object_tracker.py` | Tracker principal. Normalise les detections en `TrackedDetection`, attribue des IDs persistants et gere les pistes disparues. |
| `tracker.py` | Ancien tracker par centroide. Il attribue des `object_id`, mais le projet utilise principalement `object_tracker.py`. |
| `yolo_detector.py` | Charge YOLOv8 via `ultralytics`, detecte les objets dans les images/frames et estime une position 3D simplifiee depuis les bounding boxes. |
| `image_detector_window.py` | Fenetre d'analyse d'image. Charge une image, lance YOLO, affiche les boxes, liste les objets et exporte CSV/PNG. |
| `video_detector_window.py` | Fenetre d'analyse video. Lit la video avec OpenCV, lance YOLO dans un thread, affiche les detections, un radar camera et les exports. |
| `generate_fake_scan.py` | Script qui genere un faux fichier LiDAR `fake_scan.csv` avec plusieurs zones d'obstacles. |
| `fake_scan.csv` | Donnees de test pour le mode CSV. Contient des angles, distances et qualites simulees. |
| `requirements.txt` | Liste des dependances Python a installer. |
| `yolov8n.pt` | Modele YOLOv8 nano utilise par defaut pour la detection image/video. |
| `Readme.md` | Documentation du projet. |

## Dossiers du projet

| Dossier | Role |
| --- | --- |
| `asset/` | Contient des images et videos de test pour les fonctions image/video. |
| `logs/` | Contient les logs generes par l'application, notamment `app.log`. |
| `venv/` | Environnement virtuel Python local. Il ne fait pas partie du code source a modifier. |
| `__pycache__/` | Cache Python genere automatiquement. Peut etre supprime sans risque, Python le recreera. |
| `.git/` | Donnees internes Git du depot. Ne pas modifier manuellement. |

## Fichiers dans `asset/`

Les fichiers presents servent surtout de medias de test :

- `35553_large.jpg` : image de test.
- `images.jpeg` : image de test.
- `route_au_portugal_avec_voiture_belge.png` : image de route/voiture pour tester YOLO.
- `F1.mp4` : video de test.
- `WhatsApp Video 2026-07-06 at 11.33.36.mp4` : video de test.

## Exports

Depuis la fenetre principale :

- `detections.csv` : detections courantes du mode demo ou CSV.

Depuis la fenetre image :

- `image_detections.csv` : detections YOLO de l'image.
- `annotated_image.png` : image avec bounding boxes.

Depuis la fenetre video :

- `video_detections.csv` : detections YOLO de la frame courante.
- `annotated_frame.png` : frame affichee avec bounding boxes.

## Logs

Au lancement, `main.py` cree le dossier `logs/` si necessaire et ecrit dans :

```text
logs/app.log
```

Les logs sont aussi envoyes dans la console.

## Depannage

### YOLO non charge

Si l'interface indique que YOLO est indisponible :

1. Verifier que les dependances sont installees.
2. Verifier que `ultralytics` est installe.
3. Verifier que `yolov8n.pt` est present ou que le modele peut etre telecharge.

Commande utile :

```bash
pip install ultralytics
```

### Vue 3D indisponible

La vue 3D depend de `pyqtgraph.opengl` et `PyOpenGL`.

```bash
pip install pyqtgraph PyOpenGL
```

Si le probleme persiste, verifier les pilotes graphiques.

### Le CSV ne donne aucune detection

Verifier :

- que les colonnes `angle` et `distance` existent ;
- que les distances sont numeriques ;
- que les parametres `dbscan_eps` et `dbscan_min_samples` ne sont pas trop stricts ;
- que le fichier contient assez de points proches pour former des clusters.

### La video est lente

La detection YOLO peut etre lourde. Dans `video_detector_window.py`, les valeurs importantes sont :

- `detection_interval = 10` : detection toutes les 10 frames.
- `inference_width = 416` : largeur utilisee pour l'inference.

Augmenter `detection_interval` ou diminuer `inference_width` reduit la charge, avec moins de precision ou moins de reactivite.

## Limites actuelles

- Le bouton `Connecter capteur` ne lit pas encore un vrai RPLIDAR.
- Les distances issues de YOLO sont des estimations calculees depuis la taille des bounding boxes, pas une mesure physique.
- `tracker.py`, `bev_overlay.py` et `csv_recorder.py` sont utiles comme modules historiques ou utilitaires, mais ne sont pas au centre du flux actuel.
- Le format CSV est simple et suppose des scans de 360 points par frame.
- La vue 3D depend d'OpenGL et peut etre indisponible sur certaines machines.

## Auteurs

Garwaoui Abdelkrim et Drissi El Bouzaidi Aya.

Copyright 2026.
