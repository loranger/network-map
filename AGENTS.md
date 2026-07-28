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
│       ├── models.py        # Modèles SQLAlchemy (Device, SwitchPort, Connection, Network, Location, DeviceType)
│       ├── schemas.py       # Schémas Pydantic (validation sérialisation)
│       ├── crud.py          # Opérations CRUD + construction du graphe
│       ├── scanner.py       # Scan ARP réseau
│       └── enricher.py      # Lookup OUI fabricant + reverse DNS
├── scan-host.sh       # Script macOS : importe arp -a dans l'API
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
│           ├── Devices.vue      # Liste CRUD + scan réseau + import ARP + enrichissement + tri colonnes
│           ├── DeviceDetail.vue # Détail, ports switch (triés, nuancier couleur), connexions, enrich unitaire
│           ├── Graph.vue        # Cartographie Cytoscape.js (compound nodes 3 niveaux + fcose + légende interactive + anti-overlap)
│           ├── Networks.vue     # Gestion réseaux (CRUD + édition)
│           ├── Locations.vue    # Gestion emplacements (CRUD)
│           └── DeviceTypes.vue  # Gestion types (CRUD, couleur aléatoire sombre)
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
| Scan réseau | nmap + arp via subprocess | — |
| Frontend | Vue 3 (Composition API) | 3.5 |
| Routage | Vue Router 4 (hash history) | 4.5 |
| HTTP client | Axios | 1.7 |
| Graphique | Cytoscape.js + cytoscape-fcose | 3.31 / 2.2 |
| Icônes | @lucide/vue | — |
| Upload | python-multipart | — |
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
| name | String | Nom du périphérique |
| device_type | String | Enum: computer, iot, switch, ap, router, modem, server, other |
| manufacturer | String? | Fabricant |
| model | String? | Modèle |
| mac | String? | Adresse MAC |
| ipv4 | String? | Adresse IPv4 |
| ipv6 | String? | Adresse IPv6 |
| hostname | String? | Nom DNS court |
| ip_type | String? | static / dhcp |
| location_id | Integer FK? | Référence vers locations.id |
| notes | Text? | Notes libres |
| admin_url | String? | URL interface d'admin (ex: http://{ip}:2112, le placeholder {ip} est résolu côté frontend) |
| discovered | Boolean | Vrai si trouvé par scan automatique |
| last_seen | DateTime? | Dernière date de détection |
| created_at | DateTime | Auto |
| updated_at | DateTime | Auto |

Relations : `location_ref` (Location), `ports` (SwitchPort), `connections_a` (Connection), `connections_b` (Connection)

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
| color | String? | Couleur de câble (hex) |
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

### Location
Stocké dans la table `locations`. Emplacement physique avec étage.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| name | String | Nom de l'emplacement |
| floor | String? | Étage (RDC, 1er, etc.) |
| created_at | DateTime | Auto |

Relations : `devices` (Device)

Le champ `location_id` (FK → locations.id) est présent sur `Device`. La hiérarchie dans le graphe est : Étage (floor) > Emplacement (location) > Périphérique (device).

### DeviceType
Stocké dans la table `device_types`. Type de périphérique avec libellé et couleur.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| type | String | Identifiant technique (ex: router, switch) |
| label | String | Libellé affiché (ex: Routeur, Switch) |
| color | String | Couleur hex (ex: #3b82f6) |

Les types sont seedés au démarrage avec les couleurs d'origine. Les couleurs ne sont plus hardcodées nulle part — elles viennent de la DB via l'API. Ajout d'un nouveau type via l'UI génère une couleur aléatoire sombre (HSL, luminance 25–50%).

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
| PUT | /api/connections/{id} | Modification (couleur) |
| DELETE | /api/connections/{id} | Suppression |

### Networks
| Méthode | Route | Description |
|---|---|---|
| GET | /api/networks | Liste |
| POST | /api/networks | Création |
| PUT | /api/networks/{id} | Modification |
| DELETE | /api/networks/{id} | Suppression |

### Locations
| Méthode | Route | Description |
|---|---|---|
| GET | /api/locations | Liste |
| POST | /api/locations | Création |
| PUT | /api/locations/{id} | Modification |
| DELETE | /api/locations/{id} | Suppression |

### DeviceTypes
| Méthode | Route | Description |
|---|---|---|
| GET | /api/device-types | Liste |
| POST | /api/device-types | Création |
| PUT | /api/device-types/{id} | Modification |
| DELETE | /api/device-types/{id} | Suppression |

### Utilitaires
| Méthode | Route | Description |
|---|---|---|
| POST | /api/scan | Scan ARP (nmap ARP ping + arp -a) |
| POST | /api/scan/import | Importer output de `arp -a` depuis l'hôte |
| POST | /api/enrich | Enrichir tous les devices (OUI fabricant + reverse DNS) |
| POST | /api/enrich/{id} | Enrichir un device spécifique |
| GET | /api/graph | Données du graphe (noeuds + arêtes) |

## Graphique (cartographie)

Utilise `Cytoscape.js` avec le layout `fcose`. Les noeuds sont regroupés en **compound nodes** hiérarchiques : Étage > Emplacement > Périphérique (3 niveaux). Les arêtes utilisent le style `unbundled-bezier` avec une courbure alternée (±25px) pour un rendu organique. Les flèches directionnelles sont activées sur toutes les arêtes. Le code couleur par type de périphérique vient de la table `device_types` en DB via l'API.

Les connexions sans fil (`dashes: true`) sont affichées en pointillés via la classe CSS `edge.wireless`.

**Bug connu contourné** : avec les compound nodes, passer les éléments et le layout au constructeur Cytoscape fait disparaître les arêtes au rendu initial. Solution : créer l'instance vide, ajouter les éléments via `cy.add()`, puis lancer `layout.run()` séparément.

### Paramètres du layout fcose

| Paramètre | Valeur |
|---|---|
| nodeRepulsion | 8000 |
| idealEdgeLength | 120 |
| edgeElasticity | 0.45 |
| nestingFactor | 1.5 |
| gravity | 0.25 |
| gravityCompound | 2.0 |
| gravityRangeCompound | 2.0 |
| numIter | 2500 |
| tile | true |
| packComponents | true |

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

## Enrichissement

L'enrichissement (`POST /api/enrich` ou `POST /api/enrich/{id}`) combine :
1. **Lookup OUI** : ~80 préfixes MAC connus pour identifier le fabricant (clés normalisées sans `:`, insensibles à la casse)
2. **Reverse DNS** : résolution PTR de l'adresse IPv4

Si un hostname est trouvé par reverse DNS **et** que le nom du device commence par `device-`, le nom est automatiquement remplacé par le hostname court (partie avant le premier point).

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
- Le fichier de base de données SQLite est stocké dans un bind mount (`./datas:/app/data`)
- Les fichiers `devices.yaml` et `networks.yaml` sont conservés comme traces historiques mais ne sont plus utilisés par l'application
- Pas de système d'authentification (usage local / LAN uniquement)
- Le frontend utilise un hash router (`createWebHashHistory`) pour fonctionner sans configuration serveur avancée

## Qualité du code

### Règles à vérifier systématiquement avant chaque commit

1. **Pas de code mort** — toute fonction, variable ou import non utilisé(e) doit être supprimé(e). Vérifier avec `rg` les appels.
2. **Pas de clés dupliquées** — dans les objets JS, dictionnaires Python, etc. La dernière écrase la première (silencieux).
3. **Normalisation cohérente** — si une fonction normalise une valeur (`replace(":", "").upper()`), les données statiques doivent être normalisées au même format au moment de la définition.
4. **Pas de valeurs hardcodées redondantes** — si une valeur existe en DB (couleurs des types, etc.), elle ne doit pas être dupliquée dans le code frontend ou backend.
5. **Pas de `onclick=` dans les templates Vue** — toujours utiliser `@click` avec une fonction définie dans `<script setup>`. Le `onclick=` HTML crée des dépendances globales implicites et contourne Vue.
6. **Pas de `document.getElementById().showModal()`** — utiliser les template refs Vue (`ref="modal"`, `modal.value.showModal()`).
7. **Purger les `console.log` de debug** avant de proposer un commit.

## Bonnes pratiques pour l'IA

Avant de modifier ou d'étendre ce projet, consulter sur Context7 les documentations les plus récentes des technologies utilisées :

- **Python / FastAPI** — nouvelles fonctionnalités, dépréciations, patterns
- **Vue 3** — Composition API, réactivité, slots, téléport
- **Tailwind CSS 3** — classes utilitaires, configuration custom
- **daisyUI 4** — composants, thèmes, personnalisation
- **Cytoscape.js** — compound nodes, layouts, style, events
- **SQLAlchemy 2.0** — déclarative mapping, relationships, queries
- **Docker Compose** — networking, volumes, healthchecks
- **Nginx** — reverse proxy, configuration SPA

Ne pas deviner les API. Toujours vérifier la documentation officielle via Context7 avant d'écrire du code utilisant ces frameworks, en particulier pour les versions majeures récentes.
