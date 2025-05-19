
from datetime import datetime
from sqlalchemy import Enum as SqlEnum
import enum
from flask_login import UserMixin
from app import db
from app import login_manager








  
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
    bloco_id = db.Column(db.Integer, db.ForeignKey('bloco_formulario.id'), nullable=True)
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
    respostas = db.relationship('Resposta', backref='auditoria', lazy=True)

class Resposta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)
    auditoria_id = db.Column(db.Integer, db.ForeignKey('auditoria.id'), nullable=False)
    valor = db.Column(db.Text, nullable=False)
    data_resposta = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------- LAUDO MICROBIOLÓGICO -------------------
class LaudoMicrobiologico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_coleta = db.Column(db.Date, nullable=False)
    tipo_amostra = db.Column(db.String(100), nullable=False)
    local = db.Column(db.String(100), nullable=False)
    resultado = db.Column(db.String(50), nullable=False)
    observacoes = db.Column(db.Text)
    responsavel = db.Column(db.String(100), nullable=False)
    arquivo = db.Column(db.String(200))

# ------------------- BLOCOS DE FORMULÁRIO -------------------
class BlocoFormulario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    ordem = db.Column(db.Integer, nullable=False)
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)
    perguntas = db.relationship('Pergunta', backref='bloco', cascade="all, delete-orphan")

# ------------------- LOGIN MANAGER -------------------
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
