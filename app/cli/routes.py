import json
import os
import base64
import qrcode
from io import BytesIO
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import current_user, login_required
from weasyprint import HTML
from ..models import db, Formulario, Pergunta, Auditoria, Cliente, OpcaoPergunta, Avaliado, CampoPersonalizado, CampoPersonalizadoValor, Grupo, Resposta, Questionario, Grupo, Usuario

cli_bp = Blueprint('cli', __name__, template_folder='templates')

# ----------------------------- Home CLIQ -----------------------------
@cli_bp.route('/')
@login_required
def index():
    return redirect(url_for('cli.iniciar_aplicacao'))

# ----------------------------- Formulários -----------------------------
@cli_bp.route('/formulario/novo', methods=['GET', 'POST'])
@login_required
def criar_formulario():
    clientes = Cliente.query.all()
    avaliados = Avaliado.query.all()
    return render_template('cli/criar_formulario.html', clientes=clientes, avaliados=avaliados)

@cli_bp.route('/formulario/salvar', methods=['POST'])
@login_required
def salvar_formulario():
    nome = request.form.get('nome_formulario')
    cliente_id = request.form.get('cliente_id')
    avaliado_id = request.form.get('avaliado_id')

    if not nome:
        flash("Nome do formulário é obrigatório.", "danger")
        return redirect(url_for('cli.criar_formulario'))

    novo_formulario = Formulario(nome=nome, cliente_id=cliente_id, loja_id=avaliado_id)
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

# ----------------------------- Checklist -----------------------------
@cli_bp.route('/checklists')
@login_required
def listar_checklists():
    checklists = Auditoria.query.order_by(Auditoria.data.desc()).all()
    return render_template('cli/listar_checklists.html', checklists=checklists)

@cli_bp.route('/checklist/<int:checklist_id>/pdf')
@login_required
def gerar_pdf_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    from app.utils.pontuacao import calcular_pontuacao_auditoria
    resultado = calcular_pontuacao_auditoria(checklist) or {}
    checklist.percentual = resultado.get('percentual')

    qr_texto = f"Checklist ID: {checklist.id} - Cliente: {checklist.formulario.cliente.nome} - Data: {checklist.data.strftime('%d/%m/%Y')}"
    qr = qrcode.make(qr_texto)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    data_hoje = datetime.now().strftime('%d/%m/%Y %H:%M')

    html = render_template("cli/ver_checklist_pdf.html", checklist=checklist, qr_base64=qr_base64, data_hoje=data_hoje)
    pdf = HTML(string=html).write_pdf()

    pdf_dir = os.path.join(os.getcwd(), 'instance', 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f'checklist_{checklist.id}.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf)

    return send_file(pdf_path, mimetype='application/pdf')

@cli_bp.route('/checklist/<int:checklist_id>')
@login_required
def ver_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    return render_template('cli/ver_checklist.html', checklist=checklist)

@cli_bp.route('/checklist/<int:checklist_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    formulario = checklist.formulario
    perguntas = formulario.perguntas
    avaliados = Avaliado.query.all()

    if request.method == 'POST':
        checklist.loja_id = request.form.get('avaliado_id')
        checklist.data = datetime.utcnow()

        for resposta in checklist.respostas:
            db.session.delete(resposta)
        db.session.flush()

        for pergunta in perguntas:
            valor = request.form.get(f'pergunta_{pergunta.id}', '').strip()
            resposta = Resposta(
                pergunta_id=pergunta.id,
                auditoria_id=checklist.id,
                valor_opcoes_selecionadas=json.dumps([valor]) if valor else None
            )
            db.session.add(resposta)

        db.session.commit()
        from app.utils.pontuacao import calcular_pontuacao_auditoria
        resultado = calcular_pontuacao_auditoria(checklist)
        if resultado:
            flash(f"Checklist reavaliado com {resultado['percentual']}%", "success")
        else:
            flash("Checklist atualizado!", "success")

        return redirect(url_for('cli.listar_checklists'))

    return render_template('cli/editar_checklist.html', checklist=checklist, formulario=formulario, avaliados=avaliados)

@cli_bp.route('/checklist/<int:checklist_id>/excluir', methods=['POST'])
@login_required
def excluir_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    db.session.delete(checklist)
    db.session.commit()
    flash("Checklist excluído com sucesso!", "success")
    return redirect(url_for('cli.listar_checklists'))

# ----------------------------- Aplicar Checklist -----------------------------




@cli_bp.route('/checklist/iniciar/<int:formulario_id>')
@login_required
def selecionar_avaliado(formulario_id):
    formulario = Formulario.query.get_or_404(formulario_id)
    avaliados = Avaliado.query.order_by(Avaliado.nome.asc()).all()
    return render_template('cli/selecionar_avaliado.html', formulario=formulario, avaliados=avaliados)

@cli_bp.route('/checklist/aplicar/<int:formulario_id>/<int:avaliado_id>', methods=['GET', 'POST'])
@login_required
def aplicar_checklist_fluxo(formulario_id, avaliado_id):
    formulario = Formulario.query.get_or_404(formulario_id)
    avaliado = Avaliado.query.get_or_404(avaliado_id)
    perguntas = formulario.perguntas

    if request.method == 'POST':
        nova_checklist = Auditoria(
            data=datetime.utcnow(),
            usuario_id=current_user.id,
            loja_id=avaliado.id,
            formulario_id=formulario.id
        )
        db.session.add(nova_checklist)
        db.session.flush()

        for pergunta in perguntas:
            valor = request.form.get(f'pergunta_{pergunta.id}', '').strip()
            if pergunta.obrigatoria and not valor:
                flash(f'A pergunta "{pergunta.texto}" é obrigatória.', 'warning')
                return render_template('cli/aplicar_checklist.html', formulario=formulario, avaliado=avaliado)

            resposta = Resposta(
                pergunta_id=pergunta.id,
                auditoria_id=nova_checklist.id,
                valor_opcoes_selecionadas=json.dumps([valor]) if valor else None
            )
            db.session.add(resposta)

        db.session.commit()
        flash("Checklist aplicado com sucesso!", "success")
        return redirect(url_for('cli.listar_checklists'))

    return render_template('cli/aplicar_checklist.html', formulario=formulario, avaliado=avaliado)

# ----------------------------- Avaliados -----------------------------
@cli_bp.route('/avaliado/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_avaliado():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        endereco = request.form.get('endereco')
        idioma = request.form.get('idioma')
        cliente_id = request.form.get('cliente_id')

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

    clientes = Cliente.query.all()
    return render_template('cli/cadastrar_avaliado.html', clientes=clientes)

@cli_bp.route('/avaliados')
@login_required
def listar_avaliados():
    nome = request.args.get('nome')
    grupo_id = request.args.get('grupo_id')
    query = Avaliado.query

    if current_user.perfil != 'admin':
        query = query.filter_by(cliente_id=current_user.cliente_id)

    if nome:
        query = query.filter(Avaliado.nome.ilike(f'%{nome}%'))
    if grupo_id and grupo_id.isdigit():
        query = query.filter_by(grupo_id=int(grupo_id))

    avaliados = query.all()
    grupos = Grupo.query.all()
    return render_template('cli/listar_avaliados.html', avaliados=avaliados, grupos=grupos)

@cli_bp.route('/avaliado/editar/<int:avaliado_id>', methods=['GET', 'POST'])
@login_required
def editar_avaliado(avaliado_id):
    avaliado = Avaliado.query.get_or_404(avaliado_id)
    grupos = Grupo.query.all()
    clientes = Cliente.query.all() if current_user.perfil == 'admin' else [current_user.cliente]

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

@cli_bp.route('/avaliado/excluir/<int:avaliado_id>', methods=['POST'])
@login_required
def excluir_avaliado(avaliado_id):
    avaliado = Avaliado.query.get_or_404(avaliado_id)
    db.session.delete(avaliado)
    db.session.commit()
    flash('Avaliado excluído com sucesso.', 'success')
    return redirect(url_for('cli.listar_avaliados'))

# ----------------------------- Cliente -----------------------------
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

@cli_bp.route('/questionarios')
@login_required
def listar_questionarios():
    filtro = request.args.get('filtro', '')
    mostrar_inativos = request.args.get('inativos') == 'on'

    query = Questionario.query
    if filtro:
        query = query.filter(Questionario.nome.ilike(f'%{filtro}%'))
    if not mostrar_inativos:
        query = query.filter_by(ativo=True)

    questionarios = query.order_by(Questionario.data_atualizacao.desc()).all()
    return render_template('cli/listar_questionarios.html', questionarios=questionarios)

@cli_bp.route('/questionarios/novo', methods=['GET', 'POST'])
@login_required
def novo_questionario():
    if request.method == 'POST':
        nome = request.form.get('nome')
        versao = request.form.get('versao')
        modo = request.form.get('modo')
        idioma = request.form.get('idioma_email')
        cor_relatorio = request.form.get('cor_relatorio')
        cor_observacoes = request.form.get('cor_observacoes')

        # Arquivos
        doc_referencia = request.files.get('documento_referencia')
        logo_cabecalho = request.files.get('logotipo_cabecalho')
        logo_rodape = request.files.get('logotipo_rodape')

        uploads_dir = os.path.join('instance', 'arquivos_questionarios')
        os.makedirs(uploads_dir, exist_ok=True)

        nome_doc = None
        if doc_referencia and doc_referencia.filename:
            nome_doc = f"{datetime.utcnow().timestamp()}_{secure_filename(doc_referencia.filename)}"
            doc_referencia.save(os.path.join(uploads_dir, nome_doc))

        nome_logo_cab = None
        if logo_cabecalho and logo_cabecalho.filename:
            nome_logo_cab = f"{datetime.utcnow().timestamp()}_{secure_filename(logo_cabecalho.filename)}"
            logo_cabecalho.save(os.path.join(uploads_dir, nome_logo_cab))

        nome_logo_rod = None
        if logo_rodape and logo_rodape.filename:
            nome_logo_rod = f"{datetime.utcnow().timestamp()}_{secure_filename(logo_rodape.filename)}"
            logo_rodape.save(os.path.join(uploads_dir, nome_logo_rod))

        # Configuração Nota
        config_nota = ConfiguracaoNota(
            calcular_nota=bool(request.form.get('calcular_nota')),
            ocultar_nota=bool(request.form.get('ocultar_nota')),
            casas_decimais=int(request.form.get('casas_decimais') or 0)
        )
        db.session.add(config_nota)

        # Configuração Relatório
        config_relatorio = ConfiguracaoRelatorio(
            cor_relatorio=cor_relatorio,
            cor_observacoes=cor_observacoes,
            logotipo_cabecalho=nome_logo_cab,
            logotipo_rodape=nome_logo_rod
        )
        db.session.add(config_relatorio)

        # Configuração Email
        config_email = ConfiguracaoEmail(
            idioma=idioma,
            enviar_email=bool(request.form.get('enviar_email'))
        )
        db.session.add(config_email)
        db.session.flush()

        # Criar questionário
        questionario = Questionario(
            nome=nome,
            versao=versao,
            modo=modo,
            documento_referencia=nome_doc,
            configuracao_nota_id=config_nota.id,
            configuracao_relatorio_id=config_relatorio.id,
            configuracao_email_id=config_email.id,
            restringir_avaliados=bool(request.form.get('restringir_avaliados')),
            reincidencia_ativa=bool(request.form.get('reincidencia_ativa'))
        )
        db.session.add(questionario)
        db.session.flush()

        # Grupos
        for grupo_id in request.form.get('grupos[]', '').split(','):
            if grupo_id.strip():
                db.session.add(GrupoQuestionario(
                    grupo_id=int(grupo_id.strip()),
                    questionario_id=questionario.id
                ))

        # Avaliados
        for avaliado_id in request.form.get('avaliados[]', '').split(','):
            if avaliado_id.strip():
                db.session.add(AvaliacaoQuestionario(
                    avaliado_id=int(avaliado_id.strip()),
                    questionario_id=questionario.id
                ))

        # Usuários Autorizados
        nomes = request.form.get('usuarios_nomes[]', '').split(',')
        emails = request.form.get('usuarios_emails[]', '').split(',')
        for nome_user, email_user in zip(nomes, emails):
            if nome_user.strip() and email_user.strip():
                db.session.add(UsuarioAutorizado(
                    nome=nome_user.strip(),
                    email=email_user.strip(),
                    questionario_id=questionario.id
                ))

        # Produtos
        for produto in request.form.get('produtos[]', '').split(','):
            if produto.strip():
                db.session.add(ProdutoVinculado(
                    nome=produto.strip(),
                    questionario_id=questionario.id
                ))

        # Integrações
        for integracao in request.form.get('integracoes[]', '').split(','):
            if integracao.strip():
                db.session.add(IntegracaoVinculada(
                    nome=integracao.strip(),
                    questionario_id=questionario.id
                ))

        db.session.commit()
        flash("Questionário criado com sucesso!", "success")
        return redirect(url_for('cli.gerenciar_topicos', id=questionario.id))

    # GET
    grupos = Grupo.query.all()
    avaliados = Avaliado.query.all()
    usuarios = Usuario.query.all()
    return render_template('cli/novo_questionario.html', grupos=grupos, avaliados=avaliados, usuarios=usuarios)

    # GET: renderiza o formulário com os dados necessários
    grupos = Grupo.query.all()
    avaliados = Avaliado.query.all()
    usuarios = Usuario.query.all()
    return render_template('cli/novo_questionario.html', grupos=grupos, avaliados=avaliados, usuarios=usuarios)





@cli_bp.route('/formulario/novo_questionario', methods=['GET', 'POST'])
@login_required
def simular_envio_questionario():
    if request.method == 'POST':
        # Dados principais
        nome = request.form.get('nome')
        versao = request.form.get('versao')
        modo = request.form.get('modo')
        documento = request.files.get('documento')

        # Salvar documento de referência
        doc_path = None
        if documento and documento.filename:
            uploads_dir = os.path.join('instance', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            doc_filename = f"{datetime.utcnow().timestamp()}_{documento.filename}"
            documento.save(os.path.join(uploads_dir, doc_filename))
            doc_path = doc_filename

        # Configuração de Nota
        nota = ConfiguracaoNota(
            calcular_nota=bool(request.form.get('calcular_nota')),
            ocultar_nota=bool(request.form.get('ocultar_nota')),
            base_calculo=int(request.form.get('base_calculo') or 0),
            casas_decimais=int(request.form.get('casas_decimais') or 2),
            modo_configuracao=request.form.get('modo_configuracao') or "padrão"
        )
        db.session.add(nota)
        db.session.flush()

        # Configuração de Relatório
        logotipo_cab = request.files.get('logotipo_cabecalho')
        logotipo_rod = request.files.get('logotipo_rodape')

        logotipo_cab_path = None
        if logotipo_cab and logotipo_cab.filename:
            cab_filename = f"{datetime.utcnow().timestamp()}_cab_{logotipo_cab.filename}"
            logotipo_cab.save(os.path.join(uploads_dir, cab_filename))
            logotipo_cab_path = cab_filename

        logotipo_rod_path = None
        if logotipo_rod and logotipo_rod.filename:
            rod_filename = f"{datetime.utcnow().timestamp()}_rod_{logotipo_rod.filename}"
            logotipo_rod.save(os.path.join(uploads_dir, rod_filename))
            logotipo_rod_path = rod_filename

        relatorio = ConfiguracaoRelatorio(
            exibir_nota_anterior=bool(request.form.get('exibir_nota_anterior')),
            exibir_tabela_resumo=bool(request.form.get('exibir_tabela_resumo')),
            exibir_limites_aceitaveis=bool(request.form.get('exibir_limites_aceitaveis')),
            omitir_data_hora=bool(request.form.get('omitir_data_hora')),
            exibir_omitidas=bool(request.form.get('exibir_omitidas')),
            gerar_relatorio_nc=bool(request.form.get('gerar_relatorio_nc')),
            modo_exibicao_nota=request.form.get('modo_exibicao_nota'),
            tipo_agrupamento=request.form.get('tipo_agrupamento'),
            cor_observacoes=request.form.get('cor_observacoes'),
            cor_relatorio=request.form.get('cor_relatorio'),
            logotipo_cabecalho=logotipo_cab_path,
            logotipo_rodape=logotipo_rod_path
        )
        db.session.add(relatorio)
        db.session.flush()

        # Configuração de Email
        email = ConfiguracaoEmail(
            enviar_email=bool(request.form.get('enviar_email')),
            configurar_no_final=bool(request.form.get('configurar_no_final')),
            exibir_emails_anteriores=bool(request.form.get('exibir_emails_anteriores')),
            idioma=request.form.get('idioma')
        )
        db.session.add(email)
        db.session.flush()

        # Questionário principal
        questionario = Questionario(
            nome=nome,
            versao=versao,
            modo=modo,
            documento_referencia=doc_path,
            criado_em=datetime.utcnow(),
            configuracao_nota_id=nota.id,
            configuracao_relatorio_id=relatorio.id,
            configuracao_email_id=email.id,
            ativo=True
        )
        db.session.add(questionario)
        db.session.flush()

        # Grupos vinculados (se houver)
        grupos_ids = request.form.getlist('grupos[]')
        for grupo_id in grupos_ids:
            if grupo_id.strip().isdigit():
                gp = GrupoQuestionario(
                    questionario_id=questionario.id,
                    grupo_id=int(grupo_id)
                )
                db.session.add(gp)

        # Usuários autorizados (se houver)
        nomes_usuarios = request.form.getlist('usuarios_nomes[]')
        emails_usuarios = request.form.getlist('usuarios_emails[]')
        for nome, email in zip(nomes_usuarios, emails_usuarios):
            if nome.strip() or email.strip():
                ua = UsuarioAutorizado(
                    questionario_id=questionario.id,
                    nome=nome,
                    email=email
                )
                db.session.add(ua)

        db.session.commit()
        flash("Questionário criado com sucesso!", "success")
        return redirect(url_for('cli.listar_questionarios'))

    grupos = Grupo.query.all()
    avaliados = Avaliado.query.all()
    return render_template('cli/novo_questionario.html', grupos=grupos, avaliados=avaliados)


@cli_bp.route('/formulario/salvar', methods=['POST'])
@login_required
def salvar_questionario():
    try:
        nome = request.form.get('nome')
        versao = request.form.get('versao')
        modo = request.form.get('modo')
        criado_em = datetime.utcnow()

        # Documento de referência
        doc_file = request.files.get('documento_referencia')
        doc_filename = None
        if doc_file and doc_file.filename:
            doc_filename = secure_filename(doc_file.filename)
            doc_file.save(os.path.join(UPLOAD_FOLDER, doc_filename))

        # Configuração de nota
        calcular_nota = bool(request.form.get('calcular_nota'))
        ocultar_nota = bool(request.form.get('ocultar_nota'))
        casas_decimais = request.form.get('casas_decimais') or 0

        config_nota = ConfiguracaoNota(
            calcular_nota=calcular_nota,
            ocultar_nota=ocultar_nota,
            casas_decimais=int(casas_decimais)
        )
        db.session.add(config_nota)
        db.session.flush()  # garante que o ID será gerado

        # Configuração de relatório
        cor_relatorio = request.form.get('cor_relatorio')
        cor_observacoes = request.form.get('cor_observacoes')

        logotipo_cabecalho = request.files.get('logotipo_cabecalho')
        logotipo_rodape = request.files.get('logotipo_rodape')

        logotipo_cabecalho_path = None
        logotipo_rodape_path = None

        if logotipo_cabecalho and logotipo_cabecalho.filename:
            logotipo_cabecalho_path = secure_filename(logotipo_cabecalho.filename)
            logotipo_cabecalho.save(os.path.join(UPLOAD_FOLDER, logotipo_cabecalho_path))

        if logotipo_rodape and logotipo_rodape.filename:
            logotipo_rodape_path = secure_filename(logotipo_rodape.filename)
            logotipo_rodape.save(os.path.join(UPLOAD_FOLDER, logotipo_rodape_path))

        config_relatorio = ConfiguracaoRelatorio(
            cor_relatorio=cor_relatorio,
            cor_observacoes=cor_observacoes,
            logotipo_cabecalho=logotipo_cabecalho_path,
            logotipo_rodape=logotipo_rodape_path
        )
        db.session.add(config_relatorio)
        db.session.flush()

        # Configuração de email
        config_email = ConfiguracaoEmail()
        db.session.add(config_email)
        db.session.flush()

        # Questionário principal
        questionario = Questionario(
            nome=nome,
            versao=versao,
            modo=modo,
            documento_referencia=doc_filename,
            criado_em=criado_em,
            configuracao_nota_id=config_nota.id,
            configuracao_relatorio_id=config_relatorio.id,
            configuracao_email_id=config_email.id
        )
        db.session.add(questionario)
        db.session.flush()

        # Grupos
        grupos = request.form.getlist('grupos[]')
        for grupo in grupos:
            if grupo.strip():
                gq = GrupoQuestionario(
                    questionario_id=questionario.id,
                    grupo_id=None  # Adapte caso tenha tabela de Grupo real
                )
                db.session.add(gq)

        # Usuários autorizados
        usuarios_nomes = request.form.getlist('usuarios_nomes[]')
        usuarios_emails = request.form.getlist('usuarios_emails[]')

        for nome, email in zip(usuarios_nomes, usuarios_emails):
            if nome.strip() or email.strip():
                ua = UsuarioAutorizado(
                    questionario_id=questionario.id,
                    nome=nome,
                    email=email
                )
                db.session.add(ua)

        db.session.commit()
        flash('Questionário criado com sucesso!', 'success')
        return redirect(url_for('cli.listar_questionarios'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar questionário: {str(e)}', 'danger')
        return redirect(url_for('cli.novo_questionario'))

@cli_bp.route('/formulario')
@login_required
def listar_formularios():
    questionarios = Questionario.query.order_by(Questionario.criado_em.desc()).all()
    return render_template('cli/listar_questionarios.html', questionarios=questionarios)

# ------------------- Gerenciar Tópicos -------------------
@cli_bp.route('/questionario/<int:id>/topicos')
@login_required
def gerenciar_topicos(id):
    questionario = Questionario.query.get_or_404(id)
    topicos = Topico.query.filter_by(questionario_id=id).order_by(Topico.ordem).all()
    return render_template('cli/gerenciar_topicos.html', questionario=questionario, topicos=topicos)


@cli_bp.route('/topico/adicionar/<int:questionario_id>', methods=['POST'])
@login_required
def adicionar_topico(questionario_id):
    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    if nome:
        ordem = Topico.query.filter_by(questionario_id=questionario_id).count() + 1
        novo = Topico(nome=nome, descricao=descricao, ordem=ordem, questionario_id=questionario_id)
        db.session.add(novo)
        db.session.commit()
        flash('Tópico adicionado com sucesso!', 'success')
    return redirect(url_for('cli.gerenciar_topicos', id=questionario_id))

@cli_bp.route('/topico/<int:id>/remover')
@login_required
def remover_topico(id):
    topico = Topico.query.get_or_404(id)
    qid = topico.questionario_id
    db.session.delete(topico)
    db.session.commit()
    flash('Tópico removido com sucesso.', 'success')
    return redirect(url_for('cli.gerenciar_topicos', id=qid))

@cli_bp.route('/topico/<int:id>/duplicar')
@login_required
def duplicar_topico(id):
    topico = Topico.query.get_or_404(id)
    novo = Topico(
        nome=topico.nome + ' (Cópia)',
        descricao=topico.descricao,
        ordem=Topico.query.filter_by(questionario_id=topico.questionario_id).count() + 1,
        questionario_id=topico.questionario_id
    )
    db.session.add(novo)
    db.session.commit()
    flash('Tópico duplicado.', 'success')
    return redirect(url_for('cli.gerenciar_topicos', id=topico.questionario_id))

@cli_bp.route('/grupos')
@login_required
def listar_grupos():
    grupos = Grupo.query.all()
    return render_template('cli/listar_grupos.html', grupos=grupos)

@cli_bp.route('/grupos/novo', methods=['GET', 'POST'])
@login_required
def novo_grupo():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if nome:
            grupo = Grupo(nome=nome)
            db.session.add(grupo)
            db.session.commit()
            flash('Grupo criado com sucesso!', 'success')
            return redirect(url_for('cli.listar_grupos'))
        else:
            flash('Nome do grupo é obrigatório.', 'danger')

    return render_template('cli/novo_grupo.html')

@cli_bp.route('/grupos/cadastrar', methods=['POST'])
@login_required
def cadastrar_grupo():
    nome = request.form.get('nome')
    if nome:
        grupo = Grupo(nome=nome)
        db.session.add(grupo)
        db.session.commit()
        flash('Grupo cadastrado com sucesso!', 'success')
    else:
        flash('O nome do grupo é obrigatório!', 'danger')
    return redirect(url_for('cli.listar_grupos'))

@cli_bp.route('/checklist/iniciar', endpoint='iniciar_aplicacao')
@login_required
def iniciar_aplicacao():
    questionarios = Questionario.query.all()
    return render_template('cli/iniciar_aplicacao.html', questionarios=questionarios)
















