# app/admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from ..models import db, Cliente, Avaliado, Usuario, TipoUsuario, Grupo, LogAuditoria
from ..utils.audit import registrar_log  # <--- IMPORTANTE: Importando o gravador

# Tenta importar o decorator admin_required se ele existir no seu projeto
try:
    from ..utils.decorators import admin_required
except ImportError:
    # Cria um decorator "falso" que não faz nada caso não exista, para não quebrar
    def admin_required(f):
        return f

admin_bp = Blueprint('admin', __name__, template_folder='templates')

# ==============================================================================
# CRUD CLIENTES (EMPRESAS/TENANTS)
# ==============================================================================

@admin_bp.route('/clientes')
@login_required
@admin_required
def listar_clientes():
    """Lista todas as empresas cadastradas no sistema (SAAS)."""
    clientes = Cliente.query.all()
    return render_template('admin/clientes.html', clientes=clientes)

@admin_bp.route('/clientes/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_cliente():
    """
    Cadastra uma nova Empresa e cria automaticamente o seu primeiro Usuário Admin.
    """
    if request.method == 'POST':
        try:
            nome_cliente = request.form.get('nome')
            email_contato = request.form.get('email')

            # 1. Cria a Empresa (Cliente)
            cliente = Cliente(
                nome=nome_cliente,
                cnpj=request.form.get('cnpj'),
                endereco=request.form.get('endereco'),
                telefone=request.form.get('telefone'),
                email_contato=email_contato,
                ativo=True
            )
            
            db.session.add(cliente)
            db.session.flush() # Gera o ID do cliente sem commitar ainda

            # 2. Cria o Primeiro Usuário (Admin da Empresa)
            email_login = email_contato
            if not email_login:
                slug = nome_cliente.lower().replace(' ', '').replace('.', '')
                email_login = f"admin@{slug}.com.br"

            senha_padrao = "mudar123" # Senha temporária
            
            tipo_admin = TipoUsuario.query.filter(TipoUsuario.name.ilike('ADMIN%')).first()
            tipo_id = tipo_admin.id if tipo_admin else 1

            novo_usuario = Usuario(
                nome=f"Admin {nome_cliente}",
                email=email_login,
                senha_hash=generate_password_hash(senha_padrao),
                cliente_id=cliente.id,
                tipo_id=tipo_id,
                ativo=True
            )
            
            db.session.add(novo_usuario)
            db.session.commit()

            # --- AUDITORIA ---
            registrar_log(
                acao="Criar Cliente",
                detalhes=f"Cliente: {cliente.nome} | CNPJ: {cliente.cnpj} | Admin: {email_login}",
                entidade_tipo="Cliente",
                entidade_id=cliente.id
            )
            # -----------------

            flash(f'Cliente "{cliente.nome}" criado com sucesso!', 'success')
            flash(f'⚠️ ANOTE AS CREDENCIAIS: Login: {email_login} | Senha: {senha_padrao}', 'warning')
            
            return redirect(url_for('admin.listar_clientes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar cliente: {str(e)}', 'danger')

    return render_template('admin/cliente_form.html')

@admin_bp.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_cliente(id):
    """Edita dados cadastrais da empresa."""
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Guarda dados antigos para log (opcional, mas útil)
            dados_antigos = f"{cliente.nome} ({cliente.email_contato})"

            cliente.nome = request.form['nome']
            cliente.cnpj = request.form.get('cnpj')
            cliente.endereco = request.form.get('endereco')
            cliente.telefone = request.form.get('telefone')
            cliente.email_contato = request.form.get('email')
            
            db.session.commit()

            # --- AUDITORIA ---
            registrar_log(
                acao="Editar Cliente",
                detalhes=f"De: {dados_antigos} -> Para: {cliente.nome} ({cliente.email_contato})",
                entidade_tipo="Cliente",
                entidade_id=cliente.id
            )
            # -----------------

            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('admin.listar_clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'danger')
            
    return render_template('admin/cliente_form.html', cliente=cliente)

@admin_bp.route('/clientes/<int:id>/excluir')
@login_required
@admin_required
def excluir_cliente(id):
    """Exclui uma empresa."""
    try:
        cliente = Cliente.query.get_or_404(id)
        
        # --- AUDITORIA (ANTES DE DELETAR) ---
        registrar_log(
            acao="Excluir Cliente",
            detalhes=f"Cliente excluído: {cliente.nome} | CNPJ: {cliente.cnpj}",
            entidade_tipo="Cliente",
            entidade_id=id
        )
        # ------------------------------------

        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
        
    return redirect(url_for('admin.listar_clientes'))

# ==============================================================================
# CRUD AVALIADOS (LOJAS/UNIDADES)
# ==============================================================================

@admin_bp.route('/avaliados')
@login_required
@admin_required
def listar_avaliados():
    avaliados = Avaliado.query.join(Cliente).all()
    return render_template('admin/avaliados.html', avaliados=avaliados)

@admin_bp.route('/avaliados/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_avaliado():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    
    if request.method == 'POST':
        try:
            avaliado = Avaliado(
                nome=request.form['nome'],
                endereco=request.form.get('endereco'),
                telefone=request.form.get('telefone'),
                cliente_id=int(request.form.get('cliente_id')),
                ativo=True
            )
            db.session.add(avaliado)
            db.session.commit()

            # --- AUDITORIA ---
            registrar_log(
                acao="Criar Avaliado",
                detalhes=f"Loja: {avaliado.nome} | Cliente ID: {avaliado.cliente_id}",
                entidade_tipo="Avaliado",
                entidade_id=avaliado.id
            )
            # -----------------

            flash('Avaliado criado com sucesso!', 'success')
            return redirect(url_for('admin.listar_avaliados'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar avaliado: {str(e)}', 'danger')
            
    return render_template('admin/avaliado_form.html', clientes=clientes)

@admin_bp.route('/avaliados/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_avaliado(id):
    avaliado = Avaliado.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.nome).all()
    
    if request.method == 'POST':
        try:
            avaliado.nome = request.form['nome']
            avaliado.endereco = request.form.get('endereco')
            avaliado.telefone = request.form.get('telefone')
            avaliado.cliente_id = int(request.form.get('cliente_id'))
            
            db.session.commit()

            # --- AUDITORIA ---
            registrar_log(
                acao="Editar Avaliado",
                detalhes=f"Atualizou dados da loja: {avaliado.nome}",
                entidade_tipo="Avaliado",
                entidade_id=avaliado.id
            )
            # -----------------

            flash('Avaliado atualizado com sucesso!', 'success')
            return redirect(url_for('admin.listar_avaliados'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'danger')
            
    return render_template('admin/avaliado_form.html', avaliado=avaliado, clientes=clientes)

@admin_bp.route('/avaliados/<int:id>/excluir')
@login_required
@admin_required
def excluir_avaliado(id):
    try:
        avaliado = Avaliado.query.get_or_404(id)
        
        # --- AUDITORIA ---
        registrar_log(
            acao="Excluir Avaliado",
            detalhes=f"Loja excluída: {avaliado.nome} (ID Cliente: {avaliado.cliente_id})",
            entidade_tipo="Avaliado",
            entidade_id=id
        )
        # -----------------

        db.session.delete(avaliado)
        db.session.commit()
        flash('Avaliado excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
        
    return redirect(url_for('admin.listar_avaliados'))

# ==============================================================================
# CRUD GRUPOS
# ==============================================================================

@admin_bp.route('/grupos')
@login_required
@admin_required
def listar_grupos():
    grupos = Grupo.query.join(Cliente).order_by(Cliente.nome, Grupo.nome).all()
    return render_template('admin/grupos.html', grupos=grupos)

@admin_bp.route('/grupos/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_grupo():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    
    if request.method == 'POST':
        try:
            grupo = Grupo(
                nome=request.form['nome'],
                cliente_id=int(request.form.get('cliente_id')),
                ativo=True
            )
            db.session.add(grupo)
            db.session.commit()

            # --- AUDITORIA ---
            registrar_log(
                acao="Criar Grupo",
                detalhes=f"Grupo: {grupo.nome} | Cliente ID: {grupo.cliente_id}",
                entidade_tipo="Grupo",
                entidade_id=grupo.id
            )
            # -----------------

            flash('Grupo criado com sucesso!', 'success')
            return redirect(url_for('admin.listar_grupos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar grupo: {str(e)}', 'danger')
            
    return render_template('admin/grupo_form.html', clientes=clientes)

@admin_bp.route('/grupos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_grupo(id):
    grupo = Grupo.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.nome).all()
    
    if request.method == 'POST':
        try:
            grupo.nome = request.form['nome']
            grupo.cliente_id = int(request.form.get('cliente_id'))
            
            db.session.commit()

            # --- AUDITORIA ---
            registrar_log(
                acao="Editar Grupo",
                detalhes=f"Renomeado para: {grupo.nome}",
                entidade_tipo="Grupo",
                entidade_id=grupo.id
            )
            # -----------------

            flash('Grupo atualizado com sucesso!', 'success')
            return redirect(url_for('admin.listar_grupos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'danger')
            
    return render_template('admin/grupo_form.html', grupo=grupo, clientes=clientes)

@admin_bp.route('/grupos/<int:id>/excluir')
@login_required
@admin_required
def excluir_grupo(id):
    try:
        grupo = Grupo.query.get_or_404(id)
        
        # --- AUDITORIA ---
        registrar_log(
            acao="Excluir Grupo",
            detalhes=f"Grupo excluído: {grupo.nome}",
            entidade_tipo="Grupo",
            entidade_id=id
        )
        # -----------------

        db.session.delete(grupo)
        db.session.commit()
        flash('Grupo excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
        
    return redirect(url_for('admin.listar_grupos'))

# ==============================================================================
# AUDITORIA DO SISTEMA (NOVA ROTA)
# ==============================================================================

@admin_bp.route('/auditoria')
@login_required
@admin_required
def auditoria():
    """
    Exibe o log de todas as ações críticas do sistema.
    """
    # Busca os últimos 500 registros, ordenados do mais novo para o mais antigo
    logs = LogAuditoria.query.order_by(LogAuditoria.data_acao.desc()).limit(500).all()
    return render_template('admin/auditoria.html', logs=logs)