# Atlas Vivo MILK — Infraestrutura Digital

Implementação auto-contida do Atlas Vivo MILK para deploy num **servidor PT
com domínio próprio**. Lê, relaciona e operacionaliza os 7 blocos da
dissertação integrada (Nextcloud → código executável).

## Stack

```
nginx (TLS, domínio PT) → api (Node/Express) → PostgreSQL + pgvector
                            ↓
                    30+ connectors (DGAL, SNIG, INE, MatrizNet, PORDATA…)
                            ↓
                    NLP PT (HuggingFace) + watermark + cert JWT
```

| Camada | Tecnologia | Bloco |
|--------|-----------|-------|
| Interface + WCAG 2.1 AA | HTML + CSS MILK | 1.1 |
| Mapa + Clustering | Leaflet 1.9.4 + OSM + SNIG WMS | 2.1 |
| Crowdsourcing + GDPR | MediaRecorder + form multi-step | 3.1 |
| Backend + APIs | Node.js/Express + connectors | 4.1 |
| Gamificação | pontos + badges + leaderboard | 5.1 |
| IA/NLP | HuggingFace PT + pgvector embeddings | 6.1 |
| Segurança | watermark + SHA-256 + JWT RS256 + GDPR | 7.1 |

## Pré-requisitos no servidor PT

- Docker Engine 24+ e Docker Compose v2
- Um domínio configurado (ex.: `atlas.milk.pt`) com registo DNS A → IP do servidor
- Certbot (Let's Encrypt) para TLS automático, ou certificado próprio

## Deploy rápido

```bash
# 1. clonar / copiar esta pasta para o servidor
cd atlas_infra

# 2. configurar variáveis de ambiente
cp .env.example .env
#   editar: ATLAS_DOMAIN, POSTGRES_PASSWORD, JWT_PRIVATE_KEY_PATH, HF_TOKEN...

# 3. subir a infraestrutura completa
docker compose -f docker-compose.prod.yml up -d --build

# 4. inicializar a base de dados (schema + pgvector + dados seed)
docker compose exec api node src/db.js --migrate
docker compose exec api node src/db.js --seed

# 5. TLS com Let's Encrypt (substitua o domínio)
certbot certonly --standalone -d atlas.milk.pt
#   ou usar o helper:
./scripts/obter-tls.sh atlas.milk.pt
```

Depois de subir, o Atlas fica em `https://<ATLAS_DOMAIN>`.

## Estrutura

```
atlas_infra/
├── docker-compose.yml            # dev (Postgres + API + frontend)
├── docker-compose.prod.yml       # prod (+ nginx TLS)
├── .env.example
├── nginx/atlas.conf               # vhost domínio PT
├── scripts/
│   ├── obter-tls.sh               # Let's Encrypt helper
│   └── backup-db.sh               # backup PostgreSQL
├── backend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── server.js              # Express API
│       ├── db.js                  # pool Postgres + migrations
│       ├── schema.sql             # schema + pgvector
│       ├── routes/                # historias, freguesias, map, gamificacao, health
│       ├── connectors/            # 30+ datasources PT
│       ├── nlp/pipeline.js        # HuggingFace PT
│       └── security/              # watermark, cert JWT RS256
└── frontend/
    ├── Dockerfile
    ├── index.html                 # mapa Leaflet + painel MILK
    ├── css/milk-theme.css         # design system MILK
    └── js/{map,form,audio,gamification}.js
```

## Modelos de dados principais

- **historia** — submissão (tipo lenda/oficio/memoria/curiosidade/transformacao, titulo, resumo, audio, freguesia, lat/lng, consentimentos CC-BY-SA + GDPR)
- **freguesia** — DGAL (308 municípios, 3091 freguesias, 4289 localidades)
- **nlp_result** — score, tags, sentiment, entities, hash SHA-256
- **usuario** — pontos, badges, nível (gamificação)
- **audit_log** — append-only, imutável

## Datasources integrados (30+)

DGAL, SNIG, DGT, INE, PORDATA, BPstat, MatrizNet, MatrizPix, GeoAPI.pt,
Dados.gov.pt, Transparência.gov, Parlamento, ANAFRE, Lisboa Aberta, FCT/POLEN,
Gridmar, EMODnet… — todos em `backend/src/connectors/`.

## Governança

Segue o Protocolo Genealógico MILK: nenhuma escrita sem hash, audit log
append-only, GDPR soft-delete, CC-BY-SA 4.0 obrigatório. Nada é publicado
externamente sem curadoria (auto-approve só acima de score 0.7).

## Licença

Conteúdo submetido: CC-BY-SA 4.0. Código infraestrutura: interno MILK.
