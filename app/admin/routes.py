from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..models import db, Cliente, Avaliado  # Importar Avaliado explicitamente

admin_bp = Blueprint('admin', __name__, template_folder='templates')

# CRUD Cliente
@admin_bp.route('/clientes')
@login_required
def listar_clientes():
    clientes = Cliente.query.all()
    return render_template('admin/clientes.html', clientes=clientes)

@admin_bp.route('/clientes/novo', methods=['GET', 'POST'])
@login_required
def novo_cliente():
    if request.method == 'POST':
        cliente = Cliente(
            nome=request.form['nome'],
            cnpj=request.form.get('cnpj'),
            endereco=request.form.get('endereco'),
            telefone=request.form.get('telefone'),
            email_contato=request.form.get('email')
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente criado com sucesso!')
        return redirect(url_for('admin.listar_clientes'))
    return render_template('admin/cliente_form.html')

@admin_bp.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.cnpj = request.form.get('cnpj')
        cliente.endereco = request.form.get('endereco')
        cliente.telefone = request.form.get('telefone')
        cliente.email_contato = request.form.get('email')
        db.session.commit()
        flash('Cliente atualizado com sucesso!')
        return redirect(url_for('admin.listar_clientes'))
    return render_template('admin/cliente_form.html', cliente=cliente)

@admin_bp.route('/clientes/<int:id>/excluir')
@login_required
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente excluído com sucesso!')
    return redirect(url_for('admin.listar_clientes'))

# CRUD Avaliado/Loja
@admin_bp.route('/avaliados')
@login_required
def listar_avaliados():
    avaliados = Avaliado.query.all()
    return render_template('admin/avaliados.html', avaliados=avaliados)

@admin_bp.route('/avaliados/novo', methods=['GET', 'POST'])
@login_required
def novo_avaliado():
    clientes = Cliente.query.all()
    if request.method == 'POST':
        avaliado = Avaliado(
            nome=request.form['nome'],
            endereco=request.form.get('endereco'),
            telefone=request.form.get('telefone'),
            cliente_id=request.form.get('cliente_id')
        )
        db.session.add(avaliado)
        db.session.commit()
        flash('Avaliado criado com sucesso!')
        return redirect(url_for('admin.listar_avaliados'))
    return render_template('admin/avaliado_form.html', clientes=clientes)

@admin_bp.route('/avaliados/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_avaliado(id):
    avaliado = Avaliado.query.get_or_404(id)
    clientes = Cliente.query.all()
    if request.method == 'POST':
        avaliado.nome = request.form['nome']
        avaliado.endereco = request.form.get('endereco')
        avaliado.telefone = request.form.get('telefone')
        avaliado.cliente_id = request.form.get('cliente_id')
        db.session.commit()
        flash('Avaliado atualizado com sucesso!')
        return redirect(url_for('admin.listar_avaliados'))
    return render_template('admin/avaliado_form.html', avaliado=avaliado, clientes=clientes)

@admin_bp.route('/avaliados/<int:id>/excluir')
@login_required
def excluir_avaliado(id):
    avaliado = Avaliado.query.get_or_404(id)
    db.session.delete(avaliado)
    db.session.commit()
    flash('Avaliado excluído com sucesso!')
    return redirect(url_for('admin.listar_avaliados'))