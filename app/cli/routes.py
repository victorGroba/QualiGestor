from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import datetime
from ..models import db,Formulario, Pergunta, Auditoria, Loja, Cliente, OpcaoPergunta, Avaliado, CampoPersonalizado, CampoPersonalizadoValor

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

    perguntas_keys = [k for k in request.form if k.startswith('perguntas[') and k.endswith('][texto]')]
    perguntas_processadas = set()

    for key in perguntas_keys:
        pergunta_idx = key.split('[')[1].split(']')[0]
        if pergunta_idx in perguntas_processadas:
            continue
        perguntas_processadas.add(pergunta_idx)

        texto = request.form.get(f'perguntas[{pergunta_idx}][texto]')
        tipo = request.form.get(f'perguntas[{pergunta_idx}][tipo]')
        obrigatoria = request.form.get(f'perguntas[{pergunta_idx}][obrigatoria]') == 'on'

        nova_pergunta = Pergunta(
            texto=texto,
            tipo_resposta=tipo,
            obrigatoria=obrigatoria,
            formulario_id=novo_formulario.id
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
    perguntas = formulario.perguntas
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
                flash(f'A pergunta \"{pergunta.texto}\" é obrigatória.', 'warning')
                return render_template('cli/aplicar_checklist.html', formulario=formulario, lojas=lojas)

            # Aqui você pode salvar a resposta em uma nova tabela se desejar criar esse modelo
            # Exemplo:
            # resposta = Resposta(pergunta_id=pergunta.id, auditoria_id=nova_checklist.id, valor=valor)
            # db.session.add(resposta)

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




@cli_bp.route('/avaliado/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_avaliado():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        endereco = request.form.get('endereco')
        idioma = request.form.get('idioma')
        cliente_id = request.form.get('cliente_id')  # Vem do formulário agora

        if not nome:
            flash("Nome do avaliado é obrigatório", "danger")
            return redirect(url_for('cli.cadastrar_avaliado'))

        novo_avaliado = Avaliado(
            nome=nome,
            email=email,
            endereco=endereco,
            idioma=idioma,
            cliente_id=cliente_id
        )
        db.session.add(novo_avaliado)
        db.session.commit()
        flash("Avaliado cadastrado com sucesso!", "success")
        return redirect(url_for('cli.index'))

    # GET: carrega a tela com a lista de clientes
    clientes = Cliente.query.all()
    return render_template('cli/cadastrar_avaliado.html', clientes=clientes)


from flask import request

@cli_bp.route('/avaliados')
@login_required
def listar_avaliados():
    nome = request.args.get('nome')
    grupo_id = request.args.get('grupo_id')

    query = Avaliado.query

    if current_user.tipo != 'admin':
        query = query.filter_by(cliente_id=current_user.cliente_id)

    if nome:
        query = query.filter(Avaliado.nome.ilike(f'%{nome}%'))

    if grupo_id and grupo_id.isdigit():
        query = query.filter_by(grupo_id=int(grupo_id))

    avaliados = query.all()
    grupos = Grupo.query.all()

    return render_template('cli/listar_avaliados.html', avaliados=avaliados, grupos=grupos)


@cli_bp.route('/cliente/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_cliente():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash("Nome do cliente é obrigatório", "danger")
            return redirect(url_for('cli.cadastrar_cliente'))

        cliente = Cliente(nome=nome)
        db.session.add(cliente)
        db.session.commit()
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for('cli.index'))

    return render_template('cli/cadastrar_cliente.html')




@cli_bp.route('/avaliado/excluir/<int:avaliado_id>', methods=['POST'])
@login_required
def excluir_avaliado(avaliado_id):
    avaliado = Avaliado.query.get_or_404(avaliado_id)
    db.session.delete(avaliado)
    db.session.commit()
    flash('Avaliado excluído com sucesso.', 'success')
    return redirect(url_for('cli.listar_avaliados'))


@cli_bp.route('/avaliado/editar/<int:avaliado_id>', methods=['GET', 'POST'])
@login_required
def editar_avaliado(avaliado_id):
    avaliado = Avaliado.query.get_or_404(avaliado_id)
    grupos = Grupo.query.all()
    if current_user.tipo == 'admin':
        clientes = Cliente.query.all()
    else:
        clientes = [current_user.cliente]

    if request.method == 'POST':
        avaliado.nome = request.form.get('nome')
        avaliado.email = request.form.get('email')
        avaliado.endereco = request.form.get('endereco')
        avaliado.idioma = request.form.get('idioma')
        avaliado.grupo_id = request.form.get('grupo_id')

        if current_user.tipo == 'admin':
            avaliado.cliente_id = request.form.get('cliente_id')

        db.session.commit()
        flash("Avaliado atualizado com sucesso!", "success")
        return redirect(url_for('cli.listar_avaliados'))

    return render_template('cli/editar_avaliado.html', avaliado=avaliado, grupos=grupos, clientes=clientes)


