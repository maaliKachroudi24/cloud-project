#!/bin/bash
# ════════════════════════════════════════════════════════════════
# gen-ssl.sh – Génère un certificat SSL auto-signé (Partie 6)
# ════════════════════════════════════════════════════════════════
mkdir -p ./nginx/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./nginx/ssl/key.pem \
  -out    ./nginx/ssl/cert.pem \
  -subj "//C=TN/ST=Tunis/L=Tunis/O=GRH-ISAMM/OU=IT/CN=localhost"

echo "✅ Certificat SSL généré dans ./nginx/ssl/"
echo "   cert.pem  → Certificat public"
echo "   key.pem   → Clé privée"
