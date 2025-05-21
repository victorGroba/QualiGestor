from datetime import datetime
from sqlalchemy import Enum as SqlEnum
import enum
from flask_login import UserMixin
from . import db


from . import login_manager

# ------------------- ENUM TIPO DE RESPOSTA -------------------
class TipoResposta(enum.Enum):
    SIM_NAO = "Sim/Não"
    TEXTO = "Texto"
    NOTA = "Nota"

# ------------------- USUÁRIO -------------------
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # admin, auditor, cliente

    # Campos adicionados para multiempresa
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------- CLIENTE E LOJA -------------------
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    lojas = db.relationship('Loja', backref='cliente', lazy=True)

class Loja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)

# ------------------- FORMULÁRIO -------------------
class Formulario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    perguntas = db.relationship('Pergunta', backref='formulario', cascade="all, delete-orphan")

# ------------------- PERGUNTAS E OPÇÕES -------------------
class Pergunta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(255), nullable=False)
    tipo_resposta = db.Column(SqlEnum(TipoResposta), nullable=False)
    obrigatoria = db.Column(db.Boolean, default=True)
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)
    """ bloco_id = db.Column(db.Integer, db.ForeignKey('bloco_formulario.id'), nullable=True) """
    opcoes = db.relationship('OpcaoPergunta', backref='pergunta', lazy=True)

class OpcaoPergunta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(200), nullable=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)

# ------------------- AUDITORIA E RESPOSTAS -------------------
class Auditoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)

# ------------------- GRUPO DE AVALIADOS -------------------
class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"))

# ------------------- AVALIADO -------------------
class Avaliado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    endereco = db.Column(db.String(255))
    idioma = db.Column(db.String(10), default="pt-br")
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"))
    campos_personalizados = db.relationship("CampoPersonalizadoValor", backref="avaliado", lazy=True)

# ------------------- CAMPOS PERSONALIZADOS CONFIGURÁVEIS -------------------
class CampoPersonalizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # texto, número, data, etc
    obrigatorio = db.Column(db.Boolean, default=False)
    visivel = db.Column(db.Boolean, default=True)
    pre_configurado = db.Column(db.Boolean, default=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)

class CampoPersonalizadoValor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campo_id = db.Column(db.Integer, db.ForeignKey("campo_personalizado.id"), nullable=False)
    avaliado_id = db.Column(db.Integer, db.ForeignKey("avaliado.id"), nullable=False)
    valor = db.Column(db.Text)
