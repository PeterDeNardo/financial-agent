# Agente Financeiro Pessoal

Sistema para ingestão, análise e recomendação sobre carteira de investimentos
(Ações B3, FIIs, Renda Fixa, Cripto, Ativos Internacionais), rodando 100% em
infraestrutura própria.

## Status do projeto

- [x] Estrutura de pastas e Docker Compose
- [x] Schema inicial do banco de dados
- [x] Coletor Brapi (ações B3, FIIs, BDRs) com agendamento diário
- [x] Scheduler / agendamento dos coletores (APScheduler)
- [ ] Coletores de dados (CoinGecko, Tesouro Direto, Alpha Vantage)
- [ ] Camada de análise (indicadores de risco, rebalanceamento)
- [ ] Agente de IA (análise de mercado, análise de carteira)
- [ ] Dashboard / interface

## Pré-requisitos

- Docker Desktop instalado (com WSL2 habilitado, se estiver no Windows)
- Git

## Coleta de dados (Brapi)

O coletor **Brapi** (`coletores/coletores/brapi_collector.py`) busca cotações de ações B3, FIIs e BDRs via API pública [brapi.dev](https://brapi.dev).

### Configuração

No arquivo `.env`:

```bash
# Obrigatório para Brapi
BRAPI_TOKEN=seu_token_aqui

# Opcional: lista de tickers separados por vírgula (padrão: ITUB4)
BRAPI_TICKERS=ITUB4,VALE3,PETR4,HGLG11

# Opcional: executar coleta na inicialização do container (padrão: false)
COLLECT_ON_STARTUP=true
```

### Agendamento

- **Quando**: dias úteis (seg–sex) às **17:30 BRT** (após fechamento do mercado)
- **Verificação**: pula fins de semana e feriados nacionais (API `feriadosapi.com` com fallback fixo)
- **Timezone**: `America/Sao_Paulo`

### Dados coletados

Para cada ticker, insere/atualiza:
- **Tabela `ativos`**: ticker, nome, tipo (ação/FII/BDR), setor, moeda
- **Tabela `precos_historicos`**: data, abertura, fechamento, máxima, mínima, volume, fonte='brapi'

### Logs

```bash
docker compose logs -f collector
```

Saída esperada:
```
[collector] Conectado ao banco com sucesso (tentativa 1).
[BRAPI] Iniciando coleta...
[collector] ['ITUB4', 'VALE3', 'PETR4', 'HGLG11']
[BRAPI] Sucesso: 4 resultados
[BRAPI] Ativos: 2 novos, 2 atualizados
[BRAPI] Preços: 4 inseridos/atualizados
```

## Setup local (desenvolvimento)

1. Clone o repositório e entre na pasta do projeto.

2. Copie o arquivo de variáveis de ambiente:

   ```bash
   cp .env.example .env
   ```

3. Edite o `.env` e preencha as senhas e as chaves de API:
   - `POSTGRES_PASSWORD`, `PGADMIN_PASSWORD`
   - `BRAPI_TOKEN` (obrigatório para coleta de ações/FIIs)
   - Opcional: `BRAPI_TICKERS`, `COLLECT_ON_STARTUP`

4. Suba os containers:

   ```bash
   docker compose up -d --build
   ```

5. Verifique se tudo subiu corretamente:

   ```bash
   docker compose ps
   docker compose logs -f collector
   ```

   Você deve ver a mensagem `[collector] Iniciando serviço de coleta...` e `[collector] Conectado ao banco com sucesso` no log.

6. (Opcional) Acesse o pgAdmin em `http://localhost:5050` para inspecionar
   o banco de dados visualmente. Use as credenciais definidas no `.env`.

   Ao conectar um novo servidor no pgAdmin, use:
   - Host: `db`
   - Port: `5432`
   - Usuário/senha: os mesmos do `.env`

## Estrutura de pastas

```
financial-agent/
├── docker-compose.yml
├── .env.example
├── coletores/          # Scripts de ingestão de dados (Brapi, CoinGecko, etc.)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py               # Entry point com APScheduler
│   ├── db.py                 # DatabaseConnection wrapper
│   └── coletores/            # Módulos de coletores
│       ├── __init__.py
│       └── brapi_collector.py # Coleta Brapi (B3, FIIs, BDRs)
├── sql/init/           # Scripts SQL executados na primeira subida do banco
├── agente/             # (futuro) Lógica do agente de IA / orquestração
├── scripts/            # (futuro) Scripts utilitários (backup, migração, etc.)
└── docs/               # Documentação do projeto
```

## Schema do banco de dados

O script `sql/init/001_schema.sql` cria as tabelas na primeira subida do container Postgres (via `docker-entrypoint-initdb.d`). Usa **TimescaleDB** para séries temporais.

| Tabela | Descrição | Chave primária |
|--------|-----------|----------------|
| `ativos` | Cadastro de ativos (ações, FIIs, BDRs, cripto, renda fixa, ETFs intl) | `id` |
| `precos_historicos` | Histórico de preços (hypertable TimescaleDB) | `(ativo_id, data)` |
| `posicoes` | Posições da carteira por data (snapshot) | `id` + unique `(ativo_id, data, corretora)` |
| `indicadores_macro` | Indicadores macroeconômicos (Selic, IPCA, USD/BRL, etc.) | `id` + unique `(indicador, data)` |
| `noticias` | Notícias e contexto textual para o agente | `id` |

### Tipos de ativo (`ativos.tipo`)
- `acao` — Ações B3
- `fii` — Fundos Imobiliários
- `bdr` — Brazilian Depositary Receipts
- `renda_fixa` — Títulos públicos/privados
- `cripto` — Criptomoedas
- `etf_internacional` — ETFs internacionais

### TimescaleDB
`precos_historicos` é uma **hypertable** particionada por tempo (`data`), otimizada para consultas de séries temporais.

## Migração futura para VPS

O ambiente foi desenhado para ser portável: o mesmo `docker-compose.yml`
deve funcionar sem alterações em um VPS Linux. Ao migrar:

1. Copie o projeto (exceto `.env` e volumes locais) para o VPS.
2. Recrie o `.env` diretamente no servidor (nunca via Git).
3. Rode `docker compose up -d --build`.
4. Configure backup periódico do volume `db_data` (snapshot do provedor
   de VPS ou `pg_dump` agendado).
