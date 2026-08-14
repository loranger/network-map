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
│       ├── models.py        # Modèles SQLAlchemy (Device, SwitchPort, Connection, Network, Location, DeviceType, Setting)
│       ├── schemas.py       # Schémas Pydantic (validation sérialisation)
│       ├── crud.py          # Opérations CRUD + construction du graphe
│       ├── scanner.py       # Scan ARP réseau
│       ├── enricher.py      # Lookup OUI + reverse DNS + mDNS (zeroconf)
│       └── freebox.py       # Table DHCP du LAN via l'API Freebox OS
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
│   └── views/
│           ├── Devices.vue      # Liste CRUD + scan réseau + import ARP + enrichissement + tri colonnes
│           ├── DeviceDetail.vue # Détail, ports switch (triés, nuancier couleur), connexions, enrich unitaire
│           ├── Graph.vue        # Cartographie Cytoscape.js (compound nodes 3 niveaux + fcose + légende interactive + anti-overlap)
│           ├── Networks.vue     # Gestion réseaux (CRUD + édition)
│           ├── Locations.vue    # Gestion emplacements (CRUD, liés à un étage)
│           ├── Floors.vue       # Gestion étages (CRUD, avec défaut)
│           ├── DeviceTypes.vue  # Gestion types (CRUD, couleur aléatoire sombre)
│           └── Access.vue       # Gestion des tokens (appairage Freebox)
├── scan-host.sh       # Importe arp -a de l'hôte dans l'API
├── docker-compose.yml # Orchestration complète (ignoré par git)
├── docker-compose.example
├── .env.example       # Variables d'environnement documentées
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
|---|---|---|---|
| id | Integer PK | Auto-incrément |
| name | String | Nom du périphérique |
| device_type | String | Enum: computer, iot, switch, ap, router, modem, server, other |
| manufacturer | String? | Fabricant |
| model | String? | Modèle |
| hostname | String? | Nom DNS court |
| location_id | Integer FK? | Référence vers locations.id |
| notes | Text? | Notes libres |
| admin_url | String? | URL interface d'admin (ex: http://{ip}:2112, le placeholder {ip} est résolu côté frontend) |
| icon | String? | Nom de l'icône Lucide (fallback sur icône du type si null) |
| discovered | Boolean | Vrai si trouvé par scan automatique |
| last_seen | DateTime? | Dernière date de détection |
| created_at | DateTime | Auto |
| updated_at | DateTime | Auto |

Le champ `mac` a été supprimé de `Device` — il est désormais stocké par IP dans `DeviceIP.mac` (voir ci-dessous).

Relations : `location_ref` (Location), `ips` (DeviceIP), `ports` (SwitchPort), `connections_a` (Connection), `connections_b` (Connection), `ap_networks` (Network, via `device_ap_networks`)

### DeviceIP
Stocké dans la table `device_ips`. Une adresse IP (IPv4) par ligne, avec son adresse MAC et son rattachement réseau. Un device peut avoir plusieurs IPs.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| device_id | Integer FK → devices.id | Périphérique parent (CASCADE) |
| ipv4 | String? | Adresse IPv4 |
| mac | String? | Adresse MAC (déplacée ici depuis `devices.mac`) |
| network_id | Integer FK → networks.id? | Réseau logique (SET NULL) |
| ip_type | String? | static / dhcp |

Contrainte : index unique sur `ipv4` (évite les doublons à l'import ARP).

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

### Floor
Stocké dans la table `floors`. Étage d'un emplacement physique, avec un flag `is_default` utilisé pour la connexion automatique des clients WiFi sans emplacement.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| name | String | Nom de l'étage (unique) |
| is_default | Boolean | Étage par défaut (un seul à la fois) |
| created_at | DateTime | Auto |

Relations : `locations` (Location)

### Location
Stocké dans la table `locations`. Emplacement physique avec étage.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| name | String | Nom de l'emplacement |
| floor_id | Integer FK? | Référence vers floors.id |
| created_at | DateTime | Auto |

Relations : `floor_ref` (Floor), `devices` (Device)

Le champ `location_id` (FK → locations.id) est présent sur `Device`. La hiérarchie dans le graphe est : Étage (floor) > Emplacement (location) > Périphérique (device).

### DeviceType
Stocké dans la table `device_types`. Type de périphérique avec libellé et couleur.

| Champ | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-incrément |
| type | String | Identifiant technique (ex: router, switch) |
| label | String | Libellé affiché (ex: Routeur, Switch) |
| color | String | Couleur hex (ex: #3b82f6) |
| icon | String? | Nom de l'icône Lucide (ex: monitor, server) |

Les types sont seedés au démarrage avec les couleurs d'origine. Les couleurs ne sont plus hardcodées nulle part — elles viennent de la DB via l'API. Ajout d'un nouveau type via l'UI génère une couleur aléatoire sombre (HSL, luminance 25–50%) et propose un sélecteur d'icône (parmi 1502 icônes Lucide disponibles, avec recherche). Les icônes sont utilisées dans la liste des périphériques et dans la légende du graphe (pas sur les noeuds).

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

### Floors
| Méthode | Route | Description |
|---|---|---|
| GET | /api/floors | Liste |
| POST | /api/floors | Création |
| PUT | /api/floors/{id} | Modification |
| DELETE | /api/floors/{id} | Suppression |

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

Les connexions automatiques client→AP sont déterminées par proximité :
1. **Même emplacement** (`location_id`) — si un AP partage l'emplacement exact du client
2. **Même étage** (`floor`) — si aucun AP n'a le même emplacement, on prend un AP au même étage
3. **Étage par défaut** — si le client n'a pas d'emplacement, on utilise l'étage marqué `is_default` dans la table `floors`
4. **Premier AP** — fallback si rien ne correspond

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

Le sous-réseau par défaut est `192.168.1.0/24`, mais il est configurable :
- Via la variable d'env `SCAN_SUBNET` dans `.env` (copier `.env.example`)
- Via le champ "Sous-réseau" du bouton Scanner dans la vue Périphériques, envoyé dans le body de `POST /api/scan` (`{"subnet": "..."}`)

Des sous-réseaux entiers peuvent être exclus de la découverte via `SCAN_EXCLUDE_SUBNETS` (liste comma-séparée de CIDR, ex: `172.30.0.0/16,192.168.139.0/24`). Utile en dev macOS où le scan conteneurisé voit les réseaux internes de la VM Docker (172.30.x, etc.) qui ne doivent pas polluer la base.

### Scan périodique automatique

Un scan automatique est lancé en tâche de fond à intervalle régulier depuis le lifespan FastAPI (`periodic_scan_loop` dans `main.py`). Il réutilise `scan_network` (donc `SCAN_SUBNET` s'applique) et maintient la base à jour (`discovered`, `last_seen`, nouveaux devices). L'intervalle se configure via la variable d'env `SCAN_INTERVAL_MINUTES` en minutes, valeur **0 pour désactiver**.

### Périphériques hors ligne

Un device découvert est considéré **hors ligne** si son `last_seen` est antérieur à `OFFLINE_TIMEOUT_MINUTES`. Les devices ajoutés manuellement (`discovered=false`) sont toujours considérés en ligne. Conséquences :
- **Graphe** (`GET /api/graph`) : les devices hors ligne sont exclus des noeuds (et leurs arêtes sont filtrées).
- **Liste** (`DeviceResponse.online`) : tous les devices sont listés, avec colonne `last_seen` et ligne atténuée si `online=false`.

Sur **Linux**, `network_mode: host` + `privileged: true` permet un ARP scan complet du LAN.

Sur **macOS Docker Desktop**, le conteneur tourne dans une VM : `network_mode: host` ne partage que le réseau de la VM. Le scan intégré ne voit que les passerelles Docker. Solution : exécuter `arp -a` sur l'hôte et l'importer :

```bash
bash scan-host.sh
```

Ce script envoie le output de `arp -a` du Mac à `POST /api/scan/import` qui crée/met à jour les devices dans la base.

## Enrichissement

L'enrichissement (`POST /api/enrich` ou `POST /api/enrich/{id}`) combine, pour le fabricant et le hostname :
1. **Lookup OUI** : table de ~280 préfixes MAC pour identifier le fabricant (clés normalisées sans `:`, insensibles à la casse)
2. **Table LAN Freebox** (`freebox.py`) : hostnames DHCP fournis par l'API Freebox OS (appairage via la page **Réglages → Accès**, jeton stocké en base)
3. **mDNS/Bonjour** (`zeroconf`) : hostnames `.local` des appareils qui annoncent des services mDNS
4. **Reverse DNS** : résolution PTR de l'adresse IPv4, bornée (2s) via dnspython + éventuel serveur `DNS_SERVERS`

Si un hostname est trouvé **et** que le nom du device commence par `device-`, le nom est automatiquement remplacé par le hostname court (partie avant le premier point).

## Déploiement

### Docker Compose (production)

```bash
docker compose up -d --build
```

Le backend utilise `network_mode: host` + `privileged: true` pour le scan ARP. Le frontend proxy `/api/` vers le backend via `host.docker.internal:8000` (`extra_hosts` ajouté automatiquement).

Les variables d'environnement sont chargées via un fichier `.env` à la racine (copier `.env.example` et ajuster).

Services :
- **backend** (port 8000, host) : API FastAPI avec volume persistant pour SQLite
- **frontend** (port 8080, host) : Nginx servant le build static + proxy `/api/` vers le backend

`docker-compose.yml` est ignoré par git — copier `docker-compose.example` vers `docker-compose.yml` et ajuster selon le besoin (Traefik, ports, etc.).

### Règle absolue : tout dans Docker

**Ne jamais exécuter Python, npm, ou tout outil de build/local en dehors de Docker.** Tous les changements (backend, frontend) sont buildés et testés exclusivement via Docker Compose :

```bash
docker compose build --no-cache backend    # backend uniquement
docker compose build --no-cache frontend   # frontend uniquement
docker compose build --no-cache            # les deux
docker compose down && docker compose up -d
```

Exception : `bash scan-host.sh` (tourne sur l'hôte macOS car le scan ARP depuis Docker est limité).

### Scan réseau

Pour que nmap donne les vrais périphériques du LAN, le backend doit partager la pile réseau de l'hôte. Sur **Linux**, `network_mode: host` + `privileged: true` suffit. Sur **macOS** :
1. Activer dans Docker Desktop : **Settings → Resources → Network → Enable host networking**
2. Utiliser `bash scan-host.sh` pour un scan ARP complet (contourne la limitation VM)

## Contraintes et conventions

- Python 3.13+ requis (le scan ARP et SQLAlchemy nécessitent la version système)
- Node 26+ pour le build frontend
- Le fichier de base de données SQLite est stocké dans un bind mount (`./datas:/app/data`)
- Les fichiers `devices.yaml` et `networks.yaml` ont été supprimés — les données vivent en SQLite
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
8. **Tout dans Docker** — ne jamais exécuter Python, npm, ou tout outil de build/local en dehors de Docker. Build et test exclusivement via `docker compose build --no-cache && docker compose down && docker compose up -d`.

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
- **Freebox OS API** — login/authorize (app_token), session, lan/browser (hosts)
- **python-zeroconf** — mDNS/Bonjour, ServiceBrowser, listeners
- **dnspython** — résolution DNS/PTR, resolver nameservers

Ne pas deviner les API. Toujours vérifier la documentation officielle via Context7 avant d'écrire du code utilisant ces frameworks, en particulier pour les versions majeures récentes.
