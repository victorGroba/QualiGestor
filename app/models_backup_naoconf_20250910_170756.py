# app/models.py - VERSÃO CORRIGIDA FINAL
from datetime import datetime
from sqlalchemy import Enum as SqlEnum
import enum
from flask_login import UserMixin
from . import db

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
    """Tipos de usuário do sistema - CORRIGIDO"""
    SUPER_ADMIN = "Super Admin"
    ADMIN = "Admin"
    AUDITOR = "Auditor"
    GESTOR = "Gestor"
    VISUALIZADOR = "Visualizador"

class TipoNaoConformidade(enum.Enum):
    """Classificação das não conformidades"""
    CRITICA = "Crítica"
    MAIOR = "Maior"
    MENOR = "Menor"
    OBSERVACAO = "Observação"

# ==================== ESTRUTURA ORGANIZACIONAL ====================

class Cliente(db.Model):
    """Empresa cliente do sistema"""
    __tablename__ = "cliente"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    nome_fantasia = db.Column(db.String(100))
    cnpj = db.Column(db.String(18), unique=True)
    
    # Endereço
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    
    # Contato
    telefone = db.Column(db.String(20))
    email_contato = db.Column(db.String(120))
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    lojas = db.relationship('Loja', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')
    usuarios = db.relationship('Usuario', backref='cliente', lazy='dynamic')
    formularios = db.relationship('Formulario', backref='cliente', lazy='dynamic')
    grupos = db.relationship('Grupo', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')

class Loja(db.Model):
    """Unidades/Lojas do cliente (substitui Avaliado)"""
    __tablename__ = "loja"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20))
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), default='Loja')
    
    # Endereço
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    
    # Contato
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    gerente_nome = db.Column(db.String(100))
    
    # Status
    ativa = db.Column(db.Boolean, default=True)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'))
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    auditorias = db.relationship('Auditoria', backref='loja', lazy='dynamic')

class Grupo(db.Model):
    """Grupos de lojas para organização"""
    __tablename__ = "grupo"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    lojas = db.relationship('Loja', backref='grupo', lazy='dynamic')

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
    
    # Tipo e permissões
    tipo = db.Column(SqlEnum(TipoUsuario), nullable=False, default=TipoUsuario.VISUALIZADOR)
    
    # Compatibilidade com código antigo
    @property
    def perfil(self):
        """Propriedade para compatibilidade com código antigo"""
        if self.tipo in [TipoUsuario.SUPER_ADMIN, TipoUsuario.ADMIN]:
            return 'admin'
        return 'usuario'
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    primeiro_acesso = db.Column(db.Boolean, default=True)
    ultimo_acesso = db.Column(db.DateTime)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    auditorias_realizadas = db.relationship('Auditoria', backref='usuario', lazy='dynamic')
    formularios_criados = db.relationship('Formulario', backref='criador', lazy='dynamic', foreign_keys='Formulario.criado_por_id')

# ==================== FORMULÁRIOS E QUESTIONÁRIOS ====================

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
    
    # Configurações de exibição
    exibir_pontuacao = db.Column(db.Boolean, default=True)
    exibir_observacoes = db.Column(db.Boolean, default=True)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    publicado = db.Column(db.Boolean, default=False)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_formulario.id'))
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    publicado_em = db.Column(db.DateTime)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    blocos = db.relationship('BlocoFormulario', backref='formulario', lazy='dynamic', cascade='all, delete-orphan', order_by='BlocoFormulario.ordem')
    auditorias = db.relationship('Auditoria', backref='formulario', lazy='dynamic')
    categoria = db.relationship('CategoriaFormulario', backref='formularios')
    
    # Propriedade para compatibilidade
    @property
    def perguntas(self):
        """Retorna todas as perguntas de todos os blocos"""
        perguntas = []
        for bloco in self.blocos.order_by(BlocoFormulario.ordem):
            perguntas.extend(bloco.perguntas.order_by(Pergunta.ordem).all())
        return perguntas

class BlocoFormulario(db.Model):
    """Blocos/Seções dentro de um formulário"""
    __tablename__ = "bloco_formulario"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    ordem = db.Column(db.Integer, nullable=False)
    peso = db.Column(db.Float, default=1)
    
    # Chave estrangeira
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)
    
    # Relacionamentos
    perguntas = db.relationship('Pergunta', backref='bloco', lazy='dynamic', cascade='all, delete-orphan', order_by='Pergunta.ordem')

class Pergunta(db.Model):
    """Perguntas dentro dos blocos"""
    __tablename__ = "pergunta"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20))
    texto = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.Text)
    
    # Tipo e configurações
    tipo_resposta = db.Column(SqlEnum(TipoResposta), nullable=False)
    obrigatoria = db.Column(db.Boolean, default=True)
    permite_observacao = db.Column(db.Boolean, default=True)
    permite_foto = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer, nullable=False)
    
    # Pontuação e limites
    peso = db.Column(db.Float, default=1)
    pontuacao_maxima = db.Column(db.Float, default=10)
    valor_esperado = db.Column(db.String(255))
    limite_minimo = db.Column(db.Float)
    limite_maximo = db.Column(db.Float)
    
    # Criticidade
    critica = db.Column(db.Boolean, default=False)
    gera_nc_automatica = db.Column(db.Boolean, default=False)
    
    # Chave estrangeira
    bloco_id = db.Column(db.Integer, db.ForeignKey('bloco_formulario.id'), nullable=False)
    
    # Relacionamentos
    opcoes = db.relationship('OpcaoPergunta', backref='pergunta', lazy='dynamic', cascade='all, delete-orphan', order_by='OpcaoPergunta.ordem')
    respostas = db.relationship('Resposta', backref='pergunta', lazy='dynamic')

class OpcaoPergunta(db.Model):
    """Opções para perguntas de múltipla escolha"""
    __tablename__ = "opcao_pergunta"
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.String(100))
    pontuacao = db.Column(db.Float, default=0)
    ordem = db.Column(db.Integer, default=0)
    gera_nc = db.Column(db.Boolean, default=False)
    
    # Chave estrangeira
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)

# ==================== AUDITORIAS E RESPOSTAS ====================

class Auditoria(db.Model):
    """Aplicação de um formulário (auditoria realizada)"""
    __tablename__ = "auditoria"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True)
    
    # Status e datas
    status = db.Column(SqlEnum(StatusAuditoria), nullable=False, default=StatusAuditoria.RASCUNHO)
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime)
    
    # Pontuação
    pontuacao_obtida = db.Column(db.Float)
    pontuacao_maxima = db.Column(db.Float)
    percentual = db.Column(db.Float)
    
    # Observações
    observacoes_gerais = db.Column(db.Text)
    
    # Chaves estrangeiras
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)
    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Propriedades para compatibilidade
    @property
    def data(self):
        """Compatibilidade com código antigo"""
        return self.data_inicio
    
    @data.setter
    def data(self, value):
        """Compatibilidade com código antigo"""
        self.data_inicio = value
    
    # Relacionamentos
    respostas = db.relationship('Resposta', backref='auditoria', lazy='dynamic', cascade='all, delete-orphan')

class Resposta(db.Model):
    """Respostas individuais de cada pergunta"""
    __tablename__ = "resposta"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Valores de resposta (usar apenas o apropriado)
    valor_texto = db.Column(db.Text)
    valor_numero = db.Column(db.Float)
    valor_boolean = db.Column(db.Boolean)
    valor_data = db.Column(db.DateTime)
    valor_opcoes_selecionadas = db.Column(db.Text)  # JSON string para compatibilidade
    nao_aplicavel = db.Column(db.Boolean, default=False)
    
    # Pontuação
    pontuacao_obtida = db.Column(db.Float)
    pontuacao_maxima = db.Column(db.Float)
    
    # Observações e evidências
    observacao = db.Column(db.Text)
    foto_evidencia = db.Column(db.String(255))
    
    # Timestamps
    respondido_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Chaves estrangeiras
    auditoria_id = db.Column(db.Integer, db.ForeignKey('auditoria.id'), nullable=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)

# ==================== COMPATIBILIDADE ====================

# Alias para compatibilidade com código antigo
Avaliado = Loja
Questionario = Formulario
Topico = BlocoFormulario

# Para compatibilidade com templates antigos
class LaudoMicrobiologico(db.Model):
    """Modelo para módulo de laudos (compatibilidade)"""
    __tablename__ = "laudo_microbiologico"
    
    id = db.Column(db.Integer, primary_key=True)
    data_coleta = db.Column(db.DateTime, nullable=False)
    tipo_amostra = db.Column(db.String(100), nullable=False)
    local = db.Column(db.String(100), nullable=False)
    resultado = db.Column(db.String(50), nullable=False)
    observacoes = db.Column(db.Text)
    responsavel = db.Column(db.String(100), nullable=False)
    arquivo = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== FUNÇÃO USER LOADER ====================

from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
