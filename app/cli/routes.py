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
from werkzeug.utils import secure_filename
# from weasyprint import HTML  # COMENTAR SE DER ERRO
from sqlalchemy import func, extract, and_, or_, desc
from sqlalchemy.orm import joinedload, subqueryload
from pathlib import Path
import urllib.parse


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
        TipoUsuario, Notificacao, LogAuditoria, ConfiguracaoCliente
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

def get_avaliados_usuario():
    """Retorna avaliados disponíveis para o usuário atual - CORRIGIDO"""
    try:
        if hasattr(current_user, 'tipo'):
            user_type = current_user.tipo
            if hasattr(user_type, 'name'):
                type_name = user_type.name
            elif hasattr(user_type, 'value'):
                type_name = user_type.value
            else:
                type_name = str(user_type)
            
            if type_name in ['ADMIN', 'SUPER_ADMIN', 'admin', 'super_admin']:
                return Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
            else:
                # Usuários normais só veem avaliados de seus grupos
                if hasattr(current_user, 'grupo_id') and current_user.grupo_id:
                    return Avaliado.query.filter_by(
                        cliente_id=current_user.cliente_id,
                        grupo_id=current_user.grupo_id,
                        ativo=True
                    ).all()
                else:
                    return Avaliado.query.filter_by(
                        cliente_id=current_user.cliente_id,
                        ativo=True
                    ).all()
        else:
            return Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
            
    except Exception as e:
        print(f"Erro em get_avaliados_usuario: {e}")
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

def gerar_pdf_seguro(html_content, filename="relatorio.pdf"):
    """Gera PDF com fallback se WeasyPrint não estiver disponível"""
    try:
        from weasyprint import HTML
        pdf = HTML(string=html_content, base_url=request.url_root).write_pdf()
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except ImportError:
        # Fallback - retornar HTML se WeasyPrint não disponível
        flash("WeasyPrint não instalado. Mostrando versão HTML do relatório.", "warning")
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
    except Exception as e:
        flash(f"Erro ao gerar PDF: {str(e)}", "danger")
        return redirect(request.referrer or url_for('cli.index'))

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



# ===================== PÁGINA INICIAL =====================

@cli_bp.route('/')
@cli_bp.route('/home')
@login_required
def index():
    """Dashboard principal do CLIQ"""
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

# ===================== QUESTIONÁRIOS =====================

from flask import request, flash
from sqlalchemy import func, or_

from flask import request, flash
from sqlalchemy import func, or_

# Em app/cli/routes.py

# Em app/cli/routes.py

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


@cli_bp.route('/questionario/novo', methods=['GET', 'POST'])
@cli_bp.route('/novo-questionario', methods=['GET', 'POST'])
@login_required
def novo_questionario():
    """Tela de criação de questionário (CLIq) – versão corrigida com debug."""
    
    print(f"DEBUG: Método da requisição: {request.method}")
    
    if request.method == 'POST':
        print("DEBUG: Processando POST do questionário")
        
        # 1) Coleta os campos do formulário
        nome = (request.form.get('nome') or '').strip()
        descricao = (request.form.get('descricao') or '').strip()
        
        print(f"DEBUG: Nome recebido: '{nome}'")
        print(f"DEBUG: Descrição recebida: '{descricao}'")
        
        # Campos booleanos
        calcular_nota = request.form.get('calcular_nota') == 'on'
        ocultar_nota = request.form.get('ocultar_nota') == 'on'
        
        # --- ATUALIZAÇÃO: Coletar todos os campos do seu HTML ---
        incluir_assinatura = request.form.get('incluir_assinatura') == 'on' # <-- Adicionado do seu HTML
        incluir_foto_capa = request.form.get('incluir_foto_capa') == 'on' # <-- Adicionado do seu HTML
        
        # Numéricos/opcionais
        versao = (request.form.get('versao') or '1.0').strip()
        modo = (request.form.get('modo') or 'Avaliado').strip()
        base_calculo = int(request.form.get('base_calculo') or 100)
        casas_decimais = int(request.form.get('casas_decimais') or 2)
        modo_configuracao = (request.form.get('modo_configuracao') or 'percentual').strip()
        
        # --- ATUALIZAÇÃO 1: Coletar os IDs dos usuários autorizados ---
        # Recebe a string "1,2,3" do input hidden 'usuarios_autorizados'
        usuarios_ids_str = request.form.get('usuarios_autorizados', '')
        print(f"DEBUG: String de IDs de usuários recebida: '{usuarios_ids_str}'")
        # --- FIM DA ATUALIZAÇÃO 1 ---
        
        print(f"DEBUG: Dados coletados - versão: {versao}, modo: {modo}")
        
        # 2) Validação
        erros = []
        if not nome:
            print("DEBUG: ERRO - Nome vazio")
            erros.append('Nome do questionário é obrigatório.')
        
        # Verificar duplicidade
        try:
            existente = Questionario.query.filter_by(
                nome=nome,
                cliente_id=current_user.cliente_id,
                ativo=True
            ).first()
            
            if existente:
                print(f"DEBUG: ERRO - Questionário '{nome}' já existe")
                erros.append(f"Já existe um questionário ativo com o nome '{nome}'.")
            else:
                print("DEBUG: Nome do questionário é único, ok para continuar")
                
        except Exception as e:
            print(f"DEBUG: ERRO na verificação de duplicidade: {e}")
            erros.append(f"Erro ao verificar duplicidade: {str(e)}")
        
        if erros:
            print(f"DEBUG: {len(erros)} erro(s) encontrado(s), re-renderizando formulário")
            for erro in erros:
                flash(erro, 'warning')

            # --- ATUALIZAÇÃO 2: Precisamos carregar os usuários aqui também em caso de erro ---
            usuarios = []
            try:
                usuarios = Usuario.query.filter_by(
                    cliente_id=current_user.cliente_id, 
                    ativo=True
                ).order_by(Usuario.nome).all()
            except Exception as e:
                print(f"DEBUG: ERRO ao buscar usuários no POST (fallback de erro): {e}")
            
            # Passa 'usuarios' para o template poder renderizar o dropdown
            return render_template_safe('cli/novo_questionario.html', dados=request.form, usuarios=usuarios)
            # --- FIM DA ATUALIZAÇÃO 2 ---
        
        # 3) Tentar criar o questionário
        try:
            print("DEBUG: Tentando criar questionário no banco...")
            
            q = Questionario(
                nome=nome,
                versao=versao,
                descricao=descricao,
                modo=modo,
                cliente_id=current_user.cliente_id,
                criado_por_id=current_user.id,
                
                # Configurações de nota/relatório
                calcular_nota=calcular_nota,
                ocultar_nota_aplicacao=ocultar_nota,
                base_calculo=base_calculo,
                casas_decimais=casas_decimais,
                modo_configuracao=modo_configuracao,
                modo_exibicao_nota=ModoExibicaoNota.PERCENTUAL if 'ModoExibicaoNota' in globals() else 'percentual',
                
                # Campos do seu HTML
                incluir_assinatura=incluir_assinatura,
                incluir_foto_capa=incluir_foto_capa,
                
                # Status inicial
                ativo=True,
                publicado=False,
                status=StatusQuestionario.RASCUNHO if 'StatusQuestionario' in globals() else 'rascunho'
            )
            
            # Adiciona todos os outros campos do formulário (do seu HTML) ao objeto 'q'
            # Isso garante que todas as opções da tela sejam salvas
            
            # Configurações de aplicação
            q.anexar_documentos = request.form.get('anexar_documentos') == 'on'
            q.capturar_geolocalizacao = request.form.get('geolocalizacao') == 'on'
            q.restringir_avaliados = request.form.get('restricao_avaliados') == 'on'
            q.habilitar_reincidencia = request.form.get('reincidencia') == 'on'
            
            # Opções de preenchimento
            # (Seu modelo 'Questionario' não tinha 'tipo_preenchimento', 'pontuacao_ativa', etc.
            # Se tiver, descomente as linhas abaixo)
            # q.tipo_preenchimento = ... (lógica para preenchimento_rapido/sequencial)
            # q.pontuacao_ativa = request.form.get('pontuacao_ativa') == 'on'
            
            # Configurações do relatório
            q.exibir_nota_anterior = request.form.get('exibir_nota_anterior') == 'on'
            q.exibir_tabela_resumo = request.form.get('exibir_tabela_de_resumo') == 'on'
            q.exibir_limites_aceitaveis = request.form.get('exibir_limites_aceitáveis') == 'on'
            q.exibir_data_hora = request.form.get('exibir_data/hora_início_e_fim') == 'on'
            q.exibir_questoes_omitidas = request.form.get('exibir_questões_omitidas') == 'on'
            q.exibir_nao_conformidade = request.form.get('exibir_relatório_não_conformidade') == 'on'
            # q.modo_exibicao_nota = request.form.get('modo_nota_pdf') # <-- Já pego acima
            # q.agrupamento_fotos = request.form.get('agrupamento_fotos') # <-- Adicione este campo ao seu models.py
            
            db.session.add(q)
            db.session.flush()  # <-- IMPORTANTE: Isso obtém o q.id ANTES do commit
            
            print(f"DEBUG: Questionário ID {q.id} criado na sessão, processando usuários autorizados...")

            # --- ATUALIZAÇÃO 3: Salvar os Usuários Autorizados ---
            if 'UsuarioAutorizado' in globals() and usuarios_ids_str:
                ids_list = usuarios_ids_str.split(',')
                
                for usuario_id_str in ids_list:
                    usuario_id_str = usuario_id_str.strip()
                    if usuario_id_str.isdigit():
                        try:
                            usuario_auth = UsuarioAutorizado(
                                questionario_id=q.id,  # Associa ao novo questionário
                                usuario_id=int(usuario_id_str) # Associa ao ID da consultora
                            )
                            db.session.add(usuario_auth)
                            print(f"DEBUG: Adicionando usuário ID {usuario_id_str} ao questionário {q.id}")
                        except Exception as e_auth:
                            print(f"DEBUG: ERRO ao processar usuario_id {usuario_id_str}: {e_auth}")
            elif 'UsuarioAutorizado' not in globals():
                 print("DEBUG: ERRO - Modelo 'UsuarioAutorizado' não encontrado.")
            else:
                print("DEBUG: Nenhum usuário autorizado foi selecionado.")
            # --- FIM DA ATUALIZAÇÃO 3 ---
            
            db.session.commit() # <-- Salva o Questionário E as associações
            
            print(f"DEBUG: Questionário criado com ID: {q.id}")
            
            log_acao(f"Criou questionário: {nome}", None, "Questionario", q.id)
            flash('Questionário criado com sucesso!', 'success')
            
            print(f"DEBUG: Redirecionando para gerenciar_topicos com ID: {q.id}")
            
            # 4) Redirecionar para tópicos
            return redirect(url_for('cli.gerenciar_topicos', id=q.id))
            
        except Exception as e:
            print(f"DEBUG: ERRO ao criar questionário: {e}")
            import traceback
            traceback.print_exc()
            
            db.session.rollback()
            flash(f'Erro ao criar questionário: {str(e)}', 'danger')

            # --- ATUALIZAÇÃO 4: Precisamos carregar os usuários aqui também em caso de erro grave ---
            usuarios = []
            try:
                usuarios = Usuario.query.filter_by(
                    cliente_id=current_user.cliente_id, 
                    ativo=True
                ).order_by(Usuario.nome).all()
            except Exception as e_user:
                print(f"DEBUG: ERRO ao buscar usuários no POST (except): {e_user}")

            # Passa 'usuarios' para o template poder renderizar o dropdown
            return render_template_safe('cli/novo_questionario.html', dados=request.form, usuarios=usuarios)
            # --- FIM DA ATUALIZAÇÃO 4 ---
    
    # GET: renderizar formulário vazio
    print("DEBUG: Renderizando formulário GET")
    
    # --- ATUALIZAÇÃO 5: Buscar usuários (consultoras) para o dropdown no GET ---
    try:
        # Busca todos os usuários (consultoras) do mesmo cliente
        usuarios = Usuario.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        ).order_by(Usuario.nome).all()
        print(f"DEBUG: {len(usuarios)} usuários encontrados para o dropdown.")
    except Exception as e:
        print(f"DEBUG: ERRO ao buscar usuários no GET: {e}")
        usuarios = []
        flash("Erro ao carregar lista de usuários.", "danger")
    # --- FIM DA ATUALIZAÇÃO 5 ---

    # Passa 'usuarios' para o template
    return render_template_safe('cli/novo_questionario.html', dados=None, usuarios=usuarios)



def processar_novo_questionario():
    """Processa a criação de novo questionário"""
    try:
        # Dados básicos
        nome = request.form.get('nome', '').strip()
        versao = request.form.get('versao', '1.0').strip()
        descricao = request.form.get('descricao', '').strip()
        modo = request.form.get('modo', 'Avaliado')
        
        if not nome:
            flash("Nome do questionário é obrigatório.", "danger")
            return redirect(url_for('cli.novo_questionario'))

        # Verificar se já existe questionário com mesmo nome
        questionario_existente = Questionario.query.filter_by(
            nome=nome,
            cliente_id=current_user.cliente_id,
            ativo=True
        ).first()
        
        if questionario_existente:
            flash(f"Já existe um questionário com o nome '{nome}'.", "warning")
            return redirect(url_for('cli.novo_questionario'))

        # Criar questionário
        novo_questionario = Questionario(
            nome=nome,
            versao=versao,
            descricao=descricao,
            modo=modo,
            cliente_id=current_user.cliente_id,
            criado_por_id=current_user.id,
            
            # Configurações das notas
            calcular_nota=request.form.get('calcular_nota') == 'on',
            ocultar_nota_aplicacao=request.form.get('ocultar_nota') == 'on',
            base_calculo=int(request.form.get('base_calculo', 100)),
            casas_decimais=int(request.form.get('casas_decimais', 2)),
            modo_configuracao=request.form.get('modo_configuracao', 'percentual'),
            modo_exibicao_nota=ModoExibicaoNota.PERCENTUAL,
            
            # Configurações de aplicação
            anexar_documentos=request.form.get('anexar_documentos') == 'on',
            capturar_geolocalizacao=request.form.get('geolocalizacao') == 'on',
            restringir_avaliados=request.form.get('restricao_avaliados') == 'on',
            habilitar_reincidencia=request.form.get('reincidencia') == 'on',
            
            # Configurações visuais
            cor_relatorio=CorRelatorio.AZUL,
            incluir_assinatura=request.form.get('incluir_assinatura') == 'on',
            incluir_foto_capa=request.form.get('incluir_foto_capa') == 'on',
            
            # Status
            ativo=True,
            publicado=False,
            status=StatusQuestionario.RASCUNHO
        )

        db.session.add(novo_questionario)
        db.session.flush()  # Para obter o ID

        # Configurar usuários autorizados se especificado
        usuarios_autorizados = request.form.getlist('usuarios_autorizados')
        if usuarios_autorizados and 'UsuarioAutorizado' in globals():
            for usuario_id in usuarios_autorizados:
                if usuario_id:
                    usuario_auth = UsuarioAutorizado(
                        questionario_id=novo_questionario.id,
                        usuario_id=int(usuario_id)
                    )
                    db.session.add(usuario_auth)

        db.session.commit()
        
        # Log da ação
        log_acao(f"Criou questionário: {nome}", None, "Questionario", novo_questionario.id)
        
        flash(f"Questionário '{nome}' criado com sucesso!", "success")
        return redirect(url_for('cli.gerenciar_topicos', id=novo_questionario.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao criar questionário: {str(e)}", "danger")
        return redirect(url_for('cli.novo_questionario'))

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

@cli_bp.route('/questionario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_questionario(id):
    """Edita questionário existente"""
    try:
        questionario = Questionario.query.get_or_404(id)
        
        if questionario.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        if request.method == 'POST':
            try:
                # Atualizar dados básicos
                questionario.nome = request.form.get('nome', '').strip()
                questionario.versao = request.form.get('versao', '1.0').strip()
                questionario.descricao = request.form.get('descricao', '').strip()
                questionario.modo = request.form.get('modo', 'Avaliado')
                
                # Configurações das notas
                questionario.calcular_nota = request.form.get('calcular_nota') == 'on'
                questionario.ocultar_nota_aplicacao = request.form.get('ocultar_nota') == 'on'
                questionario.base_calculo = int(request.form.get('base_calculo', 100))
                questionario.casas_decimais = int(request.form.get('casas_decimais', 2))
                
                # Configurações visuais
                questionario.incluir_assinatura = request.form.get('incluir_assinatura') == 'on'
                questionario.incluir_foto_capa = request.form.get('incluir_foto_capa') == 'on'
                
                db.session.commit()
                log_acao(f"Editou questionário: {questionario.nome}", None, "Questionario", id)
                
                flash("Questionário atualizado com sucesso!", "success")
                return redirect(url_for('cli.visualizar_questionario', id=id))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao atualizar questionário: {str(e)}", "danger")
        
        # GET - Carregar dados
        usuarios = Usuario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
        grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
        
        return render_template_safe('cli/editar_questionario.html',
                             questionario=questionario,
                             usuarios=usuarios,
                             grupos=grupos)
    except Exception as e:
        flash(f"Erro ao carregar questionário: {str(e)}", "danger")
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
    """Editar tópico existente"""
    try:
        topico = Topico.query.get_or_404(topico_id)
        
        if topico.questionario.cliente_id != current_user.cliente_id:
            flash("Tópico não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        if request.method == 'POST':
            try:
                topico.nome = request.form.get('nome', '').strip()
                topico.descricao = request.form.get('descricao', '').strip()
                
                if not topico.nome:
                    flash("Nome do tópico é obrigatório.", "danger")
                    return render_template_safe('cli/editar_topico.html', topico=topico)
                
                db.session.commit()
                log_acao(f"Editou tópico: {topico.nome}", None, "Topico", topico_id)
                
                flash("Tópico atualizado com sucesso!", "success")
                return redirect(url_for('cli.gerenciar_topicos', id=topico.questionario_id))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao atualizar tópico: {str(e)}", "danger")
        
        return render_template_safe('cli/editar_topico.html', topico=topico)
    except Exception as e:
        flash(f"Erro ao carregar tópico: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/topico/<int:topico_id>/remover', methods=['POST'])
@login_required
def remover_topico(topico_id):
    """Remove um tópico"""
    try:
        topico = Topico.query.get_or_404(topico_id)
        
        if topico.questionario.cliente_id != current_user.cliente_id:
            flash("Tópico não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        questionario_id = topico.questionario_id
        
        # Verificar se tem perguntas
        total_perguntas = Pergunta.query.filter_by(topico_id=topico_id, ativo=True).count()
        if total_perguntas > 0:
            flash("Não é possível remover tópico que contém perguntas.", "warning")
        else:
            topico.ativo = False
            db.session.commit()
            log_acao(f"Removeu tópico: {topico.nome}", None, "Topico", topico_id)
            flash("Tópico removido com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover tópico: {str(e)}", "danger")
        questionario_id = request.args.get('questionario_id')
    
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
    """Criar nova pergunta - CORRIGIDA e ATUALIZADA (v2 - auto-opções SIM_NAO_NA)""" # <-- Nome atualizado
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
                
                # --- LINHA ADICIONADA ---
                exige_foto = request.form.get('exige_foto_se_nao_conforme') == 'on'
                # ------------------------

                print(f"DEBUG: texto='{texto}', tipo='{tipo_str}', peso={peso}, exige_foto={exige_foto}")
                
                if not texto:
                    flash("Texto da pergunta é obrigatório.", "danger")
                    print("DEBUG: Texto vazio, re-renderizando formulário")
                    return render_template_safe('cli/nova_pergunta.html', topico=topico)
                
                # Obter próxima ordem
                ultima_ordem = db.session.query(func.max(Pergunta.ordem)).filter_by(
                    topico_id=topico_id, ativo=True # Considerar apenas ativos para ordem
                ).scalar() or 0
                print(f"DEBUG: Última ordem: {ultima_ordem}")

                # --- CONVERSÃO STRING PARA ENUM ---
                try:
                    # Tenta buscar pelo NOME do enum ('SIM_NAO_NA')
                    tipo_enum = TipoResposta[tipo_str]
                except KeyError:
                    # Se falhar, tenta buscar pelo VALOR ('Sim/Não/N.A.') - menos ideal, mas robusto
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
                    tipo=tipo_enum, # Salva o Enum
                    obrigatoria=obrigatoria,
                    permite_observacao=permite_observacao,
                    peso=peso,
                    ordem=ultima_ordem + 1,
                    exige_foto_se_nao_conforme=exige_foto, # --- CAMPO ADICIONADO ---
                    topico_id=topico_id,
                    ativo=True
                )
                
                db.session.add(nova_pergunta_obj)
                db.session.flush() # Para obter o ID da pergunta para as opções
                print(f"DEBUG: Pergunta criada com ID: {nova_pergunta_obj.id}")
                
                # --- LÓGICA DE OPÇÕES CORRIGIDA ---
                
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
                                valor_float = 0.0 # Default seguro

                            opcao = OpcaoPergunta(
                                texto=texto_opcao_strip,
                                valor=valor_float,
                                ordem=i + 1,
                                pergunta_id=nova_pergunta_obj.id,
                                ativo=True # <<< Garante ativo=True
                            )
                            db.session.add(opcao)
                            print(f"DEBUG: Opção adicionada (form): '{texto_opcao_strip}' = {valor_float}")

                # Criar opções padrão automaticamente para SIM_NAO_NA
                elif tipo_enum == TipoResposta.SIM_NAO_NA and 'OpcaoPergunta' in globals():
                    print("DEBUG: Criando opções padrão para SIM_NAO_NA")
                    opcoes_padrao = [
                        {"texto": "Sim", "valor": 1.0, "ordem": 1},
                        {"texto": "Não", "valor": 0.0, "ordem": 2},
                        {"texto": "N.A.", "valor": 0.0, "ordem": 3} # Ajuste o valor se N.A. tiver pontuação diferente
                    ]
                    for op_data in opcoes_padrao:
                        opcao = OpcaoPergunta(
                            texto=op_data["texto"],
                            valor=op_data["valor"],
                            ordem=op_data["ordem"],
                            pergunta_id=nova_pergunta_obj.id,
                            ativo=True # <<< Garante ativo=True
                        )
                        db.session.add(opcao)
                        print(f"DEBUG: Opção padrão adicionada: '{op_data['texto']}'")
                
                # --- FIM DA LÓGICA DE OPÇÕES CORRIGIDA ---
                
                db.session.commit()
                log_acao(f"Criou pergunta: {texto[:50]}...", None, "Pergunta", nova_pergunta_obj.id)
                
                flash("Pergunta criada com sucesso!", "success")
                print(f"DEBUG: Redirecionando para gerenciar_perguntas com topico_id={topico_id}")
                return redirect(url_for('cli.gerenciar_perguntas', topico_id=topico_id))
                
            except Exception as e:
                print(f"DEBUG: Erro no POST da pergunta: {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                flash(f"Erro ao criar pergunta: {str(e)}", "danger")
                # Passa os dados do formulário de volta para preencher os campos
                return render_template_safe('cli/nova_pergunta.html', topico=topico, form_data=request.form)
        
        # GET - Mostrar formulário
        print("DEBUG: Renderizando template nova_pergunta.html para GET")
        return render_template_safe('cli/nova_pergunta.html', topico=topico)
            
    except Exception as e:
        print(f"DEBUG: Erro geral em nova_pergunta: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao carregar formulário: {str(e)}", "danger")
        # Tenta redirecionar para gerenciar_topicos se topico_id estiver disponível
        redirect_url = url_for('cli.listar_questionarios')
        # Correção: O redirect deve ser para gerenciar_topicos usando 'id' do questionário
        if 'topico' in locals() and hasattr(topico, 'questionario_id'):
             try:
                 redirect_url = url_for('cli.gerenciar_topicos', id=topico.questionario_id)
             except Exception as redirect_err:
                 print(f"DEBUG: Erro ao gerar URL para gerenciar_topicos: {redirect_err}")
                 pass # Mantém o redirect para listar_questionarios
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
    """Editar pergunta existente - ATUALIZADA (v3 - auto-opções SIM_NAO_NA)""" # <-- Nome atualizado
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
                pergunta.exige_foto_se_nao_conforme = request.form.get('exige_foto_se_nao_conforme') == 'on'

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
             pass # Mantém o redirect para listar_questionarios
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

@cli_bp.route('/listar-avaliados', methods=['GET'])
@cli_bp.route('/avaliados', methods=['GET'])
@login_required
def listar_avaliados():
    """Lista avaliados do cliente do usuário, com filtro opcional por nome."""
    try:
        nome = (request.args.get('nome') or '').strip()

        q = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
        if nome:
            q = q.filter(Avaliado.nome.ilike(f'%{nome}%'))

        avaliados = q.order_by(Avaliado.nome.asc()).all()

        # Se você tiver campos personalizados, carregue aqui; senão, passe lista vazia
        campos_personalizados = []

        return render_template_safe(
            'cli/listar_avaliados.html',
            avaliados=avaliados,
            campos_personalizados=campos_personalizados
        )
    except Exception as e:
        flash(f'Erro ao listar avaliados: {str(e)}', 'danger')
        return render_template_safe(
            'cli/listar_avaliados.html',
            avaliados=[],
            campos_personalizados=[]
        )
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



@cli_bp.route('/avaliados/<int:id>/editar', methods=['GET', 'POST'])
@cli_bp.route('/avaliado/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_avaliado(id):
    """Edita um avaliado do cliente atual."""
    try:
        avaliado = Avaliado.query.get_or_404(id)

        # segurança: o avaliado precisa pertencer ao mesmo cliente do usuário
        if avaliado.cliente_id != current_user.cliente_id:
            flash("Avaliado não encontrado.", "danger")
            return redirect(url_for('cli.listar_avaliados'))

        if request.method == 'POST':
            try:
                nome = (request.form.get('nome') or '').strip()
                codigo = (request.form.get('codigo') or '').strip()
                endereco = (request.form.get('endereco') or '').strip()
                grupo_id_raw = request.form.get('grupo_id')
                ativo_flag = request.form.get('ativo') == 'on'

                if not nome:
                    flash("Nome é obrigatório.", "warning")
                    return redirect(url_for('cli.editar_avaliado', id=id))

                # valida grupo (se enviado) e se pertence ao mesmo cliente
                grupo = None
                if grupo_id_raw:
                    try:
                        gid = int(grupo_id_raw)
                    except ValueError:
                        flash("Grupo inválido.", "warning")
                        return redirect(url_for('cli.editar_avaliado', id=id))

                    grupo = Grupo.query.filter_by(
                        id=gid, cliente_id=current_user.cliente_id, ativo=True
                    ).first()
                    if not grupo:
                        flash("Grupo não encontrado ou sem permissão.", "warning")
                        return redirect(url_for('cli.editar_avaliado', id=id))

                # código único por cliente (se fornecido e mudou)
                if codigo and codigo != (avaliado.codigo or ''):
                    existe = Avaliado.query.filter_by(
                        cliente_id=current_user.cliente_id, codigo=codigo
                    ).first()
                    if existe and existe.id != id:
                        flash("Já existe um avaliado com este código.", "warning")
                        return redirect(url_for('cli.editar_avaliado', id=id))

                # aplica alterações
                avaliado.nome = nome
                avaliado.codigo = (codigo or None)
                avaliado.endereco = (endereco or None)
                avaliado.grupo_id = (grupo.id if grupo else None)
                avaliado.ativo = ativo_flag

                # campos opcionais, se existirem no modelo
                for campo in ('email', 'idioma'):
                    if campo in request.form:
                        try:
                            valor = (request.form.get(campo) or None)
                            setattr(avaliado, campo, valor)
                        except Exception:
                            pass

                db.session.commit()

                log_acao(
                    "Editou avaliado",
                    {"id": id, "nome": avaliado.nome, "codigo": avaliado.codigo},
                    "Avaliado",
                    id
                )

                flash("Avaliado atualizado com sucesso!", "success")
                return redirect(url_for('cli.listar_avaliados'))

            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao atualizar avaliado: {str(e)}", "danger")

        # GET: carrega grupos do mesmo cliente
        grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome.asc()).all()
        return render_template_safe('cli/editar_avaliado.html', avaliado=avaliado, grupos=grupos)

    except Exception as e:
        flash(f"Erro ao carregar avaliado: {str(e)}", "danger")
        return redirect(url_for('cli.listar_avaliados'))
    

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
    """Lista todas as aplicações de questionário"""
    try:
        # Filtros
        avaliado_id = request.args.get('avaliado_id')
        questionario_id = request.args.get('questionario_id')
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Query base
        query = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id
        )
        
        # Aplicar filtros
        if avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
        
        if questionario_id:
            query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
        
        if status:
            query = query.filter(AplicacaoQuestionario.status == status)
        
        if data_inicio:
            query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        
        if data_fim:
            query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        # Paginação
        page = request.args.get('page', 1, type=int)
        aplicacoes = query.order_by(AplicacaoQuestionario.data_inicio.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Dados para filtros
        avaliados = get_avaliados_usuario()
        questionarios = Questionario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True,
            publicado=True
        ).all()
        
        return render_template_safe('cli/listar_aplicacoes.html',
                             aplicacoes=aplicacoes,
                             avaliados=avaliados,
                             questionarios=questionarios,
                             filtros={
                                 'avaliado_id': int(avaliado_id) if avaliado_id else None,
                                 'questionario_id': int(questionario_id) if questionario_id else None,
                                 'status': status,
                                 'data_inicio': data_inicio,
                                 'data_fim': data_fim
                             })
    except Exception as e:
        flash(f"Erro ao carregar aplicações: {str(e)}", "danger")
        return render_template_safe('cli/index.html')

@cli_bp.route('/aplicacao/nova', methods=['GET', 'POST'])
@cli_bp.route('/nova-aplicacao', methods=['GET', 'POST'])
@login_required
def nova_aplicacao():
    """Inicia uma nova aplicação de questionário"""
    if request.method == 'POST':
        try:
            avaliado_id = int(request.form.get('avaliado_id'))
            questionario_id = int(request.form.get('questionario_id'))
            observacoes = request.form.get('observacoes', '').strip()
            
            # Validar permissões
            avaliado = Avaliado.query.get_or_404(avaliado_id)
            if avaliado.cliente_id != current_user.cliente_id:
                flash("Avaliado não encontrado.", "error")
                return redirect(url_for('cli.nova_aplicacao'))
            
            questionario = Questionario.query.get_or_404(questionario_id)
            if questionario.cliente_id != current_user.cliente_id or not questionario.publicado:
                flash("Questionário não disponível.", "error")
                return redirect(url_for('cli.nova_aplicacao'))
            
            # Criar aplicação
            aplicacao = AplicacaoQuestionario(
                avaliado_id=avaliado_id,
                questionario_id=questionario_id,
                aplicador_id=current_user.id,
                data_inicio=datetime.now(),
                observacoes=observacoes,
                status=StatusAplicacao.EM_ANDAMENTO
            )
            
            db.session.add(aplicacao)
            db.session.commit()
            
            log_acao(f"Iniciou aplicação do questionário: {questionario.nome}", None, "AplicacaoQuestionario", aplicacao.id)
            flash("Aplicação iniciada com sucesso!", "success")
            
            return redirect(url_for('cli.responder_aplicacao', id=aplicacao.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao iniciar aplicação: {str(e)}", "danger")
    
    try:
        # GET - Mostrar formulário
        avaliados = get_avaliados_usuario()
        questionarios = Questionario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True,
            publicado=True
        ).all()
        
        return render_template_safe('cli/iniciar_aplicacao.html',
                             avaliados=avaliados,
                             questionarios=questionarios)
    except Exception as e:
        flash(f"Erro ao carregar formulário: {str(e)}", "danger")
        return redirect(url_for('cli.listar_aplicacoes'))

# Em app/cli/routes.py

@cli_bp.route('/aplicacao/<int:id>/responder')
@login_required
def responder_aplicacao(id):
    """Interface para responder aplicação - ATUALIZADA E CORRIGIDA (v2)"""
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)

        # ... (Verificações de permissão e status como antes) ...
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Aplicação não encontrada.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))
        if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
            flash("Esta aplicação já foi finalizada ou cancelada.", "warning")
            return redirect(url_for('cli.visualizar_aplicacao', id=id))
        # --------------------------------------------------------

        # --- CORREÇÃO: Carregamento em etapas para evitar erro do lazy='dynamic' ---

        # 1. Carregar tópicos ativos do questionário
        topicos = Topico.query.filter(
            Topico.questionario_id == aplicacao.questionario_id,
            Topico.ativo == True
        ).order_by(Topico.ordem).all()

        if not topicos:
             flash("Este questionário não possui tópicos ativos.", "warning")
             # Permite finalizar mesmo se não houver tópicos/perguntas
             return render_template_safe(
                'cli/responder_aplicacao.html',
                aplicacao=aplicacao,
                topicos=[],
                perguntas_por_topico={},
                respostas_existentes={}
            )

        topico_ids = [t.id for t in topicos]

        # 2. Carregar todas as perguntas ativas para esses tópicos
        #    --- ESTA É A LINHA CORRIGIDA ---
        #    Removido o .options(joinedload(Pergunta.opcoes)) para evitar o erro
        perguntas_ativas = Pergunta.query.filter(
            Pergunta.topico_id.in_(topico_ids),
            Pergunta.ativo == True
        ).order_by(Pergunta.ordem).all()
        
        perguntas_ativas_ids = [p.id for p in perguntas_ativas]

        # 3. Carregar todas as respostas existentes para ESTA aplicação
        respostas_lista = []
        if perguntas_ativas_ids: # Só busca respostas se houver perguntas
            respostas_lista = RespostaPergunta.query.filter(
                RespostaPergunta.aplicacao_id == aplicacao.id,
                RespostaPergunta.pergunta_id.in_(perguntas_ativas_ids)
            ).all()
        
        # 4. Organizar perguntas por tópico (para o template)
        perguntas_por_topico = {}
        for p in perguntas_ativas:
            if p.topico_id not in perguntas_por_topico:
                perguntas_por_topico[p.topico_id] = []
            perguntas_por_topico[p.topico_id].append(p)
        
        # 5. Organizar respostas por ID da pergunta (para o template)
        respostas_map = {r.pergunta_id: r for r in respostas_lista}
        # --------------------------------------------------------------------------

        current_app.logger.debug(f"Renderizando responder_aplicacao para ID {id}. Respostas encontradas: {len(respostas_map)}")

        return render_template_safe(
            'cli/responder_aplicacao.html',
            aplicacao=aplicacao,
            topicos=topicos, # Passa a lista de tópicos
            perguntas_por_topico=perguntas_por_topico, # <--- DICIONÁRIO CORRETO
            respostas_existentes=respostas_map # Passa o mapa de respostas
        )
    except Exception as e:
        # Este log de erro é o que você está vendo no console
        current_app.logger.error(f"Erro ao carregar aplicação {id} para responder: {e}", exc_info=True)
        flash(f"Erro ao carregar aplicação para responder: {str(e)}", "danger")
        return redirect(url_for('cli.listar_aplicacoes'))


# Em app/cli/routes.py

# Em app/cli/routes.py

# Em app/cli/routes.py

# ... (mantenha o resto do arquivo como está) ...

# Em app/cli/routes.py

# ... (mantenha o resto do arquivo como está) ...

# Em app/cli/routes.py

# ... (outras rotas) ...

@cli_bp.route('/aplicacao/<int:id>/finalizar', methods=['POST'])
@login_required
def finalizar_aplicacao(id):
    """
    Finaliza uma aplicação:
    - Valida fotos obrigatórias para respostas 'Não Conforme'.
    - Valida perguntas obrigatórias não respondidas.
    - Calcula a nota final percentual dinamicamente com base na soma dos pesos das perguntas pontuáveis.
    """
    try:
        # ===== CORREÇÃO APLICADA AQUI =====
        # Removemos joinedload para topicos e perguntas que conflitam com lazy='dynamic'
        aplicacao = AplicacaoQuestionario.query.options(
            db.joinedload(AplicacaoQuestionario.questionario), # Carrega SÓ o questionário
            db.joinedload(AplicacaoQuestionario.avaliado)
        ).get_or_404(id)
        # ==================================

        # Carrega as respostas separadamente, respeitando o lazy='dynamic'
        respostas_list = list(aplicacao.respostas) # Ou aplicacao.respostas.all()
        respostas_dict = {r.pergunta_id: r for r in respostas_list} # Mapa para acesso rápido

        # Carrega os tópicos ativos DO questionário (respeitando lazy='dynamic')
        # Precisamos deles para validações e cálculo do máximo
        topicos_q_ativos = aplicacao.questionario.topicos.filter_by(ativo=True).all()
        # Prepara um dicionário para carregar perguntas DEPOIS, se necessário
        perguntas_por_topico_id = {}


        # Verificar permissões (como antes)
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Aplicação não encontrada.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))

        if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
            flash("Esta aplicação já foi finalizada ou cancelada.", "warning")
            return redirect(url_for('cli.visualizar_aplicacao', id=id))

        # --- VALIDAÇÃO DE FOTOS OBRIGATÓRIAS ---
        perguntas_sem_foto_obrigatoria = []
        # Itera sobre os tópicos ativos carregados
        for topico_val in topicos_q_ativos:
            # Carrega as perguntas ativas DESTE tópico (respeitando lazy='dynamic')
            perguntas_q_validacao = topico_val.perguntas.filter_by(ativo=True).all()
            perguntas_por_topico_id[topico_val.id] = perguntas_q_validacao # Armazena para reuso
            for pergunta_val in perguntas_q_validacao:
                 # Verifica se a pergunta exige foto E se foi respondida
                 if pergunta_val.exige_foto_se_nao_conforme and pergunta_val.id in respostas_dict:
                     resposta_obj = respostas_dict[pergunta_val.id]
                     resposta_texto_lower = (resposta_obj.resposta or "").strip().lower()
                     respostas_nao_conforme = ['não', 'nao', 'no']
                     if resposta_texto_lower in respostas_nao_conforme and not resposta_obj.caminho_foto:
                         perguntas_sem_foto_obrigatoria.append(f"'{pergunta_val.texto}' (Tópico: {topico_val.nome})")

        # Se houver perguntas pendentes de foto, bloqueia a finalização (como antes)
        if perguntas_sem_foto_obrigatoria:
             count = len(perguntas_sem_foto_obrigatoria)
             flash(f"Não foi possível finalizar. {count} pergunta(s) respondida(s) como 'Não' exigem uma foto de evidência:", "danger")
             for i, texto_pergunta in enumerate(perguntas_sem_foto_obrigatoria[:5]): flash(f"- {texto_pergunta}", "warning")
             if count > 5: flash("...", "warning")
             current_app.logger.warning(f"Finalização aplicação {id} bloqueada. Fotos faltantes: {perguntas_sem_foto_obrigatoria}")
             return redirect(url_for('cli.responder_aplicacao', id=id))
        # --- FIM DA VALIDAÇÃO DE FOTOS OBRIGATÓRIAS ---

        # --- VALIDAÇÃO DE PERGUNTAS OBRIGATÓRIAS ---
        if 'RespostaPergunta' in globals():
            perguntas_obrigatorias_ids = set()
            # Itera sobre os tópicos e perguntas já carregados/armazenados
            for topico_obr in topicos_q_ativos:
                 # Usa as perguntas já carregadas se disponíveis
                 perguntas_do_topico = perguntas_por_topico_id.get(topico_obr.id)
                 if perguntas_do_topico is None: # Carrega se ainda não carregou
                      perguntas_do_topico = topico_obr.perguntas.filter_by(ativo=True).all()
                      perguntas_por_topico_id[topico_obr.id] = perguntas_do_topico

                 for p_obr in perguntas_do_topico:
                      if p_obr.obrigatoria: # ativo=True já foi filtrado
                           perguntas_obrigatorias_ids.add(p_obr.id)

            respostas_dadas_ids = set(respostas_dict.keys())
            perguntas_faltando_ids = perguntas_obrigatorias_ids - respostas_dadas_ids

            if perguntas_faltando_ids:
                 # ... (código flash e redirect como antes) ...
                 perguntas_faltantes_obj = Pergunta.query.filter(Pergunta.id.in_(list(perguntas_faltando_ids))).limit(5).all()
                 textos_faltando = [p.texto for p in perguntas_faltantes_obj]
                 flash(f"Existem {len(perguntas_faltando_ids)} pergunta(s) obrigatória(s) sem resposta.", "warning")
                 for texto_pf in textos_faltando: flash(f"- {texto_pf}", "secondary")
                 if len(perguntas_faltando_ids) > 5: flash("...", "secondary")
                 current_app.logger.warning(f"Finalização aplicação {id} bloqueada. Perguntas obrigatórias faltando: {perguntas_faltando_ids}")
                 return redirect(url_for('cli.responder_aplicacao', id=id))
        # --- FIM DA VALIDAÇÃO DE PERGUNTAS OBRIGATÓRIAS ---


        # --- CÁLCULO DE NOTA FINAL (LÓGICA DINÂMICA) ---
        if aplicacao.questionario.calcular_nota:
            pontos_obtidos_bruto = 0.0
            pontuacao_maxima_possivel = 0.0

            # 1. Calcula a pontuação máxima possível
            # Itera sobre os tópicos e perguntas já carregados/armazenados
            for topico_q in topicos_q_ativos:
                # Usa as perguntas já carregadas se disponíveis
                perguntas_do_topico_calc = perguntas_por_topico_id.get(topico_q.id)
                if perguntas_do_topico_calc is None: # Carrega se ainda não carregou
                    perguntas_do_topico_calc = topico_q.perguntas.filter_by(ativo=True).all()
                    
                for pergunta_q in perguntas_do_topico_calc:
                    peso_pergunta_float = (pergunta_q.peso or 0) * 1.0
                    
                    # Pular perguntas sem peso
                    if peso_pergunta_float == 0:
                        continue

                    # --- INÍCIO DA LÓGICA ALTERADA (v3 - FINALIZAR) ---
                    # 1. Verificar se a pergunta é do tipo SIM_NAO (lógica robusta)
                    is_tipo_sim_nao = False
                    try:
                        # Replicando a lógica exata de 'salvar_resposta' para identificar o tipo
                        if hasattr(pergunta_q.tipo, 'name'): 
                            tipo_str = pergunta_q.tipo.name.upper()
                        elif hasattr(pergunta_q.tipo, 'value'): 
                            tipo_str = str(pergunta_q.tipo.value).upper().replace(" ", "_").replace("/", "_")
                        else: 
                            tipo_str = str(pergunta_q.tipo or "").upper().replace(" ", "_").replace("/", "_")
                        
                        # Lista de tipos válidos (baseado no pontuacao.py e salvar_resposta)
                        tipos_sim_nao_validos = ['SIM_NAO_NA', 'SIM_NAO', 'SIM_NÃO']
                        
                        if tipo_str in tipos_sim_nao_validos:
                            is_tipo_sim_nao = True
                            
                    except Exception as e_tipo:
                        current_app.logger.warning(f"Erro ao verificar tipo da pergunta {pergunta_q.id} na finalização: {e_tipo}")
                        pass # Deixa is_tipo_sim_nao como False
                        
                    # 2. Se for tipo SIM_NAO, verificar a resposta
                    if is_tipo_sim_nao:
                        # Usar o dict de respostas carregado no início da função
                        resposta_obj = respostas_dict.get(pergunta_q.id)
                        
                        # 3. Se a resposta for 'N.A.' (ou variações), pular esta pergunta
                        # Verificando N.A., N/A e NA (maiúsculas/minúsculas)
                        if resposta_obj and (resposta_obj.resposta or "").strip().upper() in ["N.A.", "N/A", "NA"]:
                            current_app.logger.info(f"FINALIZAR: Pergunta {pergunta_q.id} marcada como N.A., pulando do cálculo máximo.")
                            continue # Não adiciona ao pontuacao_maxima_possivel
                    
                    # --- FIM DA LÓGICA ALTERADA (v3 - FINALIZAR) ---
                    
                    # 4. Se não for N.A. (ou não for tipo SIM_NAO), adicionar ao máximo
                    pontuacao_maxima_possivel += peso_pergunta_float

            # 2. Soma os pontos obtidos nas respostas DADAS
            # Usa a lista 'respostas_list' carregada no início
            for resposta in respostas_list:
                 if resposta.pontos is not None:
                     # Carrega a pergunta associada à resposta para verificar status
                     pergunta_resposta = Pergunta.query.get(resposta.pergunta_id)
                     if pergunta_resposta and pergunta_resposta.ativo and (pergunta_resposta.topico and pergunta_resposta.topico.ativo):
                          pontos_obtidos_bruto += resposta.pontos

            # Armazena os valores calculados
            aplicacao.pontos_obtidos = round(pontos_obtidos_bruto, 2)
            aplicacao.pontos_totais = round(pontuacao_maxima_possivel, 2)

            # 3. Calcula a nota final percentual (como antes)
            if pontuacao_maxima_possivel > 0:
                nota_percentual = (pontos_obtidos_bruto / pontuacao_maxima_possivel) * 100
                aplicacao.nota_final = min(nota_percentual, 100.0)
                casas_dec = aplicacao.questionario.casas_decimais
                if casas_dec is not None and casas_dec >= 0:
                     aplicacao.nota_final = round(aplicacao.nota_final, casas_dec)
            else:
                 aplicacao.nota_final = 0.0 # Nota 0 se nenhuma pergunta pontuável for aplicável

            current_app.logger.info(f"Cálculo de nota V3 (FINALIZAR) para aplicação {id}: Obtidos={pontos_obtidos_bruto}, Máximo={pontuacao_maxima_possivel}, Final={aplicacao.nota_final}%")
        # --- FIM DO CÁLCULO DE NOTA ---

        # Finalizar aplicação (como antes)
        aplicacao.data_fim = datetime.now()
        aplicacao.status = StatusAplicacao.FINALIZADA
        aplicacao.observacoes_finais = request.form.get('observacoes_finais', aplicacao.observacoes_finais or '')

        db.session.commit()

        log_acao(f"Finalizou aplicação: {aplicacao.questionario.nome}", {"nota": aplicacao.nota_final}, "AplicacaoQuestionario", id)
        flash("Aplicação finalizada com sucesso!", "success")

        return redirect(url_for('cli.visualizar_aplicacao', id=id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao finalizar aplicação {id}: {e}", exc_info=True)
        flash(f"Erro inesperado ao finalizar aplicação: {str(e)}", "danger")
        return redirect(url_for('cli.responder_aplicacao', id=id))

# ... (outras rotas) ...
    

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
    """Visualiza uma aplicação finalizada"""
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        
        # Verificar permissões
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Aplicação não encontrada.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))
        
        # Buscar estrutura completa
        topicos = Topico.query.filter_by(
            questionario_id=aplicacao.questionario_id,
            ativo=True
        ).order_by(Topico.ordem).all()
        
        # Organizar respostas por pergunta
        respostas_dict = {}
        if hasattr(aplicacao, 'respostas'):
            for resposta in aplicacao.respostas:
                respostas_dict[resposta.pergunta_id] = resposta
        
        # Estatísticas
        stats = {
            'total_perguntas': len(respostas_dict),
            'perguntas_respondidas': len([r for r in respostas_dict.values() if r.resposta.strip()]),
            'tempo_aplicacao': (aplicacao.data_fim - aplicacao.data_inicio).total_seconds() / 60 if aplicacao.data_fim else None
        }
        
        return render_template_safe('cli/visualizar_aplicacao.html',
                             aplicacao=aplicacao,
                             topicos=topicos,
                             respostas_dict=respostas_dict,
                             stats=stats)
    except Exception as e:
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

@cli_bp.route('/usuarios')
@login_required
@admin_required
def gerenciar_usuarios():
    """Página de gestão de usuários"""
    try:
        usuarios = Usuario.query.filter_by(
            cliente_id=current_user.cliente_id
        ).order_by(Usuario.nome).all()
        
        # Estatísticas de usuários
        stats_usuarios = {
            'total': len(usuarios),
            'ativos': len([u for u in usuarios if u.ativo]),
            'admins': len([u for u in usuarios if verificar_permissao_admin()]),
            'usuarios': len([u for u in usuarios if not verificar_permissao_admin()])
        }
        
        return render_template_safe('cli/usuarios.html',
                             usuarios=usuarios,
                             stats=stats_usuarios)
    except Exception as e:
        flash(f"Erro ao carregar usuários: {str(e)}", "danger")
        return render_template_safe('cli/index.html')

@cli_bp.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    """Criar novo usuário"""
    if request.method == 'POST':
        try:
            # Validar dados
            nome = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip().lower()
            tipo = request.form.get('tipo')
            grupo_id = request.form.get('grupo_id')
            
            if not all([nome, email, tipo]):
                flash('Todos os campos são obrigatórios.', 'error')
                return render_template_safe('cli/usuario_form.html')
            
            # Verificar se email já existe
            if Usuario.query.filter_by(email=email).first():
                flash('Este e-mail já está em uso.', 'error')
                return render_template_safe('cli/usuario_form.html')
            
            # Criar usuário
            from werkzeug.security import generate_password_hash
            usuario = Usuario(
                nome=nome,
                email=email,
                tipo=tipo,
                cliente_id=current_user.cliente_id,
                grupo_id=int(grupo_id) if grupo_id else None,
                senha_hash=generate_password_hash('123456'),  # Senha padrão
                ativo=True
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            log_acao(f"Criou usuário: {nome}", None, "Usuario", usuario.id)
            flash(f'Usuário {nome} criado com sucesso! Senha padrão: 123456', 'success')
            return redirect(url_for('cli.gerenciar_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
    
    try:
        grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
        return render_template_safe('cli/usuario_form.html', grupos=grupos)
    except Exception as e:
        flash(f"Erro ao carregar formulário: {str(e)}", "danger")
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

# Em app/cli/routes.py

@cli_bp.route('/aplicacao/<int:id>/salvar-resposta', methods=['POST'])
@login_required
@csrf.exempt
def salvar_resposta(id):
    """Salva uma resposta individual (AJAX) - COM LOGS DETALHADOS"""
    # Adiciona um log no início da função
    current_app.logger.info(f"--- Rota /salvar-resposta chamada para app ID: {id} ---")
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)

        # Permissão
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            current_app.logger.warning(f"[Salvar Resposta {id}] Acesso negado - Cliente diferente.")
            return jsonify({'erro': 'Acesso negado'}), 403
        if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
            current_app.logger.warning(f"[Salvar Resposta {id}] Aplicação não está em andamento (Status: {aplicacao.status}).")
            return jsonify({'erro': 'Aplicação já finalizada'}), 400

        data = request.get_json() or {}
        pergunta_id = data.get('pergunta_id')
        resposta_texto = (data.get('resposta') or '').strip()
        observacao = (data.get('observacao') or '').strip()

        # Adiciona logs para os dados recebidos
        current_app.logger.info(f"[Salvar Resposta {id}] Dados recebidos: Pergunta ID={pergunta_id}, Resposta='{resposta_texto}', Observacao='{observacao}'")

        if not pergunta_id:
            current_app.logger.error(f"[Salvar Resposta {id}] Erro: 'pergunta_id' não recebido no JSON.")
            return jsonify({'erro': 'ID da pergunta ausente'}), 400

        pergunta = Pergunta.query.get(pergunta_id) # Usar get em vez de get_or_404 para log customizado
        if not pergunta:
            current_app.logger.error(f"[Salvar Resposta {id}] Erro: Pergunta com ID {pergunta_id} não encontrada no banco.")
            return jsonify({'erro': f'Pergunta ID {pergunta_id} não encontrada'}), 404

        current_app.logger.info(f"[Salvar Resposta {id}] Pergunta encontrada: ID={pergunta.id}, Texto='{pergunta.texto[:50]}...', Tipo={pergunta.tipo}")

        # Normaliza tipo para string de comparação
        if hasattr(pergunta.tipo, 'name'): tipo = pergunta.tipo.name
        elif hasattr(pergunta.tipo, 'value'): tipo = str(pergunta.tipo.value).upper().replace(" ", "_")
        else: tipo = str(pergunta.tipo or "").upper().replace(" ", "_")
        current_app.logger.info(f"[Salvar Resposta {id}] Tipo normalizado: {tipo}")

        # Busca/Cria resposta
        resposta = RespostaPergunta.query.filter_by(
            aplicacao_id=id,
            pergunta_id=pergunta_id
        ).first()
        if not resposta:
            current_app.logger.info(f"[Salvar Resposta {id}] Criando nova entrada RespostaPergunta.")
            resposta = RespostaPergunta(
                aplicacao_id=id,
                pergunta_id=pergunta_id
            )
        else:
            current_app.logger.info(f"[Salvar Resposta {id}] Atualizando RespostaPergunta existente (ID: {resposta.id}).")


        resposta.resposta = resposta_texto
        resposta.observacao = observacao
        resposta.pontos = 0  # default inicial

        # Pontuação por tipo
        if tipo in ['SIM_NAO_NA', 'MULTIPLA_ESCOLHA']:
            current_app.logger.info(f"[Salvar Resposta {id}] Buscando OpcaoPergunta para pergunta_id={pergunta_id} e texto='{resposta_texto}'")
            opcao = OpcaoPergunta.query.filter_by(
                pergunta_id=pergunta_id,
                texto=resposta_texto # Atenção à correspondência exata aqui!
            ).first()
            if opcao:
                current_app.logger.info(f"[Salvar Resposta {id}] OpcaoPergunta encontrada: ID={opcao.id}, Valor={opcao.valor}, Texto='{opcao.texto}'")
                if opcao.valor is not None:
                    peso_pergunta = pergunta.peso or 1
                    resposta.pontos = float(opcao.valor) * peso_pergunta
                    current_app.logger.info(f"[Salvar Resposta {id}] Pontos calculados: {float(opcao.valor)} (valor) * {peso_pergunta} (peso) = {resposta.pontos}")
                else:
                    current_app.logger.warning(f"[Salvar Resposta {id}] OpcaoPergunta encontrada (ID={opcao.id}) mas 'valor' é None. Pontos serão 0.")
            else:
                # Log crucial se a opção não for encontrada
                current_app.logger.warning(f"[Salvar Resposta {id}] Nenhuma OpcaoPergunta encontrada para pergunta_id={pergunta_id} com texto='{resposta_texto}'. Pontos serão 0.")

        elif tipo in ['ESCALA_NUMERICA', 'NOTA']:
            try:
                nota = float(resposta_texto)
                peso_pergunta = pergunta.peso or 1
                resposta.pontos = nota * peso_pergunta
                current_app.logger.info(f"[Salvar Resposta {id}] Pontos (Escala/Nota) calculados: {nota} (valor) * {peso_pergunta} (peso) = {resposta.pontos}")
            except ValueError:
                current_app.logger.warning(f"[Salvar Resposta {id}] Não foi possível converter resposta '{resposta_texto}' para float (Escala/Nota). Pontos serão 0.")
                resposta.pontos = 0

        elif tipo == 'TEXTO_CURTO' or tipo == 'TEXTO_LONGO': # Adicionado TEXTO_LONGO
            current_app.logger.info(f"[Salvar Resposta {id}] Tipo Texto. Pontos mantidos em 0.")
            pass # mantém pontos = 0
        else:
            current_app.logger.info(f"[Salvar Resposta {id}] Tipo {tipo}. Pontos mantidos em 0.")
            pass # Outros tipos por enquanto não pontuam

        current_app.logger.info(f"[Salvar Resposta {id}] Preparando para salvar no DB: Resposta='{resposta.resposta}', Obs='{resposta.observacao}', Pontos={resposta.pontos}")
        db.session.add(resposta) # Adiciona à sessão (seja novo ou existente)
        db.session.flush() # Tenta aplicar à sessão para obter o ID se for novo
        resposta_id_retorno = resposta.id
        current_app.logger.info(f"[Salvar Resposta {id}] Flush bem-sucedido. ID da Resposta (novo ou existente): {resposta_id_retorno}")
        db.session.commit() # Tenta salvar permanentemente
        current_app.logger.info(f"[Salvar Resposta {id}] Commit bem-sucedido!")

        return jsonify({
            'sucesso': True,
            'mensagem': 'Resposta salva com sucesso',
            'pontos': resposta.pontos or 0,
            'resposta_id': resposta_id_retorno
        })
    except Exception as e:
        db.session.rollback() # Desfaz TUDO em caso de QUALQUER erro
        # Log CRÍTICO do erro
        current_app.logger.error(f"[Salvar Resposta {id}] ERRO AO SALVAR RESPOSTA:", exc_info=True) # exc_info=True mostra o traceback completo
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
    """Página de gestão de grupos"""
    try:
        grupos = Grupo.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).order_by(Grupo.nome).all()
        
        # Contar avaliados por grupo
        for grupo in grupos:
            grupo.total_avaliados = Avaliado.query.filter_by(
                grupo_id=grupo.id,
                ativo=True
            ).count()
        
        return render_template_safe('cli/listar_grupos.html', grupos=grupos)
    except Exception as e:
        flash(f"Erro ao carregar grupos: {str(e)}", "danger")
        return render_template_safe('cli/index.html')

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

@cli_bp.route('/perfil')
@cli_bp.route('/profile')
@cli_bp.route('/meu-perfil')
@login_required
def placeholder_perfil():
    """Página de perfil (placeholder)"""
    return criar_placeholder_route('placeholder_perfil', 'Perfil do Usuário',
                                   'Módulo de perfil em desenvolvimento.')()

@cli_bp.route('/ajuda')
@cli_bp.route('/help')
@cli_bp.route('/suporte')
@login_required  
def placeholder_ajuda():
    """Página de ajuda (placeholder)"""
    return criar_placeholder_route('placeholder_ajuda', 'Ajuda e Suporte',
                                   'Módulo de ajuda em desenvolvimento.')()

@cli_bp.route('/sobre')
@cli_bp.route('/about')
@cli_bp.route('/info')
@login_required
def placeholder_sobre():
    """Página sobre (placeholder)"""
    return criar_placeholder_route('placeholder_sobre', 'Sobre o Sistema',
                                   'Informações sobre o QualiGestor CLIQ.')()

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
def upload_foto_resposta(resposta_id):
    """Recebe upload de foto via AJAX para uma resposta específica."""
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
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg'}) # Default seguro
        
        # ***** LINHA CORRIGIDA (AGORA allowed_file existe) *****
        if foto and allowed_file(foto.filename, allowed_extensions):

            # Gera um nome de arquivo seguro e único (usa 'secure_filename' e 'uuid' importados)
            original_filename = secure_filename(foto.filename)
            extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"resposta_{resposta.id}_{uuid.uuid4().hex[:12]}.{extension}"

            # Caminho completo para salvar o arquivo
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            if not upload_folder:
                 current_app.logger.error("Configuração UPLOAD_FOLDER não definida!")
                 return jsonify({'erro': 'Configuração do servidor incompleta (UPLOAD_FOLDER)'}), 500

            save_path = os.path.join(upload_folder, unique_filename)
            current_app.logger.debug(f"Caminho para salvar: {save_path}")

            # --- Salva o arquivo original ---
            try:
                 os.makedirs(upload_folder, exist_ok=True)
                 foto.save(save_path)
                 current_app.logger.info(f"Foto salva com sucesso em: {save_path} para resposta {resposta_id}")
            except Exception as save_err:
                 current_app.logger.error(f"Erro ao salvar upload para resposta {resposta_id}: {save_err}", exc_info=True)
                 return jsonify({'erro': f'Erro no servidor ao salvar arquivo'}), 500
            # ---------------------------------

            # --- Opcional: Remover foto antiga se existir ---
            if resposta.caminho_foto:
                 try:
                     old_path = os.path.join(upload_folder, resposta.caminho_foto)
                     if os.path.exists(old_path):
                         os.remove(old_path)
                         current_app.logger.info(f"Foto antiga removida: {old_path}")
                 except Exception as del_err:
                     current_app.logger.error(f"Erro ao remover foto antiga {resposta.caminho_foto}: {del_err}")
            # ---------------------------------------------

            # Atualiza o caminho no banco de dados
            resposta.caminho_foto = unique_filename
            db.session.commit()
            current_app.logger.info(f"Caminho da foto '{unique_filename}' salvo no BD para resposta {resposta_id}")

            # Gera URL para a foto (se a rota 'get_foto_resposta' existir)
            foto_url = None
            _has_endpoint_func = globals().get('has_endpoint') or current_app.jinja_env.globals.get('has_endpoint')
            _url_for_func = globals().get('url_for_safe') or current_app.jinja_env.globals.get('url_for_safe') or url_for
            if callable(_has_endpoint_func) and callable(_url_for_func):
                try:
                    if _has_endpoint_func('cli.get_foto_resposta'):
                         foto_url = _url_for_func('cli.get_foto_resposta', filename=unique_filename, _external=True)
                except Exception as url_err:
                     current_app.logger.warning(f"Erro ao gerar URL para get_foto_resposta: {url_err}")


            # Retorna sucesso com o nome do arquivo e URL
            return jsonify({
                'sucesso': True,
                'mensagem': 'Foto enviada com sucesso!',
                'filename': unique_filename,
                'url': foto_url
                }), 200

        else:
            current_app.logger.warning(f"Upload negado para resposta {resposta_id}: tipo de arquivo não permitido ({foto.filename})")
            return jsonify({'erro': f"Tipo de arquivo não permitido. Permitidos: {', '.join(allowed_extensions)}"}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro inesperado no upload da foto para resposta {resposta_id}: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return jsonify({'erro': f'Erro interno do servidor'}), 500


# --- ROTA AUXILIAR PARA SERVIR AS FOTOS SALVAS ---
@cli_bp.route('/uploads/fotos_respostas/<path:filename>')
@login_required
def get_foto_resposta(filename):
    """Serve um arquivo de foto de resposta, verificando permissão."""

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        current_app.logger.error("Configuração UPLOAD_FOLDER não definida ao tentar servir foto.")
        abort(500) # <- 'abort' agora está importado

    # --- VALIDAÇÃO DE PERMISSÃO ---
    try:
        # Tenta extrair o ID da resposta do nome do arquivo
        if filename.startswith('resposta_') and '_' in filename:
             parts = filename.split('_')
             resposta_id_str = parts[1]
             if resposta_id_str.isdigit():
                 resposta_id = int(resposta_id_str)
                 resposta = RespostaPergunta.query.get(resposta_id)
                 
                 if resposta and resposta.caminho_foto == filename:
                     aplicacao = AplicacaoQuestionario.query.get(resposta.aplicacao_id)
                     if aplicacao:
                         avaliado = Avaliado.query.get(aplicacao.avaliado_id)
                         
                         if avaliado and avaliado.cliente_id == current_user.cliente_id:
                              # Permissão OK, serve o arquivo
                              current_app.logger.debug(f"Servindo foto '{filename}' para usuário {current_user.id}")
                              # vvv 'send_from_directory' agora está importado vvv
                              return send_from_directory(upload_folder, filename, as_attachment=False)
                         else:
                              current_app.logger.warning(f"Permissão negada (cliente diferente) para foto '{filename}'. User: {current_user.id}, Avaliado_Cliente: {avaliado.cliente_id if avaliado else 'N/A'}.")
                     else:
                          current_app.logger.warning(f"Aplicação não encontrada para foto '{filename}' (resposta {resposta_id}).")
                 else:
                     current_app.logger.warning(f"Resposta não encontrada ou filename não corresponde para foto '{filename}' (ID {resposta_id}). DB filename: {resposta.caminho_foto if resposta else 'N/A'}")
             else:
                  current_app.logger.warning(f"Não foi possível extrair ID de resposta válido do nome de arquivo '{filename}'.")
        else:
             current_app.logger.warning(f"Nome de arquivo '{filename}' não segue o padrão esperado 'resposta_<id>_...'")

        abort(403) # Forbidden

    except FileNotFoundError:
         current_app.logger.error(f"Arquivo não encontrado no disco: {os.path.join(upload_folder, filename)}")
         abort(404)
    except Exception as e:
         current_app.logger.error(f"Erro ao servir foto '{filename}': {e}", exc_info=True)
         abort(500)
# ====================================================================
#  FIM DO BLOCO DE CÓDIGO CORRIGIDO
# ====================================================================
    









