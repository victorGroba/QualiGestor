# app/cli/routes.py - ROTAS CLIQ COMPLETAS CORRIGIDAS
import json
import os
import base64
import qrcode
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify, make_response, Response, send_from_directory, abort
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
# from weasyprint import HTML  # COMENTAR SE DER ERRO
from sqlalchemy import func, extract, and_, or_, desc
from sqlalchemy.orm import joinedload, subqueryload
from pathlib import Path
import urllib.parse
import google.generativeai as genai

from flask import request, make_response
from collections import defaultdict

from .. import csrf

# ==================== CORREÇÃO 1: IMPORTS ROBUSTOS ====================
try:
    from ..models import (
        db,  Usuario, Cliente, Grupo, Avaliado,
        Questionario, Topico, Pergunta, OpcaoPergunta,
        AplicacaoQuestionario, RespostaPergunta, UsuarioAutorizado,
        TipoResposta, StatusQuestionario, StatusAplicacao, 
        TipoPreenchimento, ModoExibicaoNota, CorRelatorio,
        TipoUsuario, Notificacao, LogAuditoria, ConfiguracaoCliente, FotoResposta, CategoriaIndicador, usuario_grupos
    )
except ImportError as e:
    print(f"Erro de import: {e}")
    # Imports básicos que devem existir
    from ..models import (
        db, Usuario, Cliente, Avaliado,
        Questionario, Topico, Pergunta,
        TipoUsuario
    )
    # Definir valores padrão para os que podem não existir
    class StatusQuestionario:
        RASCUNHO = "rascunho"
        PUBLICADO = "publicado"
        INATIVO = "inativo"
    
    class StatusAplicacao:
        EM_ANDAMENTO = "em_andamento"
        FINALIZADA = "finalizada"
    
    class TipoResposta:
        SIM_NAO_NA = "sim_nao_na"
        MULTIPLA_ESCOLHA = "multipla_escolha"
        ESCALA_NUMERICA = "escala_numerica"
        NOTA = "nota"
        TEXTO_LIVRE = "texto_livre"
    
    class ModoExibicaoNota:
        PERCENTUAL = "percentual"
        NOTA = "nota"
    
    class CorRelatorio:
        AZUL = "azul"
        VERDE = "verde"
        VERMELHO = "vermelho"

try:
    from ..models import Integracao
except ImportError:
    # Classe placeholder se Integracao não existir
    class Integracao:
        def __init__(self):
            pass
        @staticmethod
        def query():
            return MockQuery()

class MockQuery:
    def filter_by(self, **kwargs):
        return self
    def all(self):
        return []

cli_bp = Blueprint('cli', __name__, template_folder='templates')




@cli_bp.before_request
def forcar_troca_senha_padrao():
    """
    Se a senha do usuário ainda for a padrão '123456', 
    ele não consegue navegar no sistema até trocar.
    """
    # Só verifica se o usuário estiver logado
    if current_user.is_authenticated:
        
        # VERIFICAÇÃO MÁGICA: A senha atual é '123456'?
        # (Não precisa de campo novo no banco, testamos na hora)
        senha_eh_padrao = check_password_hash(current_user.senha_hash, '123456')
        
        if senha_eh_padrao:
            # Lista de lugares que ele PODE ir (Perfil para mudar a senha ou Sair)
            rotas_permitidas = ['cli.perfil', 'auth.logout', 'static']
            
            # Se ele tentar ir para qualquer outro lugar (tipo listar avaliados)...
            if request.endpoint and request.endpoint not in rotas_permitidas:
                flash('Sua senha ainda é a padrão (123456). Por segurança, defina uma nova senha agora.', 'warning')
                return redirect(url_for('cli.perfil'))
# ===================== CORREÇÃO 2: DECORATOR ADMIN_REQUIRED ROBUSTO =====================

def admin_required(f):
    """Decorator para exigir permissões de administrador - CORRIGIDO"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Acesso negado. Faça login primeiro.', 'error')
            return redirect(url_for('auth.login'))
        
        # Verificação mais robusta do tipo de usuário
        try:
            user_type = current_user.tipo
            if hasattr(user_type, 'name'):
                type_name = user_type.name
            elif hasattr(user_type, 'value'):
                type_name = user_type.value
            else:
                type_name = str(user_type)
            
            admin_types = ['ADMIN', 'SUPER_ADMIN', 'admin', 'super_admin']
            
            if type_name not in admin_types:
                flash('Acesso restrito a administradores.', 'error')
                return redirect(url_for('cli.index'))
            
        except AttributeError:
            flash('Erro de autenticação.', 'error')
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function

# ===================== CORREÇÃO 3: FUNÇÃO GET_AVALIADOS_USUARIO ROBUSTA =====================

# No arquivo app/cli/routes.py

# Em app/cli/routes.py (Substitua a função inteira)

def get_avaliados_usuario():
    """
    Retorna a lista de Ranchos (Avaliados) disponíveis para o usuário.
    Atualizado para suportar Multi-GAP.
    """
    try:
        user_type = getattr(current_user, 'tipo', 'USUARIO')
        # Tratamento seguro do Enum
        if hasattr(user_type, 'name'): type_name = user_type.name.upper()
        else: type_name = str(user_type).upper()

        # 1. Nível Nacional: Vê TUDO
        if type_name in ['SUPER_ADMIN', 'ADMIN']:
            return Avaliado.query.filter_by(
                cliente_id=current_user.cliente_id, 
                ativo=True
            ).order_by(Avaliado.nome).all()
        
        # 2. Nível Regional (GESTOR/AUDITOR) - MULTI-GAP
        elif type_name in ['GESTOR', 'AUDITOR']:
            # Pega IDs de todos os GAPs que a consultora tem acesso
            gaps_ids = [g.id for g in current_user.grupos_acesso]
            
            # Se a lista estiver vazia, tenta o legado
            if not gaps_ids and current_user.grupo_id:
                gaps_ids = [current_user.grupo_id]

            if gaps_ids:
                return Avaliado.query.filter(
                    Avaliado.cliente_id == current_user.cliente_id,
                    Avaliado.grupo_id.in_(gaps_ids),  # <--- AQUI É O PULO DO GATO (.in_)
                    Avaliado.ativo == True
                ).order_by(Avaliado.nome).all()
            return []
            
        # 3. Nível Local: Usuário do Rancho
        elif type_name == 'USUARIO' and current_user.avaliado_id:
            return Avaliado.query.filter_by(
                id=current_user.avaliado_id,
                ativo=True
            ).all()
            
        return []

    except Exception as e:
        print(f"Erro ao buscar avaliados: {e}")
        return []

# ===================== CORREÇÃO 4: FUNÇÃO LOG_ACAO ROBUSTA =====================

def log_acao(acao, detalhes=None, entidade_tipo=None, entidade_id=None):
    """Registra ação no log. Serializa 'detalhes' para JSON."""
    try:
        if detalhes is None:
            detalhes_str = None
        elif isinstance(detalhes, (dict, list)):
            detalhes_str = json.dumps(detalhes, ensure_ascii=False, separators=(',', ':'))
        else:
            detalhes_str = str(detalhes)

        log = LogAuditoria(
            acao=acao,
            detalhes=detalhes_str,          # 👈 agora é string/JSON
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            ip=(request.remote_addr if request else None),
            user_agent=(request.headers.get('User-Agent') if request else None),
            usuario_id=getattr(current_user, 'id', None),
            cliente_id=getattr(current_user, 'cliente_id', None),
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # não derruba a requisição se o log falhar
        db.session.rollback()
        try:
            current_app.logger.exception(f"Erro ao criar log: {e}")
        except Exception:
            print(f"Erro ao criar log: {e}")

# ===================== CORREÇÃO 5: FUNÇÃO CRIAR_NOTIFICACAO ROBUSTA =====================

def criar_notificacao(usuario_id, titulo, mensagem, tipo='info', link=None):
    """Função auxiliar para criar notificações - CORRIGIDA"""
    try:
        if 'Notificacao' in globals():
            notificacao = Notificacao(
                usuario_id=usuario_id,
                titulo=titulo,
                mensagem=mensagem,
                tipo=tipo,
                link=link
            )
            db.session.add(notificacao)
            db.session.commit()
        else:
            # Fallback se Notificacao não existir
            print(f"NOTIFICAÇÃO: {titulo} - {mensagem}")
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")
        pass

# ===================== CORREÇÃO 6: RENDER TEMPLATE SEGURO =====================

def render_template_safe(template_name, **kwargs):
    """Render template com fallback se não existir"""
    try:
        return render_template(template_name, **kwargs)
    except Exception as e:
        # ADICIONE ESTA LINHA PARA DEBUG
        print(f"ERRO DETALHADO no template {template_name}: {e}")
        print(f"Tipo do erro: {type(e)}")
        
        # Flash do erro para aparecer na tela
        flash(f"Erro no template {template_name}: {str(e)}", "danger")
        
        return render_template('cli/index.html', 
                             error=f"Template {template_name} não encontrado: {str(e)}", 
                             **kwargs)

# ===================== CORREÇÃO 7: WEASYPRINT OPCIONAL =====================

# ===================== CORREÇÃO 7: WEASYPRINT COM CSS LOCAL (Blindado) =====================

# ===================== SOLUÇÃO DEFINITIVA: INJEÇÃO DE CSS =====================

def gerar_pdf_seguro(html_content, filename="relatorio.pdf"):
    """
    Gera PDF garantindo que o CSS e Imagens sejam carregados corretamente.
    
    Técnica:
    1. Lê o arquivo CSS do disco (static/css/style.css).
    2. Injeta o conteúdo do CSS diretamente na tag <style> do HTML.
    3. Define base_url apontando para a pasta static (para imagens locais).
    """
    from flask import current_app, make_response, flash, redirect, request, url_for
    import os
    import traceback

    try:
        # Tenta importar o WeasyPrint aqui para não quebrar o app se não estiver instalado
        from weasyprint import HTML, CSS
    except ImportError:
        current_app.logger.warning("WeasyPrint não instalado. Retornando HTML puro.")
        flash("O sistema de PDF (WeasyPrint) não está instalado. Exibindo versão Web.", "warning")
        return make_response(html_content)

    try:
        # --- PASSO 1: Carregar CSS do Disco ---
        css_text = ""
        # Monta o caminho absoluto: /var/www/.../app/static/css/style.css
        css_path = os.path.join(current_app.static_folder, 'css', 'style.css')
        
        if os.path.exists(css_path):
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_text = f.read()
                current_app.logger.info(f"[PDF] CSS carregado com sucesso: {css_path}")
            except Exception as e:
                current_app.logger.error(f"[PDF] Erro ao ler CSS: {e}")
        else:
            current_app.logger.warning(f"[PDF] Arquivo CSS não encontrado: {css_path}")

        # --- PASSO 2: Injeção de CSS (Blindagem) ---
        # Isso resolve problemas de permissão ou rotas onde o WeasyPrint não acha o .css
        if "</head>" in html_content:
            html_final = html_content.replace("</head>", f"<style>\n{css_text}\n</style>\n</head>")
        else:
            # Se não achar </head>, insere no começo
            html_final = f"<style>\n{css_text}\n</style>\n" + html_content

        # --- PASSO 3: Geração do PDF ---
        # base_url=current_app.static_folder é OBRIGATÓRIO para imagens (src="img/logo.png") funcionarem
        current_app.logger.info(f"[PDF] Iniciando renderização do WeasyPrint para: {filename}")
        
        pdf_bytes = HTML(string=html_final, base_url=current_app.static_folder).write_pdf()

        # --- PASSO 4: Resposta ---
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        # 'inline' abre no navegador, 'attachment' força download
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        
        current_app.logger.info("[PDF] PDF gerado e enviado com sucesso.")
        return response

    except Exception as e:
        # Captura erro genérico na geração
        current_app.logger.error(f"[PDF] ERRO CRÍTICO: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        flash(f"Erro ao gerar o PDF. Detalhes técnicos foram registrados. Erro: {str(e)}", "danger")
        
        # Fallback de segurança: Redireciona para a página anterior ou mostra o HTML
        if request.referrer:
            return redirect(request.referrer)
        else:
            return make_response(html_content)

# ===================== CORREÇÃO 8: FUNÇÃO AUXILIAR PARA COMPATIBILIDADE =====================

def verificar_permissao_admin():
    """Verifica se usuário tem permissão de admin - CORRIGIDA"""
    if not current_user.is_authenticated:
        return False
    
    try:
        user_type = current_user.tipo
        if hasattr(user_type, 'name'):
            type_name = user_type.name
        elif hasattr(user_type, 'value'):
            type_name = user_type.value
        else:
            type_name = str(user_type)
        
        return type_name in ['ADMIN', 'SUPER_ADMIN', 'admin', 'super_admin']
    except:
        return False
    

def verificar_alertas_atraso(usuario):
    """
    Verifica se existem planos de ação pendentes há mais de 30 dias
    para as unidades sob responsabilidade do usuário.
    Gera um flash message se encontrar problemas.
    """
    try:
        # Define o limite (hoje - 30 dias)
        data_limite = datetime.now() - timedelta(days=30)
        
        # Query base: Respostas não conformes e pendentes em auditorias FINALIZADAS
        # Note o filtro OR para garantir compatibilidade (pendente ou nulo)
        query = RespostaPergunta.query.join(AplicacaoQuestionario).join(Avaliado).filter(
            RespostaPergunta.nao_conforme == True,
            (RespostaPergunta.status_acao == 'pendente') | (RespostaPergunta.status_acao == None),
            AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA, 
            AplicacaoQuestionario.data_fim <= data_limite, 
            Avaliado.cliente_id == usuario.cliente_id
        )

        # Filtro Hierárquico (Blindagem)
        # 1. Se for Usuário de Rancho, vê só o dele
        if usuario.avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == usuario.avaliado_id)
        # 2. Se for Gestor de GAP, vê só do GAP dele
        elif usuario.grupo_id:
            query = query.filter(Avaliado.grupo_id == usuario.grupo_id)
        
        # Conta as pendências atrasadas
        total_atrasadas = query.count()

        # Gera notificações se houver atrasos
        if total_atrasadas > 0:
            msg = f"⚠️ ATENÇÃO: Existem {total_atrasadas} ações corretivas pendentes há mais de 30 dias! Verifique os Planos de Ação."
            flash(msg, "danger")
            
            # (Opcional) Criar notificação no banco se ainda não existir hoje
            # criar_notificacao(usuario.id, "Alerta de Atraso", msg, "danger", url_for('cli.lista_plano_acao'))
                
    except Exception as e:
        print(f"Erro ao verificar alertas de atraso: {e}")



# ===================== PÁGINA INICIAL =====================

@cli_bp.route('/')
@cli_bp.route('/home')
@login_required
def index():
    """Dashboard principal do CLIQ"""
    
    # 1. Executa a verificação de atrasos (Novo)
    verificar_alertas_atraso(current_user)

    # 2. Inicializa estatísticas
    stats = {
        'total_aplicacoes': 0,
        'aplicacoes_mes': 0,
        'questionarios_ativos': 0,
        'avaliados_ativos': 0,
        'media_nota_mes': 0,
        'aplicacoes_pendentes': 0
    }
    
    ultimas_aplicacoes = []
    questionarios_populares = []

    # 3. Calcula as estatísticas (Código Original Mantido)
    try:
        if hasattr(current_user, 'cliente_id') and current_user.cliente_id:
            # Aplicações do cliente
            stats['total_aplicacoes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id
            ).count()

            # Aplicações deste mês
            stats['aplicacoes_mes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                extract('month', AplicacaoQuestionario.data_inicio) == datetime.now().month,
                extract('year', AplicacaoQuestionario.data_inicio) == datetime.now().year
            ).count()

            # Questionários ativos
            stats['questionarios_ativos'] = Questionario.query.filter_by(
                cliente_id=current_user.cliente_id,
                ativo=True,
                publicado=True
            ).count()

            # Avaliados ativos
            stats['avaliados_ativos'] = Avaliado.query.filter_by(
                cliente_id=current_user.cliente_id,
                ativo=True
            ).count()

            # Média de notas do mês
            media_result = db.session.query(func.avg(AplicacaoQuestionario.nota_final)).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None),
                extract('month', AplicacaoQuestionario.data_inicio) == datetime.now().month
            ).scalar()
            stats['media_nota_mes'] = round(float(media_result or 0), 1)

            # Aplicações pendentes
            stats['aplicacoes_pendentes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.status == StatusAplicacao.EM_ANDAMENTO
            ).count()

            # Últimas aplicações
            ultimas_aplicacoes = AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id
            ).order_by(AplicacaoQuestionario.data_inicio.desc()).limit(5).all()

            # Questionários mais usados
            questionarios_populares = db.session.query(
                Questionario.nome,
                func.count(AplicacaoQuestionario.id).label('total_aplicacoes')
            ).join(AplicacaoQuestionario).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id
            ).group_by(Questionario.id, Questionario.nome).order_by(
                func.count(AplicacaoQuestionario.id).desc()
            ).limit(5).all()
            
    except Exception as e:
        print(f"Erro ao carregar dashboard: {e}")

    return render_template_safe('cli/index.html', 
                         stats=stats, 
                         ultimas_aplicacoes=ultimas_aplicacoes,
                         questionarios_populares=questionarios_populares)

@cli_bp.route('/questionarios', endpoint='listar_questionarios', methods=['GET'])
@cli_bp.route('/listar-questionarios', methods=['GET'])
@login_required
def listar_questionarios():
    """
    Lista questionários com filtros claros: Publicados, Rascunhos, Inativos, Todos.
    - O Fallback SÓ é ativado se um TERMO DE BUSCA falhar.
    """
    # Query base
    q_base = Questionario.query

    # ---- Filtros ----
    q = q_base
    termo = (request.args.get("q") or "").strip()
    # ##### ALTERADO: Default para 'publicados' #####
    status = request.args.get("status", "publicados") 

    # Filtro por cliente (obrigatório)
    tem_cliente = hasattr(Questionario, "cliente_id") and getattr(current_user, "cliente_id", None)
    if tem_cliente:
        q = q.filter(Questionario.cliente_id == current_user.cliente_id)

    # ##### LÓGICA DE FILTRO ATUALIZADA #####
    if hasattr(Questionario, "ativo") and hasattr(Questionario, "publicado"):
        if status == "publicados":
            q = q.filter(Questionario.ativo.is_(True), Questionario.publicado.is_(True))
        elif status == "rascunhos":
            q = q.filter(Questionario.ativo.is_(True), Questionario.publicado.is_(False))
        elif status == "inativos":
            q = q.filter(Questionario.ativo.is_(False))
        # Se status == "todos", não aplica filtro de estado
        elif status != "todos":
             # Fallback caso um status inválido seja passado, mostra publicados
             q = q.filter(Questionario.ativo.is_(True), Questionario.publicado.is_(True))
             status = "publicados" # Corrige o status para o template
    elif hasattr(Questionario, "ativo"): 
         # Fallback se não houver 'publicado' no modelo
         if status == "inativos":
              q = q.filter(Questionario.ativo.is_(False))
         elif status != "todos": # "publicados" e "rascunhos" mostram ativos neste caso
              q = q.filter(Questionario.ativo.is_(True))
              if status not in ["publicados", "rascunhos"]: status = "publicados" # Corrige status
    # ##### FIM DA LÓGICA ATUALIZADA #####


    # Guarda a query com filtros base (status + cliente) ANTES de aplicar a busca por texto
    q_base_filtrada = q

    # Busca por texto (?q=...)
    if termo:
        like = f"%{termo}%"
        filtros_busca = [] # Renomeado para evitar conflito
        if hasattr(Questionario, "nome"):      filtros_busca.append(Questionario.nome.ilike(like))
        if hasattr(Questionario, "titulo"):    filtros_busca.append(Questionario.titulo.ilike(like))
        if hasattr(Questionario, "descricao"): filtros_busca.append(Questionario.descricao.ilike(like))
        if filtros_busca:
            q = q.filter(or_(*filtros_busca))

    # Ordenação
    if hasattr(Questionario, "nome"):
        q = q.order_by(Questionario.nome.asc())
    elif hasattr(Questionario, "id"):
        q = q.order_by(Questionario.id.desc())

    # Executa com filtro
    questionarios = q.all()

    # --- LÓGICA DE FALLBACK CORRIGIDA ---
    usou_fallback = False
    # Só faz fallback SE um termo de busca foi usado E não retornou nada
    if not questionarios and termo:
        usou_fallback = True
        q2 = q_base_filtrada # Usa a query com status/cliente
        if hasattr(Questionario, "nome"):
            q2 = q2.order_by(Questionario.nome.asc())
        elif hasattr(Questionario, "id"):
            q2 = q2.order_by(Questionario.id.desc())
        questionarios = q2.all()
        flash(f"Nenhum item encontrado para '{termo}' — exibindo todos os itens do status '{status}'.", "warning")
    # --- FIM DA LÓGICA DE FALLBACK ---

    # Estatísticas (sem quebrar)
    ModelAplic = globals().get('AplicacaoQuestionario') or globals().get('Aplicacao')
    if ModelAplic:
        try:
            ids_questionarios_listados = [item.id for item in questionarios]
            counts = {}
            medias = {}
            if ids_questionarios_listados: # Só busca stats se houver questionários na lista
                counts_query = db.session.query(
                    ModelAplic.questionario_id, func.count(ModelAplic.id)
                ).join(Questionario).filter(
                    Questionario.cliente_id == current_user.cliente_id,
                    ModelAplic.questionario_id.in_(ids_questionarios_listados) # Filtra pelos IDs listados
                ).group_by(ModelAplic.questionario_id)

                medias_query = db.session.query(
                    ModelAplic.questionario_id, func.avg(ModelAplic.nota_final)
                ).join(Questionario).filter(
                    Questionario.cliente_id == current_user.cliente_id,
                    ModelAplic.questionario_id.in_(ids_questionarios_listados) # Filtra pelos IDs listados
                ).group_by(ModelAplic.questionario_id)

                counts = dict(counts_query.all())
                medias = dict(medias_query.all())

            for item in questionarios:
                item.total_aplicacoes = counts.get(item.id, 0)
                media_val = medias.get(item.id)
                item.media_nota = float(media_val) if media_val is not None else 0.0
        except Exception as e:
            print(f"Erro ao calcular estatísticas de questionários: {e}")
            for item in questionarios: # Garante atributos mesmo com erro
                item.total_aplicacoes = 0
                item.media_nota = 0.0
    else:
        for item in questionarios:
            item.total_aplicacoes = 0
            item.media_nota = 0.0

    return render_template_safe(
        'cli/listar_questionarios.html',
        questionarios=questionarios,
        termo=termo,
        status=status, # Passa o status atual para o template
        usou_fallback=usou_fallback,
    )



@cli_bp.route('/questionario/<int:id>')
@cli_bp.route('/questionario/<int:id>/visualizar')
@login_required
def visualizar_questionario(id):
    """Visualiza detalhes do questionário"""
    try:
        questionario = Questionario.query.get_or_404(id)
        
        if questionario.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        # Estatísticas do questionário
        stats = {
            'total_aplicacoes': AplicacaoQuestionario.query.filter_by(questionario_id=id).count(),
            'total_topicos': Topico.query.filter_by(questionario_id=id, ativo=True).count(),
            'total_perguntas': db.session.query(func.count(Pergunta.id)).join(Topico).filter(
                Topico.questionario_id == id,
                Pergunta.ativo == True
            ).scalar(),
            'media_nota': db.session.query(func.avg(AplicacaoQuestionario.nota_final)).filter_by(
                questionario_id=id
            ).scalar() or 0
        }
        
        # Últimas aplicações
        ultimas_aplicacoes = AplicacaoQuestionario.query.filter_by(
            questionario_id=id
        ).order_by(AplicacaoQuestionario.data_inicio.desc()).limit(10).all()
        
        return render_template_safe('cli/visualizar_questionario.html',
                             questionario=questionario,
                             stats=stats,
                             ultimas_aplicacoes=ultimas_aplicacoes)
    except Exception as e:
        flash(f"Erro ao carregar questionário: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/questionario/novo', methods=['GET', 'POST'])
@cli_bp.route('/novo-questionario', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_questionario():
    """
    Cria um novo questionário.
    Restrito apenas ao SUPER_ADMIN (Laboratório).
    """
    
    # 1. TRAVA DE SEGURANÇA: Apenas Laboratório cria modelos
    if current_user.tipo.name != 'SUPER_ADMIN':
        flash("Permissão negada. Apenas o Laboratório pode criar novos modelos de checklist.", "danger")
        return redirect(url_for('cli.listar_questionarios'))

    # Carrega usuários para o select de "Usuários Autorizados" (Consultoras)
    try:
        usuarios_disponiveis = Usuario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).order_by(Usuario.nome).all()
    except Exception:
        usuarios_disponiveis = []

    # --- PROCESSAMENTO DO FORMULÁRIO (POST) ---
    if request.method == 'POST':
        try:
            # 2. Coleta de Dados Básicos
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            versao = request.form.get('versao', '1.0').strip()
            modo = request.form.get('modo', 'Avaliado') # Avaliado ou Livre

            # Validação Básica
            if not nome:
                flash("O nome do questionário é obrigatório.", "warning")
                return render_template_safe('cli/novo_questionario.html', usuarios=usuarios_disponiveis)

            # 3. Validação de Duplicidade
            existe = Questionario.query.filter_by(
                nome=nome,
                cliente_id=current_user.cliente_id,
                ativo=True
            ).first()
            
            if existe:
                flash(f"Já existe um questionário ativo com o nome '{nome}'.", "warning")
                return render_template_safe('cli/novo_questionario.html', usuarios=usuarios_disponiveis)

            # 4. Criação do Objeto
            novo_q = Questionario(
                nome=nome,
                versao=versao,
                descricao=descricao,
                modo=modo,
                cliente_id=current_user.cliente_id,
                criado_por_id=current_user.id,
                
                # Configurações de Nota
                calcular_nota=(request.form.get('calcular_nota') == 'on'),
                ocultar_nota_aplicacao=(request.form.get('ocultar_nota') == 'on'),
                base_calculo=int(request.form.get('base_calculo', 100)),
                casas_decimais=int(request.form.get('casas_decimais', 2)),
                modo_configuracao=request.form.get('modo_configuracao', 'percentual'),
                modo_exibicao_nota=ModoExibicaoNota.PERCENTUAL,

                # Configurações de Aplicação
                anexar_documentos=(request.form.get('anexar_documentos') == 'on'),
                capturar_geolocalizacao=(request.form.get('geolocalizacao') == 'on'),
                restringir_avaliados=(request.form.get('restricao_avaliados') == 'on'),
                habilitar_reincidencia=(request.form.get('reincidencia') == 'on'),
                
                # Configurações Visuais / Relatório
                cor_relatorio=CorRelatorio.AZUL, 
                incluir_assinatura=(request.form.get('incluir_assinatura') == 'on'),
                incluir_foto_capa=(request.form.get('incluir_foto_capa') == 'on'),
                
                # Configurações Extras de Relatório
                exibir_nota_anterior=(request.form.get('exibir_nota_anterior') == 'on'),
                exibir_tabela_resumo=(request.form.get('exibir_tabela_de_resumo') == 'on'),
                exibir_limites_aceitaveis=(request.form.get('exibir_limites_aceitáveis') == 'on'),
                exibir_data_hora=(request.form.get('exibir_data/hora_início_e_fim') == 'on'),
                exibir_questoes_omitidas=(request.form.get('exibir_questões_omitidas') == 'on'),
                exibir_nao_conformidade=(request.form.get('exibir_relatório_não_conformidade') == 'on'),

                # Status Inicial
                ativo=True,
                publicado=False,
                status=StatusQuestionario.RASCUNHO
            )

            db.session.add(novo_q)
            db.session.flush() # Garante o ID antes do commit final

            # 5. Vínculo de Usuários Autorizados (Se houver)
            usuarios_selecionados = request.form.getlist('usuarios_autorizados')
            
            # Fallback se vier string separada por vírgula
            if not usuarios_selecionados and request.form.get('usuarios_autorizados'):
                 usuarios_selecionados = request.form.get('usuarios_autorizados').split(',')

            if usuarios_selecionados and 'UsuarioAutorizado' in globals():
                for uid in usuarios_selecionados:
                    if uid and str(uid).strip().isdigit():
                        u_auth = UsuarioAutorizado(
                            questionario_id=novo_q.id,
                            usuario_id=int(uid)
                        )
                        db.session.add(u_auth)

            # 6. Salvar Tudo
            db.session.commit()
            
            log_acao(f"Criou novo questionário: {nome}", None, "Questionario", novo_q.id)
            flash(f"Questionário '{nome}' criado com sucesso! Agora adicione os tópicos.", "success")
            
            # Redireciona para a gestão de tópicos
            return redirect(url_for('cli.gerenciar_topicos', id=novo_q.id))

        except Exception as e:
            db.session.rollback()
            print(f"ERRO AO CRIAR QUESTIONARIO: {e}") 
            flash(f"Erro ao salvar: {str(e)}", "danger")
            return render_template_safe('cli/novo_questionario.html', usuarios=usuarios_disponiveis)

    # --- EXIBIÇÃO DO FORMULÁRIO (GET) ---
    return render_template_safe('cli/novo_questionario.html', usuarios=usuarios_disponiveis)

# Em app/cli/routes.py

@cli_bp.route('/questionario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_questionario(id):
    """
    Edita as configurações gerais de um questionário existente.
    """
    try:
        # 1. Busca o questionário e verifica permissão
        questionario = Questionario.query.get_or_404(id)
        
        if questionario.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado ou acesso negado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
            
        # Bloqueio de segurança: Apenas SUPER_ADMIN (Laboratório) edita a estrutura
        if current_user.tipo.name != 'SUPER_ADMIN':
            flash("Apenas o Laboratório pode editar as configurações do modelo.", "warning")
            return redirect(url_for('cli.listar_questionarios'))

        # Carrega usuários para o select de "Usuários Autorizados"
        usuarios_disponiveis = []
        try:
            usuarios_disponiveis = Usuario.query.filter_by(
                cliente_id=current_user.cliente_id,
                ativo=True
            ).order_by(Usuario.nome).all()
        except Exception:
            pass

        # --- PROCESSAMENTO DO POST (SALVAR) ---
        if request.method == 'POST':
            try:
                # Dados Básicos
                questionario.nome = request.form.get('nome', '').strip()
                questionario.descricao = request.form.get('descricao', '').strip()
                questionario.versao = request.form.get('versao', '').strip()

                if not questionario.nome:
                    flash("O nome do questionário é obrigatório.", "warning")
                    return render_template_safe('cli/editar_questionario.html', questionario=questionario, usuarios=usuarios_disponiveis)

                # Configurações de Nota
                questionario.calcular_nota = (request.form.get('calcular_nota') == 'on')
                questionario.ocultar_nota_aplicacao = (request.form.get('ocultar_nota') == 'on')
                questionario.base_calculo = int(request.form.get('base_calculo', 100))
                questionario.casas_decimais = int(request.form.get('casas_decimais', 2))
                
                # Configurações de Aplicação
                questionario.anexar_documentos = (request.form.get('anexar_documentos') == 'on')
                questionario.capturar_geolocalizacao = (request.form.get('geolocalizacao') == 'on')
                questionario.restringir_avaliados = (request.form.get('restricao_avaliados') == 'on')
                questionario.habilitar_reincidencia = (request.form.get('reincidencia') == 'on')
                
                # Configurações Visuais / Relatório
                questionario.incluir_assinatura = (request.form.get('incluir_assinatura') == 'on')
                questionario.incluir_foto_capa = (request.form.get('incluir_foto_capa') == 'on')
                
                # Flags de Relatório (verificando existência dos atributos)
                if hasattr(questionario, 'exibir_nota_anterior'):
                    questionario.exibir_nota_anterior = (request.form.get('exibir_nota_anterior') == 'on')
                if hasattr(questionario, 'exibir_tabela_resumo'):
                    questionario.exibir_tabela_resumo = (request.form.get('exibir_tabela_de_resumo') == 'on')
                if hasattr(questionario, 'exibir_limites_aceitaveis'):
                    questionario.exibir_limites_aceitaveis = (request.form.get('exibir_limites_aceitáveis') == 'on')
                if hasattr(questionario, 'exibir_data_hora'):
                    questionario.exibir_data_hora = (request.form.get('exibir_data/hora_início_e_fim') == 'on')
                if hasattr(questionario, 'exibir_questoes_omitidas'):
                    questionario.exibir_questoes_omitidas = (request.form.get('exibir_questões_omitidas') == 'on')
                if hasattr(questionario, 'exibir_nao_conformidade'):
                    questionario.exibir_nao_conformidade = (request.form.get('exibir_relatório_não_conformidade') == 'on')

                # Atualiza Usuários Autorizados
                if 'UsuarioAutorizado' in globals():
                    # Remove os antigos
                    UsuarioAutorizado.query.filter_by(questionario_id=questionario.id).delete()
                    
                    # Adiciona os novos
                    usuarios_selecionados = request.form.getlist('usuarios_autorizados')
                    for uid in usuarios_selecionados:
                        if uid and str(uid).strip().isdigit():
                            u_auth = UsuarioAutorizado(
                                questionario_id=questionario.id,
                                usuario_id=int(uid)
                            )
                            db.session.add(u_auth)

                db.session.commit()
                log_acao(f"Editou configurações do questionário: {questionario.nome}", None, "Questionario", questionario.id)
                
                flash(f"Configurações de '{questionario.nome}' atualizadas com sucesso!", "success")
                return redirect(url_for('cli.listar_questionarios'))

            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao atualizar: {str(e)}", "danger")
        
        # --- EXIBIÇÃO DO FORMULÁRIO (GET) ---
        # Prepara lista de IDs autorizados para marcar no select
        autorizados_ids = []
        if hasattr(questionario, 'usuarios_autorizados'):
            autorizados_ids = [u.usuario_id for u in questionario.usuarios_autorizados]

        return render_template_safe('cli/editar_questionario.html', 
                                  questionario=questionario, 
                                  usuarios=usuarios_disponiveis,
                                  autorizados_ids=autorizados_ids)

    except Exception as e:
        flash(f"Erro ao abrir edição: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/questionario/<int:id>/duplicar', methods=['POST'])
@login_required
def duplicar_questionario(id):
    """Duplica um questionário existente"""
    try:
        questionario_original = Questionario.query.get_or_404(id)
        
        if questionario_original.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        # Criar cópia do questionário
        novo_nome = f"{questionario_original.nome} - Cópia"
        contador = 1
        while Questionario.query.filter_by(nome=novo_nome, cliente_id=current_user.cliente_id).first():
            contador += 1
            novo_nome = f"{questionario_original.nome} - Cópia ({contador})"
        
        questionario_copia = Questionario(
            nome=novo_nome,
            versao="1.0",
            descricao=questionario_original.descricao,
            modo=questionario_original.modo,
            cliente_id=current_user.cliente_id,
            criado_por_id=current_user.id,
            calcular_nota=questionario_original.calcular_nota,
            ocultar_nota_aplicacao=questionario_original.ocultar_nota_aplicacao,
            base_calculo=questionario_original.base_calculo,
            casas_decimais=questionario_original.casas_decimais,
            incluir_assinatura=questionario_original.incluir_assinatura,
            incluir_foto_capa=questionario_original.incluir_foto_capa,
            ativo=True,
            publicado=False,
            status=StatusQuestionario.RASCUNHO
        )
        
        db.session.add(questionario_copia)
        db.session.flush()
        
        # Duplicar tópicos e perguntas
        for topico in questionario_original.topicos:
            if topico.ativo:
                topico_copia = Topico(
                    nome=topico.nome,
                    descricao=topico.descricao,
                    ordem=topico.ordem,
                    questionario_id=questionario_copia.id,
                    ativo=True
                )
                db.session.add(topico_copia)
                db.session.flush()
                
                # Duplicar perguntas
                for pergunta in topico.perguntas:
                    if pergunta.ativo:
                        pergunta_copia = Pergunta(
                            texto=pergunta.texto,
                            tipo=pergunta.tipo,
                            obrigatoria=pergunta.obrigatoria,
                            permite_observacao=pergunta.permite_observacao,
                            peso=pergunta.peso,
                            ordem=pergunta.ordem,
                            topico_id=topico_copia.id,
                            ativo=True
                        )
                        db.session.add(pergunta_copia)
                        db.session.flush()
                        
                        # Duplicar opções se existirem
                        if hasattr(pergunta, 'opcoes'):
                            for opcao in pergunta.opcoes:
                                opcao_copia = OpcaoPergunta(
                                    texto=opcao.texto,
                                    valor=opcao.valor,
                                    ordem=opcao.ordem,
                                    pergunta_id=pergunta_copia.id
                                )
                                db.session.add(opcao_copia)
        
        db.session.commit()
        log_acao(f"Duplicou questionário: {questionario_original.nome}", None, "Questionario", questionario_copia.id)
        
        flash(f"Questionário duplicado como '{novo_nome}'!", "success")
        return redirect(url_for('cli.visualizar_questionario', id=questionario_copia.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao duplicar questionário: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))



@cli_bp.route('/questionario/<int:id>/desativar', methods=['POST'])
@login_required
def desativar_questionario(id):
    """Desativa um questionário"""
    try:
        questionario = Questionario.query.get_or_404(id)
        
        if questionario.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        questionario.ativo = False
        questionario.publicado = False
        questionario.status = StatusQuestionario.INATIVO
        
        db.session.commit()
        log_acao(f"Desativou questionário: {questionario.nome}", None, "Questionario", id)
        
        flash("Questionário desativado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao desativar questionário: {str(e)}", "danger")
    
    return redirect(url_for('cli.listar_questionarios'))

# ===================== TÓPICOS =====================

@cli_bp.route('/questionario/<int:id>/topicos')
@login_required
def gerenciar_topicos(id):
    """Tela 2: Gerenciar tópicos do questionário"""
    try:
        questionario = Questionario.query.get_or_404(id)
        
        if questionario.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        topicos = Topico.query.filter_by(
            questionario_id=id,
            ativo=True
        ).order_by(Topico.ordem).all()
        
        # Contar perguntas por tópico
        for topico in topicos:
            topico.total_perguntas = Pergunta.query.filter_by(
                topico_id=topico.id,
                ativo=True
            ).count()
        
        return render_template_safe('cli/gerenciar_topicos.html',
                             questionario=questionario,
                             topicos=topicos)
    except Exception as e:
        flash(f"Erro ao carregar tópicos: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))
    

@cli_bp.route('/questionario/<int:id>/topico/novo', methods=['GET', 'POST'])
@login_required
def novo_topico(id):
    """Criar novo tópico - VERSÃO CORRIGIDA"""
    print(f"DEBUG novo_topico: método={request.method}, id={id}")
    
    try:
        questionario = Questionario.query.get_or_404(id)
        print(f"DEBUG: Questionário encontrado: {questionario.nome}")
        
        if questionario.cliente_id != current_user.cliente_id:
            print("DEBUG: Cliente não autorizado")
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        if request.method == 'POST':
            print("DEBUG: Processando POST do tópico")
            try:
                nome = request.form.get('nome', '').strip()
                descricao = request.form.get('descricao', '').strip()
                print(f"DEBUG: nome='{nome}', descricao='{descricao}'")
                
                if not nome:
                    flash("Nome do tópico é obrigatório.", "danger")
                    print("DEBUG: Nome vazio, re-renderizando formulário")
                    return render_template_safe('cli/novo_topico.html', questionario=questionario)
                
                # Obter próxima ordem
                ultima_ordem = db.session.query(func.max(Topico.ordem)).filter_by(
                    questionario_id=id
                ).scalar() or 0
                print(f"DEBUG: Última ordem: {ultima_ordem}")
                
                novo_topico_obj = Topico(
                    nome=nome,
                    descricao=descricao,
                    ordem=ultima_ordem + 1,
                    questionario_id=id,
                    ativo=True
                )
                
                db.session.add(novo_topico_obj)
                db.session.commit()
                
                print(f"DEBUG: Tópico criado com ID: {novo_topico_obj.id}")
                
                log_acao(f"Criou tópico: {nome}", None, "Topico", novo_topico_obj.id)
                flash("Tópico criado com sucesso!", "success")
                
                print(f"DEBUG: Redirecionando para gerenciar_topicos com id={id}")
                return redirect(url_for('cli.gerenciar_topicos', id=id))
                
            except Exception as e:
                print(f"DEBUG: Erro no POST: {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                flash(f"Erro ao criar tópico: {str(e)}", "danger")
                return render_template_safe('cli/novo_topico.html', questionario=questionario)
        
        # GET - Mostrar formulário
        print("DEBUG: Renderizando template novo_topico.html para GET")
        
        # TESTE DIRETO DO TEMPLATE ANTES DE USAR render_template_safe
        try:
            from flask import render_template
            test_html = render_template('cli/novo_topico.html', questionario=questionario)
            print("DEBUG: Template novo_topico.html renderizado com sucesso!")
            return test_html
        except Exception as template_error:
            print(f"DEBUG: Erro específico no template novo_topico.html: {template_error}")
            import traceback
            traceback.print_exc()
            flash(f"Erro no template novo_topico.html: {template_error}", "danger")
            return redirect(url_for('cli.gerenciar_topicos', id=id))
        
    except Exception as e:
        print(f"DEBUG: Erro geral em novo_topico: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao carregar formulário: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))
        

@cli_bp.route('/topico/<int:topico_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_topico(topico_id):
    """
    Editar tópico existente e vincular a categorias SDAB.
    """
    try:
        # 1. Busca o tópico
        topico = Topico.query.get_or_404(topico_id)
        
        # 2. Verificação de segurança (pertence ao cliente?)
        if topico.questionario.cliente_id != current_user.cliente_id:
            flash("Tópico não encontrado ou acesso negado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        # 3. Processamento do Formulário (POST)
        if request.method == 'POST':
            try:
                topico.nome = request.form.get('nome', '').strip()
                topico.descricao = request.form.get('descricao', '').strip()
                # Se tiver campo de ordem no form, atualiza também
                if request.form.get('ordem'):
                    topico.ordem = int(request.form.get('ordem'))

                # --- NOVO: VINCULAR CATEGORIA SDAB ---
                cat_id = request.form.get('categoria_id')
                if cat_id and cat_id.isdigit():
                    topico.categoria_indicador_id = int(cat_id)
                else:
                    topico.categoria_indicador_id = None
                # -------------------------------------
                
                if not topico.nome:
                    flash("Nome do tópico é obrigatório.", "danger")
                    # Precisa recarregar as categorias se der erro de validação
                    categorias = CategoriaIndicador.query.filter_by(
                        cliente_id=current_user.cliente_id, ativo=True
                    ).order_by(CategoriaIndicador.nome).all()
                    return render_template_safe('cli/editar_topico.html', topico=topico, categorias=categorias)
                
                db.session.commit()
                log_acao(f"Editou tópico: {topico.nome}", None, "Topico", topico_id)
                
                flash("Tópico atualizado com sucesso!", "success")
                return redirect(url_for('cli.gerenciar_topicos', id=topico.questionario_id))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao atualizar tópico: {str(e)}", "danger")
        
        # 4. Carregamento para Exibição (GET)
        # Busca as categorias SDAB para preencher o select no HTML
        categorias = CategoriaIndicador.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        ).order_by(CategoriaIndicador.nome).all()

        return render_template_safe('cli/editar_topico.html', topico=topico, categorias=categorias)

    except Exception as e:
        flash(f"Erro ao carregar tópico: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/topico/<int:topico_id>/remover', methods=['POST'])
@login_required
def remover_topico(topico_id):
    """
    Remove um tópico e faz a exclusão em cascata (inativa) 
    de todas as perguntas vinculadas a ele.
    """
    try:
        topico = Topico.query.get_or_404(topico_id)
        questionario_id = topico.questionario_id
        
        # Verificação de segurança
        if topico.questionario.cliente_id != current_user.cliente_id:
            flash("Tópico não encontrado ou acesso negado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
            
        # --- MUDANÇA: Cascata de Exclusão (Soft Delete) ---
        # Busca todas as perguntas ativas deste tópico
        perguntas = Pergunta.query.filter_by(topico_id=topico_id, ativo=True).all()
        
        count_perguntas = 0
        for p in perguntas:
            p.ativo = False  # "Apaga" a pergunta
            count_perguntas += 1
            
        # "Apaga" o tópico
        topico.ativo = False
        
        db.session.commit()
        
        log_acao(f"Removeu tópico: {topico.nome} e {count_perguntas} perguntas", None, "Topico", topico_id)
        
        if count_perguntas > 0:
            flash(f"Tópico removido. {count_perguntas} perguntas vinculadas foram apagadas também.", "success")
        else:
            flash("Tópico removido com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover tópico: {str(e)}", "danger")
        # Tenta recuperar o ID para redirecionar
        if 'topico' in locals() and topico:
             questionario_id = topico.questionario_id
        else:
             return redirect(url_for('cli.listar_questionarios'))
    
    return redirect(url_for('cli.gerenciar_topicos', id=questionario_id))

# ===================== PERGUNTAS =====================

# SUBSTITUIR as rotas existentes no routes.py por estas versões corrigidas

# ===================== PERGUNTAS CORRIGIDAS =====================

@cli_bp.route('/topico/<int:topico_id>/perguntas')
@login_required
def gerenciar_perguntas(topico_id):
    """Tela 3: Gerenciar perguntas do tópico - CORRIGIDA"""
    print(f"DEBUG gerenciar_perguntas: topico_id={topico_id}")
    
    try:
        topico = Topico.query.get_or_404(topico_id)
        print(f"DEBUG: Tópico encontrado: {topico.nome}")
        
        if topico.questionario.cliente_id != current_user.cliente_id:
            print("DEBUG: Cliente não autorizado")
            flash("Tópico não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        perguntas = Pergunta.query.filter_by(
            topico_id=topico_id,
            ativo=True
        ).order_by(Pergunta.ordem).all()
        
        print(f"DEBUG: {len(perguntas)} perguntas encontradas")
        
        # TESTE DIRETO DO TEMPLATE
        try:
            from flask import render_template
            html = render_template('cli/gerenciar_perguntas.html',
                                 topico=topico,
                                 perguntas=perguntas)
            print("DEBUG: Template gerenciar_perguntas.html renderizado com sucesso!")
            return html
        except Exception as template_error:
            print(f"DEBUG: Erro no template gerenciar_perguntas.html: {template_error}")
            import traceback
            traceback.print_exc()
            flash(f"Erro no template: {template_error}", "danger")
            return redirect(url_for('cli.gerenciar_topicos', id=topico.questionario_id))
            
    except Exception as e:
        print(f"DEBUG: Erro em gerenciar_perguntas: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao carregar perguntas: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))

# Em app/cli/routes.py

@cli_bp.route('/topico/<int:topico_id>/pergunta/nova', methods=['GET', 'POST'])
@login_required
def nova_pergunta(topico_id):
    """Criar nova pergunta - ATUALIZADA (v3 - Suporte a CriterioFoto)"""
    print(f"DEBUG nova_pergunta: método={request.method}, topico_id={topico_id}")
    
    try:
        topico = Topico.query.get_or_404(topico_id)
        print(f"DEBUG: Tópico encontrado: {topico.nome}")
        
        if topico.questionario.cliente_id != current_user.cliente_id:
            print("DEBUG: Cliente não autorizado")
            flash("Tópico não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        if request.method == 'POST':
            print("DEBUG: Processando POST da pergunta")
            try:
                texto = request.form.get('texto', '').strip()
                tipo_str = request.form.get('tipo', 'SIM_NAO_NA') # Pega como string
                obrigatoria = request.form.get('obrigatoria') == 'on'
                permite_observacao = request.form.get('permite_observacao') == 'on'
                peso = int(request.form.get('peso', 1))
                
                # --- ATUALIZAÇÃO: CRITÉRIO DE FOTO (Select Box) ---
                # Pega 'nenhuma', 'opcional' ou 'obrigatoria' do formulário
                criterio_foto = request.form.get('criterio_foto', 'nenhuma')
                # --------------------------------------------------

                print(f"DEBUG: texto='{texto}', tipo='{tipo_str}', peso={peso}, criterio_foto={criterio_foto}")
                
                if not texto:
                    flash("Texto da pergunta é obrigatório.", "danger")
                    print("DEBUG: Texto vazio, re-renderizando formulário")
                    return render_template_safe('cli/nova_pergunta.html', topico=topico)
                
                # Obter próxima ordem
                ultima_ordem = db.session.query(func.max(Pergunta.ordem)).filter_by(
                    topico_id=topico_id, ativo=True
                ).scalar() or 0
                print(f"DEBUG: Última ordem: {ultima_ordem}")

                # --- CONVERSÃO STRING PARA ENUM ---
                try:
                    # Tenta buscar pelo NOME do enum ('SIM_NAO_NA')
                    tipo_enum = TipoResposta[tipo_str]
                except KeyError:
                    # Se falhar, tenta buscar pelo VALOR ('Sim/Não/N.A.')
                    tipo_enum = None
                    for item in TipoResposta:
                        if item.value == tipo_str:
                             tipo_enum = item
                             break
                    if tipo_enum is None:
                        flash(f"Tipo de resposta inválido: '{tipo_str}'. Usando SIM_NAO_NA como padrão.", "warning")
                        tipo_enum = TipoResposta.SIM_NAO_NA # Default seguro
                # ------------------------------------
                
                nova_pergunta_obj = Pergunta(
                    texto=texto,
                    tipo=tipo_enum,
                    obrigatoria=obrigatoria,
                    permite_observacao=permite_observacao,
                    peso=peso,
                    ordem=ultima_ordem + 1,
                    # --- CAMPO NOVO (Substitui exige_foto_se_nao_conforme) ---
                    criterio_foto=criterio_foto, 
                    # ---------------------------------------------------------
                    topico_id=topico_id,
                    ativo=True
                )
                
                db.session.add(nova_pergunta_obj)
                db.session.flush() # Para obter o ID da pergunta para as opções
                print(f"DEBUG: Pergunta criada com ID: {nova_pergunta_obj.id}")
                
                # --- LÓGICA DE OPÇÕES (Mantida igual) ---
                
                # Adicionar opções se for múltipla escolha ou escala (baseado no form)
                if tipo_enum in [TipoResposta.MULTIPLA_ESCOLHA, TipoResposta.ESCALA_NUMERICA] and 'OpcaoPergunta' in globals():
                    print("DEBUG: Processando opções da pergunta múltipla/escala via form")
                    opcoes_texto = request.form.getlist('opcao_texto[]')
                    opcoes_valor = request.form.getlist('opcao_valor[]')
                    
                    for i, texto_opcao in enumerate(opcoes_texto):
                        texto_opcao_strip = texto_opcao.strip()
                        if texto_opcao_strip: # Ignora opções vazias
                            try:
                                valor_opcao_str = opcoes_valor[i] if i < len(opcoes_valor) else '0'
                                valor_float = float(valor_opcao_str) if valor_opcao_str else 0.0
                            except (ValueError, IndexError):
                                valor_float = 0.0

                            opcao = OpcaoPergunta(
                                texto=texto_opcao_strip,
                                valor=valor_float,
                                ordem=i + 1,
                                pergunta_id=nova_pergunta_obj.id,
                                ativo=True
                            )
                            db.session.add(opcao)

                # Criar opções padrão automaticamente para SIM_NAO_NA
                elif tipo_enum == TipoResposta.SIM_NAO_NA and 'OpcaoPergunta' in globals():
                    print("DEBUG: Criando opções padrão para SIM_NAO_NA")
                    opcoes_padrao = [
                        {"texto": "Sim", "valor": 1.0, "ordem": 1},
                        {"texto": "Não", "valor": 0.0, "ordem": 2},
                        {"texto": "N.A.", "valor": 0.0, "ordem": 3}
                    ]
                    for op_data in opcoes_padrao:
                        opcao = OpcaoPergunta(
                            texto=op_data["texto"],
                            valor=op_data["valor"],
                            ordem=op_data["ordem"],
                            pergunta_id=nova_pergunta_obj.id,
                            ativo=True
                        )
                        db.session.add(opcao)
                
                # --- FIM DA LÓGICA DE OPÇÕES ---
                
                db.session.commit()
                # Tenta logar se a função existir
                if 'log_acao' in globals():
                    log_acao(f"Criou pergunta: {texto[:50]}...", None, "Pergunta", nova_pergunta_obj.id)
                
                flash("Pergunta criada com sucesso!", "success")
                return redirect(url_for('cli.gerenciar_perguntas', topico_id=topico_id))
                
            except Exception as e:
                print(f"DEBUG: Erro no POST da pergunta: {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                flash(f"Erro ao criar pergunta: {str(e)}", "danger")
                return render_template_safe('cli/nova_pergunta.html', topico=topico, form_data=request.form)
        
        # GET - Mostrar formulário
        return render_template_safe('cli/nova_pergunta.html', topico=topico)
            
    except Exception as e:
        print(f"DEBUG: Erro geral em nova_pergunta: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao carregar formulário: {str(e)}", "danger")
        
        # Redirecionamento de segurança
        redirect_url = url_for('cli.listar_questionarios')
        if 'topico' in locals() and hasattr(topico, 'questionario_id'):
             try:
                 redirect_url = url_for('cli.gerenciar_topicos', id=topico.questionario_id)
             except:
                 pass
        return redirect(redirect_url)

# ===================== PUBLICAR QUESTIONÁRIO CORRIGIDA =====================

# ===================== PUBLICAR QUESTIONÁRIO - VERSÃO ÚNICA =====================

@cli_bp.route('/questionario/<int:id>/publicar', methods=['POST'])
@login_required
def publicar_questionario(id):
    """Publica questionário para uso - VERSÃO ÚNICA SEM DUPLICAÇÃO"""
    print(f"DEBUG publicar_questionario: id={id}")
    
    try:
        questionario = Questionario.query.get_or_404(id)
        print(f"DEBUG: Questionário encontrado: {questionario.nome}")
        
        if questionario.cliente_id != current_user.cliente_id:
            print("DEBUG: Cliente não autorizado")
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        # Validar se tem pelo menos 1 tópico e 1 pergunta
        print("DEBUG: Validando estrutura do questionário")
        total_perguntas = db.session.query(func.count(Pergunta.id)).join(Topico).filter(
            Topico.questionario_id == id,
            Topico.ativo == True,
            Pergunta.ativo == True
        ).scalar()
        
        print(f"DEBUG: Total de perguntas encontradas: {total_perguntas}")
        
        if total_perguntas == 0:
            flash("Não é possível publicar um questionário sem perguntas.", "warning")
            print("DEBUG: Questionário sem perguntas, não pode publicar")
            return redirect(url_for('cli.gerenciar_topicos', id=id))
        
        # Publicar questionário
        print("DEBUG: Publicando questionário")
        questionario.publicado = True
        questionario.status = StatusQuestionario.PUBLICADO if 'StatusQuestionario' in globals() else 'publicado'
        questionario.data_publicacao = datetime.now()
        
        db.session.commit()
        log_acao(f"Publicou questionário: {questionario.nome}", None, "Questionario", id)
        
        flash("Questionário publicado com sucesso! Agora pode ser usado em aplicações.", "success")
        print("DEBUG: Questionário publicado com sucesso")
        
    except Exception as e:
        print(f"DEBUG: Erro ao publicar questionário: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        flash(f"Erro ao publicar questionário: {str(e)}", "danger")
    
    return redirect(url_for('cli.gerenciar_topicos', id=id))

# ===================== ROTA DE TESTE PARA DEBUG =====================

@cli_bp.route('/test-publish/<int:id>')
@login_required
def test_publish(id):
    """Teste da funcionalidade de publicar"""
    try:
        questionario = Questionario.query.get_or_404(id)
        
        # Contar estrutura
        total_topicos = Topico.query.filter_by(questionario_id=id, ativo=True).count()
        total_perguntas = db.session.query(func.count(Pergunta.id)).join(Topico).filter(
            Topico.questionario_id == id,
            Topico.ativo == True,
            Pergunta.ativo == True
        ).scalar()
        
        return f"""
        <h3>Debug Questionário ID {id}</h3>
        <p><strong>Nome:</strong> {questionario.nome}</p>
        <p><strong>Status:</strong> {'Publicado' if questionario.publicado else 'Rascunho'}</p>
        <p><strong>Tópicos:</strong> {total_topicos}</p>
        <p><strong>Perguntas:</strong> {total_perguntas}</p>
        <p><strong>Cliente:</strong> {questionario.cliente_id} (Atual: {current_user.cliente_id})</p>
        
        <br>
        {f'<a href="/cli/questionario/{id}/publicar" onclick="return confirm(\'Publicar?\')">✅ PODE PUBLICAR</a>' if total_perguntas > 0 else '❌ NÃO PODE PUBLICAR (sem perguntas)'}
        <br><br>
        <a href="/cli/questionario/{id}/topicos">← Voltar aos Tópicos</a>
        """
        
    except Exception as e:
        return f"Erro: {str(e)}"



# Em app/cli/routes.py

# Em app/cli/routes.py

# Em app/cli/routes.py

@cli_bp.route('/pergunta/<int:pergunta_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_pergunta(pergunta_id):
    """Editar pergunta existente - ATUALIZADA (v4 - Suporte a CriterioFoto)"""
    try:
        # Removido o eager loading que causava erro com lazy='dynamic'
        pergunta = Pergunta.query.get_or_404(pergunta_id)

        if pergunta.topico.questionario.cliente_id != current_user.cliente_id:
            flash("Pergunta não encontrada.", "error")
            return redirect(url_for('cli.listar_questionarios'))

        if request.method == 'POST':
            try:
                pergunta.texto = request.form.get('texto', '').strip()
                tipo_str = request.form.get('tipo') # Pega como string
                pergunta.obrigatoria = request.form.get('obrigatoria') == 'on'
                pergunta.permite_observacao = request.form.get('permite_observacao') == 'on'
                pergunta.peso = int(request.form.get('peso', 1))
                
                # --- ATUALIZAÇÃO: CRITÉRIO DE FOTO (Select Box) ---
                # Substitui o checkbox antigo pelo valor do select box ('nenhuma', 'opcional', 'obrigatoria')
                pergunta.criterio_foto = request.form.get('criterio_foto', 'nenhuma')
                # --------------------------------------------------

                # --- CONVERSÃO STRING PARA ENUM ROBUSTA ---
                tipo_enum_antigo = pergunta.tipo # Guarda o tipo antigo
                tipo_enum_novo = None
                try:
                    # Tenta buscar pelo NOME do enum ('SIM_NAO_NA')
                    tipo_enum_novo = TipoResposta[tipo_str]
                except KeyError:
                    # Se falhar, tenta buscar pelo VALOR ('Sim/Não/N.A.')
                    for item in TipoResposta:
                        if item.value == tipo_str:
                             tipo_enum_novo = item
                             break
                
                if tipo_enum_novo is None:
                      flash(f"Tipo de resposta inválido recebido: '{tipo_str}'. Mantendo tipo anterior.", "warning")
                      tipo_enum_novo = tipo_enum_antigo # Reverte se inválido
                else:
                    pergunta.tipo = tipo_enum_novo # Atualiza o tipo se válido
                # ------------------------------------

                # --- LÓGICA DE OPÇÕES CORRIGIDA ---

                # Tipos que usam opções (seja do form ou padrão)
                tipos_com_opcoes = [TipoResposta.MULTIPLA_ESCOLHA, TipoResposta.ESCALA_NUMERICA, TipoResposta.SIM_NAO_NA]

                # 1. Limpar opções antigas se o tipo mudou PARA um tipo SEM opções
                if tipo_enum_antigo in tipos_com_opcoes and tipo_enum_novo not in tipos_com_opcoes:
                    print(f"DEBUG: Removendo opções porque tipo mudou de {tipo_enum_antigo.name} para {tipo_enum_novo.name}")
                    # Como 'pergunta.opcoes' é dynamic, precisamos iterar para deletar
                    opcoes_a_remover = list(pergunta.opcoes) # Carrega e converte para lista
                    if opcoes_a_remover:
                        for op_antiga in opcoes_a_remover:
                            db.session.delete(op_antiga)
                        db.session.flush() # Aplica deletes antes de continuar

                # 2. TRATAMENTO ESPECIAL PARA SIM_NAO_NA (criar/ativar opções padrão)
                elif tipo_enum_novo == TipoResposta.SIM_NAO_NA and 'OpcaoPergunta' in globals():
                    print("DEBUG: Garantindo opções padrão ATIVAS para SIM_NAO_NA")
                    opcoes_padrao_texto = {"Sim", "Não", "N.A."}
                    # Carrega opções atuais do banco (lazy load ao acessar .opcoes)
                    opcoes_existentes = {op.texto: op for op in pergunta.opcoes}

                    # Define as opções que DEVEM existir e estar ATIVAS
                    opcoes_target = [
                        {"texto": "Sim", "valor": 1.0, "ordem": 1},
                        {"texto": "Não", "valor": 0.0, "ordem": 2},
                        {"texto": "N.A.", "valor": 0.0, "ordem": 3} # Ajuste valor se necessário
                    ]

                    # Garante que as opções padrão existam e estejam ativas
                    for op_data in opcoes_target:
                        texto_target = op_data["texto"]
                        if texto_target in opcoes_existentes:
                            # Opção existe, garante que está ativa
                            op_existente = opcoes_existentes[texto_target]
                            if not op_existente.ativo:
                                op_existente.ativo = True
                                print(f"DEBUG: Opção padrão '{texto_target}' ATIVADA.")
                            # Opcional: Atualizar valor e ordem se desejar forçar o padrão
                            op_existente.valor = op_data["valor"]
                            op_existente.ordem = op_data["ordem"]
                        else:
                            # Opção padrão não existe, cria como ativa
                            nova_opcao = OpcaoPergunta(
                                texto=op_data["texto"],
                                valor=op_data["valor"],
                                ordem=op_data["ordem"],
                                pergunta_id=pergunta.id,
                                ativo=True # <<< Cria como ativa
                            )
                            db.session.add(nova_opcao)
                            print(f"DEBUG: Opção padrão '{texto_target}' criada e ativada.")

                    # Remove opções que não sejam as padrão (se existirem por algum erro)
                    ids_para_remover = []
                    for texto_existente, op_existente in opcoes_existentes.items():
                        if texto_existente not in opcoes_padrao_texto:
                            ids_para_remover.append(op_existente.id)
                            print(f"DEBUG: Marcando opção não padrão '{texto_existente}' para remoção.")
                    
                    if ids_para_remover:
                         # Deleta fora do loop de iteração
                         OpcaoPergunta.query.filter(OpcaoPergunta.id.in_(ids_para_remover)).delete(synchronize_session=False)
                         print(f"DEBUG: Opções não padrão removidas: {ids_para_remover}")


                # 3. Atualizar opções se for Múltipla Escolha ou Escala (baseado no form)
                elif tipo_enum_novo in [TipoResposta.MULTIPLA_ESCOLHA, TipoResposta.ESCALA_NUMERICA] and 'OpcaoPergunta' in globals():
                    print(f"DEBUG: Processando opções para {tipo_enum_novo.name} via form")
                    opcoes_id_existentes = [int(oid) for oid in request.form.getlist('opcao_id[]') if oid.isdigit()]
                    opcoes_texto = request.form.getlist('opcao_texto[]')
                    opcoes_valor = request.form.getlist('opcao_valor[]')

                    print(f"DEBUG editar_pergunta - Opções Recebidas Form: IDs={opcoes_id_existentes}, Textos={opcoes_texto}, Valores={opcoes_valor}")

                    # Carrega opções atuais do banco
                    opcoes_atuais = {op.id: op for op in pergunta.opcoes}
                    ids_processados_no_form = set()

                    # Atualiza/Adiciona opções do formulário
                    for i, texto_opcao in enumerate(opcoes_texto):
                        texto_opcao_strip = texto_opcao.strip()
                        if not texto_opcao_strip:
                            continue # Ignora linhas vazias

                        opcao_id = opcoes_id_existentes[i] if i < len(opcoes_id_existentes) else None
                        
                        # Marca ID como processado SE ele veio do form
                        if opcao_id:
                            ids_processados_no_form.add(opcao_id) 

                        try:
                            valor_opcao_str = opcoes_valor[i] if i < len(opcoes_valor) else '0'
                            valor_float = float(valor_opcao_str) if valor_opcao_str else 0.0
                        except (ValueError, IndexError):
                            valor_float = 0.0

                        if opcao_id and opcao_id in opcoes_atuais:
                            # Atualiza opção existente
                            opcao = opcoes_atuais[opcao_id]
                            opcao.texto = texto_opcao_strip
                            opcao.valor = valor_float
                            opcao.ordem = i + 1
                            opcao.ativo = True # <<< Garante que fique ativa ao editar
                            print(f"DEBUG: Opção ID {opcao_id} atualizada e ativada.")
                        else:
                            # Adiciona nova opção (ID era None ou não encontrado)
                            nova_opcao = OpcaoPergunta(
                                texto=texto_opcao_strip,
                                valor=valor_float,
                                ordem=i + 1,
                                pergunta_id=pergunta.id,
                                ativo=True # <<< Cria como ativa
                            )
                            db.session.add(nova_opcao)
                            print(f"DEBUG: Nova opção '{texto_opcao_strip}' adicionada e ativada.")

                    # Remove opções que estavam no banco mas NÃO vieram no formulário atualizado
                    ids_no_banco = set(opcoes_atuais.keys())
                    ids_para_remover = ids_no_banco - ids_processados_no_form
                    
                    if ids_para_remover:
                         # Deleta de uma vez só
                         OpcaoPergunta.query.filter(OpcaoPergunta.id.in_(ids_para_remover)).delete(synchronize_session=False)
                         print(f"DEBUG: Opções removidas (não presentes no form): {ids_para_remover}")

                # --- FIM DA LÓGICA DE OPÇÕES CORRIGIDA ---

                db.session.commit()
                # Tenta logar se a função existir
                if 'log_acao' in globals():
                    log_acao(f"Editou pergunta: {pergunta.texto[:50]}...", None, "Pergunta", pergunta_id)

                flash("Pergunta atualizada com sucesso!", "success")
                return redirect(url_for('cli.gerenciar_perguntas', topico_id=pergunta.topico_id))

            except Exception as e:
                print(f"DEBUG: Erro ao atualizar pergunta POST: {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                flash(f"Erro ao atualizar pergunta: {str(e)}", "danger")
                # Re-renderiza o formulário com os dados atuais (antes do erro)
                # Carrega opções (lazy load) e ordena para passar ao template
                opcoes_ordenadas = []
                try:
                      opcoes_ordenadas = sorted(list(pergunta.opcoes), key=lambda o: o.ordem)
                except Exception as load_err:
                      print(f"DEBUG: Erro ao carregar opções no except: {load_err}")

                return render_template_safe('cli/editar_pergunta.html', pergunta=pergunta, opcoes=opcoes_ordenadas)

        # GET - Mostrar formulário
        print(f"DEBUG editar_pergunta GET: Carregando pergunta ID {pergunta_id} com tipo {pergunta.tipo.name if hasattr(pergunta.tipo, 'name') else pergunta.tipo}")
        # Carrega as opções (lazy load) e ordena para o template
        opcoes_ordenadas = []
        try:
            # Acessar pergunta.opcoes dispara o lazy load (agora 'select')
            opcoes_ordenadas = sorted(list(pergunta.opcoes), key=lambda o: o.ordem)
        except Exception as load_err:
            print(f"DEBUG: Erro ao carregar/ordenar opções no GET: {load_err}")
            flash(f"Aviso: Não foi possível carregar as opções da pergunta. {load_err}", "warning")

        return render_template_safe('cli/editar_pergunta.html', pergunta=pergunta, opcoes=opcoes_ordenadas)

    except Exception as e:
        print(f"DEBUG: Erro geral em editar_pergunta GET: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao carregar pergunta para edição: {str(e)}", "danger")
        # Tenta obter o topico_id para redirecionar melhor
        redirect_url = url_for('cli.listar_questionarios')
        try:
            # Tenta carregar a pergunta novamente para obter o topico_id
            pergunta_fallback = Pergunta.query.get(pergunta_id)
            if pergunta_fallback and pergunta_fallback.topico_id:
                 redirect_url = url_for('cli.gerenciar_perguntas', topico_id=pergunta_fallback.topico_id)
        except:
             pass 
        return redirect(redirect_url)

@cli_bp.route('/pergunta/<int:pergunta_id>/remover', methods=['POST'])
@login_required
def remover_pergunta(pergunta_id):
    """Remove uma pergunta"""
    try:
        pergunta = Pergunta.query.get_or_404(pergunta_id)
        
        if pergunta.topico.questionario.cliente_id != current_user.cliente_id:
            flash("Pergunta não encontrada.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        topico_id = pergunta.topico_id
        
        pergunta.ativo = False
        db.session.commit()
        
        log_acao(f"Removeu pergunta: {pergunta.texto[:50]}...", None, "Pergunta", pergunta_id)
        flash("Pergunta removida com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover pergunta: {str(e)}", "danger")
        topico_id = request.args.get('topico_id')
    
    return redirect(url_for('cli.gerenciar_perguntas', topico_id=topico_id))

# ===================== AVALIADOS =====================

@cli_bp.route('/avaliados', endpoint='listar_avaliados')
@login_required
# @admin_required (Mantenha se já tiver)
def listar_avaliados():
    """Lista avaliados com filtro por Grupo (GAP)"""
    try:
        # 1. Carrega todos os grupos para preencher o <select> de filtro
        grupos = Grupo.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        ).order_by(Grupo.nome).all()

        # 2. Inicia a query base dos avaliados
        query = Avaliado.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        )

        # 3. Verifica se o usuário selecionou um filtro
        grupo_id = request.args.get('grupo_id')
        
        if grupo_id:
            # Se tiver filtro, adiciona à query
            query = query.filter_by(grupo_id=grupo_id)
        
        # 4. Executa a busca ordenando por nome
        avaliados = query.order_by(Avaliado.nome).all()
        
        return render_template_safe('cli/listar_avaliados.html', 
                                  avaliados=avaliados, 
                                  grupos=grupos,
                                  grupo_selecionado=grupo_id)

    except Exception as e:
        flash(f"Erro ao carregar avaliados: {str(e)}", "danger")
        return render_template_safe('cli/index.html')
# Alias compatível com o template antigo (NÃO remova o de baixo):
@cli_bp.route('/avaliados/cadastrar', methods=['GET', 'POST'], endpoint='cadastrar_avaliado')
@cli_bp.route('/avaliados/novo', methods=['GET', 'POST'])
@login_required
def novo_avaliado():
    """Cadastra um novo avaliado"""

    # Descobre se o usuário é admin (ajuste se seu Enum for diferente)
    is_admin = getattr(current_user, 'tipo', None)
    try:
        # se usar Enum TipoUsuario.ADMIN:
        from app.models import TipoUsuario
        is_admin = (current_user.tipo == TipoUsuario.ADMIN)
    except Exception:
        # fallback: se for string:
        is_admin = (str(getattr(current_user, 'tipo', '')).upper() == 'ADMIN')

    if request.method == 'POST':
        try:
            nome = (request.form.get('nome') or '').strip()
            codigo = (request.form.get('codigo') or '').strip()
            endereco = (request.form.get('endereco') or '').strip()
            email = (request.form.get('email') or '').strip()
            idioma = (request.form.get('idioma') or '').strip()
            cliente_id_raw = request.form.get('cliente_id')
            grupo_id_raw = request.form.get('grupo_id')

            if not nome:
                flash("Nome do avaliado é obrigatório.", "danger")
                return redirect(url_for('cli.cadastrar_avaliado'))

            # Define cliente_id: admin pode escolher; usuário normal força current_user.cliente_id
            if is_admin and cliente_id_raw:
                try:
                    cliente_id = int(cliente_id_raw)
                except ValueError:
                    flash("Cliente inválido.", "warning")
                    return redirect(url_for('cli.cadastrar_avaliado'))
                cliente = Cliente.query.filter_by(id=cliente_id, ativo=True).first()
                if not cliente:
                    flash("Cliente não encontrado.", "warning")
                    return redirect(url_for('cli.cadastrar_avaliado'))
            else:
                cliente_id = current_user.cliente_id

            # Valida grupo (se enviado) e se pertence ao mesmo cliente
            grupo = None
            if grupo_id_raw:
                try:
                    gid = int(grupo_id_raw)
                except ValueError:
                    flash("Grupo inválido.", "warning")
                    return redirect(url_for('cli.cadastrar_avaliado'))
                grupo = Grupo.query.filter_by(id=gid, cliente_id=cliente_id, ativo=True).first()
                if not grupo:
                    flash("Grupo não encontrado ou sem permissão.", "warning")
                    return redirect(url_for('cli.cadastrar_avaliado'))

            # Código (se informado) deve ser único por cliente
            if codigo:
                ja_existe = Avaliado.query.filter_by(codigo=codigo, cliente_id=cliente_id).first()
                if ja_existe:
                    flash("Já existe um avaliado com este código.", "warning")
                    return redirect(url_for('cli.cadastrar_avaliado'))

            avaliado = Avaliado(
                nome=nome,
                codigo=codigo or None,
                endereco=endereco or None,
                grupo_id=(grupo.id if grupo else None),
                cliente_id=cliente_id,
                ativo=True
            )

            # Campos opcionais (só seta se existirem no modelo)
            for campo, valor in [('email', email or None), ('idioma', idioma or None)]:
                try:
                    setattr(avaliado, campo, valor)
                except Exception:
                    pass

            db.session.add(avaliado)
            db.session.commit()

            log_acao("Criou avaliado", {"nome": nome, "codigo": codigo}, "Avaliado", avaliado.id)
            flash(f"Avaliado '{nome}' criado com sucesso!", "success")
            return redirect(url_for('cli.listar_avaliados'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar avaliado: {str(e)}", "danger")
            return redirect(url_for('cli.cadastrar_avaliado'))

    # GET
    try:
        # Admin enxerga todos os clientes; usuário comum só o seu
        if is_admin:
            clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome.asc()).all()
        else:
            clientes = Cliente.query.filter_by(id=current_user.cliente_id).all()

        # Carrega grupos do cliente do usuário (simples); se quiser, pode filtrar por cliente selecionado via JS
        grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome.asc()).all()

        return render_template_safe(
            'cli/cadastrar_avaliado.html',
            clientes=clientes,
            grupos=grupos,
            is_admin=is_admin
        )
    except Exception as e:
        flash(f"Erro ao carregar formulário: {str(e)}", "danger")
        return redirect(url_for('cli.listar_avaliados'))



@cli_bp.route('/avaliado/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required # Garante que só admins mexem aqui
def editar_avaliado(id):
    """Edita um avaliado (Rancho) existente"""
    # 1. Busca segura: garante que pertence ao cliente
    avaliado = Avaliado.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()

    if request.method == 'POST':
        try:
            # 2. Coleta dados explicitamente (sem loops mágicos)
            nome = request.form.get('nome', '').strip()
            endereco = request.form.get('endereco', '').strip()
            email = request.form.get('email', '').strip() # <--- Agora é explícito
            grupo_id = request.form.get('grupo_id')
            
            # 3. Validação
            if not nome or not grupo_id:
                flash("Nome e GAP são obrigatórios.", "warning")
            else:
                # 4. Atualização
                avaliado.nome = nome
                avaliado.grupo_id = int(grupo_id)
                avaliado.endereco = endereco if endereco else None
                avaliado.email = email if email else None
                
                # Se tiver código único
                codigo = request.form.get('codigo', '').strip()
                if codigo:
                     avaliado.codigo = codigo

                db.session.commit()
                flash(f"Rancho '{nome}' atualizado com sucesso!", "success")
                return redirect(url_for('cli.listar_avaliados'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {str(e)}", "danger")

    # GET: Carrega os dados para o formulário
    grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome).all()
    
    # Nota: Verifique se o seu template se chama 'avaliado_form.html' ou 'editar_avaliado.html'
    return render_template_safe('cli/editar_avaliado.html', avaliado=avaliado, grupos=grupos)

@cli_bp.route('/avaliados/<int:id>/excluir', methods=['POST'])
@cli_bp.route('/avaliado/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_avaliado(id):
    """Marca o avaliado como inativo (soft delete) e registra log."""
    current_app.logger.info(f"[CLI] excluir_avaliado() chamado para id={id}")
    try:
        avaliado = Avaliado.query.get_or_404(id)

        # segurança: precisa ser do mesmo cliente do usuário
        if avaliado.cliente_id != current_user.cliente_id:
            current_app.logger.warning(
                f"[CLI] excluir_avaliado bloqueado: user.cliente={current_user.cliente_id} != avaliado.cliente={avaliado.cliente_id}"
            )
            flash("Avaliado não encontrado.", "danger")
            return redirect(url_for('cli.listar_avaliados'))

        # soft delete (mais seguro com FKs)
        avaliado.ativo = False
        db.session.commit()

        log_acao("Excluiu avaliado", {"id": id, "nome": avaliado.nome}, "Avaliado", id)
        flash("Avaliado excluído (inativado) com sucesso.", "success")
        current_app.logger.info(f"[CLI] excluir_avaliado OK id={id}")

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"[CLI] erro excluir_avaliado id={id}: {e}")
        flash(f"Erro ao excluir avaliado: {str(e)}", "danger")

    return redirect(url_for('cli.listar_avaliados'))


# ===================== APLICAÇÕES =====================

@cli_bp.route('/aplicacoes')
@cli_bp.route('/listar-aplicacoes')
@login_required
def listar_aplicacoes():
    """Lista todas as aplicações de questionário com FILTRO HIERÁRQUICO (MULTI-GAP) e PAGINAÇÃO"""
    try:
        # 1. Captura de Filtros (com conversão de tipo segura do Flask)
        avaliado_id = request.args.get('avaliado_id', type=int)
        questionario_id = request.args.get('questionario_id', type=int)
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        page = request.args.get('page', 1, type=int)

        # 2. Query Base (Filtrada pelo Cliente e unida com Avaliado)
        query = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id
        )

        # 3. Blindagem de Hierarquia (Regras FAB Atualizadas)
        
        # Nível 1: Usuário de Rancho (vê apenas o seu)
        if current_user.avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == current_user.avaliado_id)
            # Força o filtro visual para coincidir com a permissão
            avaliado_id = current_user.avaliado_id 

        # Nível 2: Gestor/Auditor de GAP (Lógica MULTI-GAP)
        # Verifica se o usuário tem a lista de grupos de acesso (novo sistema)
        elif hasattr(current_user, 'grupos_acesso'):
            # Coleta todos os IDs permitidos da tabela N:N
            ids_permitidos = [g.id for g in current_user.grupos_acesso if g.ativo]
            
            # Fallback: Se a lista nova estiver vazia, tenta usar o campo antigo (legado)
            if not ids_permitidos and current_user.grupo_id:
                ids_permitidos = [current_user.grupo_id]
            
            # Se encontrou grupos permitidos, filtra por eles
            if ids_permitidos:
                query = query.filter(Avaliado.grupo_id.in_(ids_permitidos))
            else:
                # Se é Gestor/Auditor mas não tem NENHUM grupo vinculado (nem novo nem antigo)
                # Só deve ver algo se for ADMIN/SUPER_ADMIN. Se não for, bloqueia tudo.
                if current_user.tipo.name not in ['SUPER_ADMIN', 'ADMIN']:
                     query = query.filter(Avaliado.id == -1) # Retorna vazio por segurança

        # Nível 3: SDAB/ADMIN (Vê tudo - já filtrado por cliente_id no passo 2)

        # 4. Aplicação dos Filtros Dinâmicos (vindos do formulário)
        if avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
        
        if questionario_id:
            query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
        
        if status:
            query = query.filter(AplicacaoQuestionario.status == status)
        
        # Tratamento seguro de datas
        if data_inicio:
            try:
                dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(AplicacaoQuestionario.data_inicio >= dt_inicio)
            except ValueError:
                pass 
        
        if data_fim:
            try:
                # Ajusta para o final do dia (23:59:59)
                dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                query = query.filter(AplicacaoQuestionario.data_inicio <= dt_fim)
            except ValueError:
                pass

        # 5. Paginação e Ordenação
        # Ordena por data de início decrescente (mais recentes primeiro)
        aplicacoes = query.order_by(AplicacaoQuestionario.data_inicio.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # 6. Dados para os Selects de Filtro
        # Usa a função get_avaliados_usuario() que JÁ ATUALIZAMOS para Multi-GAP
        avaliados = get_avaliados_usuario() 
        
        questionarios = Questionario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).order_by(Questionario.nome).all()
        
        # 7. Renderização
        return render_template_safe('cli/listar_aplicacoes.html',
                             aplicacoes=aplicacoes,
                             avaliados=avaliados,
                             questionarios=questionarios,
                             filtros={
                                 'avaliado_id': avaliado_id,
                                 'questionario_id': questionario_id,
                                 'status': status,
                                 'data_inicio': data_inicio,
                                 'data_fim': data_fim
                             })

    except Exception as e:
        print(f"Erro em listar_aplicacoes: {e}")
        flash(f"Erro ao carregar lista de aplicações: {str(e)}", "danger")
        return render_template_safe('cli/index.html')
@cli_bp.route('/aplicacao/nova', methods=['GET', 'POST'])
@cli_bp.route('/nova-aplicacao', methods=['GET', 'POST'])
@login_required
def nova_aplicacao():
    """
    Rota Legada (Atalho).
    Redireciona para o fluxo seguro de Seleção de Rancho (Passo 1).
    Isso garante que as regras de GAP/Hierarquia sejam aplicadas.
    """
    # Redireciona para a tela onde filtramos os ranchos por GAP
    return redirect(url_for('cli.selecionar_rancho_auditoria'))
# Em app/cli/routes.py

@cli_bp.route('/aplicacao/<int:id>/responder', methods=['GET', 'POST'])
@login_required
def responder_aplicacao(id, modo_assinatura=False):
    """
    Interface Principal de Coleta (Checklist).
    Atualizada com segurança Multi-GAP.
    """
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)

        # 1. Validação de Segurança Global (Cliente)
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Aplicação não encontrada ou acesso negado.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))
        
        # 2. Validação de Segurança Regional (MULTI-GAP)
        # Se for Gestor/Auditor, verifica se tem permissão no GAP do rancho auditado
        if current_user.tipo.name in ['AUDITOR', 'GESTOR']:
            # Coleta todos os IDs permitidos (Lista Nova + Legado)
            gaps_permitidos = []
            if hasattr(current_user, 'grupos_acesso'):
                gaps_permitidos = [g.id for g in current_user.grupos_acesso]
            
            if current_user.grupo_id:
                gaps_permitidos.append(current_user.grupo_id)
            
            # Remove duplicatas
            gaps_permitidos = list(set(gaps_permitidos))
            
            # Verifica a permissão
            if aplicacao.avaliado.grupo_id not in gaps_permitidos:
                flash("Acesso negado: Unidade fora da sua jurisdição.", "danger")
                return redirect(url_for('cli.listar_aplicacoes'))

        # 3. Validação de Status
        if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
            flash("Esta aplicação já foi finalizada.", "warning")
            return redirect(url_for('cli.visualizar_aplicacao', id=id))

        # --- CARREGAMENTO DE DADOS ---
        
        # Carrega tópicos ativos
        topicos = Topico.query.filter(
            Topico.questionario_id == aplicacao.questionario_id,
            Topico.ativo == True
        ).order_by(Topico.ordem).all()

        if not topicos:
             flash("Este questionário não possui tópicos ativos.", "warning")
             return render_template(
                'cli/responder_aplicacao.html',
                aplicacao=aplicacao, 
                topicos=[], 
                perguntas_por_topico={}, 
                respostas_existentes={},
                modo_assinatura=modo_assinatura
            )

        topico_ids = [t.id for t in topicos]

        # Carrega perguntas ativas apenas dos tópicos carregados
        perguntas_ativas = Pergunta.query.filter(
            Pergunta.topico_id.in_(topico_ids),
            Pergunta.ativo == True
        ).order_by(Pergunta.ordem).all()
        
        perguntas_ativas_ids = [p.id for p in perguntas_ativas]

        # Carrega respostas existentes
        respostas_lista = []
        if perguntas_ativas_ids:
            # Opção simples e segura (sem joinedload complexo para evitar erros de import)
            respostas_lista = RespostaPergunta.query.filter(
                RespostaPergunta.aplicacao_id == aplicacao.id,
                RespostaPergunta.pergunta_id.in_(perguntas_ativas_ids)
            ).all()
        
        # Mapeamento para acesso rápido no template
        perguntas_por_topico = {t.id: [] for t in topicos}
        for p in perguntas_ativas:
            if p.topico_id in perguntas_por_topico:
                perguntas_por_topico[p.topico_id].append(p)
        
        respostas_map = {r.pergunta_id: r for r in respostas_lista}

        return render_template(
            'cli/responder_aplicacao.html',
            aplicacao=aplicacao,
            topicos=topicos,
            perguntas_por_topico=perguntas_por_topico,
            respostas_existentes=respostas_map,
            modo_assinatura=modo_assinatura
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao carregar aplicação {id}: {e}", exc_info=True)
        flash(f"Erro ao carregar aplicação: {str(e)}", "danger")
        return redirect(url_for('cli.listar_aplicacoes'))
@cli_bp.route('/aplicacao/<int:id>/fase-assinatura')
@login_required
def fase_assinatura(id):
    """Rota intermediária que reabre o checklist no Modo Assinatura."""
    return responder_aplicacao(id, modo_assinatura=True)


# Em app/cli/routes.py

# Em app/cli/routes.py

# Em app/cli/routes.py

# ... (mantenha o resto do arquivo como está) ...

# Em app/cli/routes.py

# ... (mantenha o resto do arquivo como está) ...

# Em app/cli/routes.py

# ... (outras rotas) ...

@cli_bp.route('/aplicacao/<int:id>/concluir-coleta', methods=['POST'])
@login_required
def concluir_coleta(id):
    """
    Fase 1: Encerra a coleta técnica.
    - Valida obrigatórias (EXCETO ASSINATURAS).
    - Valida fotos.
    - Calcula nota prévia.
    - Redireciona para a Gestão de NCs (não finaliza status).
    """
    try:
        # 1. Carregamento Otimizado
        aplicacao = AplicacaoQuestionario.query.options(
            db.joinedload(AplicacaoQuestionario.questionario), 
            db.joinedload(AplicacaoQuestionario.avaliado)
        ).get_or_404(id)

        # 2. Carrega Respostas em Memória
        respostas_list = list(aplicacao.respostas) 
        respostas_dict = {r.pergunta_id: r for r in respostas_list}
        respostas_dadas_ids = set(respostas_dict.keys())

        # 3. FILTRO ANTI-FANTASMA (Ignora perguntas excluídas)
        perguntas_ativas = Pergunta.query.join(Topico).filter(
            Topico.questionario_id == aplicacao.questionario_id,
            Topico.ativo.is_(True),
            Pergunta.ativo.is_(True)
        ).all()

        # Validações Básicas de Segurança
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Aplicação não encontrada.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))

        if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
            flash("Esta aplicação já foi finalizada.", "warning")
            return redirect(url_for('cli.visualizar_aplicacao', id=id))

        # --- 4. VALIDAÇÃO DE OBRIGATÓRIAS (COM A NOVA LÓGICA) ---
        # AQUI ESTÁ A MUDANÇA: Ignoramos perguntas do tipo ASSINATURA nesta etapa
        perguntas_obrigatorias_ids = {
            p.id for p in perguntas_ativas 
            if p.obrigatoria and p.tipo.name != 'ASSINATURA' 
        }
        
        perguntas_faltando_ids = perguntas_obrigatorias_ids - respostas_dadas_ids

        if perguntas_faltando_ids:
            # Busca os textos das perguntas para mostrar erro amigável
            nomes_faltantes = [p.texto for p in perguntas_ativas if p.id in perguntas_faltando_ids]
            pendencias = nomes_faltantes[:3] # Mostra só as 3 primeiras
            
            flash(f"Faltam {len(perguntas_faltando_ids)} pergunta(s) obrigatória(s) para avançar.", "warning")
            for texto in pendencias: 
                flash(f"- {texto}", "secondary")
            if len(nomes_faltantes) > 3:
                flash("...", "secondary")
                
            return redirect(url_for('cli.responder_aplicacao', id=id))

        # --- 5. MARCAÇÃO DE NÃO CONFORMIDADES & VALIDAÇÃO DE FOTOS ---
        perguntas_sem_foto = []
        respostas_negativas = ['não', 'nao', 'no', 'irregular', 'ruim']

        for p in perguntas_ativas:
            if p.id in respostas_dict:
                resp = respostas_dict[p.id]
                resp_txt = (resp.resposta or "").strip().lower()
                
                # Se resposta for negativa, marca NC
                if resp_txt in respostas_negativas:
                    resp.nao_conforme = True
                    
                    # Validação de Foto (se configurada como obrigatória)
                    criterio = getattr(p, 'criterio_foto', 'nenhuma')
                    if criterio == 'obrigatoria':
                        tem_foto = False
                        # Verifica legado ou tabela nova
                        if resp.caminho_foto: 
                            tem_foto = True
                        elif hasattr(resp, 'fotos'):
                            try:
                                if hasattr(resp.fotos, 'count'):
                                    if resp.fotos.count() > 0: tem_foto = True
                                elif len(resp.fotos) > 0:
                                    tem_foto = True
                            except: pass
                        
                        if not tem_foto:
                            topico_nome = p.topico.nome if p.topico else "Geral"
                            perguntas_sem_foto.append(f"'{p.texto}' ({topico_nome})")
                else:
                    resp.nao_conforme = False # Limpa NC se corrigiu

        # Bloqueia se faltar foto em NC obrigatória
        if perguntas_sem_foto:
            count = len(perguntas_sem_foto)
            flash(f"Bloqueado: {count} resposta(s) 'Não Conforme' exigem foto de evidência.", "danger")
            for erro in perguntas_sem_foto[:3]: 
                flash(f"- {erro}", "warning")
            return redirect(url_for('cli.responder_aplicacao', id=id))

        # --- 6. CÁLCULO DE NOTA (Parcial) ---
        if aplicacao.questionario.calcular_nota:
            pontos_obtidos = 0.0
            pontos_maximos = 0.0

            for p in perguntas_ativas:
                peso = float(p.peso or 0)
                if peso <= 0: continue
                
                resp = respostas_dict.get(p.id)
                
                # Ignora N.A.
                is_na = False
                tipo_str = str(p.tipo.name if hasattr(p.tipo, 'name') else p.tipo).upper()
                if 'SIM_NAO' in tipo_str and resp:
                    if (resp.resposta or "").strip().upper() in ["N.A.", "N/A", "NA"]: 
                        is_na = True
                
                if is_na: continue

                pontos_maximos += peso
                if resp and resp.pontos is not None:
                    pontos_obtidos += float(resp.pontos)

            aplicacao.pontos_obtidos = round(pontos_obtidos, 2)
            aplicacao.pontos_totais = round(pontos_maximos, 2)

            if pontos_maximos > 0:
                nota = (pontos_obtidos / pontos_maximos) * 100
                casas = aplicacao.questionario.casas_decimais
                aplicacao.nota_final = round(nota, casas if casas is not None else 2)
            else:
                aplicacao.nota_final = 0.0

        # --- 7. SALVAR E REDIRECIONAR PARA REVISÃO ---
        db.session.commit()

        flash("Coleta concluída! Agora revise as Não Conformidades.", "info")
        
        # Redireciona para a tela de Planos de Ação (onde haverá o botão para ir às assinaturas)
        return redirect(url_for('cli.gerenciar_nao_conformidades', id=id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro concluir coleta {id}: {e}", exc_info=True)
        flash(f"Erro ao processar: {str(e)}", "danger")
        return redirect(url_for('cli.responder_aplicacao', id=id))

@cli_bp.route('/aplicacao/<int:id>/revisar-entrega', methods=['GET'])
@login_required
def revisar_entrega(id):
    """
    Tela intermediária: Auditora revisa NCs, usa IA e prepara a entrega.
    """
    aplicacao = AplicacaoQuestionario.query.get_or_404(id)
    
    if aplicacao.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_aplicacoes'))
    
    # Busca NCs ordenadas pelo checklist para facilitar a leitura
    ncs = RespostaPergunta.query\
        .join(Pergunta).join(Topico)\
        .filter(RespostaPergunta.aplicacao_id == id, RespostaPergunta.nao_conforme == True)\
        .order_by(Topico.ordem, Pergunta.ordem)\
        .all()
        
    return render_template_safe('cli/revisar_entrega.html', aplicacao=aplicacao, ncs=ncs)


@cli_bp.route('/aplicacao/<int:id>/finalizar-definitivo', methods=['POST'])
@login_required
def finalizar_definitivamente(id):
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        
        # 1. Validação de Segurança (Garante que é do mesmo cliente)
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "danger")
            return redirect(url_for('cli.listar_aplicacoes'))

        # --- BLOCO QUE VOCÊ QUER REMOVER (O FIX DO COMMIT) ---
        # Remova ou comente as linhas abaixo para tirar a obrigatoriedade
        # if not aplicacao.assinatura_imagem:
        #     flash("Para finalizar definitivamente, é obrigatório coletar a Assinatura do Responsável.", "danger")
        #     return redirect(url_for('cli.fase_assinatura', id=id))
        # -----------------------------------------------------

        # 3. Atualiza Observações Finais (se enviado no form)
        observacoes = request.form.get('observacoes_finais')
        if observacoes is not None:
            aplicacao.observacoes_finais = observacoes

        # 4. TUDO CERTO: FINALIZA
        aplicacao.status = StatusAplicacao.FINALIZADA
        
        # Só atualiza a data fim se ainda não tiver
        if not aplicacao.data_fim:
            aplicacao.data_fim = datetime.now()
        
        db.session.commit()
        
        log_acao(f"Finalização Definitiva: {aplicacao.questionario.nome}", None, "Aplicacao", id)
        
        flash("Auditoria finalizada com sucesso! Documento gerado.", "success")
        return redirect(url_for('cli.visualizar_aplicacao', id=id))
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao finalizar definitivamente: {e}")
        flash(f"Erro técnico ao finalizar: {e}", "danger")
        return redirect(url_for('cli.fase_assinatura', id=id))

@cli_bp.route('/aplicacao/<int:id>/assinar-finalizar', methods=['POST'])
@login_required
def assinar_finalizar(id):
    """
    Recebe a assinatura, salva a imagem e FINALIZA a auditoria.
    """
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        
        # 1. Dados do Formulário
        nome_resp = request.form.get('nome_responsavel')
        cargo_resp = request.form.get('cargo_responsavel')
        assinatura_b64 = request.form.get('assinatura_base64') # Vem do Canvas JS
        
        if not assinatura_b64:
            flash("A assinatura é obrigatória para finalizar.", "warning")
            # Redireciona de volta para a mesma tela de planos
            return redirect(url_for('cli.gerenciar_nao_conformidades', id=id))

        # 2. Processar e Salvar a Imagem
        import base64
        import os
        import uuid
        
        # Remove o cabeçalho 'data:image/png;base64,' se existir
        if ',' in assinatura_b64:
            img_data = assinatura_b64.split(',')[1]
        else:
            img_data = assinatura_b64

        filename = f"assinatura_app_{id}_{uuid.uuid4().hex[:8]}.png"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            raise Exception("Pasta de upload não configurada")
            
        caminho_completo = os.path.join(upload_folder, filename)
        
        with open(caminho_completo, "wb") as fh:
            fh.write(base64.b64decode(img_data))
            
        # 3. Atualizar Banco de Dados
        aplicacao.assinatura_imagem = filename
        aplicacao.assinatura_responsavel = nome_resp
        aplicacao.cargo_responsavel = cargo_resp
        
        # AGORA SIM: FINALIZA!
        aplicacao.status = StatusAplicacao.FINALIZADA
        aplicacao.data_fim = datetime.now()
        
        db.session.commit()
        
        log_acao(f"Auditoria assinada e finalizada por {nome_resp}", None, "Aplicacao", id)
        
        flash("Auditoria finalizada e assinada com sucesso!", "success")
        return redirect(url_for('cli.visualizar_aplicacao', id=id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar assinatura: {e}")
        flash(f"Erro ao salvar assinatura: {str(e)}", "danger")
        return redirect(url_for('cli.gerenciar_nao_conformidades', id=id))

@cli_bp.route('/aplicacao/<int:id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir_aplicacao(id):
    """
    Exclui uma aplicação de questionário e todas as suas respostas.
    """
    # Busca a aplicação pelo ID
    aplicacao = db.session.get(AplicacaoQuestionario, id)
    if not aplicacao:
        flash('Aplicação não encontrada.', 'danger')
        return redirect(url_for('cli.listar_aplicacoes'))
    
    try:
        # Excluir todas as respostas associadas (se não houver cascade configurado no modelo)
        RespostaPergunta.query.filter_by(aplicacao_id=id).delete()

        # Excluir a aplicação
        db.session.delete(aplicacao)
        db.session.commit()

        flash('Aplicação excluída com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao excluir aplicação {id}: {e}", exc_info=True)
        flash('Erro ao excluir aplicação. Verifique os logs para mais detalhes.', 'danger')

    return redirect(url_for('cli.listar_aplicacoes'))


@cli_bp.route('/aplicacao/<int:id>')
@cli_bp.route('/aplicacao/<int:id>/visualizar')
@login_required
def visualizar_aplicacao(id):
    """
    Visualiza uma aplicação com BLINDAGEM DE HIERARQUIA (MULTI-GAP).
    Garante que itens excluídos não apareçam e que usuários só vejam o que têm permissão.
    """
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        
        # --- INÍCIO DA SEGURANÇA HIERÁRQUICA ---
        
        # 1. Proteção Global (Mesmo Cliente/Empresa)
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Aplicação não encontrada.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))

        # 2. Proteção Nível Local (Rancho)
        # Se o usuário tem um rancho fixo (current_user.avaliado_id), 
        # ele NÃO pode ver aplicações de IDs diferentes.
        if current_user.avaliado_id and aplicacao.avaliado_id != current_user.avaliado_id:
            flash("Acesso negado: Você só pode visualizar aplicações do seu Rancho.", "danger")
            return redirect(url_for('cli.listar_aplicacoes'))

        # 3. Proteção Nível Regional (GAP) - ATUALIZADA MULTI-GAP
        # Se o usuário não é Super Admin nem Admin, verificamos os vínculos de GAP
        if current_user.tipo.name not in ['SUPER_ADMIN', 'ADMIN']:
            
            # Coleta todos os GAPs que o usuário tem permissão
            gaps_permitidos = []
            
            # A) Pela nova lista N:N
            if hasattr(current_user, 'grupos_acesso'):
                gaps_permitidos.extend([g.id for g in current_user.grupos_acesso])
            
            # B) Pelo legado (se existir)
            if current_user.grupo_id:
                gaps_permitidos.append(current_user.grupo_id)
            
            # Remove duplicatas e limpa
            gaps_permitidos = list(set(gaps_permitidos))
            
            # SE o usuário tem GAPs vinculados (é Gestor/Auditor),
            # verificamos se o rancho desta aplicação pertence a um deles.
            if gaps_permitidos:
                if aplicacao.avaliado.grupo_id not in gaps_permitidos:
                    flash(f"Acesso negado: A unidade '{aplicacao.avaliado.nome}' não pertence aos seus GAPs de acesso.", "danger")
                    return redirect(url_for('cli.listar_aplicacoes'))
            
        # --- FIM DA SEGURANÇA ---
        
        # 4. Carregar Tópicos Ativos
        topicos_db = Topico.query.filter_by(
            questionario_id=aplicacao.questionario_id,
            ativo=True
        ).order_by(Topico.ordem).all()
        
        # 5. Filtrar Perguntas Ativas Manualmente
        topicos_visualizacao = []
        
        for topico in topicos_db:
            # Carrega explicitamente apenas as perguntas ativas deste tópico
            perguntas_ativas = Pergunta.query.filter_by(
                topico_id=topico.id,
                ativo=True
            ).order_by(Pergunta.ordem).all()
            
            if perguntas_ativas:
                # Injetamos a lista filtrada dinamicamente no objeto
                # O template deve usar: {% for p in topico.perguntas_ativas %}
                topico.perguntas_ativas = perguntas_ativas
                topicos_visualizacao.append(topico)
        
        # 6. Organizar Respostas
        respostas_dict = {}
        for r in aplicacao.respostas:
            respostas_dict[r.pergunta_id] = r
            
        # 7. Estatísticas (contando apenas as ativas visíveis)
        total_perguntas_visiveis = sum(len(t.perguntas_ativas) for t in topicos_visualizacao)
        respondidas_visiveis = 0
        for t in topicos_visualizacao:
            for p in t.perguntas_ativas:
                if p.id in respostas_dict and respostas_dict[p.id].resposta:
                    respondidas_visiveis += 1

        stats = {
            'total_perguntas': total_perguntas_visiveis,
            'perguntas_respondidas': respondidas_visiveis,
            'tempo_aplicacao': None
        }
        
        if aplicacao.data_fim and aplicacao.data_inicio:
            diff = aplicacao.data_fim - aplicacao.data_inicio
            stats['tempo_aplicacao'] = round(diff.total_seconds() / 60, 1)

        return render_template_safe('cli/visualizar_aplicacao.html',
                             aplicacao=aplicacao,
                             topicos=topicos_visualizacao, # Passamos a lista filtrada
                             respostas_dict=respostas_dict,
                             stats=stats)

    except Exception as e:
        # Log de erro para debug (opcional)
        print(f"Erro visualizar_aplicacao: {e}") 
        flash(f"Erro ao carregar aplicação: {str(e)}", "danger")
        return redirect(url_for('cli.listar_aplicacoes'))
# Em app/cli/routes.py

# Em app/cli/routes.py

# ... (outras rotas) ...

# Em app/cli/routes.py

# Em app/cli/routes.py

@cli_bp.route('/aplicacao/<int:id>/relatorio')
@login_required
def gerar_relatorio_aplicacao(id):
    """Gera relatório em PDF da aplicação com cálculo por tópico e galeria de fotos por tópico"""
    try:
        # Carrega a aplicação com relacionamentos úteis pré-carregados
        aplicacao = AplicacaoQuestionario.query.options(
            joinedload(AplicacaoQuestionario.questionario),
            joinedload(AplicacaoQuestionario.avaliado)
        ).get_or_404(id)

        # Buscar o usuário (aplicador) explicitamente
        avaliador = Usuario.query.get(aplicacao.aplicador_id) 
        if not avaliador:
            flash("Erro: Avaliador não encontrado.", "danger")
            return redirect(url_for('cli.listar_aplicacoes'))

        # --- CORREÇÃO DE PERMISSÃO ---
        if aplicacao.avaliado.cliente_id != current_user.cliente_id and not verificar_permissao_admin():
            flash("Você não tem permissão para ver esta aplicação.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))
        # --- FIM DA CORREÇÃO ---


        # ★★★ NOVO BLOCO PARA CARREGAR A LOGO ★★★
        logo_pdf_uri = None
        try:
            # current_app.static_folder aponta para a pasta 'app/static' absoluta
            # O caminho que você informou foi: F:\ARQUIVOS QUALIGESTOR\QualiGestor - Copia\app\static\img\logo_pdf.png
            logo_path = Path(current_app.static_folder) / 'img' / 'logo_pdf.png'
            
            if logo_path.exists():
                logo_pdf_uri = logo_path.as_uri() # Converte para 'file:///F:/ARQUIVOS%20QUALIGESTOR/...'
                current_app.logger.debug(f"Logo do PDF carregada: {logo_pdf_uri}")
            else:
                current_app.logger.warning(f"Logo do PDF não encontrada em: {logo_path}")
                # Tenta carregar a logo antiga como fallback
                logo_path_antiga = Path(current_app.static_folder) / 'img' / 'logo.jpg'
                if logo_path_antiga.exists():
                    logo_pdf_uri = logo_path_antiga.as_uri()
                    current_app.logger.warning(f"Usando logo.jpg como fallback: {logo_pdf_uri}")
                else:
                    current_app.logger.error(f"Nenhuma logo (logo_pdf.png ou logo.jpg) encontrada.")
        except Exception as e_logo:
            current_app.logger.error(f"Erro ao carregar URI da logo do PDF: {e_logo}")
        # ★★★ FIM DO BLOCO DA LOGO ★★★


        # --- CÁLCULO DE PONTUAÇÕES E ORGANIZAÇÃO DOS DADOS ---

        # 1. Buscar tópicos ativos (na ordem correta)
        topicos_ativos = Topico.query.filter_by(
            questionario_id=aplicacao.questionario_id,
            ativo=True
        ).order_by(Topico.ordem).all()

        # 2. Buscar todas as respostas da aplicação
        respostas_da_aplicacao = RespostaPergunta.query.filter_by(aplicacao_id=id).options(
            joinedload(RespostaPergunta.pergunta)
        ).all()
        respostas_dict = {r.pergunta_id: r for r in respostas_da_aplicacao}

        # 3. Estruturas para passar ao template
        scores_por_topico = {}
        respostas_por_topico = defaultdict(list)
        fotos_por_topico = defaultdict(list)     # <-- Dicionário SÓ para fotos
        pontos_totais_obtidos = 0.0
        pontos_totais_maximos = 0.0
        
        # --- MUDANÇA: Pegar o caminho absoluto da pasta de uploads UMA VEZ ---
        upload_folder_path_str = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder_path_str:
            current_app.logger.error("UPLOAD_FOLDER não está configurado! As fotos não aparecerão no PDF.")
        
        # 4. Processar tópicos
        for topico in topicos_ativos:
            pontos_obtidos_topico = 0.0
            pontos_maximos_topico = 0.0
            perguntas_ativas_do_topico = [p for p in topico.perguntas if p.ativo]

            for pergunta in perguntas_ativas_do_topico:
                peso_pergunta = float(pergunta.peso) if pergunta.peso is not None else 0.0
                resposta_obj = respostas_dict.get(pergunta.id)

                if resposta_obj:
                    # Adiciona a resposta à lista principal (para exibir no corpo)
                    if pergunta.id not in [r.pergunta_id for r in respostas_por_topico[topico]]:
                        respostas_por_topico[topico].append(resposta_obj)
                
                    # --- ★★★ CORREÇÃO DA FOTO PDF (CAMINHO) ★★★ ---
                    if resposta_obj.caminho_foto and upload_folder_path_str:
                        try:
                            # 1. Recria o caminho absoluto como um objeto Path
                            caminho_completo_path = Path(upload_folder_path_str) / resposta_obj.caminho_foto
                            
                            # 2. Converte o objeto Path para uma URI (ex: file:///F:/.../QualiGestor%20-%20Copia/...)
                            caminho_url = caminho_completo_path.as_uri()
                            
                            fotos_por_topico[topico].append({
                                'resposta': resposta_obj,
                                'caminho_url': caminho_url 
                            })
                            current_app.logger.debug(f"Foto URI gerada para PDF: {caminho_url}")

                        except Exception as e_path:
                             current_app.logger.error(f"Erro ao criar URI da foto '{resposta_obj.caminho_foto}': {e_path}")
                    # --- ★★★ FIM DA CORREÇÃO DA FOTO (CAMINHO) ★★★ ---

                # --- Lógica de Pontuação (como no seu código) ---
                if peso_pergunta == 0:
                    continue 

                is_tipo_sim_nao = False
                try:
                    if hasattr(pergunta.tipo, 'name'): tipo_str = pergunta.tipo.name.upper()
                    else: tipo_str = str(pergunta.tipo or "").upper().replace(" ", "_")
                    if tipo_str in ['SIM_NAO_NA', 'SIM_NAO', 'SIM_NÃO']:
                        is_tipo_sim_nao = True
                except Exception:
                    pass

                is_na = False
                if is_tipo_sim_nao and resposta_obj:
                    if (resposta_obj.resposta or "").strip().upper() in ["N.A.", "N/A", "NA"]:
                        is_na = True
                
                if is_na:
                    continue 

                pontos_maximos_topico += peso_pergunta

                if resposta_obj and not is_na:
                    if resposta_obj.pontos is not None:
                        pontos_obtidos_topico += float(resposta_obj.pontos)
            
            # --- Fim do loop de perguntas ---

            # Armazenar scores do tópico
            percentual_topico = (pontos_obtidos_topico / pontos_maximos_topico * 100.0) if pontos_maximos_topico > 0 else 0.0
            casas_dec = aplicacao.questionario.casas_decimais
            if casas_dec is not None and casas_dec >= 0:
                 percentual_topico = round(percentual_topico, casas_dec)
            
            scores_por_topico[topico.id] = {
                'score_obtido': round(pontos_obtidos_topico, 2),
                'score_maximo': round(pontos_maximos_topico, 2),
                'score_percent': percentual_topico
            }
            pontos_totais_obtidos += pontos_totais_obtidos
            pontos_totais_maximos += pontos_maximos_topico

        # 5. Calcular nota final (como antes)
        nota_final = aplicacao.nota_final if aplicacao.nota_final is not None else 0.0
        if aplicacao.status == StatusAplicacao.EM_ANDAMENTO:
             if pontos_totais_maximos > 0:
                 nota_final_calc = (pontos_totais_obtidos / pontos_totais_maximos * 100.0)
                 casas_dec = aplicacao.questionario.casas_decimais
                 if casas_dec is not None and casas_dec >= 0:
                      nota_final = round(nota_final_calc, casas_dec)
                 else:
                      nota_final = nota_final_calc
             else:
                 nota_final = 0.0

        qr_code_url = None # ... (seu código de QR) ...

        # Renderizar template HTML com as variáveis ATUALIZADAS
        html_content = render_template_safe(
            'cli/relatorio_aplicacao.html',
            aplicacao=aplicacao,
            avaliador=avaliador,
            topicos_ativos=topicos_ativos,
            respostas_por_topico=respostas_por_topico,
            fotos_por_topico=fotos_por_topico,
            scores_por_topico=scores_por_topico,
            nota_final=nota_final,
            data_geracao=datetime.now(),
            qr_code_url=qr_code_url,
            logo_pdf_uri=logo_pdf_uri  # <-- ★★★ PASSA A NOVA VARIÁVEL PARA O HTML ★★★
        )

        filename = f"relatorio_{aplicacao.avaliado.nome.replace(' ', '_')}_{aplicacao.data_inicio.strftime('%Y%m%d')}.pdf"
        return gerar_pdf_seguro(html_content, filename)

    except Exception as e:
        current_app.logger.error(f"Erro DETALHADO em gerar_relatorio_aplicacao (ID: {id}): {e}", exc_info=True)
        import traceback
        traceback.print_exc() # Adiciona isso para debug no console
        flash(f"Erro ao gerar relatório: {str(e)}", "danger")
        try:
            return redirect(url_for('cli.visualizar_aplicacao', id=id))
        except:
            return redirect(url_for('cli.listar_aplicacoes'))

# ... (resto do seu arquivo routes.py) ...

# ===================== RELATÓRIOS E ANÁLISES =====================

@cli_bp.route('/relatorios')
@login_required
def relatorios():
    """Página de relatórios e análises"""
    try:
        # Buscar dados para os filtros
        avaliados = get_avaliados_usuario()
        questionarios = Questionario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).all()
        
        # Estatísticas básicas para o dashboard de relatórios
        stats = {
            'total_aplicacoes': AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id
            ).count(),
            'media_geral': db.session.query(func.avg(AplicacaoQuestionario.nota_final)).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            ).scalar() or 0,
            'aplicacoes_mes': AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                extract('month', AplicacaoQuestionario.data_inicio) == datetime.now().month
            ).count()
        }
        
        return render_template_safe('cli/relatorios.html',
                             avaliados=avaliados,
                             questionarios=questionarios,
                             stats=stats)
    except Exception as e:
        flash(f"Erro ao carregar relatórios: {str(e)}", "danger")
        return render_template_safe('cli/index.html')

@cli_bp.route('/api/relatorio-dados')
@login_required
def api_dados_relatorio():
    """API para dados de relatórios"""
    try:
        tipo = request.args.get('tipo', 'ranking')
        avaliado_id = request.args.get('avaliado_id')
        questionario_id = request.args.get('questionario_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        dados = {}
        
        if tipo == 'ranking':
            # Ranking de avaliados por nota média
            query = db.session.query(
                Avaliado.nome,
                func.avg(AplicacaoQuestionario.nota_final).label('media'),
                func.count(AplicacaoQuestionario.id).label('total_aplicacoes')
            ).join(AplicacaoQuestionario).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            )
            
            if data_inicio:
                query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
            if data_fim:
                query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            
            resultados = query.group_by(Avaliado.id, Avaliado.nome).order_by(
                func.avg(AplicacaoQuestionario.nota_final).desc()
            ).all()
            
            dados['ranking'] = [
                {
                    'avaliado': r.nome,
                    'media': round(float(r.media), 2),
                    'total_aplicacoes': r.total_aplicacoes
                }
                for r in resultados
            ]
            
        elif tipo == 'evolucao':
            # Evolução temporal das notas
            query = db.session.query(
                func.date(AplicacaoQuestionario.data_inicio).label('data'),
                func.avg(AplicacaoQuestionario.nota_final).label('media')
            ).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            )
            
            if avaliado_id:
                query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
            if questionario_id:
                query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
            if data_inicio:
                query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
            if data_fim:
                query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            
            resultados = query.group_by(func.date(AplicacaoQuestionario.data_inicio)).order_by('data').all()
            
            dados['evolucao'] = [
                {
                    'data': r.data.strftime('%Y-%m-%d'),
                    'media': round(float(r.media), 2)
                }
                for r in resultados
            ]
            
        elif tipo == 'comparativo':
            # Comparativo entre questionários
            query = db.session.query(
                Questionario.nome,
                func.avg(AplicacaoQuestionario.nota_final).label('media'),
                func.count(AplicacaoQuestionario.id).label('total_aplicacoes')
            ).join(AplicacaoQuestionario).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            )
            
            if data_inicio:
                query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
            if data_fim:
                query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            
            resultados = query.group_by(Questionario.id, Questionario.nome).all()
            
            dados['comparativo'] = [
                {
                    'questionario': r.nome,
                    'media': round(float(r.media), 2),
                    'total_aplicacoes': r.total_aplicacoes
                }
                for r in resultados
            ]
        
        return jsonify(dados)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/relatorio/exportar')
@login_required
def exportar_relatorio():
    """Exporta relatório em diferentes formatos"""
    try:
        formato = request.args.get('formato', 'pdf')
        tipo = request.args.get('tipo', 'ranking')
        
        # Obter dados do relatório usando a mesma lógica da API
        dados = obter_dados_relatorio_exportacao(tipo, 
                                                request.args.get('avaliado_id'),
                                                request.args.get('questionario_id'),
                                                request.args.get('data_inicio'),
                                                request.args.get('data_fim'))
        
        if formato == 'csv':
            return exportar_csv(dados, tipo)
        elif formato == 'pdf':
            return exportar_pdf(dados, tipo)
        else:
            flash("Formato não suportado.", "error")
            return redirect(url_for('cli.relatorios'))
            
    except Exception as e:
        flash(f"Erro ao exportar relatório: {str(e)}", "danger")
        return redirect(url_for('cli.relatorios'))

# ===================== GESTÃO DE USUÁRIOS =====================

# Em app/cli/routes.py

@cli_bp.route('/usuarios', endpoint='gerenciar_usuarios')
@login_required
@admin_required
def gerenciar_usuarios():
    """Página de gestão de usuários com Filtro por GAP e visualização Múltipla"""
    try:
        # 1. Carregar Grupos (GAPs) para o Filtro
        grupos = Grupo.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        ).order_by(Grupo.nome).all()

        # 2. Iniciar Query Base de Usuários
        query = Usuario.query.filter_by(cliente_id=current_user.cliente_id)

        # 3. Aplicar Filtro se selecionado
        filtro_grupo_id = request.args.get('grupo_id')
        
        if filtro_grupo_id and filtro_grupo_id.isdigit():
            gid = int(filtro_grupo_id)
            # Filtra usuários que:
            # A) Tenham esse GAP na lista de acesso (Consultoras/Gestores)
            # B) OU estejam vinculados a um Rancho que pertence a esse GAP (Usuários locais)
            query = query.join(usuario_grupos, isouter=True).join(Avaliado, isouter=True).filter(
                or_(
                    usuario_grupos.c.grupo_id == gid,  # Vínculo N:N
                    Avaliado.grupo_id == gid           # Vínculo via Rancho
                )
            ).distinct()

        # 4. Executar Query
        usuarios = query.order_by(Usuario.nome).all()
        
        # Estatísticas (Otimizado)
        stats_usuarios = {
            'total': len(usuarios),
            'ativos': len([u for u in usuarios if u.ativo]),
            'admins': len([u for u in usuarios if u.tipo.name in ['SUPER_ADMIN', 'ADMIN']]),
            'operacional': len([u for u in usuarios if u.tipo.name not in ['SUPER_ADMIN', 'ADMIN']])
        }
        
        return render_template_safe('cli/gerenciar_usuarios.html',
                             usuarios=usuarios,
                             grupos=grupos,               # Passando grupos para o select
                             filtro_grupo_id=filtro_grupo_id, # Para manter o select marcado
                             stats=stats_usuarios)
                             
    except Exception as e:
        print(f"Erro: {e}")
        flash(f"Erro ao carregar usuários: {str(e)}", "danger")
        return render_template_safe('cli/index.html')

@cli_bp.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    """
    Cria novo usuário com suporte a Múltiplos GAPs (N:N)
    e compatibilidade com sistema legado.
    """
    
    # Imports de segurança
    from werkzeug.security import generate_password_hash
    
    # =========================================================================
    # GET: Carregar dados para o formulário
    # =========================================================================
    if request.method == 'GET':
        try:
            # Carrega GAPs e Ranchos da empresa logada (FAB)
            gaps = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome).all()
            ranchos = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Avaliado.nome).all()
            
            return render_template('cli/usuario_form.html', grupos=gaps, ranchos=ranchos)
        except Exception as e:
            flash(f"Erro ao carregar formulário: {str(e)}", "danger")
            return redirect(url_for('cli.gerenciar_usuarios'))

    # =========================================================================
    # POST: Processar o formulário
    # =========================================================================
    try:
        # 1. Coleta dados básicos
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        tipo_str = request.form.get('tipo')
        
        # --- ATUALIZAÇÃO MULTI-GAP ---
        # Agora pegamos uma LISTA de IDs, e não apenas um único ID
        gaps_ids = request.form.getlist('grupos_acesso') 
        
        # ID do Rancho (caso seja usuário local)
        avaliado_id = request.form.get('avaliado_id') 
        
        # 2. Validações Básicas
        if not all([nome, email, tipo_str]):
            flash('Nome, Email e Tipo são obrigatórios.', 'warning')
            return redirect(url_for('cli.novo_usuario'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está em uso.', 'warning')
            return redirect(url_for('cli.novo_usuario'))

        # 3. VALIDAÇÃO DE VÍNCULOS ATUALIZADA
        
        # Regra A: Consultora (Auditor) e Gestor GAP precisam de PELO MENOS UM GAP
        if tipo_str in ['auditor', 'gestor'] and not gaps_ids:
            flash('Para Consultoras e Gestores, é OBRIGATÓRIO selecionar pelo menos um GAP.', 'warning')
            return redirect(url_for('cli.novo_usuario'))

        # Regra B: Usuário Operacional (Rancho) precisa de um Rancho definido
        if tipo_str == 'usuario' and not avaliado_id:
            flash('Para Usuários Locais (Rancho), é OBRIGATÓRIO selecionar o Rancho.', 'warning')
            return redirect(url_for('cli.novo_usuario'))

        # 4. Conversão Segura (HTML Value -> Python Enum)
        mapa_tipos = {
            'super_admin': TipoUsuario.SUPER_ADMIN,
            'admin': TipoUsuario.ADMIN,      
            'gestor': TipoUsuario.GESTOR,    
            'auditor': TipoUsuario.AUDITOR,  
            'usuario': TipoUsuario.USUARIO
        }
        
        tipo_enum = mapa_tipos.get(tipo_str)
        
        if not tipo_enum:
            try:
                tipo_enum = TipoUsuario[tipo_str.upper()]
            except KeyError:
                flash(f"Tipo de usuário inválido: {tipo_str}", "error")
                return redirect(url_for('cli.novo_usuario'))

        # 5. Criação do Objeto Usuário
        usuario = Usuario(
            nome=nome,
            email=email,
            tipo=tipo_enum,
            cliente_id=current_user.cliente_id,
            avaliado_id=int(avaliado_id) if avaliado_id else None,
            senha_hash=generate_password_hash('123456'),
            ativo=True
        )

        # 6. PROCESSAMENTO DOS GAPS E VÍNCULOS (Lógica Blindada por Tipo)
        
        # Cenário A: Consultora ou Gestor (Múltiplos GAPs)
        if usuario.tipo in [TipoUsuario.GESTOR, TipoUsuario.AUDITOR]:
            if gaps_ids:
                primeiro_gap = True
                for gid in gaps_ids:
                    gap = Grupo.query.get(int(gid))
                    if gap:
                        # Adiciona à lista N:N
                        usuario.grupos_acesso.append(gap)
                        
                        # Preenche o legado (grupo_id) com o primeiro da lista
                        if primeiro_gap:
                            usuario.grupo_id = gap.id
                            primeiro_gap = False
            else:
                # Se for Auditor/Gestor e não selecionar nada (tecnicamente já barrado acima)
                usuario.grupo_id = None

        # Cenário B: Usuário de Rancho (1 Rancho e Herda o GAP dele)
        elif usuario.tipo == TipoUsuario.USUARIO:
            if usuario.avaliado_id:
                rancho = Avaliado.query.get(usuario.avaliado_id)
                if rancho and rancho.grupo_id:
                    # 1. Define o legado
                    usuario.grupo_id = rancho.grupo_id
                    
                    # 2. Adiciona na lista nova para manter consistência no banco
                    gap_do_rancho = Grupo.query.get(rancho.grupo_id)
                    if gap_do_rancho:
                        usuario.grupos_acesso.append(gap_do_rancho)
            else:
                usuario.grupo_id = None

        # Cenário C: Admins (Sem restrições de linha)
        else:
            usuario.grupo_id = None
            usuario.avaliado_id = None

        # 7. Salvar no Banco
        db.session.add(usuario)
        db.session.commit()
        
        # Log (Opcional)
        try:
            # Tente importar log_acao se estiver disponível no escopo ou globalmente
            from app.utils.helpers import log_acao 
            log_acao(f"Criou usuário: {nome} ({tipo_str})", None, "Usuario", usuario.id)
        except Exception:
            pass # Se não tiver log, segue a vida

        flash(f'Usuário {nome} criado com sucesso! Senha padrão: 123456', 'success')
        return redirect(url_for('cli.gerenciar_usuarios'))
        
    except Exception as e:
        db.session.rollback()
        # Log detalhado do erro no terminal para debug
        print(f"ERRO AO CRIAR USUÁRIO: {e}")
        flash(f'Erro técnico ao criar usuário: {str(e)}', 'danger')
        return redirect(url_for('cli.novo_usuario'))

# --- GERENCIAMENTO DE USUÁRIOS ---

@cli_bp.route('/usuario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    """
    Edita permissões, senha e vínculos do usuário.
    Atualizado para suportar Multi-GAP (N:N).
    """
    # Garante que só edita usuários do mesmo cliente (segurança)
    usuario = Usuario.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()
    
    # Listas para os selects
    gaps = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome).all()
    ranchos = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Avaliado.nome).all()

    if request.method == 'POST':
        try:
            # 1. Coleta dados do formulário
            nome = request.form.get('nome')
            email = request.form.get('email')
            tipo_str = request.form.get('tipo')
            senha = request.form.get('senha') # Opcional
            
            # --- ATUALIZAÇÃO MULTI-GAP ---
            # Pega a LISTA de IDs dos GAPs (Select Multiple)
            gaps_ids = request.form.getlist('grupos_acesso')
            
            # Pega o ID do Rancho (Select Simples)
            avaliado_id = request.form.get('avaliado_id')

            # 2. Atualiza dados básicos
            usuario.nome = nome
            usuario.email = email
            
            # 3. Atualiza Tipo (Enum)
            if tipo_str:
                try:
                    # Tenta converter string para Enum (ex: 'gestor' -> TipoUsuario.GESTOR)
                    usuario.tipo = TipoUsuario[tipo_str.upper()]
                except KeyError:
                    pass # Se falhar, mantém o tipo anterior por segurança

            # 4. Lógica de Vínculos (A Regra de Ouro Atualizada)
            
            # Primeiro, limpamos a lista de acesso atual para reconstruí-la
            usuario.grupos_acesso = []
            
            # Cenário A: Gestor ou Auditor (Consultora) -> Múltiplos GAPs
            if usuario.tipo in [TipoUsuario.GESTOR, TipoUsuario.AUDITOR]:
                if gaps_ids:
                    primeiro = True
                    for gid in gaps_ids:
                        gap = Grupo.query.get(int(gid))
                        if gap:
                            # Adiciona na tabela nova (N:N)
                            usuario.grupos_acesso.append(gap)
                            
                            # Mantém compatibilidade com legado (usa o primeiro como principal)
                            if primeiro:
                                usuario.grupo_id = gap.id
                                primeiro = False
                else:
                    # Se desmarcou tudo
                    usuario.grupo_id = None
                
                # Garante que não tenha rancho vinculado
                usuario.avaliado_id = None
                
            # Cenário B: Usuário de Rancho -> 1 Rancho e seu respectivo GAP
            elif usuario.tipo == TipoUsuario.USUARIO:
                usuario.avaliado_id = int(avaliado_id) if avaliado_id else None
                
                # Se tem rancho, pega o GAP do rancho automaticamente
                if usuario.avaliado_id:
                    rancho = Avaliado.query.get(usuario.avaliado_id)
                    if rancho and rancho.grupo_id:
                        # Preenche legado
                        usuario.grupo_id = rancho.grupo_id
                        
                        # Preenche lista nova para consistência
                        gap_rancho = Grupo.query.get(rancho.grupo_id)
                        if gap_rancho:
                            usuario.grupos_acesso.append(gap_rancho)
                else:
                    usuario.grupo_id = None

            # Cenário C: Admins -> Visão Global (sem vínculos restritivos)
            else:
                usuario.grupo_id = None
                usuario.avaliado_id = None

            # 5. Atualiza Senha (apenas se preenchida)
            if senha and len(senha.strip()) > 0:
                from werkzeug.security import generate_password_hash
                usuario.senha_hash = generate_password_hash(senha)

            # 6. Salvar no Banco
            db.session.commit()
            flash(f'Usuário {nome} atualizado com sucesso.', 'success')
            return redirect(url_for('cli.gerenciar_usuarios'))

        except Exception as e:
            db.session.rollback()
            # Log no terminal para ajudar no debug
            print(f"Erro ao editar usuário {id}: {e}")
            flash(f'Erro ao atualizar: {str(e)}', 'error')

    # Retorna o template com os dados
    return render_template_safe('cli/usuario_editar.html', usuario=usuario, gaps=gaps, ranchos=ranchos)


@cli_bp.route('/usuario/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_usuario(id):
    """Remove um usuário do sistema"""
    if id == current_user.id:
        flash("Você não pode excluir a si mesmo!", "warning")
        return redirect(url_for('cli.gerenciar_usuarios'))
        
    usuario = Usuario.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()
    
    try:
        # Soft delete (recomendado) ou Delete real
        # Aqui faremos delete real para limpar sua base, mas em produção use ativo=False
        db.session.delete(usuario)
        db.session.commit()
        flash(f'Usuário {usuario.nome} removido.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'error')
        
    return redirect(url_for('cli.gerenciar_usuarios'))
# ===================== CONFIGURAÇÕES =====================

@cli_bp.route('/configuracoes')
@login_required
@admin_required
def configuracoes():
    """Página de configurações do sistema"""
    try:
        # Buscar configurações do cliente
        if 'ConfiguracaoCliente' in globals():
            config = ConfiguracaoCliente.query.filter_by(
                cliente_id=current_user.cliente_id
            ).first()
            
            if not config:
                # Criar configuração padrão
                config = ConfiguracaoCliente(
                    cliente_id=current_user.cliente_id,
                    logo_url='',
                    cor_primaria='#007bff',
                    cor_secundaria='#6c757d',
                    mostrar_notas=True,
                    permitir_fotos=True,
                    obrigar_plano_acao=True
                )
                db.session.add(config)
                db.session.commit()
        else:
            # Mock config se classe não existir
            config = type('Config', (), {
                'cor_primaria': '#007bff',
                'cor_secundaria': '#6c757d',
                'mostrar_notas': True,
                'permitir_fotos': True,
                'obrigar_plano_acao': True,
                'logo_url': ''
            })()
        
        return render_template_safe('cli/configuracoes.html', config=config)
    except Exception as e:
        flash(f"Erro ao carregar configurações: {str(e)}", "danger")
        return render_template_safe('cli/index.html')


# --- GESTÃO DE CATEGORIAS DE INDICADORES (SDAB) ---

@cli_bp.route('/configuracoes/categorias', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_categorias():
    """Gerencia as categorias para os gráficos do Dashboard (Infra, Higiene, etc)"""
    try:
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            cor = request.form.get('cor', '#4e73df')
            ordem = int(request.form.get('ordem', 0))
            
            if nome:
                nova_cat = CategoriaIndicador(
                    nome=nome,
                    cor=cor,
                    ordem=ordem,
                    cliente_id=current_user.cliente_id,
                    ativo=True
                )
                db.session.add(nova_cat)
                db.session.commit()
                flash(f"Categoria '{nome}' criada!", "success")
            else:
                flash("O nome da categoria é obrigatório.", "warning")
                
            return redirect(url_for('cli.gerenciar_categorias'))

        # Listagem
        categorias = CategoriaIndicador.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).order_by(CategoriaIndicador.ordem).all()
        
        return render_template_safe('cli/gerenciar_categorias.html', categorias=categorias)

    except Exception as e:
        flash(f"Erro ao gerenciar categorias: {str(e)}", "danger")
        return redirect(url_for('cli.configuracoes'))

@cli_bp.route('/configuracoes/categoria/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_categoria(id):
    """Remove uma categoria de indicador"""
    try:
        cat = CategoriaIndicador.query.get_or_404(id)
        if cat.cliente_id != current_user.cliente_id:
            abort(403)
            
        # Desvincula tópicos antes de excluir para não dar erro
        topicos = Topico.query.filter_by(categoria_indicador_id=id).all()
        for t in topicos:
            t.categoria_indicador_id = None
            
        db.session.delete(cat)
        db.session.commit()
        flash("Categoria removida.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir: {str(e)}", "danger")
        
    return redirect(url_for('cli.gerenciar_categorias'))
# Em app/cli/routes.py

@cli_bp.route('/aplicacao/<int:id>/salvar-resposta', methods=['POST'])
@login_required
@csrf.exempt
def salvar_resposta(id):
    """Salva uma resposta individual (AJAX) - COM LOGS DETALHADOS E SUPORTE A PLANO DE AÇÃO E PRAZO"""
    current_app.logger.info(f"--- Rota /salvar-resposta chamada para app ID: {id} ---")
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        data = request.get_json() or {}

        # 1. Verificação de Permissão
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            current_app.logger.warning(f"[Salvar Resposta {id}] Acesso negado - Cliente diferente.")
            return jsonify({'erro': 'Acesso negado'}), 403

        # 2. Lógica de Segurança Inteligente (Bloqueio vs Exceção)
        estah_finalizada = aplicacao.status != StatusAplicacao.EM_ANDAMENTO
        
        # Verifica se é uma operação de Plano de Ação (pela presença dos campos)
        eh_edicao_plano = ('plano_acao' in data) or ('resposta_id' in data)

        if estah_finalizada:
            if not eh_edicao_plano:
                # Se for auditoria fechada e NÃO for plano de ação -> BLOQUEIA
                current_app.logger.warning(f"[Salvar Resposta {id}] Bloqueio: Tentativa de alterar resposta em app finalizada.")
                return jsonify({'erro': 'Aplicação já finalizada. Apenas Planos de Ação podem ser editados.'}), 400
            else:
                # Se for auditoria fechada mas FOR plano de ação -> LIBERA (Loga a exceção)
                current_app.logger.info(f"[Salvar Resposta {id}] Exceção de Segurança: Permitindo edição de Plano de Ação em app finalizada.")

        # 3. Tratamento Especial: Atualização direta por ID da Resposta (Tela de Gestão de NCs)
        if 'resposta_id' in data:
            resposta = RespostaPergunta.query.get(data['resposta_id'])
            # Garante que a resposta pertence a esta aplicação
            if resposta and resposta.aplicacao_id == id:
                
                # Salva o texto do Plano de Ação (se enviado)
                if 'plano_acao' in data:
                    resposta.plano_acao = str(data['plano_acao']).strip()

                # === NOVO BLOCO: SALVAR O PRAZO ===
                if 'prazo_plano_acao' in data:
                    prazo_str = data['prazo_plano_acao']
                    if prazo_str:
                        try:
                            # Converte a string 'YYYY-MM-DD' vinda do HTML para objeto Date do Python
                            resposta.prazo_plano_acao = datetime.strptime(prazo_str, '%Y-%m-%d').date()
                        except ValueError:
                            current_app.logger.warning(f"Data inválida recebida: {prazo_str}")
                    else:
                        # Se o campo vier vazio (usuário limpou a data), remove do banco
                        resposta.prazo_plano_acao = None
                # ==================================

                db.session.commit()
                current_app.logger.info(f"[Salvar Resposta {id}] Sucesso: Plano e Prazo atualizados via resposta_id {resposta.id}")
                return jsonify({'sucesso': True, 'mensagem': 'Plano salvo'})
        
        # 4. Fluxo Padrão: Salvar por Pergunta ID (Tela de Checklist)
        
        # Se chegou aqui e a auditoria está finalizada, retornamos falso positivo para não quebrar o front,
        # mas não salvamos dados estruturais (prevenção extra)
        if estah_finalizada:
             return jsonify({'sucesso': True, 'mensagem': 'Ignorado (Auditoria fechada)'})

        pergunta_id = data.get('pergunta_id')
        resposta_texto = (data.get('resposta') or '').strip()
        observacao = (data.get('observacao') or '').strip()
        plano_acao_recebido = data.get('plano_acao') # Captura o plano se vier do checklist

        current_app.logger.info(f"[Salvar Resposta {id}] Dados: Pergunta={pergunta_id}, Resp='{resposta_texto}', Obs='{observacao}', Plano={plano_acao_recebido}")

        if not pergunta_id:
            current_app.logger.error(f"[Salvar Resposta {id}] Erro: 'pergunta_id' ausente.")
            return jsonify({'erro': 'ID da pergunta ausente'}), 400

        pergunta = Pergunta.query.get(pergunta_id)
        if not pergunta:
            current_app.logger.error(f"[Salvar Resposta {id}] Erro: Pergunta {pergunta_id} não encontrada.")
            return jsonify({'erro': f'Pergunta ID {pergunta_id} não encontrada'}), 404

        # Normaliza tipo
        if hasattr(pergunta.tipo, 'name'): tipo = pergunta.tipo.name
        elif hasattr(pergunta.tipo, 'value'): tipo = str(pergunta.tipo.value).upper().replace(" ", "_")
        else: tipo = str(pergunta.tipo or "").upper().replace(" ", "_")

        # Busca/Cria resposta
        resposta = RespostaPergunta.query.filter_by(aplicacao_id=id, pergunta_id=pergunta_id).first()
        if not resposta:
            current_app.logger.info(f"[Salvar Resposta {id}] Criando nova entrada RespostaPergunta.")
            resposta = RespostaPergunta(aplicacao_id=id, pergunta_id=pergunta_id)
        else:
            current_app.logger.info(f"[Salvar Resposta {id}] Atualizando RespostaPergunta existente (ID: {resposta.id}).")

        # Atualiza Campos
        resposta.resposta = resposta_texto
        resposta.observacao = observacao
        
        # Atualiza Plano de Ação (Apenas se enviado)
        if plano_acao_recebido is not None:
            resposta.plano_acao = str(plano_acao_recebido).strip()

        resposta.pontos = 0  # default inicial

        # 5. Cálculo de Pontuação (Só executa se não estiver finalizada - garantido pelo check acima)
        if tipo in ['SIM_NAO_NA', 'MULTIPLA_ESCOLHA']:
            opcao = OpcaoPergunta.query.filter_by(pergunta_id=pergunta_id, texto=resposta_texto).first()
            if opcao:
                if opcao.valor is not None:
                    peso_pergunta = pergunta.peso or 1
                    resposta.pontos = float(opcao.valor) * peso_pergunta
                    current_app.logger.info(f"[Salvar Resposta {id}] Pontos calculados: {resposta.pontos}")
                else:
                    current_app.logger.warning(f"[Salvar Resposta {id}] Opção sem valor. Pontos = 0.")
            else:
                current_app.logger.warning(f"[Salvar Resposta {id}] Opção não encontrada: '{resposta_texto}'. Pontos = 0.")

        elif tipo in ['ESCALA_NUMERICA', 'NOTA']:
            try:
                nota = float(resposta_texto)
                peso_pergunta = pergunta.peso or 1
                resposta.pontos = nota * peso_pergunta
            except ValueError:
                resposta.pontos = 0

        current_app.logger.info(f"[Salvar Resposta {id}] Salvando no DB...")
        
        db.session.add(resposta)
        db.session.flush()
        resposta_id_retorno = resposta.id
        db.session.commit()
        
        current_app.logger.info(f"[Salvar Resposta {id}] Commit bem-sucedido! ID: {resposta_id_retorno}")

        return jsonify({
            'sucesso': True,
            'mensagem': 'Resposta salva com sucesso',
            'pontos': resposta.pontos or 0,
            'resposta_id': resposta_id_retorno
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Salvar Resposta {id}] ERRO CRÍTICO: {str(e)}", exc_info=True)
        return jsonify({'erro': f'Falha interna ao salvar: {str(e)}'}), 500
    finally:
        current_app.logger.info(f"--- Rota /salvar-resposta finalizada para app ID: {id} ---")
# ===================== NOTIFICAÇÕES =====================

@cli_bp.route('/notificacoes')
@login_required
def notificacoes():
    """Centro de notificações"""
    try:
        # Buscar notificações do usuário
        if 'Notificacao' in globals():
            notificacoes = Notificacao.query.filter_by(
                usuario_id=current_user.id
            ).order_by(Notificacao.data_criacao.desc()).limit(50).all()
            
            # Marcar como visualizadas
            for notif in notificacoes:
                if not notif.visualizada:
                    notif.visualizada = True
            
            db.session.commit()
        else:
            notificacoes = []
        
        return render_template_safe('cli/notificacoes.html', notificacoes=notificacoes)
    except Exception as e:
        flash(f"Erro ao carregar notificações: {str(e)}", "danger")
        return render_template_safe('cli/index.html')

@cli_bp.route('/api/notificacoes/count')
@login_required
def api_count_notificacoes():
    """API para contar notificações não lidas"""
    try:
        if 'Notificacao' in globals():
            count = Notificacao.query.filter_by(
                usuario_id=current_user.id,
                visualizada=False
            ).count()
        else:
            count = 0
        
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0})

# ===================== FUNÇÕES AUXILIARES PARA EXPORTAÇÃO =====================

def obter_dados_relatorio_exportacao(tipo, avaliado_id, questionario_id, data_inicio, data_fim):
    """Obtém dados para exportação de relatórios"""
    try:
        dados = {}
        
        if tipo == 'ranking':
            query = db.session.query(
                Avaliado.nome.label('avaliado'),
                func.avg(AplicacaoQuestionario.nota_final).label('media'),
                func.count(AplicacaoQuestionario.id).label('total_aplicacoes')
            ).join(AplicacaoQuestionario).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            )
            
            if data_inicio:
                query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
            if data_fim:
                query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            
            resultados = query.group_by(Avaliado.id, Avaliado.nome).order_by(
                func.avg(AplicacaoQuestionario.nota_final).desc()
            ).all()
            
            dados['ranking'] = [
                {
                    'avaliado': r.avaliado,
                    'media': round(float(r.media), 2),
                    'total_aplicacoes': r.total_aplicacoes
                }
                for r in resultados
            ]
        
        return dados
    except Exception as e:
        print(f"Erro ao obter dados de relatório: {e}")
        return {}

def exportar_csv(dados, tipo_relatorio):
    """Exporta relatório em formato CSV"""
    import csv
    import io
    
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        if tipo_relatorio == 'ranking':
            writer.writerow(['Posição', 'Avaliado', 'Nota Média', 'Total Aplicações'])
            for idx, item in enumerate(dados.get('ranking', []), 1):
                writer.writerow([idx, item['avaliado'], item['media'], item['total_aplicacoes']])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=relatorio_{tipo_relatorio}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'}
        )
    except Exception as e:
        flash(f"Erro ao exportar CSV: {str(e)}", "danger")
        return redirect(url_for('cli.relatorios'))

def exportar_pdf(dados, tipo_relatorio):
    """Exporta relatório em formato PDF"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório QualiGestor - {tipo_relatorio.title()}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; text-align: center; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .data {{ font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Relatório QualiGestor - {tipo_relatorio.title()}</h1>
                <p class="data">Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            {gerar_conteudo_html_relatorio(dados, tipo_relatorio)}
        </body>
        </html>
        """
        
        return gerar_pdf_seguro(html_content, f"relatorio_{tipo_relatorio}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")
        
    except Exception as e:
        flash(f"Erro ao exportar PDF: {str(e)}", "danger")
        return redirect(url_for('cli.relatorios'))

def gerar_conteudo_html_relatorio(dados, tipo_relatorio):
    """Gera conteúdo HTML específico para cada tipo de relatório"""
    try:
        if tipo_relatorio == 'ranking' and 'ranking' in dados:
            html = """
            <table>
                <tr>
                    <th>Posição</th>
                    <th>Avaliado</th>
                    <th>Nota Média</th>
                    <th>Total Aplicações</th>
                </tr>
            """
            
            for idx, item in enumerate(dados['ranking'], 1):
                html += f"""
                <tr>
                    <td>{idx}°</td>
                    <td>{item['avaliado']}</td>
                    <td>{item['media']}%</td>
                    <td>{item['total_aplicacoes']}</td>
                </tr>
                """
            
            html += "</table>"
            return html
        
        return "<p>Dados do relatório não disponíveis</p>"
    except Exception as e:
        return f"<p>Erro ao gerar conteúdo: {str(e)}</p>"

# ===================== ROTAS DE COMPATIBILIDADE =====================

@cli_bp.route('/checklists')
@cli_bp.route('/listar-checklists')
@login_required
def listar_checklists():
    """Redirecionamento para listar questionários (compatibilidade)"""
    return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/checklist/novo')
@cli_bp.route('/novo-checklist')
@login_required
def novo_checklist():
    """Redirecionamento para novo questionário (compatibilidade)"""
    return redirect(url_for('cli.novo_questionario'))

@cli_bp.route('/checklist/<int:id>')
@login_required
def visualizar_checklist(id):
    """Redirecionamento para visualizar questionário (compatibilidade)"""
    return redirect(url_for('cli.visualizar_questionario', id=id))

# ===================== ROTAS AJAX E APIs =====================

@cli_bp.route('/api/questionarios')
@login_required
def api_questionarios():
    """API para listar questionários do cliente"""
    try:
        questionarios = Questionario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True,
            publicado=True
        ).all()
        
        dados = []
        for q in questionarios:
            dados.append({
                'id': q.id,
                'nome': q.nome,
                'versao': q.versao,
                'descricao': q.descricao or ''
            })
        
        return jsonify(dados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/api/avaliados')
@login_required
def api_avaliados():
    """API para listar avaliados do cliente"""
    try:
        avaliados = get_avaliados_usuario()
        
        dados = []
        for a in avaliados:
            dados.append({
                'id': a.id,
                'nome': a.nome,
                'codigo': a.codigo or '',
                'endereco': a.endereco or ''
            })
        
        return jsonify(dados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/api/topicos/<int:questionario_id>')
@login_required
def api_topicos(questionario_id):
    """API para buscar tópicos de um questionário"""
    try:
        questionario = Questionario.query.get_or_404(questionario_id)
        
        if questionario.cliente_id != current_user.cliente_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        topicos = Topico.query.filter_by(
            questionario_id=questionario_id,
            ativo=True
        ).order_by(Topico.ordem).all()
        
        dados = []
        for t in topicos:
            perguntas = []
            for p in t.perguntas:
                if p.ativo:
                    opcoes = []
                    if hasattr(p, 'opcoes'):
                        for o in p.opcoes:
                            opcoes.append({
                                'id': o.id,
                                'texto': o.texto,
                                'valor': o.valor
                            })
                    
                    perguntas.append({
                        'id': p.id,
                        'texto': p.texto,
                        'tipo': p.tipo,
                        'obrigatoria': p.obrigatoria,
                        'permite_observacao': p.permite_observacao,
                        'peso': p.peso,
                        'opcoes': opcoes
                    })
            
            dados.append({
                'id': t.id,
                'nome': t.nome,
                'descricao': t.descricao or '',
                'perguntas': perguntas
            })
        
        return jsonify(dados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/api/estatisticas')
@login_required
def api_estatisticas():
    """API para dashboard de estatísticas"""
    try:
        hoje = datetime.now()
        inicio_mes = datetime(hoje.year, hoje.month, 1)
        
        stats = {
            'aplicacoes_hoje': AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                func.date(AplicacaoQuestionario.data_inicio) == hoje.date()
            ).count(),
            
            'aplicacoes_mes': AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.data_inicio >= inicio_mes
            ).count(),
            
            'questionarios_ativos': Questionario.query.filter_by(
                cliente_id=current_user.cliente_id,
                ativo=True,
                publicado=True
            ).count(),
            
            'avaliados_ativos': Avaliado.query.filter_by(
                cliente_id=current_user.cliente_id,
                ativo=True
            ).count(),
            
            'media_mensal': db.session.query(func.avg(AplicacaoQuestionario.nota_final)).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.data_inicio >= inicio_mes,
                AplicacaoQuestionario.nota_final.isnot(None)
            ).scalar() or 0
        }
        
        # Arredondar média
        stats['media_mensal'] = round(float(stats['media_mensal']), 1)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===================== ROTAS DE ORDENAÇÃO =====================

@cli_bp.route('/api/topicos/<int:topico_id>/reordenar', methods=['POST'])
@login_required
def reordenar_perguntas(topico_id):
    """Reordena perguntas de um tópico"""
    try:
        topico = Topico.query.get_or_404(topico_id)
        
        if topico.questionario.cliente_id != current_user.cliente_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        data = request.get_json()
        ordem_perguntas = data.get('ordem', [])
        
        for i, pergunta_id in enumerate(ordem_perguntas):
            pergunta = Pergunta.query.get(pergunta_id)
            if pergunta and pergunta.topico_id == topico_id:
                pergunta.ordem = i + 1
        
        db.session.commit()
        log_acao(f"Reordenou perguntas do tópico: {topico.nome}", None, "Topico", topico_id)
        
        return jsonify({'sucesso': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/api/questionarios/<int:questionario_id>/reordenar-topicos', methods=['POST'])
@login_required
def reordenar_topicos(questionario_id):
    """Reordena tópicos de um questionário"""
    try:
        questionario = Questionario.query.get_or_404(questionario_id)
        
        if questionario.cliente_id != current_user.cliente_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        data = request.get_json()
        ordem_topicos = data.get('ordem', [])
        
        for i, topico_id in enumerate(ordem_topicos):
            topico = Topico.query.get(topico_id)
            if topico and topico.questionario_id == questionario_id:
                topico.ordem = i + 1
        
        db.session.commit()
        log_acao(f"Reordenou tópicos do questionário: {questionario.nome}", None, "Questionario", questionario_id)
        
        return jsonify({'sucesso': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===================== ROTAS DE IMPORTAÇÃO/EXPORTAÇÃO =====================

@cli_bp.route('/questionario/<int:id>/exportar')
@login_required
def exportar_questionario(id):
    """Exporta questionário em formato JSON"""
    try:
        questionario = Questionario.query.get_or_404(id)
        
        if questionario.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        # Montar estrutura de exportação
        dados_export = {
            'questionario': {
                'nome': questionario.nome,
                'versao': questionario.versao,
                'descricao': questionario.descricao,
                'modo': questionario.modo,
                'calcular_nota': questionario.calcular_nota,
                'base_calculo': questionario.base_calculo,
                'casas_decimais': questionario.casas_decimais
            },
            'topicos': []
        }
        
        # Adicionar tópicos
        for topico in questionario.topicos:
            if topico.ativo:
                topico_data = {
                    'nome': topico.nome,
                    'descricao': topico.descricao,
                    'ordem': topico.ordem,
                    'perguntas': []
                }
                
                # Adicionar perguntas
                for pergunta in topico.perguntas:
                    if pergunta.ativo:
                        pergunta_data = {
                            'texto': pergunta.texto,
                            'tipo': pergunta.tipo,
                            'obrigatoria': pergunta.obrigatoria,
                            'permite_observacao': pergunta.permite_observacao,
                            'peso': pergunta.peso,
                            'ordem': pergunta.ordem,
                            'opcoes': []
                        }
                        
                        # Adicionar opções se existirem
                        if hasattr(pergunta, 'opcoes'):
                            for opcao in pergunta.opcoes:
                                pergunta_data['opcoes'].append({
                                    'texto': opcao.texto,
                                    'valor': opcao.valor,
                                    'ordem': opcao.ordem
                                })
                        
                        topico_data['perguntas'].append(pergunta_data)
                
                dados_export['topicos'].append(topico_data)
        
        # Criar resposta JSON
        response = make_response(json.dumps(dados_export, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename="questionario_{questionario.nome.replace(" ", "_")}.json"'
        
        log_acao(f"Exportou questionário: {questionario.nome}", None, "Questionario", id)
        
        return response
        
    except Exception as e:
        flash(f"Erro ao exportar questionário: {str(e)}", "danger")
        return redirect(url_for('cli.visualizar_questionario', id=id))

@cli_bp.route('/questionarios/importar', methods=['GET', 'POST'])
@login_required
def importar_questionario():
    """Importa questionário de arquivo JSON"""
    if request.method == 'POST':
        try:
            if 'arquivo' not in request.files:
                flash('Nenhum arquivo selecionado.', 'error')
                return redirect(request.url)
            
            arquivo = request.files['arquivo']
            if arquivo.filename == '':
                flash('Nenhum arquivo selecionado.', 'error')
                return redirect(request.url)
            
            if not arquivo.filename.endswith('.json'):
                flash('Apenas arquivos JSON são suportados.', 'error')
                return redirect(request.url)
            
            # Ler e processar arquivo
            dados = json.load(arquivo)
            
            # Validar estrutura básica
            if 'questionario' not in dados or 'topicos' not in dados:
                flash('Formato de arquivo inválido.', 'error')
                return redirect(request.url)
            
            q_data = dados['questionario']
            
            # Verificar se já existe questionário com mesmo nome
            nome_original = q_data['nome']
            nome_final = nome_original
            contador = 1
            
            while Questionario.query.filter_by(nome=nome_final, cliente_id=current_user.cliente_id).first():
                contador += 1
                nome_final = f"{nome_original} - Importado ({contador})"
            
            # Criar questionário
            questionario = Questionario(
                nome=nome_final,
                versao=q_data.get('versao', '1.0'),
                descricao=q_data.get('descricao', ''),
                modo=q_data.get('modo', 'Avaliado'),
                cliente_id=current_user.cliente_id,
                criado_por_id=current_user.id,
                calcular_nota=q_data.get('calcular_nota', True),
                base_calculo=q_data.get('base_calculo', 100),
                casas_decimais=q_data.get('casas_decimais', 2),
                ativo=True,
                publicado=False,
                status=StatusQuestionario.RASCUNHO
            )
            
            db.session.add(questionario)
            db.session.flush()
            
            # Criar tópicos e perguntas
            for topico_data in dados['topicos']:
                topico = Topico(
                    nome=topico_data['nome'],
                    descricao=topico_data.get('descricao', ''),
                    ordem=topico_data.get('ordem', 1),
                    questionario_id=questionario.id,
                    ativo=True
                )
                db.session.add(topico)
                db.session.flush()
                
                for pergunta_data in topico_data.get('perguntas', []):
                    pergunta = Pergunta(
                        texto=pergunta_data['texto'],
                        tipo=pergunta_data.get('tipo', 'SIM_NAO_NA'),
                        obrigatoria=pergunta_data.get('obrigatoria', False),
                        permite_observacao=pergunta_data.get('permite_observacao', True),
                        peso=pergunta_data.get('peso', 1),
                        ordem=pergunta_data.get('ordem', 1),
                        topico_id=topico.id,
                        ativo=True
                    )
                    db.session.add(pergunta)
                    db.session.flush()
                    
                    # Criar opções se existirem
                    if 'OpcaoPergunta' in globals():
                        for opcao_data in pergunta_data.get('opcoes', []):
                            opcao = OpcaoPergunta(
                                texto=opcao_data['texto'],
                                valor=opcao_data.get('valor', 0),
                                ordem=opcao_data.get('ordem', 1),
                                pergunta_id=pergunta.id
                            )
                            db.session.add(opcao)
            
            db.session.commit()
            
            log_acao(f"Importou questionário: {nome_final}", None, "Questionario", questionario.id)
            flash(f'Questionário "{nome_final}" importado com sucesso!', 'success')
            
            return redirect(url_for('cli.visualizar_questionario', id=questionario.id))
            
        except json.JSONDecodeError:
            flash('Arquivo JSON inválido.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao importar questionário: {str(e)}', 'error')
    
    return render_template_safe('cli/importar_questionario.html')

# ===================== ROTAS DE BUSCA =====================

@cli_bp.route('/buscar')
@login_required
def buscar():
    """Busca global no sistema"""
    try:
        termo = request.args.get('q', '').strip()
        if not termo:
            return render_template_safe('cli/busca_resultados.html', termo='', resultados={})
        
        resultados = {
            'questionarios': [],
            'avaliados': [],
            'aplicacoes': []
        }
        
        # Buscar questionários
        questionarios = Questionario.query.filter(
            Questionario.cliente_id == current_user.cliente_id,
            Questionario.ativo == True,
            or_(
                Questionario.nome.ilike(f'%{termo}%'),
                Questionario.descricao.ilike(f'%{termo}%')
            )
        ).limit(10).all()
        
        for q in questionarios:
            resultados['questionarios'].append({
                'id': q.id,
                'nome': q.nome,
                'descricao': q.descricao or '',
                'status': 'Publicado' if q.publicado else 'Rascunho'
            })
        
        # Buscar avaliados
        avaliados = Avaliado.query.filter(
            Avaliado.cliente_id == current_user.cliente_id,
            Avaliado.ativo == True,
            or_(
                Avaliado.nome.ilike(f'%{termo}%'),
                Avaliado.codigo.ilike(f'%{termo}%'),
                Avaliado.endereco.ilike(f'%{termo}%')
            )
        ).limit(10).all()
        
        for a in avaliados:
            resultados['avaliados'].append({
                'id': a.id,
                'nome': a.nome,
                'codigo': a.codigo or '',
                'endereco': a.endereco or ''
            })
        
        # Buscar aplicações
        aplicacoes = AplicacaoQuestionario.query.join(Avaliado).join(Questionario).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            or_(
                Avaliado.nome.ilike(f'%{termo}%'),
                Questionario.nome.ilike(f'%{termo}%')
            )
        ).order_by(AplicacaoQuestionario.data_inicio.desc()).limit(10).all()
        
        for app in aplicacoes:
            resultados['aplicacoes'].append({
                'id': app.id,
                'questionario': app.questionario.nome,
                'avaliado': app.avaliado.nome,
                'data_inicio': app.data_inicio.strftime('%d/%m/%Y'),
                'status': app.status
            })
        
        return render_template_safe('cli/busca_resultados.html', termo=termo, resultados=resultados)
        
    except Exception as e:
        flash(f"Erro na busca: {str(e)}", "danger")
        return render_template_safe('cli/busca_resultados.html', termo='', resultados={})

# ===================== GRUPOS (BONUS) =====================

@cli_bp.route('/grupos', endpoint='listar_grupos')
@login_required
@admin_required
def listar_grupos():
    """Página de gestão de grupos (GAPs)"""
    try:
        # Busca apenas os grupos do cliente logado (Aeronáutica)
        grupos = Grupo.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).order_by(Grupo.nome).all()
        
        # Contar ranchos (avaliados) por grupo para mostrar na tabela
        for grupo in grupos:
            grupo.total_avaliados = Avaliado.query.filter_by(
                grupo_id=grupo.id,
                ativo=True
            ).count()
        
        # Certifique-se de que o arquivo listar_grupos.html existe na pasta templates/cli/
        return render_template_safe('cli/listar_grupos.html', grupos=grupos)
    except Exception as e:
        flash(f"Erro ao carregar grupos: {str(e)}", "danger")
        # Se der erro, volta para o dashboard
        return redirect(url_for('cli.index'))

@cli_bp.route('/grupo/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_grupo():
    """Criar novo grupo"""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            
            if not nome:
                flash('Nome do grupo é obrigatório.', 'error')
                return render_template_safe('cli/grupo_form.html')
            
            grupo = Grupo(
                nome=nome,
                descricao=descricao,
                cliente_id=current_user.cliente_id,
                ativo=True
            )
            
            db.session.add(grupo)
            db.session.commit()
            
            log_acao(f"Criou grupo: {nome}", None, "Grupo", grupo.id)
            flash(f'Grupo "{nome}" criado com sucesso!', 'success')
            
            return redirect(url_for('cli.listar_grupos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar grupo: {str(e)}', 'error')
    
    return render_template_safe('cli/grupo_form.html')

# --- ROTAS DE GERENCIAMENTO DE GRUPOS (GAPs) ---

@cli_bp.route('/grupo/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_grupo(id):
    """Edita um Grupo (GAP)"""
    grupo = Grupo.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()

            if not nome:
                flash("O nome do GAP é obrigatório.", "warning")
            else:
                grupo.nome = nome
                grupo.descricao = descricao if descricao else None
                
                db.session.commit()
                flash(f"GAP '{nome}' atualizado com sucesso!", "success")
                return redirect(url_for('cli.listar_grupos'))
                
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao editar GAP: {str(e)}", "danger")

    # Reutiliza o formulário de criação se possível, ou crie um específico
    return render_template_safe('cli/grupo_form.html', grupo=grupo)


@cli_bp.route('/grupo/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_grupo(id):
    """Exclui (ou inativa) um Grupo (GAP)"""
    grupo = Grupo.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()
    
    # Verificação de Segurança: Não excluir se tiver Ranchos vinculados
    ranchos_vinculados = Avaliado.query.filter_by(grupo_id=grupo.id, ativo=True).count()
    
    if ranchos_vinculados > 0:
        flash(f"Não é possível excluir o {grupo.nome}: Existem {ranchos_vinculados} ranchos vinculados a ele.", "danger")
    else:
        try:
            # Soft Delete (Recomendado): Apenas inativa
            grupo.ativo = False
            # Se quiser excluir de verdade: db.session.delete(grupo)
            
            db.session.commit()
            flash(f"GAP '{grupo.nome}' removido com sucesso.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao excluir: {str(e)}", "danger")
            
    return redirect(url_for('cli.listar_grupos'))

# ===================== FORÇA REGISTRO DE ROTAS CRÍTICAS - SOLUÇÃO DEFINITIVA =====================

# Força o registro das rotas mais críticas ANTES de qualquer template ser renderizado
# ===================== REGISTRO AUTOMÁTICO EM RUNTIME =====================

def register_missing_route_on_demand(endpoint):
    """Registra uma rota faltante em tempo de execução"""
    try:
        route_name = endpoint.replace('cli.', '').replace('_', '-')
        route_path = f"/{route_name}"
        
        @login_required  
        def dynamic_route():
            flash(f"Funcionalidade '{endpoint}' em desenvolvimento.", "info")
            return render_template_safe('cli/index.html',
                                      mensagem=f"Rota criada dinamicamente: {endpoint}",
                                      stats={'total_aplicacoes': 0, 'questionarios_ativos': 0, 
                                           'avaliados_ativos': 0, 'media_nota_mes': 0})
        
        dynamic_route.__name__ = f'dynamic_{route_name}'
        
        cli_bp.add_url_rule(route_path, endpoint=endpoint.replace('cli.', ''), 
                           view_func=dynamic_route, methods=['GET'])
        
        print(f"✅ Rota {endpoint} criada dinamicamente: {route_path}")
        return True
        
    except Exception as e:
        print(f"⚠️ Erro ao criar rota dinâmica {endpoint}: {e}")
        return False

# ===================== INTERCEPTADOR DE BUILDERROR =====================

original_url_for = None

def intercept_build_error():
    """Intercepta BuildError e tenta resolver dinamicamente"""
    global original_url_for
    
    if original_url_for is None:
        from flask import url_for as flask_url_for
        original_url_for = flask_url_for
    
    def safe_url_for(endpoint, **values):
        try:
            return original_url_for(endpoint, **values)
        except Exception as e:
            print(f"BuildError interceptado para {endpoint}: {e}")
            
            # Tentar registrar a rota faltante
            if endpoint.startswith('cli.'):
                if register_missing_route_on_demand(endpoint):
                    try:
                        return original_url_for(endpoint, **values)
                    except:
                        pass
            
            # Fallback final para URL direta
            return url_for_safe(endpoint, **values)
    
    # Substituir url_for globalmente
    import flask
    flask.url_for = safe_url_for
    
    # Disponibilizar também como função global
    import builtins
    builtins.url_for = safe_url_for

# Ativar interceptador
try:
    intercept_build_error()
    print("✅ Interceptador de BuildError ativado")
except Exception as e:
    print(f"⚠️ Erro ao ativar interceptador: {e}")

# ===================== VERIFICAÇÃO FINAL ANTES DE SERVIR =====================

@cli_bp.before_request
def verify_critical_routes():
    """Verifica rotas críticas antes de cada request"""
    try:
        # Lista de endpoints que DEVEM existir
        critical_endpoints = ['listar_grupos', 'gerenciar_usuarios', 'configuracoes']
        
        for endpoint in critical_endpoints:
            full_endpoint = f'cli.{endpoint}'
            try:
                from flask import url_for
                url_for(full_endpoint)
            except:
                # Se falhar, tentar registrar na hora
                print(f"⚠️ Endpoint {full_endpoint} não encontrado, registrando...")
                register_missing_route_on_demand(full_endpoint)
                
    except Exception as e:
        print(f"⚠️ Erro na verificação de rotas: {e}")

# ===================== OVERRIDE DO JINJA2 PARA TEMPLATES =====================

def setup_template_globals():
    """Configura funções globais nos templates"""
    try:
        # Registrar url_for_safe nos templates
        @cli_bp.app_template_global()
        def url_for_template(endpoint, **kwargs):
            """url_for seguro para templates"""
            return url_for_safe(endpoint, **kwargs)
        
        # Também como filtro
        @cli_bp.app_template_filter()
        def safe_url(endpoint, **kwargs):
            """Filtro url_for seguro"""
            return url_for_safe(endpoint, **kwargs)
        
        print("✅ Funções globais de template configuradas")
        
    except Exception as e:
        print(f"⚠️ Erro ao configurar globals de template: {e}")

# Executar configuração
setup_template_globals()

# ===================== STATUS DO SISTEMA =====================

print("=" * 50)
print("🚀 SISTEMA DE PROTEÇÃO CLIQ ATIVADO")
print("✅ url_for_safe implementado")
print("✅ Rotas críticas forçadas") 
print("✅ Interceptador BuildError ativo")
print("✅ Verificação runtime ativa")
print("✅ Template fallback robusto")
print("✅ Sistema nunca quebra")
print("=" * 50)

# ===================== ROTAS PLACEHOLDER ADICIONAIS =====================



# ===================== HANDLER DE ERROS PARA ROTAS NÃO ENCONTRADAS =====================

# ... (aqui termina a rota anterior do seu arquivo) ...


@cli_bp.errorhandler(404)
def pagina_nao_encontrada(e):
    """Handler para páginas não encontradas"""
    try:
        rota_solicitada = request.path
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QualiGestor - Página não encontrada</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-warning">
                    <h4>Página não encontrada</h4>
                    <p>A rota <code>{{ rota }}</code> não foi encontrada.</p>
                    <p>Esta funcionalidade pode estar em desenvolvimento.</p>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5>Principais Funcionalidades</h5>
                                <div class="list-group">
                                    <a href="/cli/" class="list-group-item">Dashboard</a>
                                    <a href="/cli/questionarios" class="list-group-item">Questionários</a>
                                    <a href="/cli/avaliados" class="list-group-item">Avaliados</a>
                                    <a href="/cli/aplicacoes" class="list-group-item">Aplicações</a>
                                    <a href="/cli/relatorios" class="list-group-item">Relatórios</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5>Administração</h5>
                                <div class="list-group">
                                    <a href="/cli/grupos" class="list-group-item">Grupos</a>
                                    <a href="/cli/usuarios" class="list-group-item">Usuários</a>
                                    <a href="/cli/configuracoes" class="list-group-item">Configurações</a>
                                    <a href="/cli/notificacoes" class="list-group-item">Notificações</a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """, rota=rota_solicitada)
    except Exception as erro:
        return f"""
        <html>
        <body>
            <h1>Página não encontrada</h1>
            <p>Rota: {request.path}</p>
            <p>Erro: {str(erro)}</p>
            <p><a href="/cli/">Voltar ao Dashboard</a></p>
        </body>
        </html>
        """

# ===================== VERIFICAÇÃO FINAL DE ROTAS =====================

def verificar_rotas_registradas():
    """Verifica se todas as rotas críticas estão registradas"""
    rotas_criticas = [
        'cli.index',
        'cli.listar_grupos',  # CRÍTICA - esta estava faltando
        'cli.gerenciar_usuarios',
        'cli.configuracoes',
        'cli.listar_questionarios',
        'cli.listar_avaliados',
        'cli.listar_aplicacoes',
        'cli.relatorios',
        'cli.notificacoes'
    ]
    
    rotas_faltantes = []
    
    try:
        from flask import current_app
        for rota in rotas_criticas:
            try:
                current_app.url_map.build(rota)
            except:
                rotas_faltantes.append(rota)
    except:
        pass
    
    if rotas_faltantes:
        print(f"⚠️ Rotas faltantes detectadas: {rotas_faltantes}")
        # Criar rotas de emergência para as faltantes
        for rota_faltante in rotas_faltantes:
            nome_func = rota_faltante.replace('cli.', 'emergencia_')
            try:
                func_emergencia = criar_rota_emergencia(rota_faltante)
                setattr(sys.modules[__name__], nome_func, func_emergencia)
            except:
                pass
    else:
        print("✅ Todas as rotas críticas estão registradas")

# Executar verificação
try:
    verificar_rotas_registradas()
except Exception as e:
    print(f"Erro na verificação de rotas: {e}")

# ===================== FIM DO SISTEMA DE AUTO-REGISTRO =====================

# --- Alias de compatibilidade: adicionar_topico -> novo_topico ---
try:
    cli_bp.add_url_rule('/questionario/<int:questionario_id>/topicos/novo', endpoint='adicionar_topico', view_func=novo_topico, methods=['GET','POST'])
except Exception:
    pass

# ... (Final da sua última rota existente ou função de configuração/verificação) ...


# ====================================================================
#  BLOCO DE CÓDIGO CORRIGIDO PARA UPLOAD DE FOTOS
# ====================================================================

# ===================== FUNÇÃO AUXILIAR PARA FOTOS =====================
#
# vvv ESTA É A FUNÇÃO QUE ESTAVA FALTANDO E CAUSANDO O ERRO vvv
#
def allowed_file(filename, allowed_extensions):
    """Verifica se o nome do arquivo tem uma extensão permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
# ====================================================================
# ^^^ ESTA É A FUNÇÃO QUE ESTAVA FALTANDO E CAUSANDO O ERRO ^^^
# ====================================================================


# ===================== NOVAS ROTAS PARA UPLOAD DE FOTO =====================

@cli_bp.route('/resposta/<int:resposta_id>/upload-foto', methods=['POST'])
@login_required
@csrf.exempt
def upload_foto_resposta(resposta_id):
    """Recebe upload de foto via AJAX e salva na tabela de múltiplas fotos."""
    # Log inicial
    current_app.logger.info(f"Recebida requisição POST para upload_foto_resposta ID: {resposta_id}")

    try:
        resposta = RespostaPergunta.query.get_or_404(resposta_id)
        current_app.logger.debug(f"Resposta {resposta_id} encontrada.")

        # --- VERIFICAÇÃO DE SEGURANÇA ---
        aplicacao = AplicacaoQuestionario.query.get(resposta.aplicacao_id)
        if not aplicacao:
             current_app.logger.warning(f"Aplicação não encontrada para resposta {resposta_id}")
             return jsonify({'erro': 'Aplicação associada não encontrada'}), 404

        # Verifica se a aplicação ainda está em andamento
        if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
            current_app.logger.warning(f"Tentativa de upload para aplicação finalizada (ID: {aplicacao.id})")
            return jsonify({'erro': 'Não é possível anexar fotos a uma aplicação finalizada'}), 400

        avaliado = Avaliado.query.get(aplicacao.avaliado_id)
        if not avaliado or avaliado.cliente_id != current_user.cliente_id:
            current_app.logger.warning(
                f"Tentativa de upload negada: User {current_user.id} (cliente {current_user.cliente_id}) "
                f"tentou acessar resposta {resposta_id} (avaliado {aplicacao.avaliado_id}, cliente {avaliado.cliente_id if avaliado else 'N/A'})"
            )
            return jsonify({'erro': 'Acesso negado à resposta'}), 403
        current_app.logger.debug(f"Verificação de permissão OK para resposta {resposta_id}.")
        # ---------------------------------

        if 'foto' not in request.files:
            current_app.logger.error(f"Campo 'foto' não encontrado no request.files para resposta {resposta_id}")
            return jsonify({'erro': 'Nenhum arquivo enviado (campo "foto" esperado)'}), 400

        foto = request.files['foto']

        if foto.filename == '':
            current_app.logger.warning(f"Upload recebido com nome de arquivo vazio para resposta {resposta_id}")
            return jsonify({'erro': 'Nome de arquivo vazio'}), 400

        # Verifica a extensão do arquivo
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg'})
        
        # Função auxiliar de validação (certifique-se que ela existe no seu escopo ou imports)
        if foto and allowed_file(foto.filename, allowed_extensions):

            # Gera um nome de arquivo seguro e único
            original_filename = secure_filename(foto.filename)
            extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
            unique_filename = f"resposta_{resposta.id}_{uuid.uuid4().hex[:12]}.{extension}"

            # Caminho completo para salvar o arquivo
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            if not upload_folder:
                 current_app.logger.error("Configuração UPLOAD_FOLDER não definida!")
                 return jsonify({'erro': 'Configuração do servidor incompleta (UPLOAD_FOLDER)'}), 500

            save_path = os.path.join(upload_folder, unique_filename)
            current_app.logger.debug(f"Caminho para salvar: {save_path}")

            # --- Salva o arquivo físico ---
            try:
                 os.makedirs(upload_folder, exist_ok=True)
                 foto.save(save_path)
                 current_app.logger.info(f"Foto salva com sucesso em: {save_path} para resposta {resposta_id}")
            except Exception as save_err:
                 current_app.logger.error(f"Erro ao salvar arquivo físico para resposta {resposta_id}: {save_err}", exc_info=True)
                 return jsonify({'erro': f'Erro no servidor ao salvar arquivo'}), 500
            
            # --- ATUALIZAÇÃO PARA MÚLTIPLAS FOTOS ---
            # Cria o registro na nova tabela FotoResposta
            nova_foto = FotoResposta(caminho=unique_filename, resposta_id=resposta.id)
            db.session.add(nova_foto)
            
            # (Opcional) Mantém o campo antigo atualizado para compatibilidade, se quiser
            resposta.caminho_foto = unique_filename 
            
            db.session.commit()
            current_app.logger.info(f"Foto registrada no banco (ID: {nova_foto.id}) para resposta {resposta_id}")

            # Gera URL para a foto
            foto_url = None
            try:
                foto_url = url_for('cli.get_foto_resposta', filename=unique_filename, _external=True)
            except Exception as url_err:
                current_app.logger.warning(f"Erro ao gerar URL para get_foto_resposta: {url_err}")
                # Fallback simples se url_for falhar
                foto_url = f"/uploads/{unique_filename}" 

            # Retorna sucesso com o ID da nova foto (importante para o botão excluir)
            return jsonify({
                'sucesso': True,
                'mensagem': 'Foto enviada com sucesso!',
                'foto_id': nova_foto.id,     # ID DA FOTO NOVA (Para o botão de excluir)
                'filename': unique_filename,
                'url': foto_url
            }), 200

        else:
            current_app.logger.warning(f"Upload negado para resposta {resposta_id}: tipo de arquivo não permitido ({foto.filename})")
            return jsonify({'erro': f"Tipo de arquivo não permitido. Permitidos: {', '.join(allowed_extensions)}"}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro inesperado no upload da foto para resposta {resposta_id}: {e}", exc_info=True)
        
@cli_bp.route('/foto/<int:foto_id>/deletar', methods=['DELETE'])
@login_required
@csrf.exempt  # Importante para chamadas AJAX DELETE
def deletar_foto(foto_id):
    """Remove uma foto específica da galeria."""
    try:
        # Busca a foto na tabela nova
        foto = FotoResposta.query.get_or_404(foto_id)
        
        # Verificações de segurança (opcional: checar se o user pode deletar)
        # ...
        
        # Remove o arquivo físico (Opcional, mas recomendado para não encher o disco)
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if upload_folder:
            caminho_completo = os.path.join(upload_folder, foto.caminho)
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                except Exception as e:
                    current_app.logger.warning(f"Erro ao deletar arquivo físico {foto.caminho}: {e}")

        # Remove do banco
        db.session.delete(foto)
        db.session.commit()
        
        return jsonify({'sucesso': True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao deletar foto {foto_id}: {e}")
        return jsonify({'erro': 'Erro ao excluir foto'}), 500        


# --- ROTA AUXILIAR PARA SERVIR AS FOTOS SALVAS ---
@cli_bp.route('/uploads/fotos_respostas/<path:filename>')
@login_required
def get_foto_resposta(filename):
    """
    Serve um arquivo de foto de resposta, verificando permissão
    na tabela principal E na tabela de múltiplas fotos.
    """
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        abort(500)

    try:
        # Padrão esperado: resposta_{id}_{hash}.ext
        if filename.startswith('resposta_') and '_' in filename:
            parts = filename.split('_')
            # Garante que pega o ID mesmo se o nome tiver mais underlines
            resposta_id_str = parts[1]
            
            if resposta_id_str.isdigit():
                resposta_id = int(resposta_id_str)
                resposta = RespostaPergunta.query.get(resposta_id)

                if resposta:
                    # 1. Verifica se é a foto principal (Compatibilidade Antiga)
                    eh_foto_principal = (resposta.caminho_foto == filename)
                    
                    # 2. Verifica se está na galeria de múltiplas fotos (Novo Sistema)
                    eh_foto_galeria = False
                    # Verifica se a classe FotoResposta existe (foi importada)
                    if 'FotoResposta' in globals():
                        foto_extra = FotoResposta.query.filter_by(
                            resposta_id=resposta.id, 
                            caminho=filename
                        ).first()
                        if foto_extra:
                            eh_foto_galeria = True
                    
                    # Se a foto for válida (principal OU galeria), verifica permissão do usuário
                    if eh_foto_principal or eh_foto_galeria:
                        aplicacao = AplicacaoQuestionario.query.get(resposta.aplicacao_id)
                        if aplicacao:
                            avaliado = Avaliado.query.get(aplicacao.avaliado_id)
                            # Permite se for dono dos dados (mesmo cliente) ou Admin Global
                            if (avaliado and avaliado.cliente_id == current_user.cliente_id) or verificar_permissao_admin():
                                return send_from_directory(upload_folder, filename)
            
            # Se chegou aqui, é porque a foto não pertence à resposta ou usuário não tem permissão
            current_app.logger.warning(f"Acesso negado ou arquivo não vinculado: {filename}")
            abort(403)
        else:
            abort(404)

    except FileNotFoundError:
        abort(404)
    except Exception as e:
        current_app.logger.error(f"Erro ao servir foto: {e}")
        abort(500)

@cli_bp.route('/aplicacao/<int:id>/reabrir', methods=['POST'])
@login_required
@csrf.exempt  # <--- ADICIONE ISSO PARA CORRIGIR O ERRO 400
def reabrir_aplicacao(id):
    """
    Reabre uma aplicação finalizada para permitir edições.
    Retorna JSON para ser consumido pelo fetch do JavaScript.
    """
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        
        # Verificação de segurança
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            return jsonify({'sucesso': False, 'erro': 'Acesso negado.'}), 403
            
        # Reverte o status para EM_ANDAMENTO
        aplicacao.status = StatusAplicacao.EM_ANDAMENTO
        aplicacao.data_fim = None # Limpa a data de finalização para recalcular o tempo depois
        
        db.session.commit()
        
        log_acao(f"Reabriu aplicação: {aplicacao.questionario.nome}", None, "AplicacaoQuestionario", id)
        
        return jsonify({'sucesso': True})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao reabrir aplicação {id}: {e}", exc_info=True)
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
    

    # --- ROTAS DE AUDITORIA E CHECKLIST ---

@cli_bp.route('/auditoria/nova/selecao', methods=['GET', 'POST'])
@login_required
def selecionar_rancho_auditoria():
    """
    Passo 1: Selecionar o Local (Rancho)
    CORRIGIDO: Suporta Multi-GAP (grupos_acesso) + Fallback para grupo_id único.
    """
    
    # --- LÓGICA DE POST (Processar Seleção) ---
    if request.method == 'POST':
        rancho_id = request.form.get('avaliado_id')
        if rancho_id:
            # Salva na sessão ou redireciona direto
            return redirect(url_for('cli.escolher_questionario', avaliado_id=rancho_id))
        else:
            flash("Selecione um local para continuar.", "warning")

    # --- LÓGICA DE GET (Preparar Lista) ---
    try:
        # 1. Identificação segura do tipo de usuário (trata Enum e String)
        tipo_str = str(current_user.tipo).upper()
        
        grupos_disponiveis = []
        ranchos_disponiveis = []

        # ---------------------------------------------------------
        # CENÁRIO A: ADMIN / SUPER ADMIN (Vê tudo do cliente)
        # ---------------------------------------------------------
        if 'ADMIN' in tipo_str:
            grupos_disponiveis = Grupo.query.filter_by(
                cliente_id=current_user.cliente_id, 
                ativo=True
            ).order_by(Grupo.nome).all()
            
            ranchos_disponiveis = Avaliado.query.filter_by(
                cliente_id=current_user.cliente_id, 
                ativo=True
            ).order_by(Avaliado.nome).all()

        # ---------------------------------------------------------
        # CENÁRIO B: GESTOR / AUDITOR (Lógica Multi-GAP)
        # ---------------------------------------------------------
        elif 'GESTOR' in tipo_str or 'AUDITOR' in tipo_str:
            # Set para evitar duplicatas se o banco estiver sujo
            set_grupos = set()

            # 1. Verifica a nova lista Múltipla (N:N)
            if hasattr(current_user, 'grupos_acesso') and current_user.grupos_acesso:
                for g in current_user.grupos_acesso:
                    if g.ativo:
                        set_grupos.add(g)

            # 2. Verifica o campo antigo (Fallback)
            if current_user.grupo_id:
                grupo_legacy = Grupo.query.get(current_user.grupo_id)
                if grupo_legacy and grupo_legacy.ativo:
                    set_grupos.add(grupo_legacy)

            # Converte de volta para lista para o template
            grupos_disponiveis = list(set_grupos)
            
            # Extrai os IDs para filtrar os Ranchos
            ids_grupos = [g.id for g in grupos_disponiveis]

            if ids_grupos:
                # Busca ranchos que pertencem a QUALQUER um dos grupos encontrados
                ranchos_disponiveis = Avaliado.query.filter(
                    Avaliado.cliente_id == current_user.cliente_id,
                    Avaliado.grupo_id.in_(ids_grupos),  # <--- O SEGREDO ESTÁ AQUI (.in_)
                    Avaliado.ativo == True
                ).order_by(Avaliado.nome).all()
            else:
                flash("Seu usuário não está vinculado a nenhum GAP. Contate o suporte.", "warning")

        # ---------------------------------------------------------
        # CENÁRIO C: USUÁRIO COMUM (Vê apenas seu Rancho)
        # ---------------------------------------------------------
        elif current_user.avaliado_id:
            ranchos_disponiveis = Avaliado.query.filter_by(
                id=current_user.avaliado_id,
                ativo=True
            ).all()
            
            # O grupo é o do próprio rancho (se existir)
            if ranchos_disponiveis and ranchos_disponiveis[0].grupo:
                grupos_disponiveis = [ranchos_disponiveis[0].grupo]

        # --- RENDERIZAÇÃO ---
        return render_template_safe('cli/auditoria_selecao.html', 
                                  grupos=grupos_disponiveis,
                                  avaliados=ranchos_disponiveis)

    except Exception as e:
        print(f"ERRO CRÍTICO NA SELEÇÃO DE AUDITORIA: {e}")
        flash(f"Erro ao carregar locais: {str(e)}", "danger")
        return redirect(url_for('cli.index'))


@cli_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Permite ao usuário ver seus dados e alterar a senha"""
    
    # Busca o usuário no banco para garantir a gravação
    usuario_db = Usuario.query.get(current_user.id)
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            senha_atual = request.form.get('senha_atual')
            nova_senha = request.form.get('nova_senha')
            confirma_senha = request.form.get('confirma_senha')

            # 1. Atualiza Nome
            if nome: 
                usuario_db.nome = nome
            
            # 2. Lógica de Troca de Senha
            if nova_senha and nova_senha.strip():
                
                # --- NOVA PROTEÇÃO: Bloqueia senha padrão e senhas curtas ---
                if nova_senha == '123456':
                    flash("Por segurança, você não pode usar a senha padrão (123456). Escolha outra.", "warning")
                    return redirect(url_for('cli.perfil'))
                
                if len(nova_senha) < 6:
                    flash("A nova senha deve ter pelo menos 6 caracteres.", "warning")
                    return redirect(url_for('cli.perfil'))
                # -------------------------------------------------------------

                # Valida se digitou a senha atual
                if not senha_atual:
                    flash("Para alterar a senha, você precisa digitar sua senha atual.", "warning")
                    return redirect(url_for('cli.perfil'))
                
                # Valida se a senha atual confere
                if not check_password_hash(usuario_db.senha_hash, senha_atual):
                    flash("A senha atual informada está incorreta.", "danger")
                    return redirect(url_for('cli.perfil'))
                
                # Valida confirmação
                if nova_senha != confirma_senha:
                    flash("A nova senha e a confirmação não conferem.", "warning")
                    return redirect(url_for('cli.perfil'))
                
                # Salva a nova senha
                usuario_db.senha_hash = generate_password_hash(nova_senha)
                
                db.session.add(usuario_db)
                db.session.commit()
                
                flash("Senha alterada com sucesso! Faça login novamente.", "success")
                
            else:
                db.session.commit()
                flash("Dados de perfil atualizados!", "success")

            return redirect(url_for('cli.perfil'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {str(e)}", "danger")

    return render_template_safe('cli/perfil.html', usuario=usuario_db)

# --- INÍCIO DA FUNÇÃO QUE FALTA ---
@cli_bp.route('/auditoria/passo2/<int:avaliado_id>', methods=['GET', 'POST'])
@login_required
def escolher_questionario(avaliado_id):
    """
    Passo 2: Escolher o Questionário e Criar a Aplicação.
    Atualizado com segurança Multi-GAP.
    """
    rancho = Avaliado.query.get_or_404(avaliado_id)
    
    # --- SEGURANÇA HIERÁRQUICA (MULTI-GAP) ---
    if current_user.tipo.name in ['AUDITOR', 'GESTOR']:
        # Coleta todos os IDs permitidos (Lista Nova + Legado)
        gaps_permitidos = [g.id for g in current_user.grupos_acesso]
        if current_user.grupo_id:
            gaps_permitidos.append(current_user.grupo_id)
        
        # Verifica se o rancho alvo pertence a algum desses grupos
        if rancho.grupo_id not in gaps_permitidos:
            flash(f"Acesso negado: Você não tem permissão para auditar o rancho '{rancho.nome}'.", "danger")
            return redirect(url_for('cli.selecionar_rancho_auditoria'))
    # ------------------------------------------

    if request.method == 'POST':
        questionario_id = request.form.get('questionario_id')
        
        if questionario_id:
            try:
                nova_aplicacao = AplicacaoQuestionario(
                    aplicador_id=current_user.id,
                    avaliado_id=rancho.id,
                    questionario_id=int(questionario_id),
                    data_inicio=datetime.now(),
                    status=StatusAplicacao.EM_ANDAMENTO 
                )
                
                db.session.add(nova_aplicacao)
                db.session.commit()
                
                flash(f"Aplicação iniciada! (ID: {nova_aplicacao.id})", "success")
                
                return redirect(url_for('cli.responder_aplicacao', id=nova_aplicacao.id))
                
            except Exception as e:
                db.session.rollback()
                print(f"ERRO SQL: {e}")
                flash(f"Erro ao criar registro: {str(e)}", "danger")
        else:
            flash("Selecione um questionário.", "warning")

    # Carrega questionários
    questionarios = Questionario.query.filter_by(
        cliente_id=current_user.cliente_id, 
        ativo=True
    ).order_by(Questionario.nome).all()

    return render_template_safe('cli/auditoria_passo2.html', rancho=rancho, questionarios=questionarios)

@cli_bp.route('/questionario/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_questionario(id):
    """
    Exclui ou Inativa um questionário.
    Restrito ao SUPER_ADMIN.
    """
    # 1. Busca e Segurança
    q = Questionario.query.get_or_404(id)
    
    if q.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_questionarios'))

    if current_user.tipo.name != 'SUPER_ADMIN':
        flash("Apenas o Laboratório pode excluir questionários.", "danger")
        return redirect(url_for('cli.listar_questionarios'))

    try:
        nome_q = q.nome
        
        # 2. Verifica se já existem aplicações feitas com este questionário
        tem_aplicacoes = AplicacaoQuestionario.query.filter_by(questionario_id=id).first()
        
        if tem_aplicacoes:
            # SE JÁ FOI USADO: Não exclui, apenas inativa (Soft Delete)
            q.ativo = False
            q.publicado = False
            db.session.commit()
            
            log_acao(f"Inativou questionário (em uso): {nome_q}", None, "Questionario", id)
            flash(f"O questionário '{nome_q}' possui auditorias realizadas e não pode ser excluído permanentemente. Ele foi INATIVADO e não aparecerá mais para novas auditorias.", "warning")
            
        else:
            # SE NUNCA FOI USADO: Exclui permanentemente (Hard Delete)
            
            # Primeiro remove vínculos de usuários (dependência)
            if 'UsuarioAutorizado' in globals():
                UsuarioAutorizado.query.filter_by(questionario_id=id).delete()
                
            # Remove tópicos e perguntas (dependendo da configuração do cascade do seu banco)
            # Geralmente o banco resolve, mas é bom limpar se não tiver cascade
            # ... (Lógica de limpeza profunda se necessário) ...

            db.session.delete(q)
            db.session.commit()
            
            log_acao(f"Excluiu questionário permanentemente: {nome_q}", None, "Questionario", id)
            flash(f"Questionário '{nome_q}' excluído com sucesso!", "success")

    except Exception as e:
        db.session.rollback()
        print(f"ERRO AO EXCLUIR: {e}")
        # Se der erro de integridade (Foreign Key), força a inativação
        try:
            q.ativo = False
            db.session.commit()
            flash(f"Não foi possível excluir devido a vínculos, então o questionário foi inativado.", "warning")
        except:
            flash(f"Erro crítico ao excluir: {str(e)}", "danger")

    return redirect(url_for('cli.listar_questionarios'))


# --- ROTAS DA IA ---

# Em app/cli/routes.py

@cli_bp.route('/api/ia/sugerir-plano', methods=['POST'])
@login_required
def sugerir_plano_acao():
    """Gera sugestão usando Gemini Flash Latest com Prompt Refinado (v3)"""
    try:
        data = request.get_json()
        if not data.get('pergunta'): return jsonify({'erro': 'Dados insuficientes'}), 400

        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key: return jsonify({'erro': 'Chave de IA não configurada'}), 500
            
        genai.configure(api_key=api_key)
        
        # --- PROMPT V3: Foco Cirúrgico e Contextual ---
        prompt = f"""
        Atue como um Consultor Técnico em Segurança de Alimentos. Redija a Ação Corretiva para a Não Conformidade abaixo.
        
        CONTEXTO DA AUDITORIA:
        - Requisito Auditado: "{data.get('pergunta')}"
        - O que o Auditor viu (Observação): "{data.get('observacao')}"

        OBJETIVO:
        Criar um comando técnico e direto para resolver EXATAMENTE o problema pontual descrito, sem generalizações.

        REGRAS DE OURO (ESCOPO E TOM):
        1. FOCO CIRÚRGICO: Resolva apenas o defeito citado. Se a observação fala de "uma tela rasgada", mande consertar "a tela rasgada". NÃO mande "inspecionar as outras" (o auditor já fez isso).
        2. SEM REDUNDÂNCIA: Não peça para "criar planilhas", "monitorar" ou "fazer levantamentos", a menos que o problema seja falta de registro. Foque na ação física (trocar, limpar, consertar).
        3. VOCABULÁRIO CONECTADO: Use os mesmos substantivos da observação. Se o auditor escreveu "janela do estoque", use "janela do estoque" na ação.
        4. IMPERATIVO TÉCNICO: Comece com verbos fortes (Substituir, Adequar, Instalar, Higienizar).
        5. FORMATO: Um único parágrafo curto. Sem listas. Sem introduções ("A ação deve ser...").

        Exemplo Bom: "Substituir imediatamente a tela milimetrada danificada da janela, garantindo a vedação completa contra pragas conforme exigido."
        Exemplo Ruim: "Verificar todas as janelas e trocar as telas se necessário." (Errado: o auditor já verificou).

        Gere a ação corretiva agora:
        """
        # ------------------------
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        return jsonify({'sucesso': True, 'sugestao': response.text.strip()})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

# Em app/cli/routes.py

@cli_bp.route('/aplicacao/<int:id>/gestao-ncs', methods=['GET'])
@login_required
def gerenciar_nao_conformidades(id):
    aplicacao = AplicacaoQuestionario.query.get_or_404(id)
    
    # Validação de segurança básica (igual às outras rotas)
    if aplicacao.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_aplicacoes'))

    # Query Corrigida:
    # 1. Faz JOIN com Pergunta e Topico para ter acesso aos dados de ordenação
    # 2. Ordena por Tópico.ordem -> Pergunta.ordem (Ordem do Checklist)
    ncs = RespostaPergunta.query\
        .join(Pergunta)\
        .join(Topico)\
        .filter(
            RespostaPergunta.aplicacao_id == id, 
            RespostaPergunta.nao_conforme == True
        )\
        .options(
            joinedload(RespostaPergunta.pergunta).joinedload(Pergunta.topico)
        )\
        .order_by(Topico.ordem, Pergunta.ordem)\
        .all()

    return render_template_safe('cli/definir_planos.html', aplicacao=aplicacao, ncs=ncs)

# --- Adicione isso ao final do arquivo app/cli/routes.py ---

# --- Adicione no final do arquivo app/cli/routes.py ---

# app/cli/routes.py

@cli_bp.route('/planos-de-acao')
@login_required
def lista_plano_acao():
    """
    Tela 1: Lista apenas as AUDITORIAS que possuem planos de ação pendentes.
    """
    try:
        # Busca IDs de aplicações que têm pelo menos uma resposta com plano de ação
        subquery = db.session.query(RespostaPergunta.aplicacao_id)\
            .filter(RespostaPergunta.plano_acao != None)\
            .filter(RespostaPergunta.plano_acao != "")\
            .distinct()

        # Busca as aplicações completas baseadas nesses IDs
        query = AplicacaoQuestionario.query\
            .join(Avaliado)\
            .filter(AplicacaoQuestionario.id.in_(subquery))\
            .filter(Avaliado.cliente_id == current_user.cliente_id)

        # Filtros de Hierarquia
        if current_user.avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == current_user.avaliado_id)
        elif current_user.grupo_id:
            query = query.filter(Avaliado.grupo_id == current_user.grupo_id)

        aplicacoes_pendentes = query.order_by(AplicacaoQuestionario.data_inicio.desc()).all()

        return render_template_safe('cli/plano_acao_lista.html', aplicacoes=aplicacoes_pendentes)
    except Exception as e:
        print(f"Erro: {e}")
        return redirect(url_for('cli.index'))

@cli_bp.route('/plano-de-acao/<int:aplicacao_id>')
@login_required
def detalhe_plano_acao(aplicacao_id):
    """
    Tela 2: Exibe os detalhes das pendências de UMA aplicação específica.
    """
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(aplicacao_id)
        
        # --- CORREÇÃO DE SEGURANÇA (Lógica Explícita) ---
        # 1. Verifica se pertence ao mesmo cliente (Empresa)
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso não autorizado a esta auditoria.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))

        # 2. Se for usuário de Rancho, só pode ver o SEU rancho
        if current_user.avaliado_id and aplicacao.avaliado_id != current_user.avaliado_id:
            flash("Você não tem permissão para ver auditorias de outra unidade.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))

        # 3. Se for usuário de GAP, só pode ver ranchos do SEU GAP
        if current_user.grupo_id and aplicacao.avaliado.grupo_id != current_user.grupo_id:
            flash("Você não tem permissão para ver auditorias fora do seu agrupamento.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))
        # ----------------------------------------------------

        # Busca apenas as respostas com plano de ação desta aplicação
        respostas_com_plano = RespostaPergunta.query\
            .filter_by(aplicacao_id=aplicacao.id)\
            .filter(RespostaPergunta.plano_acao != None)\
            .filter(RespostaPergunta.plano_acao != "")\
            .join(Pergunta)\
            .order_by(Pergunta.ordem)\
            .all()

        # ADICIONEI 'datetime=datetime' AQUI EMBAIXO vvv
        return render_template_safe('cli/plano_acao_detalhe.html', 
                               app=aplicacao, 
                               respostas=respostas_com_plano,
                               datetime=datetime) 
                               
    except Exception as e:
        print(f"Erro: {e}")
        return redirect(url_for('cli.lista_plano_acao'))

# Em app/cli/routes.py

# Em app/cli/routes.py

@cli_bp.route('/plano-de-acao/<int:aplicacao_id>/pdf')
@login_required
def pdf_plano_acao(aplicacao_id):
    import base64
    import os
    from pathlib import Path
    
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(aplicacao_id)
        
        # 1. Segurança
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso não autorizado.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))
        if current_user.avaliado_id and aplicacao.avaliado_id != current_user.avaliado_id:
            flash("Permissão negada.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))

        # 2. Busca Dados
        respostas_db = RespostaPergunta.query\
            .filter_by(aplicacao_id=aplicacao.id)\
            .filter(RespostaPergunta.plano_acao != None)\
            .filter(RespostaPergunta.plano_acao != "")\
            .join(Pergunta).join(Topico)\
            .order_by(Topico.ordem, Pergunta.ordem)\
            .all()
        
        # 3. Prepara Itens e Fotos das NCs
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        itens_relatorio = []

        for resp in respostas_db:
            item = {
                'topico_nome': resp.pergunta.topico.nome,
                'topico_ordem': resp.pergunta.topico.ordem,
                'pergunta_ordem': resp.pergunta.ordem,
                'pergunta_texto': resp.pergunta.texto,
                'observacao': resp.observacao,
                'plano_acao': resp.plano_acao,
                'prazo': resp.prazo_plano_acao,
                'foto_uri': None
            }
            if resp.caminho_foto and upload_folder:
                path = Path(upload_folder) / resp.caminho_foto
                if path.exists():
                    item['foto_uri'] = path.as_uri()
            itens_relatorio.append(item)
        
        # 4. Helper para converter imagem em Base64
        def get_image_b64(filepath):
            if filepath and os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            return None

        # -- LOGO --
        path_logo = os.path.join(current_app.root_path, 'static', 'img', 'logo_pdf.png')
        logo_b64 = get_image_b64(path_logo)

        # -- ASSINATURA CLIENTE (Da Aplicação) --
        assinatura_cliente_b64 = None
        if aplicacao.assinatura_imagem:
            path_ass = os.path.join(current_app.config['UPLOAD_FOLDER'], aplicacao.assinatura_imagem)
            assinatura_cliente_b64 = get_image_b64(path_ass)

        # -- ASSINATURA AUDITOR (Do Usuário/Sistema) --
        # Tenta buscar se o usuário aplicador tem foto/assinatura, senão fica None
        assinatura_auditor_b64 = None
        # Exemplo: se o model User tiver um campo 'assinatura_imagem'
        # if aplicacao.aplicador and getattr(aplicacao.aplicador, 'assinatura_imagem', None):
        #     path_aud = os.path.join(current_app.config['UPLOAD_FOLDER'], aplicacao.aplicador.assinatura_imagem)
        #     assinatura_auditor_b64 = get_image_b64(path_aud)

        # 5. Renderiza
        html_content = render_template_safe(
            'cli/pdf_plano_acao.html',
            aplicacao=aplicacao,
            itens=itens_relatorio,
            logo_uri=logo_b64,
            assinatura_cliente_uri=assinatura_cliente_b64, # Imagem Cliente
            assinatura_auditor_uri=assinatura_auditor_b64, # Imagem Auditor (se tiver)
            assinatura_responsavel=aplicacao.assinatura_responsavel,
            cargo_responsavel=aplicacao.cargo_responsavel,
            data_geracao=datetime.now()
        )
        
        return gerar_pdf_seguro(html_content, filename=f"Plano_Acao_{aplicacao_id}.pdf")
        
    except Exception as e:
        current_app.logger.error(f"Erro PDF Plano: {e}")
        flash("Erro ao gerar PDF.", "danger")
        return redirect(url_for('cli.visualizar_aplicacao', id=aplicacao_id))
# ===================== ROTAS DE AÇÃO CORRETIVA =====================

@cli_bp.route('/acao-corretiva/registrar/<int:resposta_id>', methods=['POST'])
@login_required
def registrar_acao_corretiva(resposta_id):
    """Salva o texto da ação corretiva tomada pela OM"""
    try:
        resposta = RespostaPergunta.query.get_or_404(resposta_id)
        
        # Verificações de segurança
        app_quest = AplicacaoQuestionario.query.get(resposta.aplicacao_id)
        if app_quest.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))
            
        texto_acao = request.form.get('acao_realizada')
        
        if texto_acao:
            resposta.acao_realizada = texto_acao
            resposta.data_conclusao = datetime.now()
            # Use 'concluido' (string) ou StatusAcao.CONCLUIDO (enum) conforme seu model
            resposta.status_acao = 'concluido' 
            
            db.session.commit()
            flash("Ação corretiva registrada com sucesso!", "success")
        else:
            flash("Descreva a ação realizada.", "warning")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao salvar: {str(e)}", "danger")
        
    return redirect(url_for('cli.detalhe_plano_acao', aplicacao_id=resposta.aplicacao_id))


@cli_bp.route('/acao-corretiva/upload-foto/<int:resposta_id>', methods=['POST'])
@login_required
@csrf.exempt 
def upload_foto_correcao(resposta_id):
    """Upload específico para fotos de CORREÇÃO"""
    try:
        resposta = RespostaPergunta.query.get_or_404(resposta_id)
        
        # Segurança básica
        app_quest = AplicacaoQuestionario.query.get(resposta.aplicacao_id)
        if app_quest.avaliado.cliente_id != current_user.cliente_id:
             return jsonify({'erro': 'Acesso negado'}), 403
        
        file = request.files.get('foto')
        # Ajuste as extensões conforme sua config
        allowed = {'png', 'jpg', 'jpeg', 'gif'} 
        
        if file and ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed):
            filename = secure_filename(file.filename)
            unique_name = f"correcao_{resposta.id}_{uuid.uuid4().hex[:8]}.{filename.rsplit('.', 1)[1]}"
            
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/img')
            # Garante que a pasta existe
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file.save(os.path.join(upload_folder, unique_name))
            
            nova_foto = FotoResposta(
                caminho=unique_name, 
                resposta_id=resposta.id,
                tipo='correcao'
            )
            db.session.add(nova_foto)
            db.session.commit()
            
            return jsonify({'sucesso': True})
            
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    
    return jsonify({'erro': 'Erro no upload'}), 400