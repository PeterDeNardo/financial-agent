-- Schema inicial do sistema de gestão financeira/patrimonial.
-- Este script roda automaticamente na primeira vez que o container
-- do Postgres sobe (via docker-entrypoint-initdb.d).

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Cadastro de ativos (ações, FIIs, cripto, renda fixa, internacionais)
CREATE TABLE IF NOT EXISTS ativos (
    id          SERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL UNIQUE,
    nome        TEXT,
    tipo        TEXT NOT NULL CHECK (tipo IN (
                    'acao', 'fii', 'renda_fixa', 'cripto', 'bdr', 'etf_internacional'
                )),
    setor       TEXT,
    moeda       TEXT NOT NULL DEFAULT 'BRL',
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Histórico de preços — tabela "hypertable" do TimescaleDB
CREATE TABLE IF NOT EXISTS precos_historicos (
    ativo_id    INTEGER NOT NULL REFERENCES ativos(id),
    data        TIMESTAMPTZ NOT NULL,
    abertura    NUMERIC(18, 6),
    fechamento  NUMERIC(18, 6) NOT NULL,
    maxima      NUMERIC(18, 6),
    minima      NUMERIC(18, 6),
    volume      NUMERIC(20, 2),
    fonte       TEXT NOT NULL,  -- ex: 'brapi', 'coingecko', 'tesouro_direto'
    PRIMARY KEY (ativo_id, data)
);

SELECT create_hypertable('precos_historicos', 'data', if_not_exists => TRUE);

-- Posições da carteira ao longo do tempo (snapshot por data)
CREATE TABLE IF NOT EXISTS posicoes (
    id              SERIAL PRIMARY KEY,
    ativo_id        INTEGER NOT NULL REFERENCES ativos(id),
    data            DATE NOT NULL,
    quantidade      NUMERIC(20, 8) NOT NULL,
    preco_medio     NUMERIC(18, 6),
    corretora       TEXT,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ativo_id, data, corretora)
);

-- Indicadores macroeconômicos (Selic, IPCA, câmbio, etc.)
CREATE TABLE IF NOT EXISTS indicadores_macro (
    id          SERIAL PRIMARY KEY,
    indicador   TEXT NOT NULL,  -- ex: 'selic', 'ipca', 'usd_brl'
    data        DATE NOT NULL,
    valor       NUMERIC(18, 6) NOT NULL,
    fonte       TEXT NOT NULL DEFAULT 'bacen_sgs',
    UNIQUE (indicador, data)
);

-- Notícias e contexto textual, para o agente consultar/relacionar com ativos
CREATE TABLE IF NOT EXISTS noticias (
    id                  SERIAL PRIMARY KEY,
    data                TIMESTAMPTZ NOT NULL,
    fonte               TEXT NOT NULL,
    titulo              TEXT NOT NULL,
    conteudo            TEXT,
    url                 TEXT,
    ativos_relacionados INTEGER[] DEFAULT '{}',
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices auxiliares
CREATE INDEX IF NOT EXISTS idx_precos_ativo_data ON precos_historicos (ativo_id, data DESC);
CREATE INDEX IF NOT EXISTS idx_posicoes_data ON posicoes (data DESC);
CREATE INDEX IF NOT EXISTS idx_noticias_data ON noticias (data DESC);
