# Network Map

## Objectif

Interface web de cartographie et documentation du réseau local. Permet de lister, scanner, documenter et visualiser les périphériques réseau (ordinateurs, IoT, switches avec ports, AP WiFi mesh, routeurs, modems, serveurs) ainsi que leurs interconnexions sous forme de graphe orienté.

## Architecture

```
network-map/
├── backend/           # API REST Python
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # Points d'entrée FastAPI + routes
│       ├── database.py      # Connexion SQLite + session
│       ├── models.py        # Modèles SQLAlchemy (Device, SwitchPort, Connection, Network)
│       ├── schemas.py       # Schémas Pydantic (validation sérialisation)
│       ├── crud.py          # Opérations CRUD + construction du graphe
│       └── scanner.py       # Scan ARP réseau
├── frontend/          # Interface web Vue 3
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.js          # Bootstrap Vue Router (hash history)
│       ├── App.vue          # Layout principal (drawer sidebar responsive)
│       ├── style.css        # Tailwind + styles graph-container
│       └── views/
│           ├── Devices.vue      # Liste CRUD + scan réseau
│           ├── DeviceDetail.vue # Détail, ports switch, connexions
│           ├── Graph.vue        # Cartographie vis-network
│           └── Networks.vue     # Gestion réseaux
├── devices.yaml       # Données initiales (périphériques) — conservé comme référence
├── networks.yaml      # Données initiales (réseaux) — conservé comme référence
├── docker-compose.yml # Orchestration complète
└── AGENTS.md          # Ce fichier
```

## Stack technique

| Couche | Technologie | Version |
|---|---|---|
| Base de données | SQLite via SQLAlchemy | 2.0 |
| Backend API | Python 3.13 + FastAPI | 0.115 |
| Validation | Pydantic | 2.10 |
| Serveur ASGI | Uvicorn | 0.34 |
| Scan réseau | ARP via subprocess (net-tools) | — |
| Frontend | Vue 3 (Composition API) | 3.5 |
| Routage | Vue Router 4 (hash history) | 4.5 |
| HTTP client | Axios | 1.7 |
| Graphique | vis-network + vis-data | 9.1 / 7.1 |
| Icônes | SVG inline (Lucide-compatible) | — |
| CSS | Tailwind CSS 3 + daisyUI 4 | 3.4 / 4.12 |
| Build | Vite | 6.0 |
| Conteneurisation | Docker + Docker Compose | — |
| Proxy production | Nginx (stable-alpine) | — |

## Modèle de données (SQLite)

### Device
Stocké dans la table `devices`. Représente tout périphérique réseau.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| name | String (unique) | Nom du périphérique |
| device_type | String | Enum: computer, iot, switch, ap, router, modem, server, other |
| manufacturer | String? | Fabricant |
| model | String? | Modèle |
| mac | String? | Adresse MAC |
| ipv4 | String? | Adresse IPv4 |
| ipv6 | String? | Adresse IPv6 |
| location | String? | Emplacement physique |
| notes | Text? | Notes libres |
| discovered | Boolean | Vrai si trouvé par scan automatique |
| last_seen | DateTime? | Dernière date de détection |
| created_at | DateTime | Auto |
| updated_at | DateTime | Auto |

Relations : `ports` (SwitchPort), `connections_a` (Connection), `connections_b` (Connection)

### SwitchPort
Stocké dans la table `switch_ports`. Ports d'un switch.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| switch_id | Integer FK → devices.id | Switch parent |
| name | String | Nom du port (ex: "Port 1", "GE1") |
| connected_device_id | Integer FK → devices.id? | Périphérique connecté |
| vlan | String? | VLAN |
| poe | Boolean | Power over Ethernet |
| notes | Text? | Notes |

### Connection
Stocké dans la table `connections`. Lien entre deux périphériques.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| device_a_id | Integer FK → devices.id | Périphérique source |
| device_b_id | Integer FK → devices.id | Périphérique destination |
| type | String | wired / wireless |
| technology | String? | Ethernet, WiFi, etc. |
| speed | String? | 1GbE, 2.4GHz, 5GHz |
| notes | Text? | Notes |

### Network
Stocké dans la table `networks`. Réseau logique (WiFi, Mesh, filaire).

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| name | String | Nom du réseau |
| ssid | String? | SSID WiFi |
| type | String | wifi / mesh / wired |
| subnet | String? | Sous-réseau (192.168.1.0/24) |
| gateway | String? | Passerelle |
| dns | String? | DNS |

## API REST

Toutes les routes sont préfixées par `/api`.

### Devices
| Méthode | Route | Description |
|---|---|---|
| GET | /api/devices | Liste (filtres: ?type=, ?location=) |
| GET | /api/devices/{id} | Détail |
| POST | /api/devices | Création |
| PUT | /api/devices/{id} | Modification partielle |
| DELETE | /api/devices/{id} | Suppression |
| GET | /api/devices/{id}/ports | Ports d'un switch |
| POST | /api/devices/{id}/ports | Ajout d'un port |
| DELETE | /api/ports/{id} | Suppression d'un port |

### Connections
| Méthode | Route | Description |
|---|---|---|
| GET | /api/connections | Liste |
| POST | /api/connections | Création |
| DELETE | /api/connections/{id} | Suppression |

### Networks
| Méthode | Route | Description |
|---|---|---|
| GET | /api/networks | Liste |
| POST | /api/networks | Création |
| DELETE | /api/networks/{id} | Suppression |

### Utilitaires
| Méthode | Route | Description |
|---|---|---|
| POST | /api/scan | Scan ARP (nmap ARP ping + arp -a) |
| POST | /api/scan/import | Importer output de `arp -a` depuis l'hôte |
| GET | /api/graph | Données du graphe (noeuds + arêtes) |

## Graphique (cartographie)

Utilise `vis-network` avec le solver physique `forceAtlas2Based`. Les flèches directionnelles sont activées sur toutes les arêtes. Le code couleur par type de périphérique est défini dans `crud.py` et `Graph.vue` :

| Type | Couleur |
|---|---|
| router | Bleu (#3b82f6) |
| modem | Violet (#8b5cf6) |
| ap | Cyan (#06b6d4) |
| switch | Orange (#f59e0b) |
| computer | Vert (#10b981) |
| server | Rouge (#ef4444) |
| iot | Rose (#ec4899) |
| other | Gris (#6b7280) |

Les connexions sans fil (`type: "wireless"`) sont affichées en pointillés. Les arêtes sont courbées (`curvedCW`) avec un label indiquant la technologie.

## Scan réseau

Le scanner combine deux méthodes :
1. **nmap -sn -PR** (ARP ping) — nécessite `privileged: true` + Docker Desktop "Host Networking" activé
2. **arp -a** — fallback si nmap ne trouve rien

Sur **Linux**, `network_mode: host` + `privileged: true` permet un ARP scan complet du LAN.

Sur **macOS Docker Desktop**, le conteneur tourne dans une VM : `network_mode: host` ne partage que le réseau de la VM. Le scan intégré ne voit que les passerelles Docker. Solution : exécuter `arp -a` sur l'hôte et l'importer :

```bash
bash scan-host.sh
```

Ce script envoie le output de `arp -a` du Mac à `POST /api/scan/import` qui crée/met à jour les devices dans la base.

## Déploiement

### Docker Compose (production)

```bash
docker compose up -d --build
```

Les deux services utilisent `network_mode: host` pour partager la pile réseau de l'hôte, nécessaire au scan ARP.

Deux services :
- **backend** (port 8000) : API FastAPI avec volume persistant pour SQLite
- **frontend** (port 8080) : Nginx servant le build static + proxy `/api/` via `localhost:8000`

### Développement local

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev    # → http://localhost:5173 (proxy /api → localhost:8000)
```

En dev, Vite proxyifie `/api` vers `localhost:8000` (voir `vite.config.js`).

### Scan réseau

Pour que nmap donne les vrais périphériques du LAN, le backend doit partager la pile réseau de l'hôte. Sur **Linux**, `network_mode: host` + `privileged: true` suffit. Sur **macOS** :
1. Activer dans Docker Desktop : **Settings → Resources → Network → Enable host networking**
2. Utiliser `bash scan-host.sh` pour un scan ARP complet (contourne la limitation VM)

## Contraintes et conventions

- Python 3.13+ requis (le scan ARP et SQLAlchemy nécessitent la version système)
- Node 26+ pour le build frontend
- Le fichier de base de données SQLite est stocké dans un volume Docker (`network-map-data:/app/data`)
- Les fichiers `devices.yaml` et `networks.yaml` sont conservés comme traces historiques mais ne sont plus utilisés par l'application
- Pas de système d'authentification (usage local / LAN uniquement)
- Le frontend utilise un hash router (`createWebHashHistory`) pour fonctionner sans configuration serveur avancée

## Bonnes pratiques pour l'IA

Avant de modifier ou d'étendre ce projet, consulter sur Context7 les documentations les plus récentes des technologies utilisées :

- **Python / FastAPI** — nouvelles fonctionnalités, dépréciations, patterns
- **Vue 3** — Composition API, réactivité, slots, téléport
- **Tailwind CSS 3** — classes utilitaires, configuration custom
- **daisyUI 4** — composants, thèmes, personnalisation
- **vis-network** — options de physique, layout hiérarchique, events
- **SQLAlchemy 2.0** — déclarative mapping, relationships, queries
- **Docker Compose** — networking, volumes, healthchecks
- **Nginx** — reverse proxy, configuration SPA

Ne pas deviner les API. Toujours vérifier la documentation officielle via Context7 avant d'écrire du code utilisant ces frameworks, en particulier pour les versions majeures récentes.
