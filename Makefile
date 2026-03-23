# ════════════════════════════════════════════════════════════════
# Makefile – Commandes simplifiées pour le Mini-Projet Cloud GRH
# ════════════════════════════════════════════════════════════════

.PHONY: help ssl up down scale logs test clean status

help:  ## Afficher l'aide
	@echo ""
	@echo "  ╔══════════════════════════════════════════════════════╗"
	@echo "  ║   GRH Microservices – Mini-Projet Cloud ISAMM 2026  ║"
	@echo "  ╚══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  make ssl      → Générer les certificats SSL (Partie 6)"
	@echo "  make up       → Démarrer tous les services"
	@echo "  make down     → Arrêter tous les services"
	@echo "  make scale    → Scaler app1 à 3 instances (Partie 7)"
	@echo "  make logs     → Voir les logs en temps réel"
	@echo "  make status   → Statut des conteneurs"
	@echo "  make test     → Tester les endpoints API"
	@echo "  make clean    → Supprimer conteneurs + volumes"
	@echo ""

ssl:  ## Partie 6 – Générer certificat SSL auto-signé
	@echo "🔐 Génération du certificat SSL..."
	@bash nginx/gen-ssl.sh

up: ssl  ## Démarrer tous les services
	@echo "🚀 Démarrage de la plateforme GRH..."
	docker compose up -d --build
	@echo ""
	@echo "✅ Services démarrés !"
	@echo ""
	@echo "  🌐 API Gateway  → https://localhost"
	@echo "  📊 Grafana      → http://localhost:3000  (admin/admin123)"
	@echo "  📈 Prometheus   → http://localhost:9090"
	@echo "  🖥️  cAdvisor     → http://localhost:8080"
	@echo ""

down:  ## Arrêter tous les services
	@echo "⏹️  Arrêt des services..."
	docker compose down

# ── Partie 7 : Scalabilité ───────────────────────────────────
scale:  ## Scaler app1 à 3 instances (Partie 7)
	@echo "⚡ Scalabilité – Lancement de 3 instances app1..."
	docker compose up -d --scale app1=3 --no-recreate
	@echo "✅ 3 instances de app1 actives (load balancing Nginx)"

scale-full:  ## Scaler les 3 microservices
	docker compose up -d --scale app1=3 --scale app2=2 --scale app3=2

logs:  ## Voir les logs en temps réel
	docker compose logs -f --tail=100

logs-app1:  ## Logs microservice 1
	docker compose logs -f app1

logs-nginx:  ## Logs Nginx
	docker compose logs -f nginx

status:  ## Statut de tous les conteneurs
	@echo "📊 Statut des services :"
	docker compose ps
	@echo ""
	@echo "📦 Utilisation des ressources :"
	docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# ── Tests API (Partie 1) ─────────────────────────────────────
test:  ## Tester tous les endpoints API
	@echo "🧪 Test des endpoints API..."
	@echo ""
	@echo "── App1 : Employees ──"
	curl -sk https://localhost/api/employees | python3 -m json.tool | head -30
	@echo ""
	@echo "── App2 : Payroll Stats ──"
	curl -sk https://localhost/api/payroll/stats | python3 -m json.tool
	@echo ""
	@echo "── App3 : Jobs ──"
	curl -sk https://localhost/api/jobs | python3 -m json.tool | head -30
	@echo ""
	@echo "── Health Checks ──"
	curl -sk https://localhost/health/app1
	curl -sk https://localhost/health/app2
	curl -sk https://localhost/health/app3

test-post:  ## Tester la création d'un employé
	curl -sk -X POST https://localhost/api/employees \
	  -H "Content-Type: application/json" \
	  -d '{"name":"Test User","email":"test@grh.tn","department":"IT","role":"Dev","salary":3000}' \
	  | python3 -m json.tool

test-task:  ## Tester la création d'une tâche (Partie 1 – TODO API)
	curl -sk -X POST https://localhost/api/tasks \
	  -H "Content-Type: application/json" \
	  -d '{"title":"Réviser les contrats Q2","priority":"high","assigned_to":1}' \
	  | python3 -m json.tool

test-load:  ## Test de charge (Partie 7 – Scalabilité)
	@echo "⚡ Test de charge sur 100 requêtes..."
	@for i in $$(seq 1 100); do \
	  curl -sk https://localhost/api/stats > /dev/null & \
	done; wait
	@echo "✅ Test de charge terminé. Vérifiez Grafana pour les métriques."

clean:  ## Supprimer tous les conteneurs et volumes
	@echo "🧹 Nettoyage complet..."
	docker compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Nettoyage terminé"

rebuild:  ## Reconstruire les images sans cache
	docker compose build --no-cache
	docker compose up -d
