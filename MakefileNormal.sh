#!/bin/bash

echo "═══════════════════════════════════════════════"
echo "   GRH Microservices – Commands (No Makefile)"
echo "═══════════════════════════════════════════════"

case "$1" in

ssl)
  echo "🔐 Generating SSL..."
  bash nginx/gen-ssl.sh
  ;;

up)
  echo "🚀 Starting services..."
  bash nginx/gen-ssl.sh
  docker compose up -d --build
  echo "✅ Services started!"
  ;;

down)
  echo "⏹️ Stopping services..."
  docker compose down
  ;;

scale)
  echo "⚡ Scaling app1..."
  docker compose up -d --scale app1=3 --no-recreate
  ;;

scale-full)
  echo "⚡ Scaling all services..."
  docker compose up -d --scale app1=3 --scale app2=2 --scale app3=2
  ;;

logs)
  docker compose logs -f --tail=100
  ;;

logs-app1)
  docker compose logs -f app1
  ;;

logs-nginx)
  docker compose logs -f nginx
  ;;

status)
  echo "📊 Containers status:"
  docker compose ps
  echo ""
  echo "📦 Resources:"
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
  ;;

test)
  echo "🧪 Testing APIs..."

  echo "── App1 ──"
  curl -sk https://localhost/api/employees | python -m json.tool | head -30

  echo "── App2 ──"
  curl -sk https://localhost/api/payroll/stats | python -m json.tool

  echo "── App3 ──"
  curl -sk https://localhost/api/jobs | python -m json.tool | head -30

  echo "── Health ──"
  curl -sk https://localhost/health/app1
  curl -sk https://localhost/health/app2
  curl -sk https://localhost/health/app3
  ;;

test-post)
  curl -sk -X POST https://localhost/api/employees \
    -H "Content-Type: application/json" \
    -d '{"name":"Test User","email":"test@grh.tn","department":"IT","role":"Dev","salary":3000}' \
    | python3 -m json.tool
  ;;

test-task)
  curl -sk -X POST https://localhost/api/tasks \
    -H "Content-Type: application/json" \
    -d '{"title":"Réviser les contrats Q2","priority":"high","assigned_to":1}' \
    | python3 -m json.tool
  ;;

test-load)
  echo "⚡ Load test..."
  for i in $(seq 1 100); do
    curl -sk https://localhost/api/stats > /dev/null &
  done
  wait
  echo "✅ Done"
  ;;

clean)
  echo "🧹 Cleaning..."
  docker compose down -v --remove-orphans
  docker system prune -f
  ;;

rebuild)
  echo "🔁 Rebuilding..."
  docker compose build --no-cache
  docker compose up -d
  ;;

*)
  echo ""
  echo "Usage:"
  echo "  ./commands.sh ssl"
  echo "  ./commands.sh up"
  echo "  ./commands.sh down"
  echo "  ./commands.sh scale"
  echo "  ./commands.sh scale-full"
  echo "  ./commands.sh logs"
  echo "  ./commands.sh logs-app1"
  echo "  ./commands.sh logs-nginx"
  echo "  ./commands.sh status"
  echo "  ./commands.sh test"
  echo "  ./commands.sh test-post"
  echo "  ./commands.sh test-task"
  echo "  ./commands.sh test-load"
  echo "  ./commands.sh clean"
  echo "  ./commands.sh rebuild"
  echo ""
  ;;
esac