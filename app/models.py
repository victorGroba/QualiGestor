# app/models.py
from datetime import datetime
from sqlalchemy import Enum as SqlEnum
import enum
from flask_login import UserMixin
from . import db
from . import login_manager

# ==================== ENUMS ====================

class TipoResposta(enum.Enum):
    """Tipos de resposta disponíveis para perguntas"""
    SIM_NAO_NA = "Sim/Não/N.A."
    SIM_NAO = "Sim/Não"
    TEXTO = "Texto"
    TEXTO_LONGO = "Texto Longo"
    NUMERO = "Número"
    NOTA = "Nota (0-10)"
    PERCENTUAL = "Percentual (0-100)"
    MULTIPLA_ESCOLHA = "Múltipla Escolha"
    UNICA_ESCOLHA = "Única Escolha"
    IMAGEM = "Imagem"
    DATA = "Data"
    HORA = "Hora"
    DATA_HORA = "Data e Hora"

class StatusAuditoria(enum.Enum):
    """Status possíveis de uma auditoria"""
    RASCUNHO = "Rascunho"
    EM_ANDAMENTO = "Em Andamento"
    CONCLUIDA = "Concluída"
    CANCELADA = "Cancelada"
    APROVADA = "Aprovada"

class TipoUsuario(enum.Enum):
    """Tipos de usuário do sistema"""
    SUPER_ADMIN = "Super Admin"
    ADMIN_CLIENTE = "Admin Cliente"
    AUDITOR = "Auditor"
    GESTOR_LOJA = "Gestor Loja"
    VISUALIZADOR = "Visualizador"

class TipoNaoConformidade(enum.Enum):
    """Classificação das não conformidades"""
    CRITICA = "Crítica"
    MAIOR = "Maior"
    MENOR = "Menor"
    OBSERVACAO = "Observação"

# ==================== TABELAS DE CONFIGURAÇÃO ====================

class PlanoSaaS(db.Model):
    """Planos de assinatura para clientes"""
    __tablename__ = "plano_saas"
    
    id = db.Column(db.Integer, primary_key=True)
    nome_plano = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    preco_mensal = db.Column(db.Numeric(10, 2))
    limite_usuarios = db.Column(db.Integer)
    limite_lojas = db.Column(db.Integer)
    limite_formularios = db.Column(db.Integer)
    limite_auditorias_mes = db.Column(db.Integer)
    funcionalidades = db.Column(db.JSON)  # Lista de funcionalidades em JSON
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    clientes = db.relationship('Cliente', backref='plano', lazy='dynamic')

# ==================== ESTRUTURA ORGANIZACIONAL ====================

class Cliente(db.Model):
    """Empresa cliente do sistema"""
    __tablename__ = "cliente"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    nome_fantasia = db.Column(db.String(100))
    cnpj = db.Column(db.String(18), unique=True)
    inscricao_estadual = db.Column(db.String(20))
    
    # Endereço
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    
    # Contato
    telefone = db.Column(db.String(20))
    email_contato = db.Column(db.String(120))
    website = db.Column(db.String(255))
    
    # Configurações
    logo_url = db.Column(db.String(255))
    cor_primaria = db.Column(db.String(7))  # Cor HEX
    cor_secundaria = db.Column(db.String(7))
    
    # Status e Plano
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_expiracao = db.Column(db.DateTime)
    plano_saas_id = db.Column(db.Integer, db.ForeignKey('plano_saas.id'))
    
    # Relacionamentos
    lojas = db.relationship('Loja', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')
    usuarios = db.relationship('Usuario', backref='cliente', lazy='dynamic')
    formularios = db.relationship('Formulario', backref='cliente', lazy='dynamic')
    grupos = db.relationship('Grupo', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')

class Loja(db.Model):
    """Unidades/Lojas do cliente"""
    __tablename__ = "loja"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)  # Código interno da loja
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))  # Loja, Filial, Centro de Distribuição, etc.
    
    # Endereço
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Contato
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    gerente_nome = db.Column(db.String(100))
    gerente_telefone = db.Column(db.String(20))
    gerente_email = db.Column(db.String(120))
    
    # Configurações
    ativa = db.Column(db.Boolean, default=True)
    horario_funcionamento = db.Column(db.String(255))
    observacoes = db.Column(db.Text)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'))
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    grupo = db.relationship('Grupo', backref='lojas')
    auditorias = db.relationship('Auditoria', backref='loja', lazy='dynamic')
    usuarios_responsaveis = db.relationship('Usuario', secondary='loja_usuario', backref='lojas_responsaveis')

# Tabela associativa para múltiplos responsáveis por loja
loja_usuario = db.Table('loja_usuario',
    db.Column('loja_id', db.Integer, db.ForeignKey('loja.id'), primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
)

class Grupo(db.Model):
    """Grupos de lojas para organização"""
    __tablename__ = "grupo"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== USUÁRIOS E AUTENTICAÇÃO ====================

class Usuario(db.Model, UserMixin):
    """Usuários do sistema"""
    __tablename__ = "usuario"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados pessoais
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), unique=True)
    telefone = db.Column(db.String(20))
    foto_url = db.Column(db.String(255))
    
    # Tipo e permissões
    tipo = db.Column(SqlEnum(TipoUsuario), nullable=False, default=TipoUsuario.VISUALIZADOR)
    permissoes = db.Column(db.JSON)  # Permissões específicas em JSON
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    primeiro_acesso = db.Column(db.Boolean, default=True)
    ultimo_acesso = db.Column(db.DateTime)
    token_reset_senha = db.Column(db.String(100))
    token_expiracao = db.Column(db.DateTime)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos

    # Auditor (quem executa/aplica a auditoria) -> Auditoria.usuario_id
    auditorias_realizadas = db.relationship(
        'Auditoria',
        foreign_keys='Auditoria.usuario_id',
        back_populates='auditor',
        lazy='dynamic'
    )

    # Aprovador (quem aprova a auditoria) -> Auditoria.aprovador_id
    auditorias_aprovadas = db.relationship(
        'Auditoria',
        foreign_keys='Auditoria.aprovador_id',
        back_populates='aprovador_user',
        lazy='dynamic'
    )

    # Formulários criados por este usuário
    formularios_criados = db.relationship(
        'Formulario',
        back_populates='criador',
        lazy='dynamic',
        foreign_keys='Formulario.criado_por_id'
    )


    # Planos de ação sob responsabilidade deste usuário
    planos_acao = db.relationship(
        'PlanoAcao',
        foreign_keys='PlanoAcao.responsavel_id',
        back_populates='responsavel',
        lazy='dynamic'
    )

    # Planos que este usuário verificou
    planos_verificados = db.relationship(
        'PlanoAcao',
        foreign_keys='PlanoAcao.verificado_por_id',
        back_populates='verificado_por',
        lazy='dynamic'
    )



# ==================== FORMULÁRIOS E QUESTIONÁRIOS ====================

class Formulario(db.Model):
    """Templates de formulários/checklists"""
    __tablename__ = "formulario"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    versao = db.Column(db.String(10), default='1.0')
    
    # Configurações de pontuação
    pontuacao_ativa = db.Column(db.Boolean, default=True)
    pontuacao_maxima = db.Column(db.Float, default=100)
    peso_total = db.Column(db.Float, default=100)
    formula_calculo = db.Column(db.String(50), default='PERCENTUAL')  # PERCENTUAL, SOMA, MEDIA
    
    # Configurações de exibição
    exibir_pontuacao = db.Column(db.Boolean, default=True)
    exibir_observacoes = db.Column(db.Boolean, default=True)
    obrigar_foto = db.Column(db.Boolean, default=False)
    obrigar_plano_acao = db.Column(db.Boolean, default=False)
    permitir_na = db.Column(db.Boolean, default=True)  # Permitir "Não Aplicável"
    
    # Configurações de relatório
    gerar_relatorio_pdf = db.Column(db.Boolean, default=True)
    enviar_email_conclusao = db.Column(db.Boolean, default=False)
    emails_destinatarios = db.Column(db.JSON)  # Lista de emails em JSON
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    publicado = db.Column(db.Boolean, default=False)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))  # ← já existia
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_formulario.id'))
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    publicado_em = db.Column(db.DateTime)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    # Pareia com Usuario.formularios_criados (FK explícita para evitar ambiguidade)
    criador = db.relationship(
        'Usuario',
        back_populates='formularios_criados',
        foreign_keys=[criado_por_id]
    )

    blocos = db.relationship(
        'BlocoFormulario',
        backref='formulario',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='BlocoFormulario.ordem'
    )
    auditorias = db.relationship('Auditoria', backref='formulario', lazy='dynamic')
    categoria = db.relationship('CategoriaFormulario', backref='formularios')


class CategoriaFormulario(db.Model):
    """Categorias para organização de formulários"""
    __tablename__ = "categoria_formulario"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    icone = db.Column(db.String(50))
    cor = db.Column(db.String(7))
    ordem = db.Column(db.Integer, default=0)
    ativa = db.Column(db.Boolean, default=True)

class BlocoFormulario(db.Model):
    """Blocos/Seções dentro de um formulário"""
    __tablename__ = "bloco_formulario"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    ordem = db.Column(db.Integer, nullable=False)
    peso = db.Column(db.Float, default=1)  # Peso do bloco na pontuação total
    
    # Configurações
    expansivel = db.Column(db.Boolean, default=True)
    obrigatorio = db.Column(db.Boolean, default=True)
    
    # Chave estrangeira
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)
    
    # Relacionamentos
    perguntas = db.relationship('Pergunta', backref='bloco', lazy='dynamic', 
                               cascade='all, delete-orphan', order_by='Pergunta.ordem')

class Pergunta(db.Model):
    """Perguntas dentro dos blocos"""
    __tablename__ = "pergunta"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20))  # Código da pergunta (ex: BL01-P01)
    texto = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.Text)  # Texto auxiliar/dica
    
    # Tipo e configurações
    tipo_resposta = db.Column(SqlEnum(TipoResposta), nullable=False)
    obrigatoria = db.Column(db.Boolean, default=True)
    permite_observacao = db.Column(db.Boolean, default=True)
    permite_foto = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer, nullable=False)
    
    # Pontuação e limites
    peso = db.Column(db.Float, default=1)
    pontuacao_maxima = db.Column(db.Float, default=10)
    valor_esperado = db.Column(db.String(255))  # Resposta esperada
    limite_minimo = db.Column(db.Float)  # Para tipos numéricos
    limite_maximo = db.Column(db.Float)
    
    # Criticidade
    critica = db.Column(db.Boolean, default=False)  # Pergunta crítica
    gera_nc_automatica = db.Column(db.Boolean, default=False)  # Gera NC se resposta negativa
    
    # Condicionais
    condicional = db.Column(db.Boolean, default=False)
    condicao_pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'))
    condicao_resposta = db.Column(db.String(255))  # Valor que ativa esta pergunta
    
    # Chave estrangeira
    bloco_id = db.Column(db.Integer, db.ForeignKey('bloco_formulario.id'), nullable=False)
    
    # Relacionamentos
    opcoes = db.relationship('OpcaoPergunta', backref='pergunta', lazy='dynamic', 
                           cascade='all, delete-orphan', order_by='OpcaoPergunta.ordem')
    respostas = db.relationship('Resposta', backref='pergunta', lazy='dynamic')
    perguntas_dependentes = db.relationship('Pergunta', 
                                          backref=db.backref('pergunta_condicional', remote_side=[id]))

class OpcaoPergunta(db.Model):
    """Opções para perguntas de múltipla escolha"""
    __tablename__ = "opcao_pergunta"
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.String(100))  # Valor interno
    pontuacao = db.Column(db.Float, default=0)  # Pontos desta opção
    ordem = db.Column(db.Integer, default=0)
    cor = db.Column(db.String(7))  # Cor de destaque
    gera_nc = db.Column(db.Boolean, default=False)  # Se esta opção gera não conformidade
    
    # Chave estrangeira
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)

# ==================== AUDITORIAS E RESPOSTAS ====================

class Auditoria(db.Model):
    """Aplicação de um formulário (auditoria realizada)"""
    __tablename__ = "auditoria"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True)  # AUD-2024-00001
    
    # Status e datas
    status = db.Column(SqlEnum(StatusAuditoria), nullable=False, default=StatusAuditoria.RASCUNHO)
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime)
    data_programada = db.Column(db.DateTime)
    prazo_conclusao = db.Column(db.DateTime)
    
    # Pontuação
    pontuacao_obtida = db.Column(db.Float)
    pontuacao_maxima = db.Column(db.Float)
    percentual = db.Column(db.Float)
    
    # Observações e evidências
    observacoes_gerais = db.Column(db.Text)
    assinatura_digital = db.Column(db.Text)  # Base64 da assinatura
    localizacao_gps = db.Column(db.String(100))
    
    # Chaves estrangeiras
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)
    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=False)

    # Quem executou a auditoria
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    # Quem aprovou a auditoria
    aprovador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos

    respostas = db.relationship(
        'Resposta',
        backref='auditoria',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    anexos = db.relationship(
        'AnexoAuditoria',
        backref='auditoria',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    nao_conformidades = db.relationship(
        'NaoConformidade',
        backref='auditoria',
        lazy='dynamic'
    )

    # Relacionamento com o usuário que aplicou (auditor)
    auditor = db.relationship(
        'Usuario',
        foreign_keys=[usuario_id],
        back_populates='auditorias_realizadas'
    )

    # Relacionamento com o usuário que aprovou
    aprovador_user = db.relationship(
        'Usuario',
        foreign_keys=[aprovador_id],
        back_populates='auditorias_aprovadas'
    )

class Resposta(db.Model):
    """Respostas individuais de cada pergunta"""
    __tablename__ = "resposta"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Valores de resposta (usar apenas o apropriado)
    valor_texto = db.Column(db.Text)
    valor_numero = db.Column(db.Float)
    valor_boolean = db.Column(db.Boolean)
    valor_data = db.Column(db.DateTime)
    valor_opcao_ids = db.Column(db.JSON)  # IDs das opções selecionadas
    nao_aplicavel = db.Column(db.Boolean, default=False)
    
    # Pontuação
    pontuacao_obtida = db.Column(db.Float)
    pontuacao_maxima = db.Column(db.Float)
    
    # Observações e evidências
    observacao = db.Column(db.Text)
    foto_evidencia = db.Column(db.String(255))  # Path da foto
    
    # Timestamps
    respondido_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Chaves estrangeiras
    auditoria_id = db.Column(db.Integer, db.ForeignKey('auditoria.id'), nullable=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)

class AnexoAuditoria(db.Model):
    """Arquivos anexados à auditoria"""
    __tablename__ = "anexo_auditoria"
    
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho = db.Column(db.String(500), nullable=False)
    tipo = db.Column(db.String(50))  # imagem, documento, video
    tamanho = db.Column(db.Integer)  # Em bytes
    descricao = db.Column(db.Text)
    
    # Chaves estrangeiras
    auditoria_id = db.Column(db.Integer, db.ForeignKey('auditoria.id'), nullable=False)
    resposta_id = db.Column(db.Integer, db.ForeignKey('resposta.id'))
    
    # Timestamps
    enviado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    resposta = db.relationship('Resposta', backref='anexos')

# ==================== NÃO CONFORMIDADES E PLANOS DE AÇÃO ====================

class NaoConformidade(db.Model):
    """Registro de não conformidades identificadas"""
    __tablename__ = "nao_conformidade"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True)  # NC-2024-00001
    
    # Classificação
    tipo = db.Column(SqlEnum(TipoNaoConformidade), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='Aberta')  # Aberta, Em Tratamento, Resolvida, Cancelada
    prioridade = db.Column(db.String(20), default='Media')  # Baixa, Media, Alta, Critica
    
    # Datas
    data_identificacao = db.Column(db.DateTime, default=datetime.utcnow)
    prazo_resolucao = db.Column(db.DateTime)
    data_resolucao = db.Column(db.DateTime)
    
    # Análise
    causa_raiz = db.Column(db.Text)
    impacto = db.Column(db.Text)
    recorrente = db.Column(db.Boolean, default=False)
    
    # Chaves estrangeiras
    auditoria_id = db.Column(db.Integer, db.ForeignKey('auditoria.id'), nullable=False)
    resposta_id = db.Column(db.Integer, db.ForeignKey('resposta.id'))
    identificado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    
    # Relacionamentos
    resposta = db.relationship('Resposta', backref='nao_conformidades')
    identificado_por = db.relationship('Usuario', backref='ncs_identificadas')
    planos_acao = db.relationship('PlanoAcao', backref='nao_conformidade', lazy='dynamic')

class PlanoAcao(db.Model):
    """Planos de ação para resolver não conformidades"""
    __tablename__ = "plano_acao"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True)  # PA-2024-00001
    
    # Descrição
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    acao_corretiva = db.Column(db.Text)
    acao_preventiva = db.Column(db.Text)
    
    # Status e datas
    status = db.Column(db.String(50), default='Pendente')  # Pendente, Em Execução, Concluído, Cancelado
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    prazo_execucao = db.Column(db.DateTime, nullable=False)
    data_conclusao = db.Column(db.DateTime)
    
    # Verificação
    eficaz = db.Column(db.Boolean)
    observacoes_verificacao = db.Column(db.Text)
    data_verificacao = db.Column(db.DateTime)
    
    # Chaves estrangeiras
    nao_conformidade_id = db.Column(db.Integer, db.ForeignKey('nao_conformidade.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    verificado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    
    # Relacionamentos (FKs explícitas + pareamentos)
    # -> pareia com Usuario.planos_acao
    responsavel = db.relationship(
        'Usuario',
        foreign_keys=[responsavel_id],
        back_populates='planos_acao'
    )

    # -> pareia com Usuario.planos_verificados
    verificado_por = db.relationship(
        'Usuario',
        foreign_keys=[verificado_por_id],
        back_populates='planos_verificados'
    )

    # Demais relacionamentos
    historico = db.relationship(
        'HistoricoPlanoAcao',
        backref='plano_acao',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )


class HistoricoPlanoAcao(db.Model):
    """Histórico de alterações no plano de ação"""
    __tablename__ = "historico_plano_acao"
    
    id = db.Column(db.Integer, primary_key=True)
    acao = db.Column(db.String(100), nullable=False)  # Criado, Atualizado, Status Alterado, etc
    descricao = db.Column(db.Text)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Chaves estrangeiras
    plano_acao_id = db.Column(db.Integer, db.ForeignKey('plano_acao.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='historicos_plano_acao')

# ==================== AUDITORIA DO SISTEMA ====================

class LogAuditoria(db.Model):
    """Log de todas as ações do sistema para auditoria"""
    __tablename__ = "log_auditoria"
    
    id = db.Column(db.Integer, primary_key=True)
    tabela = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer)
    acao = db.Column(db.String(20), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    dados_anteriores = db.Column(db.JSON)
    dados_novos = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    # Timestamps
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Chave estrangeira
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='logs_auditoria')

# ==================== FUNÇÕES AUXILIARES ====================

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))