from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import db, Formulario, Pergunta, Auditoria, Resposta, Loja, Cliente, BlocoFormulario
from flask_login import current_user, login_required
from datetime import datetime

cli_bp = Blueprint('cli', __name__, template_folder='templates')


@cli_bp.route('/')
@login_required
def index():
    formularios = Formulario.query.all()
    return render_template('cli/index.html', formularios=formularios)

@cli_bp.route('/formulario/novo', methods=['GET', 'POST'])
@login_required
def criar_formulario():
    clientes = Cliente.query.all()
    lojas = Loja.query.all()
    return render_template('cli/criar_formulario.html', clientes=clientes, lojas=lojas)

@cli_bp.route('/formulario/salvar', methods=['POST'])
@login_required
def salvar_formulario():
    nome = request.form.get('nome_formulario')
    cliente_id = request.form.get('cliente_id')
    loja_id = request.form.get('loja_id')

    if not nome:
        flash("Nome do formulário é obrigatório.", "danger")
        return redirect(url_for('cli.criar_formulario'))

    novo_formulario = Formulario(nome=nome, cliente_id=cliente_id, loja_id=loja_id)
    db.session.add(novo_formulario)
    db.session.flush()

    blocos = []
    for key in request.form:
        if key.startswith('blocos[') and key.endswith('][nome]'):
            bloco_idx = key.split('[')[1].split(']')[0]
            nome_bloco = request.form.get(f'blocos[{bloco_idx}][nome]')
            bloco = BlocoFormulario(nome=nome_bloco, ordem=int(bloco_idx), formulario_id=novo_formulario.id)
            db.session.add(bloco)
            blocos.append((bloco_idx, bloco))

    db.session.flush()

    for bloco_idx, bloco in blocos:
        pergunta_keys = [k for k in request.form if k.startswith(f'blocos[{bloco_idx}][perguntas]')]
        perguntas_processadas = set()

        for key in pergunta_keys:
            path = key.split('[')
            if len(path) < 5:
                continue
            pergunta_idx = path[3].strip(']')
            if pergunta_idx in perguntas_processadas:
                continue
            perguntas_processadas.add(pergunta_idx)

            texto = request.form.get(f'blocos[{bloco_idx}][perguntas][{pergunta_idx}][texto]')
            tipo = request.form.get(f'blocos[{bloco_idx}][perguntas][{pergunta_idx}][tipo]')
            obrigatoria = request.form.get(f'blocos[{bloco_idx}][perguntas][{pergunta_idx}][obrigatoria]') == 'on'

            nova_pergunta = Pergunta(
                texto=texto,
                tipo_resposta=tipo,
                obrigatoria=obrigatoria,
                formulario_id=novo_formulario.id,
                bloco_id=bloco.id
            )
            db.session.add(nova_pergunta)

    db.session.commit()
    flash("Formulário salvo com sucesso!", "success")
    return redirect(url_for('cli.visualizar_formulario', formulario_id=novo_formulario.id))

@cli_bp.route('/formulario/<int:formulario_id>')
@login_required
def visualizar_formulario(formulario_id):
    formulario = Formulario.query.get_or_404(formulario_id)
    return render_template('cli/formulario_visualizacao.html', formulario=formulario)

@cli_bp.route('/checklist/aplicar/<int:formulario_id>', methods=['GET', 'POST'])
@login_required
def aplicar_checklist(formulario_id):
    formulario = Formulario.query.get_or_404(formulario_id)
    perguntas = [p for bloco in formulario.blocos for p in bloco.perguntas]
    lojas = Loja.query.all()

    if request.method == 'POST':
        loja_id = request.form.get('loja_id')
        if not loja_id:
            flash('Selecione a loja.', 'danger')
            return render_template('cli/aplicar_checklist.html', formulario=formulario, lojas=lojas)

        nova_checklist = Auditoria(
            data=datetime.utcnow(),
            usuario_id=current_user.id,
            loja_id=loja_id,
            formulario_id=formulario.id
        )
        db.session.add(nova_checklist)
        db.session.flush()

        for pergunta in perguntas:
            valor = request.form.get(f'pergunta_{pergunta.id}', '').strip()
            if pergunta.obrigatoria and not valor:
                flash(f'A pergunta "{pergunta.texto}" é obrigatória.', 'warning')
                return render_template('cli/aplicar_checklist.html', formulario=formulario, lojas=lojas)

            resposta = Resposta(
                pergunta_id=pergunta.id,
                auditoria_id=nova_checklist.id,
                valor=valor
            )
            db.session.add(resposta)

        db.session.commit()
        flash('Checklist salvo com sucesso!', 'success')
        return redirect(url_for('cli.index'))

    return render_template('cli/aplicar_checklist.html', formulario=formulario, lojas=lojas)

@cli_bp.route('/checklists')
@login_required
def listar_checklists():
    checklists = Auditoria.query.order_by(Auditoria.data.desc()).all()
    return render_template('cli/listar_checklists.html', checklists=checklists)

@cli_bp.route('/checklist/<int:checklist_id>')
@login_required
def ver_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    return render_template('cli/ver_checklist.html', checklist=checklist)