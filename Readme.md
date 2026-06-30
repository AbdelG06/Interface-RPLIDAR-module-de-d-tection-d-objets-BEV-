# RPLIDAR BEV Detection System

## Description

RPLIDAR BEV Detection System est une application Python développée avec **PySide6** et **PyQtGraph** permettant :

- La visualisation temps réel d'un nuage de points LiDAR.
- L'affichage Bird Eye View (BEV).
- L'affichage de la vue polaire.
- La détection automatique d'objets par clustering DBSCAN.
- Le suivi d'objets avec identifiants persistants.
- L'import de fichiers CSV simulant un RPLIDAR.
- L'export des détections au format CSV et JSON.
- La surveillance d'une zone de sécurité configurable.
- La simulation complète du système sans matériel RPLIDAR.

Le projet est réalisé conformément au cahier des charges :

- Visualisation BEV
- Détection d'objets
- Clustering spatial
- Tracking
- Alertes proximité
- Export des détections
- Architecture modulaire

---

# Fonctionnalités

## Interface graphique

- Interface moderne Dark Mode
- PySide6
- PyQtGraph haute performance
- Zoom
- Pan
- Rafraîchissement temps réel

## Visualisation

### Vue Bird Eye View (BEV)

Affichage cartésien :

- Axe X (mètres)
- Axe Y (mètres)
- Nuage de points
- Boîtes englobantes
- Identifiants objets

### Vue Polaire

Affichage :

- Angle
- Distance

comme un radar classique.

---

# Détection d'objets

La détection repose sur :

```python
sklearn.cluster.DBSCAN

Paramètres :

eps = 0.3
min_samples = 4 

Chaque objet détecté possède :

ID
Centreïde
Distance
Angle
Largeur
Hauteur
Bounding Box
Nombre de points 

Tracking
Le système conserve un identifiant unique pour chaque objet grâce à un tracker basé sur la distance euclidienne.
Exemple : 

Frame 1

ID 1
ID 2
ID 3

Frame 2

ID 1
ID 2
ID 3
`` 

Zone de sécurité
Une alerte est émise lorsqu'un objet entre dans une zone de proximité.
Configuration :

safety_radius = 2.0
` 

exemple : ALERTE - Objet 3 à 1.65 m

Structure du projet : 

project/
│
├── main.py
│
├── config/
│   └── config.json
│
├── models/
│   └── object_detection.py
│
├── lidar/
│   ├── csv_player.py
│   └── csv_recorder.py
│
├── detector/
│   ├── dbscan_detector.py
│   └── tracker.py
│
├── ui/
│   ├── bev_widget.py
│   ├── polar_widget.py
│   ├── bev_overlay.py
│   ├── controls_panel.py
│   ├── detections_table.py
│   ├── metrics_widget.py
│   ├── theme.py
│   └── main_window.py
│
├── utils/
│   ├── alert_manager.py
│   ├── config_loader.py
│   └── json_exporter.py
│
├── data/
│
├── exports/
│
└── fake_scan.csv


Installation
Prérequis

Python 3.10+
Windows 10/11
Linux Ubuntu 22+
KR260 PYNQ


Création environnement virtuel
Windows : 

python -m venv venv 

Activation : 

venv\Scripts\activate 

Linux : source venv/bin/activate

Installation des dépendances : 

pip install pandas
pip install numpy
pip install scipy
pip install scikit-learn
pip install pyqtgraph
pip install PySide6
pip install pyserial
pip install openpyxl 

Génération d'un faux scan
Lancer  : python generate_fake_scan.py 

le fichier : fake_scan.csv ; fake_scan.csv
sera généré automatiquement. 

Format CSV attendu : 

timestamp,angle,distance,quality
0,0,8.0,15
0,1,8.0,15
0,2,8.0,15
...

Lancement : python main.py

Utilisation
Importer un scan
Cliquer : 

IMPORT CSV

Sélectionner : 

fake_scan.csv

Démarrer
Cliquer :

START SCAN

Le système affiche :

BEV
Vue polaire
Objets détectés
Métriques


Arrêter
Cliquer :

STOP SCAN

Technologies utilisées
Interface : PySide6
PyQtGraph


Traitement : 

NumPy
Pandas
SciPy 

Détection :

Scikit-Learn
DBSCAN

Visualisation : 

Bird Eye View
Polar Radar View 

Garwaoui Abdelkrim  & Drissi El Bouzaidi Aya
Copyright © 2026
 