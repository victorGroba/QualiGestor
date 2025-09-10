# app/cli/routes.py - IMPLEMENTAÇÃO COMPLETA
import json
import os
import base64
import qrcode
from io import BytesIO
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from weasyprint import HTML

# Importações dos modelos
from ..models import (
    db, Usuario, Cliente, Loja, Grupo,
    Formulario, BlocoFormulario, Pergunta, OpcaoPergunta,
    Resposta, Auditoria, CategoriaFormulario,
    TipoResposta, StatusAuditoria, TipoUsuario, NaoConformidade
)

cli_bp = Blueprint('cli', __name__, template_folder='templates')

# ===================== PÁGINA INICIAL =====================

@cli_bp.route('/')
@cli_bp.route('/home')
@login_required
def index():
    """Dashboard principal do CLIQ"""
    # Estatísticas básicas
    stats = {
        'total_auditorias': 0,
        'auditorias_mes': 0,
        'formularios_ativos': 0,
        'lojas_ativas': 0
    }
    
    ultimas_auditorias = []
    
    if hasattr(current_user, 'cliente_id') and current_user.cliente_id:
        # Auditorias do cliente
        stats['total_auditorias'] = Auditoria.query.join(Loja).filter(
            Loja.cliente_id == current_user.cliente_id
        ).count()
        
        # Auditorias deste mês
        stats['auditorias_mes'] = Auditoria.query.join(Loja).filter(
            Loja.cliente_id == current_user.cliente_id,
            db.extract('month', Auditoria.data_inicio) == datetime.now().month,
            db.extract('year', Auditoria.data_inicio) == datetime.now().year
        ).count()
        
        # Formulários ativos
        stats['formularios_ativos'] = Formulario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).count()
        
        # Lojas ativas
        stats['lojas_ativas'] = Loja.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativa=True
        ).count()
        
        # Últimas auditorias
        ultimas_auditorias = Auditoria.query.join(Loja).filter(
            Loja.cliente_id == current_user.cliente_id
        ).order_by(Auditoria.data_inicio.desc()).limit(5).all()
    
    return render_template('cli/index.html', stats=stats, ultimas_auditorias=ultimas_auditorias)

# ===================== FORMULÁRIOS =====================

@cli_bp.route('/formularios')
@login_required
def listar_formularios():
    """Lista todos os formulários do cliente"""
    formularios = Formulario.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativo=True
    ).order_by(Formulario.nome).all()
    
    return render_template('cli/listar_formularios.html', formularios=formularios)

@cli_bp.route('/formulario/novo', methods=['GET', 'POST'])
@login_required
def criar_formulario():
    """Cria um novo formulário"""
    if request.method == 'POST':
        return processar_novo_formulario()
    
    # GET - Mostrar formulário
    clientes = Cliente.query.all()
    lojas = Loja.query.filter_by(cliente_id=current_user.cliente_id, ativa=True).all()
    categorias = CategoriaFormulario.query.filter_by(ativa=True).all()
    
    return render_template('cli/criar_formulario.html', 
                         clientes=clientes, 
                         lojas=lojas,
                         categorias=categorias)

def processar_novo_formulario():
    """Processa a criação de novo formulário"""
    nome = request.form.get('nome_formulario')
    descricao = request.form.get('descricao', '')
    categoria_id = request.form.get('categoria_id')
    
    if not nome:
        flash("Nome do formulário é obrigatório.", "danger")
        return redirect(url_for('cli.criar_formulario'))

    # Criar formulário
    novo_formulario = Formulario(
        nome=nome,
        descricao=descricao,
        cliente_id=current_user.cliente_id,
        criado_por_id=current_user.id,
        categoria_id=categoria_id,
        versao='1.0',
        pontuacao_ativa=True,
        ativo=True,
        publicado=False
    )
    db.session.add(novo_formulario)
    db.session.flush()
    
    # Criar bloco padrão
    bloco = BlocoFormulario(
        nome="Bloco Principal",
        ordem=1,
        formulario_id=novo_formulario.id
    )
    db.session.add(bloco)
    db.session.flush()
    
    # Processar perguntas do formulário
    perguntas_keys = [k for k in request.form if k.startswith('perguntas[') and k.endswith('][texto]')]
    perguntas_processadas = set()
    
    for idx, key in enumerate(perguntas_keys):
        pergunta_idx = key.split('[')[1].split(']')[0]
        if pergunta_idx in perguntas_processadas:
            continue
        perguntas_processadas.add(pergunta_idx)
        
        texto = request.form.get(f'perguntas[{pergunta_idx}][texto]')
        tipo = request.form.get(f'perguntas[{pergunta_idx}][tipo]')
        obrigatoria = request.form.get(f'perguntas[{pergunta_idx}][obrigatoria]') == 'on'
        peso = float(request.form.get(f'perguntas[{pergunta_idx}][peso]', 10))
        
        if not texto or not tipo:
            continue
            
        # Mapear tipo string para enum
        tipo_enum = mapear_tipo_resposta(tipo)
        
        nova_pergunta = Pergunta(
            texto=texto,
            tipo_resposta=tipo_enum,
            obrigatoria=obrigatoria,
            ordem=idx + 1,
            bloco_id=bloco.id,
            peso=peso,
            pontuacao_maxima=peso
        )
        db.session.add(nova_pergunta)
        
        # Criar opções para perguntas de múltipla escolha
        if tipo in ['SIM_NAO', 'SIM_NAO_NA']:
            opcoes = [
                ('Sim', 'Sim', peso),
                ('Não', 'Não', 0)
            ]
            if tipo == 'SIM_NAO_NA':
                opcoes.append(('N/A', 'N/A', 0))
                
            for ordem, (texto_opcao, valor_opcao, pontuacao) in enumerate(opcoes):
                opcao = OpcaoPergunta(
                    texto=texto_opcao,
                    valor=valor_opcao,
                    pontuacao=pontuacao,
                    ordem=ordem,
                    pergunta_id=nova_pergunta.id
                )
                db.session.add(opcao)
    
    db.session.commit()
    flash("Formulário criado com sucesso!", "success")
    return redirect(url_for('cli.visualizar_formulario', formulario_id=novo_formulario.id))

@cli_bp.route('/formulario/<int:formulario_id>')
@login_required
def visualizar_formulario(formulario_id):
    """Visualiza um formulário específico"""
    formulario = Formulario.query.get_or_404(formulario_id)
    
    # Verificar permissão
    if formulario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_formularios'))
    
    return render_template('cli/formulario_visualizacao.html', formulario=formulario)

@cli_bp.route('/formulario/<int:formulario_id>/publicar', methods=['POST'])
@login_required
def publicar_formulario(formulario_id):
    """Publica um formulário para uso"""
    formulario = Formulario.query.get_or_404(formulario_id)
    
    if formulario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_formularios'))
    
    formulario.publicado = True
    formulario.publicado_em = datetime.utcnow()
    db.session.commit()
    
    flash("Formulário publicado com sucesso!", "success")
    return redirect(url_for('cli.visualizar_formulario', formulario_id=formulario_id))

# ===================== APLICAÇÃO DE CHECKLISTS =====================

@cli_bp.route('/aplicar')
@cli_bp.route('/iniciar-aplicacao')
@login_required
def iniciar_aplicacao():
    """Página inicial para aplicar checklists"""
    formularios = Formulario.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativo=True,
        publicado=True
    ).order_by(Formulario.nome).all()
    
    return render_template('cli/iniciar_aplicacao.html', formularios=formularios)

@cli_bp.route('/aplicar/<int:formulario_id>')
@login_required
def selecionar_loja(formulario_id):
    """Seleciona a loja para aplicar o checklist"""
    formulario = Formulario.query.get_or_404(formulario_id)
    
    if formulario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.iniciar_aplicacao'))
    
    lojas = Loja.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativa=True
    ).order_by(Loja.nome).all()
    
    return render_template('cli/selecionar_loja.html', 
                         formulario=formulario, 
                         lojas=lojas)

@cli_bp.route('/aplicar/<int:formulario_id>/<int:loja_id>', methods=['GET', 'POST'])
@login_required
def aplicar_checklist(formulario_id, loja_id):
    """Aplica o checklist em uma loja específica"""
    formulario = Formulario.query.get_or_404(formulario_id)
    loja = Loja.query.get_or_404(loja_id)
    
    # Verificar permissões
    if formulario.cliente_id != current_user.cliente_id or loja.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.iniciar_aplicacao'))
    
    if request.method == 'POST':
        return processar_checklist(formulario, loja)
    
    # GET - Mostrar formulário para preenchimento
    return render_template('cli/aplicar_checklist.html', 
                         formulario=formulario, 
                         loja=loja)

def processar_checklist(formulario, loja):
    """Processa o envio do checklist preenchido"""
    # Criar nova auditoria
    nova_auditoria = Auditoria(
        formulario_id=formulario.id,
        loja_id=loja.id,
        usuario_id=current_user.id,
        status=StatusAuditoria.EM_ANDAMENTO,
        data_inicio=datetime.utcnow()
    )
    
    # Gerar código único
    ano = datetime.now().year
    contador = Auditoria.query.filter(
        db.extract('year', Auditoria.data_inicio) == ano
    ).count() + 1
    nova_auditoria.codigo = f"AUD-{ano}-{contador:05d}"
    
    db.session.add(nova_auditoria)
    db.session.flush()
    
    # Processar respostas
    pontuacao_total = 0
    pontuacao_maxima = 0
    
    for bloco in formulario.blocos.order_by(BlocoFormulario.ordem):
        for pergunta in bloco.perguntas.order_by(Pergunta.ordem):
            valor = request.form.get(f'pergunta_{pergunta.id}', '').strip()
            observacao = request.form.get(f'obs_{pergunta.id}', '').strip()
            
            # Verificar se pergunta obrigatória foi respondida
            if pergunta.obrigatoria and not valor:
                flash(f'A pergunta "{pergunta.texto}" é obrigatória.', 'warning')
                db.session.rollback()
                return render_template('cli/aplicar_checklist.html', 
                                     formulario=formulario, 
                                     loja=loja)
            
            # Criar resposta
            resposta = Resposta(
                pergunta_id=pergunta.id,
                auditoria_id=nova_auditoria.id,
                observacao=observacao
            )
            
            # Processar valor baseado no tipo
            pontos_obtidos = processar_resposta_pergunta(resposta, pergunta, valor)
            pontuacao_total += pontos_obtidos
            pontuacao_maxima += pergunta.pontuacao_maxima or pergunta.peso
            
            db.session.add(resposta)
    
    # Observações gerais
    nova_auditoria.observacoes_gerais = request.form.get('observacoes_gerais', '')
    
    # Calcular pontuação final
    nova_auditoria.pontuacao_obtida = pontuacao_total
    nova_auditoria.pontuacao_maxima = pontuacao_maxima
    nova_auditoria.percentual = (pontuacao_total / pontuacao_maxima * 100) if pontuacao_maxima > 0 else 0
    
    # Finalizar auditoria
    nova_auditoria.status = StatusAuditoria.CONCLUIDA
    nova_auditoria.data_conclusao = datetime.utcnow()
    
    db.session.commit()
    
    flash(f"Checklist aplicado com sucesso! Pontuação: {nova_auditoria.percentual:.1f}%", "success")
    return redirect(url_for('cli.ver_checklist', checklist_id=nova_auditoria.id))

def processar_resposta_pergunta(resposta, pergunta, valor):
    """Processa uma resposta específica e calcula pontuação"""
    if not valor:
        return 0
    
    peso = pergunta.pontuacao_maxima or pergunta.peso or 10
    
    # Sim/Não
    if pergunta.tipo_resposta in [TipoResposta.SIM_NAO, TipoResposta.SIM_NAO_NA]:
        resposta.valor_opcoes_selecionadas = json.dumps([valor])
        if valor.upper() == 'SIM':
            resposta.pontuacao_obtida = peso
            return peso
        elif valor.upper() == 'N/A':
            resposta.pontuacao_obtida = peso  # N/A conta como conforme
            return peso
        else:
            resposta.pontuacao_obtida = 0
            return 0
    
    # Texto
    elif pergunta.tipo_resposta in [TipoResposta.TEXTO, TipoResposta.TEXTO_LONGO]:
        resposta.valor_texto = valor
        if valor.strip():
            resposta.pontuacao_obtida = peso
            return peso
        return 0
    
    # Número/Nota
    elif pergunta.tipo_resposta in [TipoResposta.NUMERO, TipoResposta.NOTA]:
        try:
            numero = float(valor)
            resposta.valor_numero = numero
            
            if pergunta.tipo_resposta == TipoResposta.NOTA:
                # Nota de 0-10, calcular proporcionalmente
                nota_max = pergunta.limite_maximo or 10
                nota_min = pergunta.limite_minimo or 0
                percentual = (numero - nota_min) / (nota_max - nota_min)
                pontos = peso * percentual
                resposta.pontuacao_obtida = pontos
                return pontos
            else:
                # Número simples, se preencheu ganha pontos
                resposta.pontuacao_obtida = peso
                return peso
        except ValueError:
            resposta.valor_texto = valor
            return 0
    
    # Outros tipos
    else:
        resposta.valor_texto = valor
        if valor.strip():
            resposta.pontuacao_obtida = peso
            return peso
        return 0

# ===================== VISUALIZAÇÃO E GESTÃO DE CHECKLISTS =====================

@cli_bp.route('/checklists')
@login_required
def listar_checklists():
    """Lista todos os checklists aplicados"""
    page = request.args.get('page', 1, type=int)
    
    query = Auditoria.query.join(Loja).filter(
        Loja.cliente_id == current_user.cliente_id
    ).order_by(Auditoria.data_inicio.desc())
    
    # Filtros
    formulario_id = request.args.get('formulario_id', type=int)
    loja_id = request.args.get('loja_id', type=int)
    status = request.args.get('status')
    
    if formulario_id:
        query = query.filter(Auditoria.formulario_id == formulario_id)
    if loja_id:
        query = query.filter(Auditoria.loja_id == loja_id)
    if status:
        try:
            status_enum = StatusAuditoria[status.upper()]
            query = query.filter(Auditoria.status == status_enum)
        except KeyError:
            pass
    
    auditorias = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Para os filtros
    formularios = Formulario.query.filter_by(
        cliente_id=current_user.cliente_id, ativo=True
    ).all()
    lojas = Loja.query.filter_by(
        cliente_id=current_user.cliente_id, ativa=True
    ).all()
    
    return render_template('cli/listar_checklists.html', 
                         auditorias=auditorias,
                         formularios=formularios,
                         lojas=lojas)

@cli_bp.route('/checklist/<int:checklist_id>')
@login_required
def ver_checklist(checklist_id):
    """Visualiza um checklist específico"""
    auditoria = Auditoria.query.get_or_404(checklist_id)
    
    # Verificar permissão
    if auditoria.loja.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_checklists'))
    
    return render_template('cli/ver_checklist.html', checklist=auditoria)

@cli_bp.route('/checklist/<int:checklist_id>/pdf')
@login_required
def gerar_pdf_checklist(checklist_id):
    """Gera PDF do checklist"""
    auditoria = Auditoria.query.get_or_404(checklist_id)
    
    # Verificar permissão
    if auditoria.loja.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_checklists'))
    
    # Gerar QR Code
    qr_texto = f"Checklist ID: {auditoria.id} - {auditoria.codigo}"
    qr = qrcode.make(qr_texto)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    data_hoje = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Renderizar HTML
    html = render_template("cli/checklist_pdf.html", 
                          checklist=auditoria, 
                          qr_base64=qr_base64, 
                          data_hoje=data_hoje)
    
    # Gerar PDF
    pdf = HTML(string=html).write_pdf()
    
    # Salvar arquivo
    pdf_dir = os.path.join(os.getcwd(), 'instance', 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f'checklist_{auditoria.id}.pdf')
    
    with open(pdf_path, 'wb') as f:
        f.write(pdf)
    
    return send_file(pdf_path, 
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'Checklist_{auditoria.codigo}.pdf')

@cli_bp.route('/checklist/<int:checklist_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_checklist(checklist_id):
    """Edita um checklist existente"""
    auditoria = Auditoria.query.get_or_404(checklist_id)
    
    # Verificar permissão
    if auditoria.loja.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_checklists'))
    
    if request.method == 'POST':
        return atualizar_checklist(auditoria)
    
    # GET - Mostrar formulário de edição
    lojas = Loja.query.filter_by(
        cliente_id=current_user.cliente_id, ativa=True
    ).all()
    
    return render_template('cli/editar_checklist.html', 
                         checklist=auditoria,
                         formulario=auditoria.formulario,
                         lojas=lojas)

def atualizar_checklist(auditoria):
    """Atualiza os dados de um checklist"""
    # Atualizar loja se necessário
    nova_loja_id = request.form.get('loja_id', type=int)
    if nova_loja_id and nova_loja_id != auditoria.loja_id:
        auditoria.loja_id = nova_loja_id
    
    # Atualizar observações gerais
    auditoria.observacoes_gerais = request.form.get('observacoes_gerais', '')
    
    # Remover respostas antigas
    for resposta in auditoria.respostas:
        db.session.delete(resposta)
    db.session.flush()
    
    # Processar novas respostas (reutilizar lógica)
    pontuacao_total = 0
    pontuacao_maxima = 0
    
    for bloco in auditoria.formulario.blocos.order_by(BlocoFormulario.ordem):
        for pergunta in bloco.perguntas.order_by(Pergunta.ordem):
            valor = request.form.get(f'pergunta_{pergunta.id}', '').strip()
            observacao = request.form.get(f'obs_{pergunta.id}', '').strip()
            
            resposta = Resposta(
                pergunta_id=pergunta.id,
                auditoria_id=auditoria.id,
                observacao=observacao
            )
            
            pontos_obtidos = processar_resposta_pergunta(resposta, pergunta, valor)
            pontuacao_total += pontos_obtidos
            pontuacao_maxima += pergunta.pontuacao_maxima or pergunta.peso
            
            db.session.add(resposta)
    
    # Atualizar pontuação
    auditoria.pontuacao_obtida = pontuacao_total
    auditoria.pontuacao_maxima = pontuacao_maxima
    auditoria.percentual = (pontuacao_total / pontuacao_maxima * 100) if pontuacao_maxima > 0 else 0
    auditoria.atualizado_em = datetime.utcnow()
    
    db.session.commit()
    
    flash("Checklist atualizado com sucesso!", "success")
    return redirect(url_for('cli.ver_checklist', checklist_id=auditoria.id))

@cli_bp.route('/checklist/<int:checklist_id>/excluir', methods=['POST'])
@login_required
def excluir_checklist(checklist_id):
    """Exclui um checklist"""
    auditoria = Auditoria.query.get_or_404(checklist_id)
    
    # Verificar permissão
    if auditoria.loja.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_checklists'))
    
    # Verificar se pode excluir (apenas rascunhos ou em andamento)
    if auditoria.status in [StatusAuditoria.CONCLUIDA, StatusAuditoria.APROVADA]:
        flash("Não é possível excluir checklists concluídos ou aprovados.", "warning")
        return redirect(url_for('cli.ver_checklist', checklist_id=checklist_id))
    
    db.session.delete(auditoria)
    db.session.commit()
    
    flash("Checklist excluído com sucesso!", "success")
    return redirect(url_for('cli.listar_checklists'))

# ===================== GESTÃO DE LOJAS =====================

@cli_bp.route('/lojas')
@login_required
def listar_lojas():
    """Lista as lojas do cliente"""
    lojas = Loja.query.filter_by(
        cliente_id=current_user.cliente_id
    ).order_by(Loja.nome).all()
    
    return render_template('cli/listar_lojas.html', lojas=lojas)

@cli_bp.route('/loja/nova', methods=['GET', 'POST'])
@login_required
def nova_loja():
    """Cria uma nova loja"""
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
    ).all()
    
    return render_template('cli/nova_loja.html', grupos=grupos)

# ===================== GESTÃO DE GRUPOS =====================

@cli_bp.route('/grupos')
@login_required
def listar_grupos():
    """Lista os grupos do cliente"""
    grupos = Grupo.query.filter_by(
        cliente_id=current_user.cliente_id, ativo=True
    ).all()
    
    return render_template('cli/listar_grupos.html', grupos=grupos)

@cli_bp.route('/grupo/novo', methods=['GET', 'POST'])
@login_required
def novo_grupo():
    """Cria um novo grupo"""
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

# ===================== FUNÇÕES AUXILIARES =====================

def mapear_tipo_resposta(tipo_str):
    """Mapeia string para enum TipoResposta"""
    mapeamento = {
        'SIM_NAO': TipoResposta.SIM_NAO,
        'SIM_NAO_NA': TipoResposta.SIM_NAO_NA,
        'TEXTO': TipoResposta.TEXTO,
        'TEXTO_LONGO': TipoResposta.TEXTO_LONGO,
        'NUMERO': TipoResposta.NUMERO,
        'NOTA': TipoResposta.NOTA,
        'PERCENTUAL': TipoResposta.PERCENTUAL,
        'MULTIPLA_ESCOLHA': TipoResposta.MULTIPLA_ESCOLHA,
        'UNICA_ESCOLHA': TipoResposta.UNICA_ESCOLHA,
        'IMAGEM': TipoResposta.IMAGEM,
        'DATA': TipoResposta.DATA,
        'HORA': TipoResposta.HORA,
        'DATA_HORA': TipoResposta.DATA_HORA
    }
    
    return mapeamento.get(tipo_str, TipoResposta.TEXTO)

# ===================== API ROUTES (AJAX) =====================

@cli_bp.route('/api/formularios/<int:loja_id>')
@login_required
def api_formularios_loja(loja_id):
    """API para buscar formulários disponíveis para uma loja"""
    loja = Loja.query.get_or_404(loja_id)
    
    if loja.cliente_id != current_user.cliente_id:
        return jsonify({'error': 'Acesso negado'}), 403
    
    formularios = Formulario.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativo=True,
        publicado=True
    ).all()
    
    formularios_data = [{
        'id': f.id,
        'nome': f.nome,
        'descricao': f.descricao or '',
        'versao': f.versao,
        'categoria': f.categoria.nome if f.categoria else 'Sem categoria'
    } for f in formularios]
    
    return jsonify(formularios_data)

@cli_bp.route('/api/resposta/salvar', methods=['POST'])
@login_required
def api_salvar_resposta():
    """API para salvar resposta via AJAX"""
    data = request.get_json()
    
    auditoria_id = data.get('auditoria_id')
    pergunta_id = data.get('pergunta_id')
    valor = data.get('valor')
    observacao = data.get('observacao', '')
    
    auditoria = Auditoria.query.get_or_404(auditoria_id)
    pergunta = Pergunta.query.get_or_404(pergunta_id)
    
    # Verificar permissão
    if auditoria.loja.cliente_id != current_user.cliente_id:
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Buscar ou criar resposta
    resposta = Resposta.query.filter_by(
        auditoria_id=auditoria_id,
        pergunta_id=pergunta_id
    ).first()
    
    if not resposta:
        resposta = Resposta(
            auditoria_id=auditoria_id,
            pergunta_id=pergunta_id
        )
        db.session.add(resposta)
    
    # Atualizar resposta
    resposta.observacao = observacao
    pontos_obtidos = processar_resposta_pergunta(resposta, pergunta, valor)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Resposta salva com sucesso',
        'pontuacao_obtida': pontos_obtidos
    })

# ===================== COMPATIBILIDADE =====================

# Rotas para compatibilidade com templates antigos
@cli_bp.route('/avaliados')
@login_required
def listar_avaliados():
    """Redireciona para listagem de lojas (compatibilidade)"""
    return redirect(url_for('cli.listar_lojas'))

@cli_bp.route('/questionarios')
@login_required
def listar_questionarios():
    """Redireciona para listagem de formulários (compatibilidade)"""
    return redirect(url_for('cli.listar_formularios'))