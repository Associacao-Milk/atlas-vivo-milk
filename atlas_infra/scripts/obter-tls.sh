#!/usr/bin/env bash
# Obter certificado TLS Let's Encrypt para o domínio PT do Atlas.
# Uso: ./scripts/obter-tls.sh atlas.milk.pt
set -euo pipefail

DOMAIN="${1:-}"
if [ -z "$DOMAIN" ]; then
  echo "Uso: $0 <domínio>  (ex.: atlas.milk.pt)"; exit 1
fi

cd "$(dirname "$0")/.."

echo "A obter certificado Let's Encrypt para: $DOMAIN"
echo "Certifique-se de que o DNS A de $DOMAIN aponta para este servidor e que o nginx já responde em :80."

# Standalone (para nginx ainda não configurado) — usa a partilha certbot-web do compose
docker run --rm \
  -v certbot-etc:/etc/letsencrypt \
  -v certbot-var:/var/lib/letsencrypt \
  -v certbot-web:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" --non-interactive --agree-tos -m somostodospossiveis@gmail.com --no-eff-email

echo ""
echo "Certificado obtido em /etc/letsencrypt/live/$DOMAIN/"
echo "Renovar automaticamente (crontab):"
echo "  0 3 * * * docker run --rm -v certbot-etc:/etc/letsencrypt -v certbot-var:/var/lib/letsencrypt -v certbot-web:/var/www/certbot certbot/certbot renew --webroot -w /var/www/certbot && docker exec atlas-nginx nginx -s reload"
