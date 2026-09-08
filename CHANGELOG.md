# CHANGELOG — BF Agents Squad Framework

Todas as modificações notáveis no repositório `bf-agents-squad` e na arquitetura de orquestração agnóstica da BF Labs serão documentadas neste arquivo.

---

## [1.0.0-BF] - 2026-09-08

### 🚀 Novas Funcionalidades & Arquitetura

#### 1. State Machine Atômica via GitHub Issues (Estilo `/orchestrator`)
- **Substituição do `state.json` estático por GitHub Issues:** Eliminou race conditions quando múltiplos subagentes executam em paralelo em `git worktrees`.
- **Labels de Estado:** `status:pending`, `status:in-progress`, `status:hitl-approval`, `status:completed`, `status:failed`, e `squad:bf-<nome>`.
- **`ESTADO_SQUAD.md` Local:** Visão operacional Markdown gerada no root de cada squad, sincronizada dinamicamente com as Issues do GitHub via `bin/squad-github-engine.py`.

#### 2. Naming Convention Semântico de Runs & Arquitetura de Saídas
- **Pastas Isoladas e Semânticas:** Formato `output/YYYY-MM-DD_<context-title-kebab>_run-XX/` para identificação rápida por data e assunto (ex: `2026-09-08_new-ai-instagram-carousels_run-01/`).
- **Symlink Dinâmico `latest/`:** Aponta automaticamente para a pasta de saídas da rodada mais recente.
- **Rastreabilidade Tripla:** Saídas salvas no filesystem local, commitadas/anexadas na Issue do GitHub, e enviadas ao operador via Telegram/mídia (`MEDIA:...`).

#### 3. Coleta de Inteligência Focada (ClawMem + Second Brain por Tema)
- **Check-in de Contexto (HITL Prompt):** Se o usuário não especificar fontes no prompt inicial, o Arquiteto pergunta explicitamente se deve analisar o Second Brain e o ClawMem.
- **Busca Específica por Tema:** Executa `clawmem search "<tema do squad / tipo de agente>"` e pesquisa em `/root/BF-Second-Brain/` para extrair inteligência, regras de negócio e ofertas ligadas ao escopo exato do squad.
- **Injeção Automática:** Grava o contexto resgatado em `_memory/memories.md` e customiza as personas dos agentes (`agents/*.custom.md`).

#### 4. Distinção Cirúrgica de Execução (`subagent` vs `inline`)
- **`subagent`:** Dispara processo isolado (`delegate_task` no Hermes, `subagent` no Claude Code) com janela de contexto limpa para pesquisas, scraping ou geração de código/artes.
- **`inline`:** Executa na janela de chat atual para transformações rápidas de texto, formatação de copy e revisões leves de QA sem overhead de spawn.

#### 5. Skill Universal Agnóstica (`bf-arquiteto-squad`)
- Criada em `/root/.agents/skills/bf-arquiteto-squad/SKILL.md` (symlinked em `/root/.hermes/skills/bf-arquiteto-squad`).
- Funciona identicamente no Hermes, Claude Code, Codex, OpenCode, Cursor ou qualquer CLI lendo Open Agent Skills.

---

### 📂 Arquivos Criados & Modificados no Root (`/root/bf-agents-squad/`)

- `bin/squad-github-engine.py` — Engine de criação de Epics/Issues e sync de estado no GitHub.
- `bin/squad-runner.py` — Engine de execução, naming semântico de runs e gerenciamento do symlink `latest/`.
- `templates/bf-squad-template/` — Blueprint canônico completo com `squad.yaml`, `squad-party.csv`, `agents/`, `pipeline/`, `output/`, `_memory/` e `ESTADO_SQUAD.md`.
- `_opensquad/core/architect.agent.yaml` — Configuração do Arquiteto BF Squad com as regras de busca de contexto e fatiamento em Issues.
- `CHANGELOG.md` — Este documento de registro histórico de alterações.
