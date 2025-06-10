from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import db, Cliente

from flask_login import login_required


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


# CRUD Loja
@admin_bp.route('/lojas')
@login_required
def listar_lojas():
    lojas = Loja.query.all()
    return render_template('admin/lojas.html', lojas=lojas)

@admin_bp.route('/lojas/nova', methods=['GET', 'POST'])
@login_required
def nova_loja():
    clientes = Cliente.query.all()
    if request.method == 'POST':
        loja = Loja(
            nome=request.form['nome'],
            endereco=request.form.get('endereco'),
            telefone=request.form.get('telefone'),
            cliente_id=request.form.get('cliente_id')
        )
        db.session.add(loja)
        db.session.commit()
        flash('Loja criada com sucesso!')
        return redirect(url_for('admin.listar_lojas'))
    return render_template('admin/loja_form.html', clientes=clientes)

@admin_bp.route('/lojas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_loja(id):
    loja = Loja.query.get_or_404(id)
    clientes = Cliente.query.all()
    if request.method == 'POST':
        loja.nome = request.form['nome']
        loja.endereco = request.form.get('endereco')
        loja.telefone = request.form.get('telefone')
        loja.cliente_id = request.form.get('cliente_id')
        db.session.commit()
        flash('Loja atualizada com sucesso!')
        return redirect(url_for('admin.listar_lojas'))
    return render_template('admin/loja_form.html', loja=loja, clientes=clientes)

@admin_bp.route('/lojas/<int:id>/excluir')
@login_required
def excluir_loja(id):
    loja = Loja.query.get_or_404(id)
    db.session.delete(loja)
    db.session.commit()
    flash('Loja excluída com sucesso!')
    return redirect(url_for('admin.listar_lojas'))
