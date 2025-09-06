import json
import os
import base64
import qrcode
from io import BytesIO
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from weasyprint import HTML



# Importações básicas que existem em ambas versões
from ..models import (
    db, Usuario, Cliente, Loja,
    Formulario, BlocoFormulario, Pergunta, OpcaoPergunta,
    Resposta, Auditoria, Grupo,
    TipoResposta, StatusAuditoria, TipoUsuario
)


# Tentativa de importar novos modelos (se existirem)
try:
    from ..models import (
        Loja, BlocoFormulario, OpcaoPergunta, 
        StatusAuditoria, TipoResposta, TipoUsuario,
        NaoConformidade, PlanoAcao, AnexoAuditoria,
        CategoriaFormulario, LogAuditoria
    )
    NOVO_MODELO = True
except ImportError:
    NOVO_MODELO = False
    # Manter compatibilidade com modelo antigo
    from ..models import (
        Avaliado, Questionario, Topico,
        ConfiguracaoNota, ConfiguracaoRelatorio, ConfiguracaoEmail,
        UsuarioAutorizado, GrupoQuestionario
    )

cli_bp = Blueprint('cli', __name__, template_folder='templates')

# ===================== FUNÇÕES AUXILIARES =====================

def get_lojas_ou_avaliados():
    """Retorna lojas (novo modelo) ou avaliados (modelo antigo)"""
    if NOVO_MODELO:
        if hasattr(current_user, 'cliente_id'):
            return Loja.query.filter_by(cliente_id=current_user.cliente_id, ativa=True).all()
        return []
    else:
        return Avaliado.query.all()

def get_entidade_por_id(entity_id):
    """Busca loja ou avaliado dependendo do modelo"""
    if NOVO_MODELO:
        return Loja.query.get_or_404(entity_id)
    else:
        return Avaliado.query.get_or_404(entity_id)

# ===================== ROTAS PRINCIPAIS =====================

@cli_bp.route('/')
@login_required
def index():
    """Redireciona para a página apropriada"""
    if NOVO_MODELO:
        return redirect(url_for('cli.home'))
    else:
        return redirect(url_for('cli.iniciar_aplicacao'))

@cli_bp.route('/home')
@login_required
def home():
    """Dashboard do CLIQ com estatísticas"""
    stats = {}
    ultimas_auditorias = []
    
    if NOVO_MODELO:
        # Estatísticas do novo modelo
        stats = {
            'total_auditorias': Auditoria.query.join(Loja).filter(
                Loja.cliente_id == current_user.cliente_id
            ).count() if hasattr(current_user, 'cliente_id') else 0,
            
            'auditorias_mes': Auditoria.query.filter(
                db.extract('month', Auditoria.data_inicio) == datetime.now().month,
                db.extract('year', Auditoria.data_inicio) == datetime.now().year
            ).count() if hasattr(Auditoria, 'data_inicio') else 0,
            
            'formularios_ativos': Formulario.query.filter_by(
                cliente_id=current_user.cliente_id,
                ativo=True
            ).count() if hasattr(Formulario, 'ativo') else Formulario.query.count(),
            
            'lojas_ativas': Loja.query.filter_by(
                cliente_id=current_user.cliente_id,
                ativa=True
            ).count()
        }
        
        ultimas_auditorias = Auditoria.query.join(Loja).filter(
            Loja.cliente_id == current_user.cliente_id
        ).order_by(Auditoria.data_inicio.desc()).limit(5).all() if hasattr(Auditoria, 'data_inicio') else []
    else:
        # Estatísticas do modelo antigo
        stats = {
            'total_auditorias': Auditoria.query.count(),
            'auditorias_mes': Auditoria.query.filter(
                db.extract('month', Auditoria.data) == datetime.now().month
            ).count(),
            'formularios_ativos': Formulario.query.count(),
            'lojas_ativas': Avaliado.query.count()
        }
        
        ultimas_auditorias = Auditoria.query.order_by(Auditoria.data.desc()).limit(5).all()
    
    return render_template('cli/home.html', stats=stats, ultimas_auditorias=ultimas_auditorias)

# ===================== FORMULÁRIOS =====================

@cli_bp.route('/formulario/novo', methods=['GET', 'POST'])
@login_required
def criar_formulario():
    clientes = Cliente.query.all()
    
    if NOVO_MODELO:
        entidades = Loja.query.filter_by(cliente_id=current_user.cliente_id).all() if hasattr(current_user, 'cliente_id') else []
        categorias = CategoriaFormulario.query.filter_by(ativa=True).all() if 'CategoriaFormulario' in globals() else []
    else:
        entidades = Avaliado.query.all()
        categorias = []
    
    return render_template('cli/criar_formulario.html', 
                         clientes=clientes, 
                         avaliados=entidades,
                         categorias=categorias,
                         novo_modelo=NOVO_MODELO)

@cli_bp.route('/formulario/salvar', methods=['POST'])
@login_required
def salvar_formulario():
    nome = request.form.get('nome_formulario')
    cliente_id = request.form.get('cliente_id')
    
    if not nome:
        flash("Nome do formulário é obrigatório.", "danger")
        return redirect(url_for('cli.criar_formulario'))

    if NOVO_MODELO:
        # Criar formulário no novo modelo
        novo_formulario = Formulario(
            nome=nome,
            cliente_id=cliente_id or current_user.cliente_id,
            versao='1.0',
            pontuacao_ativa=True,
            criado_por_id=current_user.id,
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
        
        # Processar perguntas
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
            
            # Mapear tipo antigo para novo enum se necessário
            tipo_mapeado = mapear_tipo_resposta(tipo)
            
            nova_pergunta = Pergunta(
                texto=texto,
                tipo_resposta=tipo_mapeado,
                obrigatoria=obrigatoria,
                ordem=idx + 1,
                bloco_id=bloco.id,
                peso=1,
                pontuacao_maxima=10
            )
            db.session.add(nova_pergunta)
    else:
        # Criar formulário no modelo antigo
        avaliado_id = request.form.get('avaliado_id')
        novo_formulario = Formulario(
            nome=nome,
            cliente_id=cliente_id,
            avaliado_id=avaliado_id
        )
        db.session.add(novo_formulario)
        db.session.flush()
        
        # Processar perguntas modelo antigo
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
    return render_template('cli/formulario_visualizacao.html', 
                         formulario=formulario,
                         novo_modelo=NOVO_MODELO)

# ===================== CHECKLISTS / AUDITORIAS =====================

@cli_bp.route('/checklists')
@login_required
def listar_checklists():
    if NOVO_MODELO and hasattr(current_user, 'cliente_id'):
        checklists = Auditoria.query.join(Loja).filter(
            Loja.cliente_id == current_user.cliente_id
        ).order_by(Auditoria.data_inicio.desc() if hasattr(Auditoria, 'data_inicio') else Auditoria.id.desc()).all()
    else:
        checklists = Auditoria.query.order_by(
            Auditoria.data.desc() if hasattr(Auditoria, 'data') else Auditoria.id.desc()
        ).all()
    
    return render_template('cli/listar_checklists.html', 
                         checklists=checklists,
                         novo_modelo=NOVO_MODELO)

@cli_bp.route('/checklist/<int:checklist_id>')
@login_required
def ver_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    return render_template('cli/ver_checklist.html', 
                         checklist=checklist,
                         novo_modelo=NOVO_MODELO)

@cli_bp.route('/checklist/<int:checklist_id>/pdf')
@login_required
def gerar_pdf_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    
    # Calcular pontuação se disponível
    if NOVO_MODELO and hasattr(checklist, 'pontuacao_obtida'):
        percentual = checklist.percentual
    else:
        from app.utils.pontuacao import calcular_pontuacao_auditoria
        resultado = calcular_pontuacao_auditoria(checklist) or {}
        percentual = resultado.get('percentual', 0)
    
    # Gerar QR Code
    qr_texto = f"Checklist ID: {checklist.id} - Data: {datetime.now().strftime('%d/%m/%Y')}"
    qr = qrcode.make(qr_texto)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    data_hoje = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    html = render_template("cli/ver_checklist_pdf.html", 
                          checklist=checklist, 
                          qr_base64=qr_base64, 
                          data_hoje=data_hoje,
                          percentual=percentual,
                          novo_modelo=NOVO_MODELO)
    pdf = HTML(string=html).write_pdf()
    
    pdf_dir = os.path.join(os.getcwd(), 'instance', 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f'checklist_{checklist.id}.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf)
    
    return send_file(pdf_path, mimetype='application/pdf')

@cli_bp.route('/checklist/<int:checklist_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    formulario = checklist.formulario
    
    if NOVO_MODELO:
        entidades = Loja.query.filter_by(cliente_id=current_user.cliente_id).all()
        perguntas = []
        for bloco in formulario.blocos:
            perguntas.extend(bloco.perguntas.all())
    else:
        entidades = Avaliado.query.all()
        perguntas = formulario.perguntas
    
    if request.method == 'POST':
        # Atualizar loja/avaliado
        if NOVO_MODELO:
            checklist.loja_id = request.form.get('loja_id')
            if hasattr(checklist, 'atualizado_em'):
                checklist.atualizado_em = datetime.utcnow()
        else:
            checklist.avaliado_id = request.form.get('avaliado_id')
            checklist.data = datetime.utcnow()
        
        # Remover respostas antigas
        for resposta in checklist.respostas:
            db.session.delete(resposta)
        db.session.flush()
        
        # Adicionar novas respostas
        for pergunta in perguntas:
            valor = request.form.get(f'pergunta_{pergunta.id}', '').strip()
            
            resposta = Resposta(
                pergunta_id=pergunta.id,
                auditoria_id=checklist.id
            )
            
            if NOVO_MODELO:
                # Processar resposta baseado no tipo
                processar_resposta_novo_modelo(resposta, pergunta, valor)
            else:
                resposta.valor_opcoes_selecionadas = json.dumps([valor]) if valor else None
            
            db.session.add(resposta)
        
        db.session.commit()
        flash("Checklist atualizado com sucesso!", "success")
        return redirect(url_for('cli.listar_checklists'))
    
    return render_template('cli/editar_checklist.html', 
                         checklist=checklist, 
                         formulario=formulario,
                         entidades=entidades,
                         avaliados=entidades,  # Compatibilidade
                         novo_modelo=NOVO_MODELO)

@cli_bp.route('/checklist/<int:checklist_id>/excluir', methods=['POST'])
@login_required
def excluir_checklist(checklist_id):
    checklist = Auditoria.query.get_or_404(checklist_id)
    db.session.delete(checklist)
    db.session.commit()
    flash("Checklist excluído com sucesso!", "success")
    return redirect(url_for('cli.listar_checklists'))

# ===================== APLICAÇÃO DE CHECKLIST =====================

@cli_bp.route('/checklist/iniciar', endpoint='iniciar_aplicacao')
@login_required
def iniciar_aplicacao():
    if NOVO_MODELO:
        formularios = Formulario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True,
            publicado=True
        ).all() if hasattr(current_user, 'cliente_id') else []
    else:
        # Compatibilidade com Questionarios
        if 'Questionario' in globals():
            questionarios = Questionario.query.all()
            return render_template('cli/iniciar_aplicacao.html', questionarios=questionarios)
        formularios = Formulario.query.all()
    
    return render_template('cli/iniciar_aplicacao.html', 
                         formularios=formularios,
                         questionarios=formularios,  # Compatibilidade
                         novo_modelo=NOVO_MODELO)

@cli_bp.route('/checklist/iniciar/<int:formulario_id>')
@login_required
def selecionar_avaliado(formulario_id):
    formulario = Formulario.query.get_or_404(formulario_id)
    
    if NOVO_MODELO:
        entidades = Loja.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativa=True
        ).order_by(Loja.nome.asc()).all()
    else:
        entidades = Avaliado.query.order_by(Avaliado.nome.asc()).all()
    
    return render_template('cli/selecionar_avaliado.html', 
                         formulario=formulario, 
                         avaliados=entidades,
                         lojas=entidades if NOVO_MODELO else None,
                         novo_modelo=NOVO_MODELO)

@cli_bp.route('/checklist/aplicar/<int:formulario_id>/<int:entidade_id>', methods=['GET', 'POST'])
@login_required
def aplicar_checklist_fluxo(formulario_id, entidade_id):
    formulario = Formulario.query.get_or_404(formulario_id)
    
    if NOVO_MODELO:
        entidade = Loja.query.get_or_404(entidade_id)
        perguntas = []
        for bloco in formulario.blocos.order_by(BlocoFormulario.ordem):
            perguntas.extend(bloco.perguntas.order_by(Pergunta.ordem).all())
    else:
        entidade = Avaliado.query.get_or_404(entidade_id)
        perguntas = formulario.perguntas
    
    if request.method == 'POST':
        # Criar nova auditoria
        nova_checklist = Auditoria(
            usuario_id=current_user.id,
            formulario_id=formulario.id
        )
        
        if NOVO_MODELO:
            nova_checklist.loja_id = entidade.id
            nova_checklist.status = StatusAuditoria.EM_ANDAMENTO if 'StatusAuditoria' in globals() else 'em_andamento'
            nova_checklist.data_inicio = datetime.utcnow()
            
            # Gerar código único
            ano = datetime.now().year
            contador = Auditoria.query.filter(
                db.extract('year', Auditoria.data_inicio) == ano
            ).count() + 1
            nova_checklist.codigo = f"AUD-{ano}-{contador:05d}"
        else:
            nova_checklist.avaliado_id = entidade.id
            nova_checklist.data = datetime.utcnow()
        
        db.session.add(nova_checklist)
        db.session.flush()
        
        # Processar respostas
        for pergunta in perguntas:
            valor = request.form.get(f'pergunta_{pergunta.id}', '').strip()
            
            if pergunta.obrigatoria and not valor:
                flash(f'A pergunta "{pergunta.texto}" é obrigatória.', 'warning')
                return render_template('cli/aplicar_checklist.html', 
                                     formulario=formulario, 
                                     avaliado=entidade,
                                     loja=entidade if NOVO_MODELO else None,
                                     novo_modelo=NOVO_MODELO)
            
            resposta = Resposta(
                pergunta_id=pergunta.id,
                auditoria_id=nova_checklist.id
            )
            
            if NOVO_MODELO:
                processar_resposta_novo_modelo(resposta, pergunta, valor)
            else:
                resposta.valor_opcoes_selecionadas = json.dumps([valor]) if valor else None
            
            db.session.add(resposta)
        
        # Finalizar auditoria se novo modelo
        if NOVO_MODELO:
            nova_checklist.status = StatusAuditoria.CONCLUIDA if 'StatusAuditoria' in globals() else 'concluida'
            nova_checklist.data_conclusao = datetime.utcnow()
            calcular_pontuacao_auditoria_novo_modelo(nova_checklist)
        
        db.session.commit()
        flash("Checklist aplicado com sucesso!", "success")
        return redirect(url_for('cli.listar_checklists'))
    
    return render_template('cli/aplicar_checklist.html', 
                         formulario=formulario, 
                         avaliado=entidade,
                         loja=entidade if NOVO_MODELO else None,
                         novo_modelo=NOVO_MODELO)

# ===================== AVALIADOS (COMPATIBILIDADE) =====================

@cli_bp.route('/avaliado/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_avaliado():
    if NOVO_MODELO:
        return redirect(url_for('admin.cadastrar_loja'))
    
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
    if NOVO_MODELO:
        # Redirecionar para listagem de lojas
        return redirect(url_for('admin.listar_lojas'))
    
    nome = request.args.get('nome')
    grupo_id = request.args.get('grupo_id')
    query = Avaliado.query
    
    if hasattr(current_user, 'perfil') and current_user.perfil != 'admin':
        query = query.filter_by(cliente_id=current_user.cliente_id)
    
    if nome:
        query = query.filter(Avaliado.nome.ilike(f'%{nome}%'))
    if grupo_id and grupo_id.isdigit():
        query = query.filter_by(grupo_id=int(grupo_id))
    
    avaliados = query.all()
    grupos = Grupo.query.all()
    return render_template('cli/listar_avaliados.html', avaliados=avaliados, grupos=grupos)

# ===================== GRUPOS =====================

@cli_bp.route('/grupos')
@login_required
def listar_grupos():
    if hasattr(current_user, 'cliente_id'):
        grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id).all()
    else:
        grupos = Grupo.query.all()
    
    return render_template('cli/listar_grupos.html', 
                         grupos=grupos,
                         novo_modelo=NOVO_MODELO)

@cli_bp.route('/grupos/novo', methods=['GET', 'POST'])
@login_required
def novo_grupo():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao', '')
        
        if nome:
            grupo = Grupo(nome=nome)
            if NOVO_MODELO:
                grupo.descricao = descricao
                if hasattr(current_user, 'cliente_id'):
                    grupo.cliente_id = current_user.cliente_id
            
            db.session.add(grupo)
            db.session.commit()
            flash('Grupo criado com sucesso!', 'success')
            return redirect(url_for('cli.listar_grupos'))
        else:
            flash('Nome do grupo é obrigatório.', 'danger')
    
    return render_template('cli/novo_grupo.html', novo_modelo=NOVO_MODELO)

# ===================== QUESTIONÁRIOS (COMPATIBILIDADE) =====================

if not NOVO_MODELO and 'Questionario' in globals():
    
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
    
    @cli_bp.route('/questionario/<int:id>/topicos')
    @login_required
    def gerenciar_topicos(id):
        questionario = Questionario.query.get_or_404(id)
        topicos = Topico.query.filter_by(questionario_id=id).order_by(Topico.ordem).all()
        return render_template('cli/gerenciar_topicos.html', questionario=questionario, topicos=topicos)

# ===================== FUNÇÕES AUXILIARES =====================

def mapear_tipo_resposta(tipo_antigo):
    """Mapeia tipos de resposta antigos para o novo enum"""
    if not NOVO_MODELO or 'TipoResposta' not in globals():
        return tipo_antigo
    
    mapeamento = {
        'Sim/Não': TipoResposta.SIM_NAO,
        'Texto': TipoResposta.TEXTO,
        'Nota': TipoResposta.NOTA,
        'Múltipla Escolha': TipoResposta.MULTIPLA_ESCOLHA,
        'Única Escolha': TipoResposta.UNICA_ESCOLHA,
        'Número': TipoResposta.NUMERO,
        'Data': TipoResposta.DATA,
        'Hora': TipoResposta.HORA
    }
    
    # Se for string, tentar mapear
    if isinstance(tipo_antigo, str):
        return mapeamento.get(tipo_antigo, TipoResposta.TEXTO)
    
    return tipo_antigo

def processar_resposta_novo_modelo(resposta, pergunta, valor):
    """Processa resposta de acordo com o tipo no novo modelo"""
    if not valor:
        return
    
    if not NOVO_MODELO:
        resposta.valor_opcoes_selecionadas = json.dumps([valor])
        return
    
    tipo = pergunta.tipo_resposta
    
    # Se for enum, pegar o valor
    if hasattr(tipo, 'value'):
        tipo = tipo.value
    
    if tipo in ['SIM_NAO', 'SIM_NAO_NA', 'Sim/Não']:
        resposta.valor_boolean = (valor.lower() == 'sim')
        resposta.pontuacao_obtida = pergunta.pontuacao_maxima if resposta.valor_boolean else 0
        
    elif tipo in ['TEXTO', 'TEXTO_LONGO', 'Texto']:
        resposta.valor_texto = valor
        resposta.pontuacao_obtida = pergunta.pontuacao_maxima if valor else 0
        
    elif tipo in ['NUMERO', 'NOTA', 'PERCENTUAL', 'Número', 'Nota']:
        try:
            resposta.valor_numero = float(valor)
            if tipo == 'NOTA' or tipo == 'Nota':
                resposta.pontuacao_obtida = (float(valor) / 10) * pergunta.pontuacao_maxima
            else:
                resposta.pontuacao_obtida = pergunta.pontuacao_maxima if float(valor) > 0 else 0
        except ValueError:
            resposta.valor_numero = 0
            resposta.pontuacao_obtida = 0
            
    elif tipo in ['DATA', 'HORA', 'DATA_HORA', 'Data', 'Hora']:
        try:
            resposta.valor_data = datetime.fromisoformat(valor)
            resposta.pontuacao_obtida = pergunta.pontuacao_maxima if valor else 0
        except ValueError:
            resposta.valor_texto = valor
            resposta.pontuacao_obtida = 0
    
    elif tipo in ['MULTIPLA_ESCOLHA', 'UNICA_ESCOLHA', 'Múltipla Escolha', 'Única Escolha']:
        if isinstance(valor, list):
            resposta.valor_opcao_ids = valor
        else:
            resposta.valor_opcao_ids = [valor]
        resposta.pontuacao_obtida = pergunta.pontuacao_maxima if valor else 0
    
    else:
        # Fallback para compatibilidade
        resposta.valor_opcoes_selecionadas = json.dumps([valor]) if valor else None
        resposta.pontuacao_obtida = pergunta.pontuacao_maxima if hasattr(pergunta, 'pontuacao_maxima') else 0

def calcular_pontuacao_auditoria_novo_modelo(auditoria):
    """Calcula a pontuação total de uma auditoria no novo modelo"""
    if not NOVO_MODELO or not hasattr(auditoria, 'pontuacao_obtida'):
        return
    
    pontuacao_total = 0
    pontuacao_maxima = 0
    
    for resposta in auditoria.respostas:
        if hasattr(resposta, 'pontuacao_obtida') and resposta.pontuacao_obtida:
            pontuacao_total += resposta.pontuacao_obtida
        if hasattr(resposta, 'pontuacao_maxima') and resposta.pontuacao_maxima:
            pontuacao_maxima += resposta.pontuacao_maxima
        elif hasattr(resposta.pergunta, 'pontuacao_maxima'):
            pontuacao_maxima += resposta.pergunta.pontuacao_maxima
    
    auditoria.pontuacao_obtida = pontuacao_total
    auditoria.pontuacao_maxima = pontuacao_maxima
    auditoria.percentual = (pontuacao_total / pontuacao_maxima * 100) if pontuacao_maxima > 0 else 0

# ===================== ROTAS ADICIONAIS PARA NOVO MODELO =====================

if NOVO_MODELO:
    
    @cli_bp.route('/aplicar')
    @login_required
    def aplicar_checklist():
        """Página de seleção para aplicar checklist (novo modelo)"""
        lojas = Loja.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativa=True
        ).order_by(Loja.nome).all()
        
        return render_template('cli/aplicar_checklist_novo.html', lojas=lojas)
    
    @cli_bp.route('/get_formularios/<int:loja_id>')
    @login_required
    def get_formularios(loja_id):
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
            'descricao': f.descricao if hasattr(f, 'descricao') else '',
            'versao': f.versao if hasattr(f, 'versao') else '1.0',
            'categoria': f.categoria.nome if hasattr(f, 'categoria') and f.categoria else 'Sem categoria'
        } for f in formularios]
        
        return jsonify(formularios_data)
    
    @cli_bp.route('/salvar_resposta', methods=['POST'])
    @login_required
    def salvar_resposta():
        """Salvar resposta de uma pergunta via AJAX"""
        data = request.get_json()
        
        auditoria_id = data.get('auditoria_id')
        pergunta_id = data.get('pergunta_id')
        valor = data.get('valor')
        observacao = data.get('observacao', '')
        nao_aplicavel = data.get('nao_aplicavel', False)
        
        auditoria = Auditoria.query.get_or_404(auditoria_id)
        pergunta = Pergunta.query.get_or_404(pergunta_id)
        
        if auditoria.usuario_id != current_user.id:
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
        
        # Processar resposta
        if hasattr(resposta, 'observacao'):
            resposta.observacao = observacao
        if hasattr(resposta, 'nao_aplicavel'):
            resposta.nao_aplicavel = nao_aplicavel
        
        processar_resposta_novo_modelo(resposta, pergunta, valor)
        
        # Atualizar timestamp se existir
        if hasattr(resposta, 'atualizado_em'):
            resposta.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Resposta salva com sucesso',
            'pontuacao_obtida': resposta.pontuacao_obtida if hasattr(resposta, 'pontuacao_obtida') else 0
        })
    
    @cli_bp.route('/historico')
    @login_required
    def historico():
        """Histórico de auditorias com filtros"""
        page = request.args.get('page', 1, type=int)
        
        # Filtros
        loja_id = request.args.get('loja_id', type=int)
        formulario_id = request.args.get('formulario_id', type=int)
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Query base
        query = Auditoria.query.join(Loja).filter(
            Loja.cliente_id == current_user.cliente_id
        )
        
        # Aplicar filtros
        if loja_id:
            query = query.filter(Auditoria.loja_id == loja_id)
        if formulario_id:
            query = query.filter(Auditoria.formulario_id == formulario_id)
        if status and hasattr(StatusAuditoria, status.upper()):
            query = query.filter(Auditoria.status == StatusAuditoria[status.upper()])
        if data_inicio:
            query = query.filter(Auditoria.data_inicio >= datetime.fromisoformat(data_inicio))
        if data_fim:
            query = query.filter(Auditoria.data_inicio <= datetime.fromisoformat(data_fim))
        
        # Ordenar e paginar
        auditorias = query.order_by(Auditoria.data_inicio.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Buscar lojas e formulários para os filtros
        lojas = Loja.query.filter_by(cliente_id=current_user.cliente_id, ativa=True).all()
        formularios = Formulario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
        
        return render_template('cli/historico.html',
                             auditorias=auditorias,
                             lojas=lojas,
                             formularios=formularios,
                             filtros={
                                 'loja_id': loja_id,
                                 'formulario_id': formulario_id,
                                 'status': status,
                                 'data_inicio': data_inicio,
                                 'data_fim': data_fim
                             })

# ===================== CLIENTE =====================

@cli_bp.route('/cliente/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_cliente():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash("Nome do cliente é obrigatório", "danger")
            return redirect(url_for('cli.cadastrar_cliente'))
        
        cliente = Cliente(nome=nome)
        
        # Adicionar campos extras se existirem no novo modelo
        if NOVO_MODELO:
            cliente.nome_fantasia = request.form.get('nome_fantasia')
            cliente.cnpj = request.form.get('cnpj')
            cliente.telefone = request.form.get('telefone')
            cliente.email_contato = request.form.get('email')
            cliente.endereco = request.form.get('endereco')
            cliente.cidade = request.form.get('cidade')
            cliente.estado = request.form.get('estado')
            cliente.cep = request.form.get('cep')
        
        db.session.add(cliente)
        db.session.commit()
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for('cli.index'))
    
    return render_template('cli/cadastrar_cliente.html', novo_modelo=NOVO_MODELO)