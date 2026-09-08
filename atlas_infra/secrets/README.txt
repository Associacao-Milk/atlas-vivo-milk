# Colocar aqui as chaves JWT RS256 (gerar antes do primeiro deploy):
#
#   openssl genrsa -out jwt-private.pem 2048
#   openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem
#
# Estes ficheiros são montados em /run/secrets no contentor da API (read-only).
# NÃO commitar chaves reais para o repositório.
