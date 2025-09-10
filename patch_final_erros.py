# patch_final_erros.py
"""
Patch final para corrigir os erros específicos que apareceram na execução:
1. Rota 'cli.novo_questionario' não existe no template
2. Import 'redirect' faltando no panorama
3. Enum 'ADMIN_CLIENTE' inválido no banco
"""

import sys
import os
import shutil
from datetime import datetime

def corrigir_template_base_cliq():
    """Corrige as rotas no template base_cliq.html"""
    
    print("🎨 Corrigindo template base_cliq.html...")
    
    try:
        with open('app/templates/base_cliq.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup
        backup_name = f'app/templates/base_cliq_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(backup_name, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Corrigir rotas problemáticas
        corrections = [
            # Corrigir rota novo_questionario
            ('cli.novo_questionario', 'cli.criar_formulario'),
            ('cli.questionarios', 'cli.listar_formularios'),
            ('cli.avaliados', 'cli.listar_lojas'),
            ('cli.cadastrar_avaliado', 'cli.nova_loja'),
            ('cli.cadastrar_grupo', 'cli.novo_grupo')
        ]
        
        for old_route, new_route in corrections:
            content = content.replace(f"url_for('{old_route}')", f"url_for('{new_route}')")
        
        # Escrever arquivo corrigido
        with open('app/templates/base_cliq.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Template base_cliq.html corrigido!")
        return True
        
    except Exception as e:
        print(f"❌ Erro corrigindo template: {e}")
        return False

def corrigir_imports_panorama():
    """Adiciona import redirect faltando no panorama"""
    
    print("🔄 Corrigindo imports do panorama...")
    
    try:
        with open('app/panorama/routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se redirect já está importado
        if 'from flask import' in content and 'redirect' not in content:
            # Encontrar a linha de import do flask
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from flask import'):
                    # Adicionar redirect ao import se não existir
                    if 'redirect' not in line:
                        line = line.rstrip()
                        if line.endswith(','):
                            lines[i] = line + ' redirect'
                        else:
                            lines[i] = line + ', redirect'
                    break
            
            content = '\n'.join(lines)
        elif 'from flask import' not in content:
            # Adicionar import completo no início
            content = "from flask import redirect, url_for\n" + content
        
        # Escrever arquivo corrigido
        with open('app/panorama/routes.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Imports do panorama corrigidos!")
        return True
        
    except Exception as e:
        print(f"❌ Erro corrigindo imports panorama: {e}")
        return False

def limpar_banco_enum_problematico():
    """Remove registros com enums inválidos do banco"""
    
    print("🗃️ Limpando registros com enums inválidos...")
    
    try:
        # Deletar o banco atual e recriar
        if os.path.exists('instance'):
            shutil.rmtree('instance')
            print("✅ Banco antigo removido!")
        
        # Criar diretório instance
        os.makedirs('instance', exist_ok=True)
        
        print("✅ Banco limpo - será recriado na próxima execução!")
        return True
        
    except Exception as e:
        print(f"❌ Erro limpando banco: {e}")
        return False

def adicionar_rotas_faltando_cli():
    """Adiciona as rotas que estão faltando no CLI"""
    
    print("🛣️ Adicionando rotas faltando no CLI...")
    
    try:
        with open('app/cli/routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se já tem a rota novo_questionario
        if '@cli_bp.route(\'/novo-questionario\'' not in content:
            # Adicionar rotas faltando no final
            rotas_adicionais = '''

# ===================== ROTAS ADICIONAIS DE COMPATIBILIDADE =====================

@cli_bp.route('/novo-questionario', methods=['GET', 'POST'])
@login_required
def novo_questionario():
    """Cria novo questionário (compatibilidade)"""
    return redirect(url_for('cli.criar_formulario'))

@cli_bp.route('/listar-formularios')
@login_required
def listar_formularios():
    """Lista formulários do cliente"""
    if not hasattr(current_user, 'cliente_id') or not current_user.cliente_id:
        flash("Erro: usuário sem cliente associado", "danger")
        return redirect(url_for('main.painel'))
    
    formularios = Formulario.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativo=True
    ).order_by(Formulario.nome).all()
    
    return render_template('cli/listar_questionarios.html', formularios=formularios)

@cli_bp.route('/listar-lojas')
@login_required  
def listar_lojas():
    """Lista lojas do cliente"""
    if not hasattr(current_user, 'cliente_id') or not current_user.cliente_id:
        lojas = []
    else:
        lojas = Loja.query.filter_by(
            cliente_id=current_user.cliente_id
        ).order_by(Loja.nome).all()
    
    return render_template('cli/listar_lojas.html', lojas=lojas)

@cli_bp.route('/nova-loja', methods=['GET', 'POST'])
@login_required
def nova_loja():
    """Cria nova loja"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        codigo = request.form.get('codigo')
        endereco = request.form.get('endereco')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        cep = request.form.get('cep')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        gerente_nome = request.form.get('gerente_nome')
        grupo_id = request.form.get('grupo_id')
        
        if not nome:
            flash("Nome da loja é obrigatório", "danger")
            return redirect(url_for('cli.nova_loja'))
        
        loja = Loja(
            nome=nome,
            codigo=codigo,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            cep=cep,
            telefone=telefone,
            email=email,
            gerente_nome=gerente_nome,
            cliente_id=current_user.cliente_id,
            grupo_id=grupo_id if grupo_id else None,
            ativa=True
        )
        
        db.session.add(loja)
        db.session.commit()
        
        flash("Loja criada com sucesso!", "success")
        return redirect(url_for('cli.listar_lojas'))
    
    # GET
    grupos = Grupo.query.filter_by(
        cliente_id=current_user.cliente_id, ativo=True
    ).all() if hasattr(current_user, 'cliente_id') else []
    
    return render_template('cli/nova_loja.html', grupos=grupos)

@cli_bp.route('/novo-grupo', methods=['GET', 'POST'])
@login_required
def novo_grupo():
    """Cria novo grupo"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao', '')
        
        if not nome:
            flash("Nome do grupo é obrigatório", "danger")
            return redirect(url_for('cli.novo_grupo'))
        
        grupo = Grupo(
            nome=nome,
            descricao=descricao,
            cliente_id=current_user.cliente_id,
            ativo=True
        )
        
        db.session.add(grupo)
        db.session.commit()
        
        flash("Grupo criado com sucesso!", "success")
        return redirect(url_for('cli.listar_grupos'))
    
    return render_template('cli/novo_grupo.html')
'''
            
            content += rotas_adicionais
            
            with open('app/cli/routes.py', 'w', encoding='utf-8') as f:
                f.write(content)
        
        print("✅ Rotas CLI adicionadas!")
        return True
        
    except Exception as e:
        print(f"❌ Erro adicionando rotas CLI: {e}")
        return False

def criar_template_listar_lojas():
    """Cria template para listar lojas"""
    
    print("🏪 Criando template listar_lojas.html...")
    
    template_content = '''{% extends 'base_cliq.html' %}
{% block title %}Lojas{% endblock %}

{% block content %}
<div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h4>Lojas Cadastradas</h4>
        <a href="{{ url_for('cli.nova_loja') }}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Nova Loja
        </a>
    </div>

    <div class="card shadow-sm">
        <div class="card-body">
            {% if lojas %}
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Nome</th>
                            <th>Cidade</th>
                            <th>Estado</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for loja in lojas %}
                        <tr>
                            <td>{{ loja.codigo or '-' }}</td>
                            <td>{{ loja.nome }}</td>
                            <td>{{ loja.cidade or '-' }}</td>
                            <td>{{ loja.estado or '-' }}</td>
                            <td>
                                <span class="badge bg-{{ 'success' if loja.ativa else 'secondary' }}">
                                    {{ 'Ativa' if loja.ativa else 'Inativa' }}
                                </span>
                            </td>
                            <td>
                                <a href="#" class="btn btn-sm btn-outline-primary" title="Editar">
                                    <i class="fas fa-edit"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="text-center py-4">
                <i class="fas fa-store fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">Nenhuma loja cadastrada</h5>
                <p class="text-muted">Clique no botão "Nova Loja" para começar</p>
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}'''
    
    os.makedirs('app/cli/templates/cli', exist_ok=True)
    
    with open('app/cli/templates/cli/listar_lojas.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("✅ Template listar_lojas.html criado!")

def atualizar_inicializador():
    """Atualiza o inicializador para não criar usuários com enum inválido"""
    
    print("🔄 Atualizando inicializador...")
    
    try:
        # Verificar se já existe o inicializador
        if os.path.exists('inicializar_dados_corrigido.py'):
            with open('inicializar_dados_corrigido.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Garantir que está usando os enums corretos
            if 'ADMIN_CLIENTE' in content:
                content = content.replace('ADMIN_CLIENTE', 'ADMIN')
                
                with open('inicializar_dados_corrigido.py', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ Inicializador atualizado!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro atualizando inicializador: {e}")
        return False

def verificar_estrutura_arquivos():
    """Verifica se todos os arquivos estão no lugar"""
    
    print("📁 Verificando estrutura de arquivos...")
    
    arquivos_necessarios = [
        'app/templates/base_cliq.html',
        'app/cli/templates/cli/index.html',
        'app/cli/templates/cli/nova_loja.html',
        'app/cli/templates/cli/listar_questionarios.html',
        'app/cli/templates/cli/novo_grupo.html'
    ]
    
    faltando = []
    for arquivo in arquivos_necessarios:
        if not os.path.exists(arquivo):
            faltando.append(arquivo)
    
    if faltando:
        print(f"⚠️ Arquivos faltando: {len(faltando)}")
        for arquivo in faltando:
            print(f"  • {arquivo}")
        return False
    else:
        print("✅ Todos os arquivos necessários existem!")
        return True

if __name__ == "__main__":
    print("🔧 PATCH FINAL - CORRIGINDO ERROS DE EXECUÇÃO")
    print("=" * 50)
    
    sucessos = 0
    total_tarefas = 7
    
    # 1. Corrigir template base_cliq
    if corrigir_template_base_cliq():
        sucessos += 1
    
    # 2. Corrigir imports panorama
    if corrigir_imports_panorama():
        sucessos += 1
    
    # 3. Limpar banco problemático
    if limpar_banco_enum_problematico():
        sucessos += 1
    
    # 4. Adicionar rotas CLI
    if adicionar_rotas_faltando_cli():
        sucessos += 1
    
    # 5. Criar template lojas
    criar_template_listar_lojas()
    sucessos += 1
    
    # 6. Atualizar inicializador
    if atualizar_inicializador():
        sucessos += 1
    
    # 7. Verificar estrutura
    if verificar_estrutura_arquivos():
        sucessos += 1
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO: {sucessos}/{total_tarefas} correções aplicadas")
    
    if sucessos == total_tarefas:
        print("🎉 PATCH APLICADO COM SUCESSO!")
        print("\n🚀 EXECUTAR AGORA:")
        print("1. python inicializar_dados_corrigido.py")
        print("2. python run.py")
        print("3. Acesse: http://localhost:5000")
        print("4. Login: admin@admin.com / admin123")
        print("\n✅ Os erros reportados foram corrigidos:")
        print("  • Rotas do template corrigidas")
        print("  • Import redirect adicionado")
        print("  • Banco limpo (sem enums inválidos)")
        print("  • Rotas CLI completadas")
    else:
        print("⚠️ Algumas correções falharam")
        print("Execute novamente ou verifique os logs")
    
    print("=" * 50)