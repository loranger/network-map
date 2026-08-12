# Network Map

Interface web de cartographie et documentation du réseau local.

Liste, scanne, documente et visualise les périphériques réseau (ordinateurs, IoT, switches, points d'accès WiFi mesh, routeurs, modems, serveurs) ainsi que leurs interconnexions sous forme de graphe orienté.

## Démarrage rapide

```bash
git clone <url> && cd network-map
docker compose up -d --build
```

Le frontend est accessible sur `http://<serveur>:8080`, l'API backend sur le port `8000`.

## Configuration

Copier `.env.example` vers `.env` à la racine du projet et ajuster :

| Variable | Rôle | Défaut |
|---|---|---|
| `SCAN_SUBNET` | Sous-réseau à scanner | `192.168.1.0/24` |
| `SCAN_INTERVAL_MINUTES` | Intervalle du scan périodique | `15` (0 = désactiver) |
| `OFFLINE_TIMEOUT_MINUTES` | Délai hors ligne | `30` |
| `SCAN_EXCLUDE_SUBNETS` | Sous-réseaux à exclure (CIDR, séparés par des virgules) | _(vide)_ |

## Architecture

```
network-map/
├── backend/               # API REST Python (FastAPI + SQLAlchemy)
│   ├── Dockerfile
│   └── app/
│       ├── main.py        # Points d'entrée FastAPI + routes
│       ├── models.py      # Modèles SQLAlchemy
│       ├── schemas.py     # Schémas Pydantic
│       ├── crud.py        # Opérations CRUD + construction du graphe
│       ├── scanner.py     # Scan ARP réseau
│       ├── enricher.py    # Lookup OUI fabricant + reverse DNS
│       └── database.py    # Connexion SQLite
├── frontend/              # Interface Vue 3 (Vite + Tailwind + daisyUI)
│   ├── Dockerfile
│   └── src/
│       ├── views/         # Pages (liste, détail, carte, types…)
│       ├── components/    # Composants réutilisables
│       ├── icons.js       # Catalogue d'icônes Lucide (1502)
│       ├── App.vue        # Layout + thème dark/light
│       └── main.js        # Bootstrap Vue Router
├── docker-compose.yml
├── AGENTS.md              # Documentation technique détaillée
└── scan-host.sh           # Scan ARP depuis l'hôte macOS
```

## Déploiement

### Linux (serveur cible)

Le scan ARP fonctionne nativement : le backend tourne en `network_mode: host` + `privileged: true` et voit le vrai réseau local.

```bash
docker compose up -d --build
```

### macOS (développement local)

Sous Docker Desktop, le conteneur vit dans une VM et ne voit pas le LAN. Deux solutions :

1. Désactiver le scan périodique : `SCAN_INTERVAL_MINUTES=0` dans `.env`
2. Lancer `bash scan-host.sh` pour importer la table ARP de l'hôte

## Stockage

SQLite via un bind mount (`./datas:/app/data`). Pas de dépendance externe.

## Icônes

1502 icônes Lucide intégrées, librement associables à chaque type de périphérique via l'interface. Les périphériques peuvent aussi avoir leur propre icône (fallback sur l'icône du type).

## Stack

| Couche | Technologie |
|---|---|
| Base de données | SQLite via SQLAlchemy 2.0 |
| Backend | Python 3.13 + FastAPI 0.115 |
| Frontend | Vue 3.5 (Composition API) + Vue Router 4 |
| Graphique | Cytoscape.js 3.31 + cytoscape-fcose |
| CSS | Tailwind 3.4 + daisyUI 4.12 |
| Icônes | Lucide (via @lucide/vue) |
| Build | Vite 6.0 |
| Conteneurisation | Docker + Docker Compose |
