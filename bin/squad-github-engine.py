#!/usr/bin/env python3
import sys, os, json, yaml, subprocess

def run_cmd(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def check_governance(repo_dir):
    code, out, err = run_cmd("gh repo view", cwd=repo_dir)
    if code != 0:
        print(f"[ERRO Governança] Repositório GitHub inacessível ou sem remote origin: {err}")
        return False
    print(f"[Governança OK] Remote GitHub validado: {out.splitlines()[0]}")
    return True

def create_squad_labels(repo_dir, squad_code):
    labels = [
        ("status:pending", "1D76DB", "Etapa aguardando execução"),
        ("status:in-progress", "FBCA04", "Etapa em execução pelo agente"),
        ("status:hitl-approval", "D93F0B", "Aguardando decisão/aprovação humana"),
        ("status:completed", "0E8A16", "Etapa concluída e auditada pelo QA"),
        ("status:failed", "B60205", "Etapa reprovada pelo QA"),
        (f"squad:{squad_code}", "5319E7", f"Pertence ao squad {squad_code}")
    ]
    for name, color, desc in labels:
        cmd = f'gh label create "{name}" --color "{color}" --description "{desc}" --force'
        run_cmd(cmd, cwd=repo_dir)
    print(f"[Labels Sync] Labels do squad '{squad_code}' sincronizadas no GitHub.")

def publish_squad_issues(squad_dir):
    squad_dir = Path(squad_dir).resolve()
    squad_yaml_path = squad_dir / 'squad.yaml'
    pipeline_yaml_path = squad_dir / 'pipeline' / 'pipeline.yaml'

    if not squad_yaml_path.exists() or not pipeline_yaml_path.exists():
        print(f"[Erro] Arquivos de manifesto não encontrados em {squad_dir}")
        return False

    with open(squad_yaml_path) as f: squad_cfg = yaml.safe_load(f)
    with open(pipeline_yaml_path) as f: pipe_cfg = yaml.safe_load(f)

    squad_code = squad_cfg.get('code', squad_dir.name)
    repo_dir = squad_dir.parents[1] if squad_dir.parents[1].name != '/' else squad_dir

    if not check_governance(repo_dir):
        return False

    create_squad_labels(repo_dir, squad_code)

    # 1. Criar Epic Master
    epic_title = f"EPIC: [{squad_cfg.get('name', squad_code)}] Execution Pipeline"
    epic_body = f"""# Epic Orchestration Pipeline — {squad_cfg.get('name')}

**Squad Code:** `{squad_code}`
**Descrição:** {squad_cfg.get('description')}

## DAG de Execução
"""
    for step in pipe_cfg.get('steps', []):
        step_type = step.get('type', 'agent_execution')
        epic_body += f"- [ ] **{step['id']}** ({step.get('agent', step_type)})
"

    cmd_epic = f'gh issue create --title "{epic_title}" --body {json.dumps(epic_body)} --label "squad:{squad_code}"'
    code, out_epic, err = run_cmd(cmd_epic, cwd=repo_dir)
    print(f"[Epic Criado] {out_epic}")

    # 2. Criar Sub-Issues para cada Step
    step_issues = {}
    for step in pipe_cfg.get('steps', []):
        step_id = step['id']
        step_type = step.get('type', 'agent_execution')
        is_hitl = (step_type == 'human_in_the_loop')

        initial_label = "status:hitl-approval" if is_hitl else "status:pending"
        title = f"[{squad_code}] Step: {step_id}"
        
        body = f"""---
squad: {squad_code}
step_id: {step_id}
type: {step_type}
agent: {step.get('agent', 'N/A')}
spec: {step.get('spec', 'N/A')}
depends_on: {step.get('depends_on', [])}
outputs: {step.get('outputs', [])}
---

## Requisitos do Passo
{step.get('prompt', 'Executar spec definida em ' + str(step.get('spec')))}

## Criterios de Aceite
- [ ] Executar passo via subagent/inline
- [ ] Validar arquivos de saída em `{step.get('outputs', [])}`
- [ ] Executar QA Auditoria antes de encerrar
"""
        cmd_step = f'gh issue create --title "{title}" --body {json.dumps(body)} --label "squad:{squad_code},{initial_label}"'
        code, out_step, err = run_cmd(cmd_step, cwd=repo_dir)
        step_issues[step_id] = out_step
        print(f"  └─ [Step Issue] {step_id}: {out_step}")

    # 3. Gerar ESTADO_SQUAD.md local sincronizado
    sync_markdown_state(squad_dir, squad_code, pipe_cfg, step_issues)
    return True

def sync_markdown_state(squad_dir, squad_code, pipe_cfg, step_issues):
    md_path = squad_dir / 'ESTADO_SQUAD.md'
    content = f"# ESTADO DO SQUAD — {squad_code.upper()}

"
    content += f"**Fonte de Verdade Persistente:** GitHub Issues (`squad:{squad_code}`)

"
    content += "## Mapeamento de DAG & Status

"
    content += "| Step ID | Agente / Tipo | GitHub Issue | Status |
"
    content += "| :--- | :--- | :--- | :--- |
"

    for step in pipe_cfg.get('steps', []):
        s_id = step['id']
        s_agent = step.get('agent', step.get('type'))
        issue_url = step_issues.get(s_id, 'N/A')
        initial_label = "HITL Waiting" if step.get('type') == 'human_in_the_loop' else "Pending"
        content += f"| `{s_id}` | {s_agent} | {issue_url} | `{initial_label}` |
"

    md_path.write_text(content)
    print(f"[Estado Sincronizado] {md_path}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        publish_squad_issues(sys.argv[1])
    else:
        print("Uso: python3 squad-github-engine.py /caminho/para/squads/bf-squad-<nome>")
