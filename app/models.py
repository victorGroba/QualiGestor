# app/models.py
from datetime import datetime
from sqlalchemy import Enum as SqlEnum
import enum
from flask_login import UserMixin
from . import db

# ==================== ENUMS ====================

class TipoResposta(enum.Enum):
    """Tipos de resposta disponíveis para perguntas"""
    SIM_NAO_NA = "Sim/Não/N.A."
    MULTIPLA_ESCOLHA = "Múltipla Escolha"
    ESCALA_NUMERICA = "Escala Numérica"
    NOTA = "Nota"
    TEXTO_CURTO = "Texto Curto"
    TEXTO_LONGO = "Texto Longo"
    FOTO = "Foto"
    DATA = "Data"
    HORA = "Hora"
    NUMERO = "Número"
    PORCENTAGEM = "Porcentagem"
    MOEDA = "Moeda"
    ASSINATURA = "Assinatura Digital"

class CriterioFoto(enum.Enum):
    """Define a obrigatoriedade da foto"""
    NENHUMA = "nenhuma"          # Não pede foto
    OPCIONAL = "opcional"        # Botão de foto aparece, mas usuário não é obrigado
    OBRIGATORIA = "obrigatoria"  # Botão aparece e sistema bloqueia se não enviar

class TipoUsuario(enum.Enum):
    """Tipos de usuário do sistema"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    GESTOR = "gestor"
    AUDITOR = "auditor"
    USUARIO = "usuario"
    VISUALIZADOR = "visualizador"

class StatusQuestionario(enum.Enum):
    """Status de um questionário"""
    RASCUNHO = "rascunho"
    PUBLICADO = "publicado"
    ARQUIVADO = "arquivado"
    INATIVO = "inativo"

class StatusAplicacao(enum.Enum):
    """Status de uma aplicação"""
    EM_ANDAMENTO = "em_andamento"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"
    PAUSADA = "pausada"

class TipoPreenchimento(enum.Enum):
    """Tipo de preenchimento do questionário"""
    RAPIDO = "rapido"
    DETALHADO = "detalhado"
    COMPLETO = "completo"

class ModoExibicaoNota(enum.Enum):
    """Modo de exibição da nota no relatório"""
    PERCENTUAL = "percentual"
    PONTOS = "pontos"
    AMBOS = "ambos"
    OCULTAR = "ocultar"

class CorRelatorio(enum.Enum):
    """Cores disponíveis para o relatório"""
    AZUL = "azul"
    VERDE = "verde"
    VERMELHO = "vermelho"
    LARANJA = "laranja"
    ROXO = "roxo"
    CINZA = "cinza"

# ==================== MODELOS BÁSICOS ====================

class Cliente(db.Model):
    """Clientes do sistema (empresas)"""
    __tablename__ = "cliente"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    razao_social = db.Column(db.String(200))
    cnpj = db.Column(db.String(18))
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Configurações
    plano = db.Column(db.String(50), default='basico')
    limite_usuarios = db.Column(db.Integer, default=10)
    limite_questionarios = db.Column(db.Integer, default=50)
    
    # Relacionamentos
    usuarios = db.relationship('Usuario', backref='cliente', lazy='dynamic')
    grupos = db.relationship('Grupo', backref='cliente', lazy='dynamic')
    avaliados = db.relationship('Avaliado', backref='cliente', lazy='dynamic')
    questionarios = db.relationship('Questionario', backref='cliente', lazy='dynamic')

class Grupo(db.Model):
    """Grupos para organização de avaliados"""
    __tablename__ = "grupo"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    avaliados = db.relationship('Avaliado', backref='grupo', lazy='dynamic')
    usuarios = db.relationship('Usuario', backref='grupo', lazy='dynamic')

class Avaliado(db.Model):
    """Entidades que serão avaliadas (Lojas, Unidades, etc)"""
    __tablename__ = "avaliado"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20))
    nome = db.Column(db.String(100), nullable=False)
    
    # Dados de localização
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    
    # Contato
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    responsavel = db.Column(db.String(100))
    
    # Campos personalizados (JSON)
    campos_personalizados = db.Column(db.Text)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'))
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    aplicacoes = db.relationship('AplicacaoQuestionario', backref='avaliado', lazy='dynamic')

class Usuario(db.Model, UserMixin):
    """
    Tabela de Usuários com Hierarquia Multi-Tenant (Cliente -> Grupo -> Avaliado)
    """
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)

    # --- DADOS PESSOAIS ---
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))

    # --- PERMISSÕES ---
    # Enum: SUPER_ADMIN, ADMIN_CLIENTE, GESTOR_GRUPO, AUDITOR, COMUM
    tipo = db.Column(SqlEnum(TipoUsuario), nullable=False, default=TipoUsuario.USUARIO)
    ativo = db.Column(db.Boolean, default=True)
    ultimo_acesso = db.Column(db.DateTime)

    # --- HIERARQUIA SISUB (O CORAÇÃO DO SISTEMA) ---

    # Nível 1: CLIENTE (Ex: FAB) - Obrigatório
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)

    # Nível 2: GRUPO (Ex: GAP Galeão) - Opcional
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=True)

    # Nível 3: AVALIADO (Ex: Rancho Oficiais) - Opcional
    avaliado_id = db.Column(db.Integer, db.ForeignKey('avaliado.id'), nullable=True)

    # --- METADADOS ---
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # --- RELACIONAMENTOS (LINKS PARA O PYTHON) ---

    # 1. CLIENTE: NÃO PRECISA DEFINIR AQUI (Já existe na classe Cliente como backref='usuarios')
    # cliente = db.relationship('Cliente', backref='usuarios')

    # 2. GRUPO: NÃO PRECISA DEFINIR AQUI (Já existe na classe Grupo como backref='usuarios')
    # grupo = db.relationship('Grupo', backref='usuarios')

    # 3. AVALIADO: ESSE PRECISA! (A classe Avaliado não tinha vinculo com usuário)
    # Cria o link u.avaliado e cria a lista rancho.usuarios_vinculados
    avaliado = db.relationship('Avaliado', backref='usuarios_vinculados')

    # --- MÉTODOS DE SEGURANÇA ---

    def check_password(self, password):
        """Verifica se a senha está correta"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.senha_hash, password)

    def set_password(self, password):
        """Criptografa e define nova senha"""
        from werkzeug.security import generate_password_hash
        self.senha_hash = generate_password_hash(password)

    def __repr__(self):
        return f'<Usuario {self.nome} - {self.email}>'
# ==================== QUESTIONÁRIOS E ESTRUTURA ====================

class Questionario(db.Model):
    """Questionários/Formulários do sistema"""
    __tablename__ = "questionario"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    versao = db.Column(db.String(20), default='1.0')
    modo = db.Column(db.String(50), default='Avaliado')  # Avaliado, Autoavaliação
    documento_referencia = db.Column(db.String(255))
    
    # Configurações das notas
    calcular_nota = db.Column(db.Boolean, default=True)
    ocultar_nota_aplicacao = db.Column(db.Boolean, default=False)
    base_calculo = db.Column(db.Integer, default=100)
    casas_decimais = db.Column(db.Integer, default=2)
    modo_configuracao = db.Column(db.String(20), default='percentual')  # percentual, pontos
    modo_exibicao_nota = db.Column(SqlEnum(ModoExibicaoNota), default=ModoExibicaoNota.PERCENTUAL)
    
    # Configurações de aplicação
    anexar_documentos = db.Column(db.Boolean, default=False)
    capturar_geolocalizacao = db.Column(db.Boolean, default=False)
    restringir_avaliados = db.Column(db.Boolean, default=False)
    habilitar_reincidencia = db.Column(db.Boolean, default=False)
    
    # Opções de preenchimento
    tipo_preenchimento = db.Column(SqlEnum(TipoPreenchimento), default=TipoPreenchimento.RAPIDO)
    pontuacao_ativa = db.Column(db.Boolean, default=True)
    
    # Configurações do relatório
    exibir_nota_anterior = db.Column(db.Boolean, default=False)
    exibir_tabela_resumo = db.Column(db.Boolean, default=True)
    exibir_limites_aceitaveis = db.Column(db.Boolean, default=False)
    exibir_data_hora = db.Column(db.Boolean, default=True)
    exibir_questoes_omitidas = db.Column(db.Boolean, default=False)
    exibir_nao_conformidade = db.Column(db.Boolean, default=True)
    
    # Configurações visuais
    cor_relatorio = db.Column(SqlEnum(CorRelatorio), default=CorRelatorio.AZUL)
    incluir_assinatura = db.Column(db.Boolean, default=True)
    incluir_foto_capa = db.Column(db.Boolean, default=False)
    agrupamento_fotos = db.Column(db.String(20), default='topico')  # topico, pergunta
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    publicado = db.Column(db.Boolean, default=False)
    status = db.Column(SqlEnum(StatusQuestionario), default=StatusQuestionario.RASCUNHO)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_publicacao = db.Column(db.DateTime)
    
    # Relacionamentos
    topicos = db.relationship('Topico', backref='questionario', lazy='dynamic', cascade='all, delete-orphan')
    aplicacoes = db.relationship('AplicacaoQuestionario', backref='questionario', lazy='dynamic')
    usuarios_autorizados = db.relationship('UsuarioAutorizado', backref='questionario', lazy='dynamic', cascade='all, delete-orphan')

class Topico(db.Model):
    """Tópicos dos questionários"""
    __tablename__ = "topico"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    ordem = db.Column(db.Integer, default=1)
    ativo = db.Column(db.Boolean, default=True)
    
    # Chaves estrangeiras
    questionario_id = db.Column(db.Integer, db.ForeignKey('questionario.id'), nullable=False)
    
    # Vínculo com CategoriaIndicador
    categoria_indicador_id = db.Column(db.Integer, db.ForeignKey('categoria_indicador.id'), nullable=True)

    # Relacionamentos
    perguntas = db.relationship('Pergunta', backref='topico', lazy='dynamic', cascade='all, delete-orphan')

class Pergunta(db.Model):
    """Perguntas dentro dos tópicos"""
    __tablename__ = "pergunta"
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    tipo = db.Column(SqlEnum(TipoResposta), nullable=False)
    obrigatoria = db.Column(db.Boolean, default=False)
    permite_observacao = db.Column(db.Boolean, default=True)
    peso = db.Column(db.Integer, default=1)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, default=True)
    
    # --- CAMPO LEGADO ---
    exige_foto_se_nao_conforme = db.Column(db.Boolean, default=False, nullable=False) 
    
    # --- NOVO CAMPO (FLEXIBILIDADE DE FOTO) ---
    # Usamos db.String em vez de SqlEnum para facilitar migração em ambientes híbridos (Postgres/SQLite)
    criterio_foto = db.Column(db.String(20), default='nenhuma', server_default='nenhuma')
    # ------------------------------------------
    
    # Configurações específicas por tipo
    configuracoes = db.Column(db.Text)  # JSON para configurações específicas
    
    # Chaves estrangeiras
    topico_id = db.Column(db.Integer, db.ForeignKey('topico.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    opcoes = db.relationship('OpcaoPergunta', backref='pergunta', lazy='select', cascade='all, delete-orphan')
    respostas = db.relationship('RespostaPergunta', backref='pergunta', lazy='dynamic')

class OpcaoPergunta(db.Model):
    """Opções de resposta para perguntas de múltipla escolha"""
    __tablename__ = "opcao_pergunta"
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, default=0)  # Pontuação da opção
    ordem = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, default=True)
    
    # Chaves estrangeiras
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)

# ==================== APLICAÇÕES E RESPOSTAS ====================

class AplicacaoQuestionario(db.Model):
    """Aplicações de questionários (instâncias respondidas)"""
    __tablename__ = "aplicacao_questionario"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados da aplicação
    data_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime)
    status = db.Column(SqlEnum(StatusAplicacao), default=StatusAplicacao.EM_ANDAMENTO)
    
    # Notas e pontuação
    nota_final = db.Column(db.Float)
    pontos_obtidos = db.Column(db.Float)
    pontos_totais = db.Column(db.Float)
    
    # Observações e comentários
    observacoes = db.Column(db.Text)  # Observações iniciais
    observacoes_finais = db.Column(db.Text)  # Observações ao finalizar
    
    # Dados de localização (se capturado)
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    endereco_capturado = db.Column(db.String(255))
    
    # Chaves estrangeiras
    questionario_id = db.Column(db.Integer, db.ForeignKey('questionario.id'), nullable=False)
    avaliado_id = db.Column(db.Integer, db.ForeignKey('avaliado.id'), nullable=False)
    aplicador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamentos
    respostas = db.relationship('RespostaPergunta', backref='aplicacao', lazy='dynamic', cascade='all, delete-orphan')

class RespostaPergunta(db.Model):
    """Respostas dadas às perguntas durante uma aplicação"""
    __tablename__ = "resposta_pergunta"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados da resposta
    resposta = db.Column(db.Text)
    observacao = db.Column(db.Text)
    pontos = db.Column(db.Float)

    # MANTENHA ESTE CAMPO (para compatibilidade com dados antigos)
    caminho_foto = db.Column(db.String(255), nullable=True)
    
    # Metadados
    data_resposta = db.Column(db.DateTime, default=datetime.utcnow)
    tempo_resposta = db.Column(db.Integer)
    
    # Para não conformidades
    nao_conforme = db.Column(db.Boolean, default=False)
    plano_acao = db.Column(db.Text)
    prazo_plano_acao = db.Column(db.Date)
    responsavel_plano_acao = db.Column(db.String(100))
    
    # Chaves estrangeiras
    aplicacao_id = db.Column(db.Integer, db.ForeignKey('aplicacao_questionario.id'), nullable=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)

    # === NOVO: RELACIONAMENTO PARA MÚLTIPLAS FOTOS ===
    # Isso cria a "lista" de fotos dentro da resposta
    fotos = db.relationship('FotoResposta', backref='resposta_pai', lazy='dynamic', cascade='all, delete-orphan')


# === NOVA CLASSE (Adicione logo abaixo da classe acima) ===
class FotoResposta(db.Model):
    """Tabela para armazenar múltiplas fotos de uma resposta"""
    __tablename__ = 'foto_resposta'
    
    id = db.Column(db.Integer, primary_key=True)
    caminho = db.Column(db.String(255), nullable=False) # Nome do arquivo
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Chave estrangeira que liga esta foto à resposta mãe
    resposta_id = db.Column(db.Integer, db.ForeignKey('resposta_pergunta.id'), nullable=False)

# ==================== USUÁRIOS AUTORIZADOS ====================

class UsuarioAutorizado(db.Model):
    """Usuários autorizados a usar um questionário específico"""
    __tablename__ = "usuario_autorizado"
    
    id = db.Column(db.Integer, primary_key=True)
    questionario_id = db.Column(db.Integer, db.ForeignKey('questionario.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    usuario = db.relationship('Usuario', backref='questionarios_autorizados')

# ==================== NOTIFICAÇÕES ====================

class Notificacao(db.Model):
    """Sistema de notificações"""
    __tablename__ = "notificacao"
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='info')  # info, success, warning, danger
    link = db.Column(db.String(255))  # Link relacionado à notificação
    
    # Status
    visualizada = db.Column(db.Boolean, default=False)
    data_visualizacao = db.Column(db.DateTime)
    
    # Chaves estrangeiras
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== LOGS E AUDITORIA ====================

class LogAuditoria(db.Model):
    """Log de auditoria das ações do sistema"""
    __tablename__ = "log_auditoria"
    
    id = db.Column(db.Integer, primary_key=True)
    acao = db.Column(db.String(200), nullable=False)
    detalhes = db.Column(db.Text)
    
    # Informações da entidade afetada
    entidade_tipo = db.Column(db.String(50))  # Tipo da entidade (Questionario, Usuario, etc.)
    entidade_id = db.Column(db.Integer)  # ID da entidade
    
    # Informações da requisição
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    # Chaves estrangeiras
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Timestamp
    data_acao = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== CONFIGURAÇÕES ====================

class ConfiguracaoCliente(db.Model):
    """Configurações específicas do cliente"""
    __tablename__ = "configuracao_cliente"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Configurações visuais
    logo_url = db.Column(db.String(255))
    cor_primaria = db.Column(db.String(7), default='#007bff')  # Hex color
    cor_secundaria = db.Column(db.String(7), default='#6c757d')  # Hex color
    
    # Configurações funcionais
    mostrar_notas = db.Column(db.Boolean, default=True)
    permitir_fotos = db.Column(db.Boolean, default=True)
    obrigar_plano_acao = db.Column(db.Boolean, default=False)
    
    # Configurações de notificação
    notificar_aplicacoes_finalizadas = db.Column(db.Boolean, default=True)
    notificar_nao_conformidades = db.Column(db.Boolean, default=True)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    cliente_rel = db.relationship('Cliente', backref='configuracao')

# ==================== INTEGRAÇÕES ====================

class Integracao(db.Model):
    """Integrações disponíveis no sistema"""
    __tablename__ = "integracao"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # webhook, api, email
    configuracao = db.Column(db.Text)  # JSON com configurações específicas
    ativa = db.Column(db.Boolean, default=True)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class CategoriaIndicador(db.Model):
    """
    As 'Gavetas' do Relatório.
    Ex: Infraestrutura, Higiene Pessoal, Controle de Pragas.
    """
    __tablename__ = "categoria_indicador"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)  # Nome que aparece no título do gráfico
    ordem = db.Column(db.Integer, default=0)          # Ordem que aparece no painel
    cor = db.Column(db.String(7), default='#4e73df')  # Cor da barra no gráfico
    ativo = db.Column(db.Boolean, default=True)
    
    # Vínculo com Cliente (para cada cliente poder ter seus próprios indicadores)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Relacionamento inverso
    topicos = db.relationship('Topico', backref='indicador', lazy='dynamic')

# ==================== FUNÇÕES AUXILIARES ====================

def init_db():
    """Inicializa o banco de dados"""
    db.create_all()

def criar_admin_padrao():
    """Cria usuário admin padrão se não existir"""
    admin = Usuario.query.filter_by(email='admin@admin.com').first()
    if not admin:
        # Criar cliente padrão
        cliente = Cliente(
            nome='Empresa Padrão',
            razao_social='Empresa Padrão Ltda',
            email='contato@empresa.com'
        )
        db.session.add(cliente)
        db.session.flush()
        
        # Criar admin
        from werkzeug.security import generate_password_hash
        admin = Usuario(
            nome='Administrador',
            email='admin@admin.com',
            senha_hash=generate_password_hash('admin123'),
            tipo=TipoUsuario.ADMIN,
            cliente_id=cliente.id,
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        return True
    return False
