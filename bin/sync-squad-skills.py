#!/usr/bin/env python3
import os, sys, yaml
from pathlib import Path

def sync_squad_skills():
    root_dir = Path('/root/bf-agents-squad')
    squads_dir = root_dir / 'squads'
    skills_base = Path('/root/.agents/skills')
    hermes_skills_base = Path('/root/.hermes/skills')

    if not squads_dir.exists():
        print(f"[Aviso] Pasta {squads_dir} não encontrada.")
        return

    registered = []
    for squad_folder in squads_dir.iterdir():
        if squad_folder.is_dir() and (squad_folder / 'squad.yaml').exists():
            squad_yaml = squad_folder / 'squad.yaml'
            with open(squad_yaml) as f: cfg = yaml.safe_load(f)
            
            squad_code = cfg.get('code', squad_folder.name)
            squad_name = cfg.get('name', squad_folder.name)
            skill_name = f"bf-squad-{squad_code}" if not squad_code.startswith('bf-') else squad_code

            target_skill_dir = skills_base / skill_name
            target_skill_dir.mkdir(parents=True, exist_ok=True)

            skill_md_content = f"""---
name: {skill_name}
description: Executa o Squad {squad_name} ({squad_code}) com base nas GitHub Issues e saídas em {squad_folder}/output/.
---

# {squad_name.upper()} — Execution Skill

Executa a esteira do Squad **{squad_name}** em `/root/bf-agents-squad/squads/{squad_folder.name}/`.

## Comandos Rápidos
- **Status do Squad:** `python3 /root/bf-agents-squad/bin/squad-runner.py status /root/bf-agents-squad/squads/{squad_folder.name}`
- **Iniciar Rodada:** `python3 /root/bf-agents-squad/bin/squad-runner.py init-run /root/bf-agents-squad/squads/{squad_folder.name} "[Nome-do-Projeto]"`

## Regras de Execução
1. Consulte as Issues com a label `squad:{squad_code}` no GitHub.
2. Pegue o próximo passo com label `status:pending`.
3. Executa o passo em modo `subagent` ou `inline` conforme definido no `squad-party.csv`.
4. Salva a saída na pasta da run em `output/latest/` e anexa o log na Issue do GitHub (`gh issue comment`).
5. Transfira a label para `status:completed` ou `status:hitl-approval`.
"""
            (target_skill_dir / 'SKILL.md').write_text(skill_md_content)

            # Symlink in hermes
            hermes_target = hermes_skills_base / skill_name
            if hermes_target.is_symlink() or hermes_target.exists():
                os.system(f"rm -rf {hermes_target}")
            os.symlink(str(target_skill_dir), str(hermes_target))

            registered.append(skill_name)

    print(f"[Sync Concluído] Skills de Squads registradas/atualizadas: {len(registered)}")
    for r in registered:
        print(f"  └─ /{r}")

if __name__ == '__main__':
    sync_squad_skills()
