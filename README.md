# Agente Financeiro Pessoal

Sistema para ingestão, análise e recomendação sobre carteira de investimentos
(Ações B3, FIIs, Renda Fixa, Cripto, Ativos Internacionais), rodando 100% em
infraestrutura própria.

## Status do projeto

- [x] Estrutura de pastas e Docker Compose
- [x] Schema inicial do banco de dados
- [ ] Coletores de dados (Brapi, CoinGecko, Tesouro Direto, Alpha Vantage)
- [ ] Scheduler / agendamento dos coletores
- [ ] Camada de análise (indicadores de risco, rebalanceamento)
- [ ] Agente de IA (análise de mercado, análise de carteira)
- [ ] Dashboard / interface

## Pré-requisitos

- Docker Desktop instalado (com WSL2 habilitado, se estiver no Windows)
- Git

## Setup local (desenvolvimento)

1. Clone o repositório e entre na pasta do projeto.

2. Copie o arquivo de variáveis de ambiente:

   ```bash
   cp .env.example .env
   ```

3. Edite o `.env` e preencha as senhas e as chaves de API que você já tiver
   (pode deixar em branco por enquanto — os coletores ainda não foram
   implementados).

4. Suba os containers:

   ```bash
   docker compose up -d --build
   ```

5. Verifique se tudo subiu corretamente:

   ```bash
   docker compose ps
   docker compose logs -f collector
   ```

   Você deve ver a mensagem `[collector] Serviço pronto.` no log.

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
│   └── main.py
├── sql/init/           # Scripts SQL executados na primeira subida do banco
├── agente/             # (futuro) Lógica do agente de IA / orquestração
├── scripts/            # (futuro) Scripts utilitários (backup, migração, etc.)
└── docs/               # Documentação do projeto
```

## Migração futura para VPS

O ambiente foi desenhado para ser portável: o mesmo `docker-compose.yml`
deve funcionar sem alterações em um VPS Linux. Ao migrar:

1. Copie o projeto (exceto `.env` e volumes locais) para o VPS.
2. Recrie o `.env` diretamente no servidor (nunca via Git).
3. Rode `docker compose up -d --build`.
4. Configure backup periódico do volume `db_data` (snapshot do provedor
   de VPS ou `pg_dump` agendado).
