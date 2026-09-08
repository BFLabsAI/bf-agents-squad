#!/usr/bin/env python3
import sys, os, json, yaml, subprocess
from datetime import datetime
from pathlib import Path

def run_cmd(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def get_or_create_run_dir(squad_dir):
    squad_dir = Path(squad_dir).resolve()
    output_dir = squad_dir / 'output'
    output_dir.mkdir(exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    existing_runs = sorted(list(output_dir.glob(f"{today_str}_run-*")))
    run_num = len(existing_runs) + 1
    
    current_run_dir = output_dir / f"{today_str}_run-{run_num:02d}"
    current_run_dir.mkdir(parents=True, exist_ok=True)

    # Link latest
    latest_link = output_dir / 'latest'
    if latest_link.is_symlink() or latest_link.exists():
        latest_link.unlink()
    try:
        latest_link.symlink_to(current_run_dir, target_is_directory=True)
    except Exception:
        pass

    return current_run_dir

def print_squad_status(squad_dir):
    squad_dir = Path(squad_dir).resolve()
    squad_yaml = squad_dir / 'squad.yaml'
    pipe_yaml = squad_dir / 'pipeline' / 'pipeline.yaml'

    if not squad_yaml.exists():
        print(f"[Erro] Manifesto squad.yaml não encontrado em {squad_dir}")
        return

    with open(squad_yaml) as f: squad_cfg = yaml.safe_load(f)
    with open(pipe_yaml) as f: pipe_cfg = yaml.safe_load(f)

    squad_name = squad_cfg.get('name', squad_dir.name)
    squad_code = squad_cfg.get('code', squad_dir.name)

    # Get issue status from gh
    repo_dir = squad_dir.parents[1] if squad_dir.parents[1].name != '/' else squad_dir
    _, out, _ = run_cmd(f'gh issue list --label "squad:{squad_code}" --state all --json number,title,state,labels', cwd=repo_dir)
    
    issues = json.loads(out) if out else []

    print(f"\n=========================================")
    print(f"📋 SQUAD {squad_name.upper()} ({squad_code})")
    print(f"=========================================")
    print(f"• Saídas em: {squad_dir}/output/latest/")
    print(f"• Total de Steps no Pipeline: {len(pipe_cfg.get('steps', []))}")
    print(f"• Total de Issues no GitHub: {len(issues)}\n")

    for step in pipe_cfg.get('steps', []):
        s_id = step['id']
        s_type = step.get('type', 'agent_execution')
        matched_issue = next((i for i in issues if s_id in i['title']), None)
        
        status_label = "PENDENTE"
        if matched_issue:
            lbl_names = [l['name'] for l in matched_issue.get('labels', [])]
            if "status:completed" in lbl_names: status_label = "✅ CONCLUÍDO"
            elif "status:hitl-approval" in lbl_names: status_label = "⏸️ CHECKPOINT (HITL)"
            elif "status:in-progress" in lbl_names: status_label = "🔂 EM EXECUÇÃO"
            elif "status:failed" in lbl_names: status_label = "❌ FALHOU"

        print(f"  [{status_label}] {s_id} ({step.get('agent', s_type)})")
    print(f"=========================================\n")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'init-run':
            squad_path = sys.argv[2]
            run_dir = get_or_create_run_dir(squad_path)
            print(f"[Run Inicializada] Pasta de saídas da rodada: {run_dir}")
        elif cmd == 'status':
            squad_path = sys.argv[2]
            print_squad_status(squad_path)
    else:
        print("Uso: python3 squad-runner.py [init-run | status] /caminho/do/squad")
