#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix 'cli.adicionar_topico' BuildError by normalizing to 'cli.novo_topico'
and (optionally) creating an alias endpoint in routes if needed.
"""
import os, re, shutil, sys

def backup(p):
    if os.path.exists(p) and not os.path.exists(p + ".bak"):
        shutil.copy2(p, p + ".bak")

def read(p):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def write(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", errors="ignore") as f:
        f.write(data)

def replace_in_templates(app_dir):
    base = os.path.join(app_dir, "cli", "templates")
    if not os.path.exists(base):
        return 0
    count = 0
    for root, _, files in os.walk(base):
        for fn in files:
            if not fn.endswith((".html", ".htm", ".jinja2")):
                continue
            path = os.path.join(root, fn)
            txt = read(path)
            new = txt
            new = new.replace("url_for('cli.adicionar_topico'", "url_for('cli.novo_topico'")
            new = new.replace('url_for("cli.adicionar_topico"', 'url_for("cli.novo_topico"')
            if new != txt:
                backup(path)
                write(path, new)
                count += 1
    return count

def ensure_alias_in_routes(app_dir):
    routes = os.path.join(app_dir, "cli", "routes.py")
    if not os.path.exists(routes):
        print("! routes.py não encontrado:", routes)
        return False
    txt = read(routes)
    if "def novo_topico" not in txt:
        print("! Função novo_topico não encontrada. Pulei alias.")
        return False

    if "endpoint='adicionar_topico'" in txt or ("add_url_rule(" in txt and "adicionar_topico" in txt):
        print("✓ Alias 'adicionar_topico' já existe.")
        return True

    alias = """
# --- Alias de compatibilidade: adicionar_topico -> novo_topico ---
try:
    cli_bp.add_url_rule('/questionario/<int:questionario_id>/topicos/novo', endpoint='adicionar_topico', view_func=novo_topico, methods=['GET','POST'])
except Exception:
    pass
"""

    backup(routes)
    write(routes, txt + "\n" + alias)
    return True

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(base) == "app":
        app_dir = base
    else:
        app_dir = os.path.join(base, "app")
    touched = replace_in_templates(app_dir)
    print(f"→ Templates atualizados: {touched} arquivo(s).")

    aliased = ensure_alias_in_routes(app_dir)
    if aliased:
        print("→ Alias de rota 'adicionar_topico' criado (ou já existia).")
    print("Pronto. Reinicie o servidor e teste /cli/questionario/<id>/topicos.")

if __name__ == "__main__":
    main()
