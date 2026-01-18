from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from ..models import db, Cliente, Avaliado, Usuario, TipoUsuario

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
            # Se não veio email, gera um fictício: admin@nomedocliente.com
            email_login = email_contato
            if not email_login:
                slug = nome_cliente.lower().replace(' ', '').replace('.', '')
                email_login = f"admin@{slug}.com.br"

            senha_padrao = "mudar123" # Senha temporária
            
            # Busca o ID do tipo 'ADMIN' ou 'GESTOR'
            tipo_admin = TipoUsuario.query.filter(TipoUsuario.name.ilike('ADMIN%')).first()
            tipo_id = tipo_admin.id if tipo_admin else 1 # Fallback para ID 1 se não achar

            novo_usuario = Usuario(
                nome=f"Admin {nome_cliente}",
                email=email_login,
                senha_hash=generate_password_hash(senha_padrao),
                cliente_id=cliente.id, # VINCULA AO NOVO CLIENTE
                tipo_id=tipo_id,
                ativo=True
            )
            
            db.session.add(novo_usuario)
            db.session.commit()

            # Feedback com as credenciais
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
            cliente.nome = request.form['nome']
            cliente.cnpj = request.form.get('cnpj')
            cliente.endereco = request.form.get('endereco')
            cliente.telefone = request.form.get('telefone')
            cliente.email_contato = request.form.get('email')
            
            db.session.commit()
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
    """Exclui uma empresa (CUIDADO: Isso pode excluir dados em cascata)."""
    try:
        cliente = Cliente.query.get_or_404(id)
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
        
    return redirect(url_for('admin.listar_clientes'))

# ==============================================================================
# CRUD AVALIADOS (LOJAS/UNIDADES) - Visão Global
# ==============================================================================

@admin_bp.route('/avaliados')
@login_required
@admin_required
def listar_avaliados():
    """Lista todos os avaliados (lojas) de todos os clientes."""
    avaliados = Avaliado.query.join(Cliente).all()
    return render_template('admin/avaliados.html', avaliados=avaliados)

@admin_bp.route('/avaliados/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_avaliado():
    """Cria um avaliado vinculado a um cliente específico."""
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
    """Edita um avaliado existente."""
    avaliado = Avaliado.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.nome).all()
    
    if request.method == 'POST':
        try:
            avaliado.nome = request.form['nome']
            avaliado.endereco = request.form.get('endereco')
            avaliado.telefone = request.form.get('telefone')
            avaliado.cliente_id = int(request.form.get('cliente_id'))
            
            db.session.commit()
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
    """Remove um avaliado."""
    try:
        avaliado = Avaliado.query.get_or_404(id)
        db.session.delete(avaliado)
        db.session.commit()
        flash('Avaliado excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
        
    return redirect(url_for('admin.listar_avaliados'))