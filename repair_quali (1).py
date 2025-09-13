#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch QualiGestor (CLI + base_cliq) to fix BuildError and template conflicts.

What it does:
1) app/cli/routes.py
   - Map /grupos endpoint to endpoint='listar_grupos' and rename function to listar_grupos
   - Render 'cli/listar_grupos.html' (not 'cli/grupos.html')
   - Change 'novo_avaliado' GET to render 'cli/cadastrar_avaliado.html'
   - Change nova_aplicacao GET to render 'cli/iniciar_aplicacao.html'
   - Remove the 'force_register_critical_routes' hack to avoid duplicates

2) app/templates/base_cliq.html
   - Fix <title> block ('title' block was wrapping scripts)
   - Update nav link 'nova_loja' -> 'novo_avaliado' and label

3) app/cli/templates/cli/dashboard.html and usuarios.html
   - Remove duplicated {% extends %} / duplicated 'block title' sections, keeping the first section only.

4) Create minimal template app/cli/templates/cli/editar_avaliado.html if missing.

Usage:
    python repair_quali.py /path/to/QualiGestor
If no path is given, it tries to patch in-place where this script is stored.

It creates .bak backups of any modified file.
"""

import sys, os, re, shutil, io, textwrap, pathlib

def backup(path):
    if os.path.exists(path) and not os.path.exists(path + ".bak"):
        shutil.copy2(path, path + ".bak")

def read(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', errors='ignore') as f:
        f.write(content)

def patch_routes_cli(routes_path):
    print(f"-> Patching routes: {routes_path}")
    backup(routes_path)
    txt = read(routes_path)

    # 1) Fix grupos endpoint and function name + template
    # Change decorator: @cli_bp.route('/grupos') -> @cli_bp.route('/grupos', endpoint='listar_grupos')
    txt = re.sub(
        r"@cli_bp\.route\('/grupos'\)\s*\n(\s*@login_required\s*\n)?(\s*@admin_required\s*\n)?\s*def\s+gerenciar_grupos\s*\(\):",
        r"@cli_bp.route('/grupos', endpoint='listar_grupos')\n@login_required\n@admin_required\ndef listar_grupos():",
        txt,
        flags=re.MULTILINE
    )
    # Ensure render_template for grupos points to listar_grupos.html
    txt = txt.replace("render_template_safe('cli/grupos.html'", "render_template_safe('cli/listar_grupos.html'" )

    # 2) Remove force_register_critical_routes (whole function and the call)
    txt = re.sub(
        r"\n\s*def\s+force_register_critical_routes\([\s\S]*?\)\s*#\s*Executar\s+IMEDIATAMENTE\s*\n\s*force_register_critical_routes\(\)\s*\n",
        "\n",
        txt,
        flags=re.MULTILINE
    )

    # 3) novo_avaliado template path (GET)
    txt = txt.replace("render_template_safe('cli/novo_avaliado.html'", "render_template_safe('cli/cadastrar_avaliado.html'" )

    # 4) nova_aplicacao GET template path
    txt = txt.replace("render_template_safe('cli/nova_aplicacao.html'", "render_template_safe('cli/iniciar_aplicacao.html'" )

    write(routes_path, txt)
    print("   ✓ routes.py patched.")

def patch_base_cliq(base_path):
    print(f"-> Patching base_cliq: {base_path}")
    backup(base_path)
    html = read(base_path)

    # Fix the <title> block to not contain scripts
    # Replace from <title>{% block title %}... scripts ...{% endblock %}</title>
    # to <title>{% block title %}CLIQ - QualiGestor{% endblock %}</title>
    html = re.sub(
        r"<title>\s*{\%\s*block\s+title\s*%}.*?{\%\s*endblock\s*%}\s*</title>",
        "<title>{% block title %}CLIQ - QualiGestor{% endblock %}</title>",
        html,
        flags=re.DOTALL
    )

    # Update the 'Novo avaliado' nav link to use correct endpoint
    html = html.replace("url_for('cli.nova_loja')", "url_for('cli.novo_avaliado')")

    write(base_path, html)
    print("   ✓ base_cliq.html patched.")

def strip_duplicate_blocks(path):
    print(f"-> Cleaning duplicate blocks: {path}")
    backup(path)
    txt = read(path)

    # Keep only the first {% extends ... %} block and remove subsequent ones and subsequent 'block title' definitions
    parts = re.split(r"({%\s*extends\s+['\"][^'\"]+['\"]\s*%})", txt)
    if len(parts) > 3:
        # Keep only first extends and everything after the first extends until a *next* extends; drop later ones
        first = parts[1] + parts[2]
        # Remove duplicate 'block title' definitions beyond the first occurrence
        # Find first block title
        first_title = re.search(r"{\%\s*block\s+title\s*%}", first)
        if first_title:
            # Remove any subsequent occurrences
            first = (first[:first_title.end()] +
                     re.sub(r"{\%\s*block\s+title\s*%}[\s\S]*?{\%\s*endblock\s*%}", "", first[first_title.end():], count=10))
            # Ensure there is at least one endblock after the first title
            if "{% endblock %}" not in first[first_title.end():]:
                first += "{% endblock %}"
        write(path, first)
        print("   ✓ Cleaned extra extends/title blocks.")
    else:
        # Still remove duplicate 'block title' occurrences if present
        matches = list(re.finditer(r"{\%\s*block\s+title\s*%}", txt))
        if len(matches) > 1:
            keep_until = matches[1].start()
            txt = txt[:keep_until] + re.sub(r"{\%\s*block\s+title\s*%}[\s\S]*?{\%\s*endblock\s*%}", "", txt[keep_until:], count=10)
            write(path, txt)
            print("   ✓ Removed duplicated 'block title'.")
        else:
            print("   ✓ No duplicates detected.")

def ensure_editar_avaliado_template(path):
    if not os.path.exists(path):
        print(f"-> Creating minimal template: {path}")
        content = """{% extends 'base_cliq.html' %}
{% block title %}Editar Avaliado{% endblock %}
{% block content %}
<div class=\"container py-4\">
  <h4>Editar Avaliado</h4>
  <form method=\"POST\">
    <div class=\"mb-3\">
      <label class=\"form-label\">Nome</label>
      <input type=\"text\" name=\"nome\" class=\"form-control\" value=\"{{ avaliado.nome }}\" required>
    </div>
    <div class=\"mb-3\">
      <label class=\"form-label\">Código</label>
      <input type=\"text\" name=\"codigo\" class=\"form-control\" value=\"{{ avaliado.codigo }}\">
    </div>
    <div class=\"mb-3\">
      <label class=\"form-label\">Grupo</label>
      <select name=\"grupo_id\" class=\"form-select\">
        <option value=\"\">-- Selecionar --</option>
        {% for g in grupos %}
        <option value=\"{{ g.id }}\" {% if avaliado.grupo_id==g.id %}selected{% endif %}>{{ g.nome }}</option>
        {% endfor %}
      </select>
    </div>
    <button class=\"btn btn-primary\" type=\"submit\">Salvar</button>
    <a class=\"btn btn-secondary\" href=\"{{ url_for('cli.listar_avaliados') }}\">Cancelar</a>
  </form>
</div>
{% endblock %}
"""
        write(path, content)
        print("   ✓ editar_avaliado.html created.")
    else:
        print("   ✓ editar_avaliado.html already exists.")

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    proj = base
    if os.path.basename(proj) == 'app':
        proj = os.path.dirname(proj)
    app_dir = os.path.join(proj, 'app')
    routes_cli = os.path.join(app_dir, 'cli', 'routes.py')
    base_cliq = os.path.join(app_dir, 'templates', 'base_cliq.html')
    tmpl_dir = os.path.join(app_dir, 'cli', 'templates', 'cli')
    dashboard_tmpl = os.path.join(tmpl_dir, 'dashboard.html')
    usuarios_tmpl = os.path.join(tmpl_dir, 'usuarios.html')
    editar_avaliado_tmpl = os.path.join(tmpl_dir, 'editar_avaliado.html')

    if not os.path.exists(routes_cli):
        print("! routes.py not found:", routes_cli)
        sys.exit(1)

    patch_routes_cli(routes_cli)
    patch_base_cliq(base_cliq)
    if os.path.exists(dashboard_tmpl):
        strip_duplicate_blocks(dashboard_tmpl)
    if os.path.exists(usuarios_tmpl):
        strip_duplicate_blocks(usuarios_tmpl)

    ensure_editar_avaliado_template(editar_avaliado_tmpl)
    print("\nDone. Restart your dev server and test /cli again.")

if __name__ == '__main__':
    main()
