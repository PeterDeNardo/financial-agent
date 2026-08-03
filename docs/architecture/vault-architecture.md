# Vault de Documentação - Arquitetura para Humano + IA

> **Objetivo**: Repositório local-first legível por humanos no Obsidian e navegável por agentes de IA via filesystem. Baseado em padrões validados: SPEC-v3 (jrcruciani), PARA + Zettelkasten (agentic-vault), Three-Zone (pharos-ai), LLM Wiki (Ar9av), Onboarding-as-code (obsidian-agent-brain).

---

## Estrutura do Vault

```
vault/
├── 00-Inbox/                    # Captura bruta não processada (PARA Inbox)
│   └── *.md                     # Web clips, meeting notes, ideias rápidas
│
├── 10-Projects/                 # Projetos ativos com objetivo definido (PARA Projects)
│   ├── _PROJECT-INDEX.md        # Mapa de todos os projetos
│   └── <project-name>/          # Um por projeto ativo
│       ├── _project.md          # Bridge card: estado, decisões, próxima ação, write-back rules
│       ├── current-state.md     # Estado atual (o que foi feito, o que está em andamento)
│       ├── decisions.md         # Log de decisões com alternativas rejeitadas
│       ├── open-questions.md    # Perguntas abertas (checkbox + link para decision quando resolvida)
│       ├── architecture.md      # Decisões arquiteturais específicas do projeto
│       ├── context/             # Contexto adicional (opcional)
│       └── handoffs/            # Cartões de transição entre sessões/agentes
│
├── 20-Areas/                    # Domínios contínuos sem fim definido (PARA Areas)
│   ├── _AREA-INDEX.md           # Mapa de áreas
│   └── <area-name>/             # Ex: backend, frontend, devops, security, product
│       ├── _area.md             # Definição da área, responsabilidades, métricas
│       ├── standards.md         # Padrões, convenções, style guides
│       ├── runbooks/            # Procedimentos operacionais
│       └── references/          # Links para resources relevantes
│
├── 30-Resources/                # Material de referência externo (PARA Resources)
│   ├── _RESOURCE-INDEX.md       # Catálogo de fontes (Source Catalog)
│   ├── articles/                # Resumos de artigos, papers, blogs
│   ├── books/                   # Resumos de livros
│   ├── tools/                   # Documentação de ferramentas, APIs
│   └── courses/                 # Notas de cursos, certificações
│
├── 40-Archive/                  # Projetos/áreas/ideias inativos (PARA Archive)
│   ├── _ARCHIVE-INDEX.md        # Taxonomia de arquivamento
│   ├── projects/                # Projetos concluídos/pausados
│   ├── areas/                   # Áreas descontinuadas
│   └── ideas/                   # Ideias não perseguidas
│
├── 50-System/                   # Infraestrutura do vault (não é conteúdo do usuário)
│   ├── templates/               # Templates de notas (Project, Area, Decision, etc.)
│   ├── scripts/                 # Helper scripts (health check, index generation)
│   ├── governance/              # Regras para agentes (write-back, review gates)
│   │   ├── START-HERE.md        # Ponto de entrada OBRIGATÓRIO para agentes
│   │   ├── write-back-rules.md  # O que agentes podem/escrever, quando perguntar
│   │   ├── review-gates.md      # Checkpoints de validação
│   │   └── maintenance-loop.md  # Rotinas de limpeza, dedup, link repair
│   └── recall/                  # Mapeamento tarefa → contexto
│       ├── task-maps/           # Mapas: "task type" → arquivos a ler
│       └── recall-fields.md     # Campos padronizados para recall
│
├── 60-Agents/                   # Workspace compartilhado entre agentes
│   ├── skills/                  # Skills reutilizáveis (uma pasta canônica)
│   │   ├── SKILLS-REGISTRY.md   # Índice de skills disponíveis
│   │   ├── inbox-triage.md      # Processar inbox → promover para Projects/Areas
│   │   ├── atomic-note.md       # Criar nota atômica com links obrigatórios
│   │   ├── decision-log.md      # Registrar decisão com alternativas rejeitadas
│   │   ├── contradiction-recon.md # Detectar e resolver contradições
│   │   ├── vault-qa.md          # Responder perguntas sobre o vault
│   │   └── ...                  # Outras skills
│   ├── steering/                # Convenções lidas sob demanda
│   │   ├── file-naming.md       # Convenção de nomes de arquivos
│   │   ├── tag-taxonomy.md      # Tags canônicas
│   │   ├── security-practices.md # Práticas de segurança (secrets, PII)
│   │   ├── session-continuity.md # Protocolo de continuidade entre sessões
│   │   ├── bi-temporal-facts.md # Rastreamento de fatos com validade temporal
│   │   └── ultramode.md         # Modo operacional rigoroso (verify-first)
│   └── outputs/                 # Entregáveis gerados por agentes
│
├── 70-Raw/                      # Material imutável fonte (Three-Zone: raw/)
│   ├── conversations/           # Exports de chats (Claude, Codex, etc.)
│   ├── transcripts/             # Transcrições de reuniões
│   ├── exports/                 # Exports de ferramentas (Notion, Linear, etc.)
│   └── attachments/             # PDFs, imagens, arquivos brutos
│
├── 80-Sessions/                 # Logs de sessão de trabalho (episódicos)
│   ├── YYYY-MM-DD/
│   │   ├── session-<id>.md      # Log da sessão: escopo, ações, decisões, write-backs
│   │   └── context-snapshot.md  # Snapshot do estado relevante ao final
│   └── _SESSION-INDEX.md        # Índice cronológico
│
└── 90-Meta/                     # Metadados do vault
    ├── CLAUDE.md                # Bootstrap auto-carregado pelo Claude Code
    ├── AGENTS.md                # Constituição universal do vault (regras para TODOS agentes)
    ├── USER.md                  # Identidade do dono: expertise, preferências, valores
    ├── WORKFLOW.md              # Protocolo de sessão: start/end, switch topics, vault vs session
    ├── vault-config.yaml        # Configuração estruturada (paths, tags, status vocabulary)
    ├── tag-conventions.md       # Tags canônicas
    ├── status-vocabulary.md     # Valores permitidos para frontmatter status:
    └── audit-log.md             # Histórico de auditorias trimestrais
```

---

## Princípios de Design

### 1. Three-Zone Architecture (pharos-ai)
| Zona | Path | Propósito |
|------|------|-----------|
| **Raw** | `70-Raw/` | Captura imutável, nunca editada, staging buffer |
| **Wiki** | `10-Projects/`, `20-Areas/`, `30-Resources/` | Conhecimento sintetizado, linkado, navegável |
| **Entry** | `90-Meta/CLAUDE.md` | Ponto de partida único, < 50 linhas, aponta para Project Hub |

### 2. PARA + Zettelkasten Híbrido (agentic-vault)
- **PARA** para organização de alto nível (Projects, Areas, Resources, Archive)
- **Zettelkasten** dentro de cada projeto/área: notas atômicas, links inline obrigatórios, MOCs (Maps of Content)

### 3. Atomic Facts + Events (SPEC-v3)
- Um fato durável = um arquivo em `10-Projects/<name>/` ou `20-Areas/<name>/`
- Frontmatter tipado (YAML) para query/filtro
- Eventos em `80-Sessions/` (append-only, episódico)

### 4. Onboarding-as-Code (obsidian-agent-brain)
Quatro arquivos em `90-Meta/` que TODO agente lê na inicialização:
1. `CLAUDE.md` → bootstrap (auto-load no Claude Code)
2. `AGENTS.md` → constituição universal (regras, estrutura, convenções)
3. `USER.md` → identidade do dono (adaptação do agente a VOCÊ)
4. `WORKFLOW.md` → protocolo de sessão (vault = estado, sessão = workspace)

### 5. Governance Layer (agentic-vault)
- `AGENTS.md` = fonte de verdade única
- Configs por agente (`.claude/`, `.codex/`, etc.) só sobrescrevem **preferências**, nunca **protocolos**
- Script `sync-agents.ps1` detecta drift

### 6. Recall System (Moxi-Lab)
- `50-System/recall/task-maps/` mapeia tipo de tarefa → arquivos mínimos a ler
- Bridge cards em `10-Projects/<name>/_project.md` = contexto mínimo para começar

---

## Fluxo de Trabalho do Agente

```
INÍCIO DA SESSÃO
├── 1. Ler 90-Meta/CLAUDE.md (auto-load)
├── 2. Ler 90-Meta/AGENTS.md (constituição)
├── 3. Ler 90-Meta/USER.md (identidade do usuário)
├── 4. Ler 90-Meta/WORKFLOW.md (protocolo)
├── 5. Declarar escopo: "Hoje trabalhamos em X"
├── 6. Ler bridge card: 10-Projects/X/_project.md
├── 7. Ler recall map: 50-System/recall/task-maps/<task-type>.md
├── 8. Executar tarefa (ler apenas o necessário via link traversal)
└── 9. FIM DA SESSÃO → Write-back obrigatório:
    ├── Atualizar 10-Projects/X/current-state.md
    ├── Registrar decisões em 10-Projects/X/decisions.md
    ├── Atualizar open-questions.md
    ├── Log em 80-Sessions/YYYY-MM-DD/session-<id>.md
    └── Promover lições para 20-Areas/ ou 20-SharedAssets/
```

---

## Convenções de Arquivo

### Frontmatter Obrigatório (todas as notas wiki)
```yaml
---
title: "Título Descritivo"
type: project|area|resource|decision|concept|procedure|reference
status: active|completed|archived|on-hold|draft
tags: [tag1, tag2]           # De tag-conventions.md
created: YYYY-MM-DD
updated: YYYY-MM-DD
project: "<project-name>"    # Se aplicável
area: "<area-name>"          # Se aplicável
aliases: ["alternative names"]
---
```

### Links Internos (Wikilinks)
- **Obrigatório**: Mínimo 2 `[[links]]` inline no corpo (não no final)
- **Alcance**: Toda nota alcançável de `CLAUDE.md` em ≤ 3 hops
- **Sem duplicatas**: Atualizar nota existente em vez de criar variante

### Templates
Localizados em `50-System/templates/`:
- `project-bridge-card.md` → `_project.md`
- `area-definition.md` → `_area.md`
- `decision-log.md` → `decisions.md`
- `open-questions.md`
- `session-log.md`
- `concept-note.md`
- `procedure.md`
- `resource-summary.md`
- `meeting-note.md`
- `daily-note.md`

---

## Integração com Obsidian

### Plugins Recomendados (Core)
- **Bases** (core) - Dashboards, views, queries
- **Kanban** - Board em `10-Projects/To Do.md`
- **Templater** - Templates dinâmicos
- **Calendar** - Navegação temporal em `80-Sessions/`
- **Excalidraw** - Diagramas em notas
- **Dataview** - Queries avançadas (indices, dashboards)

### Plugins Comunitários Úteis
- **Smart Connections** - Embeddings + busca semântica (opcional)
- **Various Complements** - Autocomplete de wikilinks/tags
- **Outliner** - Listas colapsáveis
- **Linter** - Formatação consistente

### Configuração `.obsidian/`
```json
// app.json
{
  "alwaysUpdateLinks": true,
  "newLinkFormat": "relative",
  "useMarkdownLinks": false
}
// workspace.json - salva layout de painéis
```

---

## Scripts de Automação (`50-System/scripts/`)

| Script | Gatilho | Ação |
|--------|---------|------|
| `vault-health-check.ps1` | Manual / CI | Órfãos, links quebrados, frontmatter inválido, tags não canônicas |
| `generate-indexes.ps1` | Pós-sessão | Atualizar `_*-INDEX.md`, `_SESSION-INDEX.md` |
| `vault-git-snapshot.ps1` | SessionEnd hook | Commit local com secret-gate, bundle mensal off-root |
| `sync-agents.ps1` | Manual | Verificar drift entre AGENTS.md e configs por agente |
| `inbox-triage.ps1` | Skill inbox-triage | Processar 00-Inbox → promover para Projects/Areas |

---

## Arquivos de Entrada (90-Meta/) - Detalhamento

### CLAUDE.md (Bootstrap - < 50 linhas)
```markdown
# Vault Memory Entry

@10-Projects/_PROJECT-INDEX.md — Mapa de projetos ativos
@20-Areas/_AREA-INDEX.md — Mapa de áreas de responsabilidade
@50-System/governance/START-HERE.md — Protocolo de inicialização do agente
@90-Meta/AGENTS.md — Constituição do vault
@90-Meta/USER.md — Identidade do usuário
@90-Meta/WORKFLOW.md — Protocolo de sessão
```

### AGENTS.md (Constituição Universal)
- Estrutura de pastas e contratos
- Regras operacionais (read-first, write-back, review gates)
- Tabela de resolução de conflitos entre agentes
- Prioridade de steering docs
- Skill registry pointer

### USER.md (Identidade)
```markdown
# User Profile

## Expertise
- Domínios principais: ...
- Stack tecnológica: ...
- Anos de experiência: ...

## Comunicação
- Estilo preferido: direto/conciso/pedagógico
- Nível de detalhe padrão: ...
- Idiomas: ...

## Valores & Preferências
- Princípios de design: ...
- Trade-offs preferidos: ...
- Ferramentas preferidas: ...

## Contexto Atual
- Projeto principal: ...
- Foco atual: ...
- Restrições ativas: ...
```

### WORKFLOW.md (Protocolo de Sessão)
- Mental model: "Vault = estado persistente, Sessão = workspace efêmero"
- Início: declaração de escopo → carregar bridge card + recall map
- Durante: link traversal, não full-scan
- Fim: write-back estruturado → log de sessão → promover lições
- Troca de tópico: nova sessão ou `/clear`
- Sessões paralelas: terminais separados, tópicos separados

---

## Métricas de Saúde do Vault

| Métrica | Alvo | Verificação |
|---------|------|-------------|
| Órfãos (sem backlinks) | 0 | `vault-health-check` |
| Links quebrados | 0 | `vault-health-check` |
| Notas sem 2+ links inline | 0 | Linter custom |
| Alcance ≤ 3 hops de CLAUDE.md | 100% | Script custom |
| Tags não canônicas | 0 | `vault-health-check` |
| Frontmatter inválido | 0 | Linter |
| Inbox > 7 dias sem processar | 0 | Dashboard Kanban |
| Sessions sem write-back | 0 | `_SESSION-INDEX.md` |

---

## Migração de Vault Existente

1. **Não reconstrua** - adicione estrutura gradualmente
2. Crie `10-Projects/<projeto-atual>/_project.md` primeiro (bridge card)
3. Mova notas relacionadas para baixo do projeto
4. Adicione `90-Meta/` com os 4 arquivos de onboarding
5. Configure `50-System/governance/START-HERE.md`
6. Rode `vault-health-check` e corrija incrementalmente
7. Adicione skills/steering conforme necessidade

---

## Referências dos Padrões Utilizados

| Padrão | Repo/Artigo | Contribuição Principal |
|--------|-------------|------------------------|
| SPEC-v3 | jrcruciani/obsidian-memory-for-ai | Atomic facts, events, schemas, inbox/outbox, generated views |
| PARA + Zettelkasten | kurtvalcorza/agentic-vault | Organização híbrida, AGENTS.md governance, 36 skills, git snapshots |
| Three-Zone | pharos-ai (hashnode) | raw/wiki/entry, hub-first traversal, decision logs com rejected alternatives |
| LLM Wiki Skills | Ar9av/obsidian-wiki | Karpathy pattern, skill-based framework, project org, manifest tracking |
| Onboarding-as-Code | LikelyMalware/obsidian-agent-brain | CLAUDE/AGENTS/USER/WORKFLOW.md, PARA folders, Smart Connections + MCP |
| AI Workflow Kit | Moxi-Lab/obsidian-ai-workflow-kit | START-HERE.md, project bridge cards, pipeline, recall, governance, Bases |
| Long-term Memory | eslamgenio/long-term-agent-memory | Inbox, sessions, projects, concepts, entities, references, procedures, decisions |

---

*Documentação viva - atualize conforme o vault evolui. Última revisão: 2026-08-03*