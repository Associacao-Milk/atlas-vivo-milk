-- Atlas Vivo MILK — schema PostgreSQL + pgvector
-- Bloco 4.1 (backend) + 6.1 (embeddings) + 7.1 (auditoria)

-- Extensão pgvector para similaridade vetorial (detecção duplicatas, pesquisa semântica)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- ENTIDADES TERRITORIAIS (DGAL)
-- ============================================================
CREATE TABLE IF NOT EXISTS freguesia (
  id              SERIAL PRIMARY KEY,
  codigo_dgal     TEXT UNIQUE NOT NULL,
  nome            TEXT NOT NULL,
  municipio       TEXT NOT NULL,
  distrito        TEXT NOT NULL,
  codigo_municipio TEXT,
  regiao          TEXT,                 -- Continente / Açores / Madeira
  ccdr            TEXT,                 -- Comissão de Coordenação e Desenvolvimento Regional
  geom_centro     JSONB,                -- {lat, lng}
  created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_freguesia_nome ON freguesia USING GIN (to_tsvector('portuguese', nome));
CREATE INDEX IF NOT EXISTS idx_freguesia_municipio ON freguesia(municipio);

CREATE TABLE IF NOT EXISTS localidade (
  id          SERIAL PRIMARY KEY,
  nome        TEXT NOT NULL,
  freguesia_id INTEGER REFERENCES freguesia(id),
  geom_centro JSONB
);
CREATE INDEX IF NOT EXISTS idx_localidade_nome ON localidade USING GIN (to_tsvector('portuguese', nome));

-- ============================================================
-- ENTIDADE PRINCIPAL — HISTÓRIA (submissão crowdsourced)
-- ============================================================
CREATE TYPE tipo_historia AS ENUM ('lenda','oficio','memoria','curiosidade','transformacao');
CREATE TYPE estado_historia AS ENUM ('rascunho','submetida','em_curadoria','aprovada','publicada','rejeitada','removida');
CREATE TYPE nivel_anonimato AS ENUM ('completo','primeiro-nome','nome-completo','pseudonimo');

CREATE TABLE IF NOT EXISTS historia (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo              TEXT NOT NULL CHECK (char_length(titulo) <= 120),
  resumo              TEXT NOT NULL CHECK (char_length(resumo) <= 300),
  tipo                tipo_historia NOT NULL,
  corpo               TEXT,                    -- transcrição áudio se aplicável
  freguesia_id        INTEGER REFERENCES freguesia(id),
  freguesia_nome      TEXT,                    -- denormalizado para submissão antes de validação
  lat                 DOUBLE PRECISION,
  lng                 DOUBLE PRECISION,
  audio_path          TEXT,                    -- caminho no volume uploads
  audio_mime          TEXT,
  audio_duracao_seg   INTEGER,
  anonimato           nivel_anonimato NOT NULL DEFAULT 'completo',
  nome_submissor      TEXT,                    -- só se anonimato != completo
  email_submissor     TEXT NOT NULL,            -- interno, nunca publicado
  consent_cc_by_sa    BOOLEAN NOT NULL DEFAULT FALSE,
  consent_privacidade BOOLEAN NOT NULL DEFAULT FALSE,
  consent_arquivo     BOOLEAN NOT NULL DEFAULT FALSE,
  estado              estado_historia NOT NULL DEFAULT 'submetida',
  visibilidade_publica BOOLEAN NOT NULL DEFAULT FALSE,
  cert_token          TEXT,                    -- JWT RS256 de autenticidade
  cert_hash           TEXT,                    -- SHA-256 imutável
  embedding           vector(384),             -- sentence-transformers pt
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at        TIMESTAMPTZ,
  removed_at          TIMESTAMPTZ               -- GDPR soft-delete
);
CREATE INDEX IF NOT EXISTS idx_historia_estado ON historia(estado);
CREATE INDEX IF NOT EXISTS idx_historia_tipo ON historia(tipo);
CREATE INDEX IF NOT EXISTS idx_historia_freguesia ON historia(freguesia_id);
CREATE INDEX IF NOT EXISTS idx_historia_publicada ON historia(visibilidade_publica) WHERE visibilidade_publica = TRUE;
-- Pesquisa semântica (detecção duplicatas cosine > 0.95 — Bloco 6.1)
CREATE INDEX IF NOT EXISTS idx_historia_embedding ON historia USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- NLP RESULT (pipeline IA — Bloco 4.1/6.1)
-- ============================================================
CREATE TABLE IF NOT EXISTS nlp_result (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  historia_id     UUID NOT NULL REFERENCES historia(id) ON DELETE CASCADE,
  score           DOUBLE PRECISION,            -- 0..1 (auto-approve > 0.7)
  tags            TEXT[],                      -- Clima, Água, Trabalho, Identidade…
  sentiment       DOUBLE PRECISION,            -- 0..1 (alegria..medo)
  sentiment_label TEXT,
  entities        JSONB,                       -- {pessoas:[], lugares:[], datas:[]}
  anacronismos    TEXT[],
  modelo          TEXT,                         -- bertimbau / xlm-roberta
  created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_nlp_historia ON nlp_result(historia_id);

-- ============================================================
-- GAMIFICAÇÃO (Bloco 5.1)
-- ============================================================
CREATE TABLE IF NOT EXISTS usuario (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email               TEXT UNIQUE NOT NULL,
  nome                TEXT,
  pontos              INTEGER NOT NULL DEFAULT 0,
  nivel               INTEGER NOT NULL DEFAULT 1,
  badges              TEXT[] DEFAULT ARRAY[]::TEXT[],
  historias_submetidas INTEGER NOT NULL DEFAULT 0,
  historias_validadas  INTEGER NOT NULL DEFAULT 0,
  ccdr                TEXT,                      -- leaderboard regional
  created_at          TIMESTAMPTZ DEFAULT now()
);
-- Badges: historiador (+5), guardiao (+1000 pts), curador (+10 validadas), padrinho_milk

CREATE TABLE IF NOT EXISTS missao (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo        TEXT NOT NULL,
  descricao     TEXT,
  pontos        INTEGER NOT NULL DEFAULT 10,
  geo_lat       DOUBLE PRECISION,
  geo_lng       DOUBLE PRECISION,
  geo_raio_m    INTEGER,
  ativa         BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- CURADORIA (filas de aprovação)
-- ============================================================
CREATE TABLE IF NOT EXISTS curadoria_acao (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  historia_id   UUID NOT NULL REFERENCES historia(id),
  curador_email TEXT NOT NULL,
  decisao       TEXT NOT NULL CHECK (decisao IN ('aprovar','rejeitar','pedir_alteracoes')),
  fundamento    TEXT,
  created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_curadoria_historia ON curadoria_acao(historia_id);

-- ============================================================
-- AUDIT LOG — append-only, imutável (Bloco 7.1)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
  id            BIGSERIAL PRIMARY KEY,
  ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor         TEXT NOT NULL,
  acao          TEXT NOT NULL,
  entidade      TEXT,
  entidade_id   TEXT,
  antes         JSONB,
  depois        JSONB,
  ip            TEXT
);
-- Não há UPDATE/DELETE permitidos ao nível da aplicação (RLS ou trigger)

-- ============================================================
-- DATASOURCE CACHE (connectors 30+ APIs)
-- ============================================================
CREATE TABLE IF NOT EXISTS datasource_cache (
  source_id     TEXT NOT NULL,
  endpoint      TEXT NOT NULL,
  params_hash   TEXT NOT NULL,
  payload       JSONB NOT NULL,
  fetched_at    TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (source_id, endpoint, params_hash)
);
