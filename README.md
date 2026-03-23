# 🚀 GRH Microservices – Mini-Projet Cloud ISAMM 2026

> **Dr. Fatma SIALA KALLEL** · ISAMM 2ING INLOG & INREV · 2026

Plateforme de gestion des ressources humaines conteneurisée en micro-services.  
Chaque partie du sujet est couverte et documentée.

---

## 🏗️ Architecture Finale

```
                        ┌──────────────────────────────┐
                        │           USER               │
                        └──────────────┬───────────────┘
                                       │ HTTPS:443 / HTTP:80
                        ┌──────────────▼───────────────┐
                        │    NGINX (API Gateway)        │
                        │    Load Balancer + TLS        │
                        └──────┬──────────┬────────┬───┘
                               │          │        │
               ┌───────────────▼──┐  ┌────▼────┐ ┌▼────────┐
               │  Flask App1      │  │ App2    │ │ App3    │
               │  (Employees,     │  │ (Paie)  │ │ (Recru) │
               │   Tasks, Leaves) │  │ :5001   │ │ :5002   │
               └───────┬──────────┘  └────┬────┘ └────┬────┘
                       │                  │            │
               ┌───────▼──────────────────▼────────────▼────┐
               │              PostgreSQL :5432               │
               │           (Volume persistant)               │
               └─────────────────────────────────────────────┘
               ┌─────────────────────────────────────────────┐
               │               Redis :6379                   │
               │         (Cache + Sessions + Compteur)       │
               └─────────────────────────────────────────────┘
               ┌──────────────┐ ┌──────────┐ ┌─────────────┐
               │  Prometheus  │ │ Grafana  │ │  cAdvisor   │
               │   :9090      │ │  :3000   │ │   :8080     │
               └──────────────┘ └──────────┘ └─────────────┘
```

---

## 📋 Parties du projet

| Partie | Description | Fichiers clés |
|--------|-------------|---------------|
| **1** | API GRH complète (Employees, Tasks, Leaves, Payroll, Jobs) | `app1/app.py`, `app2/app.py`, `app3/app.py` |
| **2** | PostgreSQL + volumes persistants | `docker-compose.yml` → service `db`, `db/init.sql` |
| **3** | Redis (cache, compteur visites, sessions) | Intégré dans chaque `app.py` |
| **4** | Monitoring : Prometheus + Grafana + cAdvisor | `monitoring/prometheus.yml`, `docker-compose.yml` |
| **5** | CI/CD GitHub Actions | `ci/ci-cd.yml` → copier dans `.github/workflows/` |
| **6** | HTTPS Nginx + API Gateway | `nginx/nginx.conf`, `nginx/gen-ssl.sh` |
| **7** | Scalabilité Docker Compose | `make scale` ou `docker compose up --scale app1=3` |

---

## 🚀 Démarrage rapide

```bash
# 1. Cloner le projet
git clone https://github.com/<votre-username>/grh-microservices.git
cd grh-microservices

# 2. Tout démarrer (SSL + build + run)
make up

# 3. Vérifier le statut
make status

# 4. Tester les APIs
make test
```

---

## 🌐 Accès aux services

| Service | URL | Identifiants |
|---------|-----|--------------|
| API Gateway | `https://localhost` | — |
| Employees API | `https://localhost/api/employees` | — |
| Tasks API | `https://localhost/api/tasks` | — |
| Payroll API | `https://localhost/api/payslips` | — |
| Jobs API | `https://localhost/api/jobs` | — |
| Grafana | `http://localhost:3000` | admin / admin123 |
| Prometheus | `http://localhost:9090` | — |
| cAdvisor | `http://localhost:8080` | — |

---

## 📌 Partie 1 – API GRH

### Microservice 1 : Employees (app1 – port 5003)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/employees` | Liste tous les employés (avec cache Redis) |
| POST | `/employees` | Créer un employé |
| GET | `/employees/<id>` | Détail d'un employé |
| PUT | `/employees/<id>` | Modifier un employé |
| DELETE | `/employees/<id>` | Supprimer un employé |
| GET | `/tasks` | Liste des tâches |
| POST | `/tasks` | Créer une tâche |
| DELETE | `/tasks/<id>` | Supprimer une tâche |
| GET | `/leaves` | Demandes de congé |
| POST | `/leaves` | Soumettre une demande |
| PATCH | `/leaves/<id>/approve` | Approuver un congé |
| PATCH | `/leaves/<id>/reject` | Refuser un congé |
| GET | `/stats` | Statistiques dashboard |

### Microservice 2 : Paie (app2 – port 5001)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/payslips` | Liste des fiches de paie |
| POST | `/payslips/calculate` | Calculer et générer une fiche |
| DELETE | `/payslips/<id>` | Supprimer une fiche |
| GET | `/payroll/stats` | Statistiques masse salariale |

### Microservice 3 : Recrutement (app3 – port 5002)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/jobs` | Offres d'emploi ouvertes |
| POST | `/jobs` | Publier une offre |
| DELETE | `/jobs/<id>` | Fermer une offre |
| GET | `/candidates` | Liste des candidats |
| POST | `/candidates` | Ajouter un candidat |
| PATCH | `/candidates/<id>/stage` | Avancer dans le pipeline |
| DELETE | `/candidates/<id>` | Supprimer un candidat |

---

## 🗄️ Partie 2 – Base de données PostgreSQL

```yaml
# Extrait docker-compose.yml
db:
  image: postgres:14-alpine
  environment:
    POSTGRES_DB:       grh
    POSTGRES_USER:     admin
    POSTGRES_PASSWORD: admin
  volumes:
    - db-data:/var/lib/postgresql/data  # Persistance des données
```

**Tables créées automatiquement par SQLAlchemy :**
- `employees` – Données employés
- `tasks` – Tâches RH
- `leave_requests` – Demandes de congé
- `payslips` – Fiches de paie
- `job_offers` – Offres d'emploi
- `candidates` – Candidats au recrutement

---

## ⚡ Partie 3 – Cache Redis

Redis est utilisé pour :
1. **Cache des requêtes** : `GET /employees` mis en cache 60s
2. **Cache des stats** : tableau de bord mis en cache 30s
3. **Compteur de visites** : `redis.incr('visits:app1')`
4. **Invalidation automatique** : le cache est vidé après chaque écriture

```python
# Exemple de cache Redis dans app.py
cached = redis_client.get('employees:all')
if cached:
    return jsonify({'data': json.loads(cached), 'source': 'cache'})
# ... requête DB ...
redis_client.setex('employees:all', 60, json.dumps(data))
```

---

## 📊 Partie 4 – Monitoring

### Accès
- **Grafana** : http://localhost:3000 (admin/admin123)
- **Prometheus** : http://localhost:9090
- **cAdvisor** : http://localhost:8080

### Métriques collectées
- CPU et RAM par conteneur (cAdvisor)
- Métriques système host (node-exporter)
- Métriques applicatives Flask
- Nombre de requêtes par service

### Configurer Grafana
1. Aller sur http://localhost:3000
2. Configuration → Data Sources → Add data source
3. Choisir **Prometheus** → URL : `http://prometheus:9090`
4. Importer un dashboard Docker : ID **193** ou **1860**

---

## 🔄 Partie 5 – CI/CD GitHub Actions

```bash
# Copier le fichier CI/CD
mkdir -p .github/workflows
cp ci/ci-cd.yml .github/workflows/ci-cd.yml

# Configurer les secrets GitHub
# Settings → Secrets → Actions :
# DOCKER_HUB_USERNAME = votre_username
# DOCKER_HUB_TOKEN    = votre_token_dockerhub
```

**Pipeline (3 étapes) :**
1. 🧪 **Test** → Tests unitaires avec PostgreSQL et Redis de test
2. 🏗️ **Build** → Construction et push des 3 images Docker Hub
3. 🚀 **Deploy** → `docker compose up` + health checks

---

## 🔐 Partie 6 – HTTPS + API Gateway

```bash
# Générer le certificat SSL auto-signé
make ssl
# ou
bash nginx/gen-ssl.sh
```

**Fonctionnalités Nginx :**
- Redirection HTTP → HTTPS automatique
- Load balancing entre instances (least_conn)
- Rate limiting (30 req/min par IP)
- Headers de sécurité (HSTS, X-Frame-Options...)
- Routing API Gateway vers les microservices

---

## ⚡ Partie 7 – Scalabilité

```bash
# Scaler app1 à 3 instances
make scale
# ou directement :
docker compose up -d --scale app1=3

# Scaler tous les microservices
make scale-full
# docker compose up -d --scale app1=3 --scale app2=2 --scale app3=2

# Test de charge
make test-load
```

**Comment fonctionne le load balancing ?**  
Nginx utilise l'algorithme `least_conn` pour distribuer les requêtes entre les 3 instances de app1. Docker DNS résout automatiquement le nom `app1` vers les 3 conteneurs.

---

## ☁️ Déploiement Azure

```bash
# 1. Créer un Resource Group
az group create --name grh-rg --location westeurope

# 2. Créer une VM
az vm create \
  --resource-group grh-rg \
  --name grh-vm \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys

# 3. Ouvrir les ports
az vm open-port --resource-group grh-rg --name grh-vm --port 80,443,3000,9090

# 4. Se connecter et déployer
ssh azureuser@<IP_VM>
git clone https://github.com/<user>/grh-microservices.git
cd grh-microservices
make up
```

---

## 📦 Structure du projet

```
grh-microservices/
├── app1/                    # Microservice Employees/Tasks/Leaves
│   ├── app.py               # API Flask
│   ├── requirements.txt     # Dépendances Python
│   └── Dockerfile           # Image Docker
├── app2/                    # Microservice Paie
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── app3/                    # Microservice Recrutement
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/
│   ├── nginx.conf           # Config Nginx HTTPS + Gateway
│   └── gen-ssl.sh           # Script génération SSL
├── monitoring/
│   └── prometheus.yml       # Config Prometheus
├── db/
│   └── init.sql             # Init PostgreSQL
├── ci/
│   └── ci-cd.yml            # Pipeline GitHub Actions
├── docker-compose.yml       # Orchestration complète
├── Makefile                 # Commandes simplifiées
└── README.md
```

---

## 🛠️ Commandes utiles

```bash
make help        # Afficher toutes les commandes
make up          # Démarrer la plateforme
make down        # Arrêter la plateforme
make scale       # Scaler à 3 instances (Partie 7)
make logs        # Voir les logs
make status      # Statut + métriques ressources
make test        # Tester les APIs
make test-post   # Créer un employé via API
make test-load   # Test de charge 100 requêtes
make clean       # Tout supprimer
```
