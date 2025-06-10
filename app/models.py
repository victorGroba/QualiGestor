# app/models.py
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
    # NOVOS TIPOS
    MULTIPLA_ESCOLHA = "Múltipla Escolha"
    UNICA_ESCOLHA = "Única Escolha"
    IMAGEM = "Imagem"
    DATA = "Data"
    HORA = "Hora"

# ------------------- USUÁRIO -------------------
class Usuario(db.Model, UserMixin):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

    perfil = db.Column(db.String(50), nullable=False, default='usuario')  # 'admin' ou 'usuario'

    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref='usuarios')

    avaliado_id = db.Column(db.Integer, db.ForeignKey('avaliado.id'), nullable=True)
    avaliado = db.relationship('Avaliado', backref='usuarios')

    def __repr__(self):
        return f"<Usuario {self.email} ({self.perfil})>"


    
# NOVO: Tabela para Planos SaaS (DEFINIDA ANTES DE CLIENTE)
class PlanoSaaS(db.Model):
    __tablename__ = "plano_saas"  # <- Adicione esta linha!
    
    id = db.Column(db.Integer, primary_key=True)
    nome_plano = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    preco_mensal = db.Column(db.Numeric(10, 2))
    limite_usuarios = db.Column(db.Integer)
    limite_formularios = db.Column(db.Integer)
    limite_auditorias = db.Column(db.Integer)
    funcionalidades_disponiveis = db.Column(db.Text)


# ------------------- CLIENTE E LOJA -------------------
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=True) # Exemplo de adição
    endereco = db.Column(db.String(255), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email_contato = db.Column(db.String(120), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    data_ativacao = db.Column(db.DateTime, default=datetime.utcnow)

    
    formularios = db.relationship('Formulario', backref='cliente_rel', lazy=True) # Renomeado para evitar conflito
    plano_saas_id = db.Column(db.Integer, db.ForeignKey('plano_saas.id'), nullable=True) # Novo campo
    plano_saas = db.relationship('PlanoSaaS', backref='clientes') # Nova relação



# ------------------- FORMULÁRIO -------------------
class Formulario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)

    avaliado_id = db.Column(db.Integer, db.ForeignKey('avaliado.id'), nullable=True)
    avaliado = db.relationship('Avaliado', backref='formularios', lazy=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    exibir_tabela_relatorio = db.Column(db.Boolean, default=True)
    exibir_limites_aceitaveis = db.Column(db.Boolean, default=False)
    gerar_relatorio_nao_conformidade = db.Column(db.Boolean, default=False)

    pontuacao_ativa = db.Column(db.Boolean, default=False)  # ✅ NOVO: ativa cálculo de nota

    blocos = db.relationship('BlocoFormulario', backref='formulario', cascade="all, delete-orphan", order_by="BlocoFormulario.ordem")
    perguntas = db.relationship('Pergunta', backref='formulario', cascade="all, delete-orphan") 
    criado_por_usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    criado_por_usuario = db.relationship('Usuario', backref='formularios_criados')



# NOVO: Tabela para Blocos de Formulário
class BlocoFormulario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    ordem = db.Column(db.Integer, nullable=False) # Ordem dos blocos no formulário
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)
    perguntas = db.relationship('Pergunta', backref='bloco', cascade="all, delete-orphan", order_by="Pergunta.id") # Perguntas pertencem a blocos

# ------------------- PERGUNTAS E OPÇÕES -------------------
class Pergunta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(255), nullable=False)
    tipo_resposta = db.Column(SqlEnum(TipoResposta), nullable=False) # TipoResposta agora inclui novos tipos
    obrigatoria = db.Column(db.Boolean, default=True)

    # Chave estrangeira para BlocoFormulario (NOVO)
    bloco_id = db.Column(db.Integer, db.ForeignKey('bloco_formulario.id'), nullable=False)

    # Removido ou ajustado: formulario_id direto, pois a Pergunta pertence a um Bloco que pertence a um Formulário
    # Mantido para compatibilidade ou se houver perguntas fora de blocos, mas o ideal é que todas pertençam a um bloco
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False) 

    # NOVOS CAMPOS ADICIONAIS
    observacao_campo = db.Column(db.Boolean, default=False) # Se o campo permite uma observação extra
    peso = db.Column(db.Integer, default=1) # Para pontuação em relatórios
    limite_min = db.Column(db.Float, nullable=True) # Para respostas tipo NOTA
    limite_max = db.Column(db.Float, nullable=True) # Para respostas tipo NOTA

    opcoes = db.relationship('OpcaoPergunta', backref='pergunta', cascade="all, delete-orphan", lazy=True)

class OpcaoPergunta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(200), nullable=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)
    valor = db.Column(db.String(255), nullable=True) # Para um valor específico da opção (ex: "Bom":5, "Ruim":0)

# ------------------- AUDITORIA E RESPOSTAS -------------------
class Auditoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)

    # ALTERADO: agora vincula ao Avaliado
    avaliado_id = db.Column(db.Integer, db.ForeignKey('avaliado.id'), nullable=False)
    avaliado = db.relationship('Avaliado', backref='auditorias', lazy=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario.id'), nullable=False)

    status = db.Column(db.String(50), default='concluida')
    observacoes_gerais = db.Column(db.Text, nullable=True)

    usuario = db.relationship('Usuario', backref='auditorias_realizadas', lazy=True)
    formulario = db.relationship('Formulario', backref='auditorias_aplicadas', lazy=True)
    respostas = db.relationship('Resposta', backref='auditoria', cascade="all, delete-orphan", lazy=True)


# NOVO: Tabela para Respostas
class Resposta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auditoria_id = db.Column(db.Integer, db.ForeignKey('auditoria.id'), nullable=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)
    data_resposta = db.Column(db.DateTime, default=datetime.utcnow)

    # Campos para diferentes tipos de resposta (use apenas um por resposta)
    valor_texto = db.Column(db.Text, nullable=True)
    valor_boolean = db.Column(db.Boolean, nullable=True)
    valor_numero = db.Column(db.Float, nullable=True)
    valor_opcoes_selecionadas = db.Column(db.Text, nullable=True) # Armazena JSON de IDs/textos selecionados
    valor_arquivo = db.Column(db.String(255), nullable=True) # Caminho para o arquivo (para tipo IMAGEM)

    # ✅ NOVO: valor numérico obtido (apenas para checklists com pontuação)
    nota_obtida = db.Column(db.Float, nullable=True)

    # Relações
    pergunta = db.relationship('Pergunta', backref='respostas_recebidas', lazy=True)



# ------------------- GRUPO DE AVALIADOS -------------------
class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"))
    cliente = db.relationship('Cliente', backref='grupos', lazy=True) # Adicionar relação

# ------------------- AVALIADO -------------------
class Avaliado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    endereco = db.Column(db.String(255))
    idioma = db.Column(db.String(10), default="pt-br")
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"))

    # Relações
    cliente = db.relationship('Cliente', backref='avaliados', lazy=True)
    grupo = db.relationship('Grupo', backref='membros_avaliados', lazy=True)
    campos_personalizados = db.relationship("CampoPersonalizadoValor", backref="avaliado", cascade="all, delete-orphan", lazy=True)

# ------------------- CAMPOS PERSONALIZADOS CONFIGURÁVEIS -------------------
class CampoPersonalizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # texto, número, data, lista
    obrigatorio = db.Column(db.Boolean, default=False)
    visivel = db.Column(db.Boolean, default=True)
    pre_configurado = db.Column(db.Boolean, default=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)

    cliente = db.relationship('Cliente', backref='campos_personalizados', lazy=True) # Adicionar relação

class CampoPersonalizadoValor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campo_id = db.Column(db.Integer, db.ForeignKey("campo_personalizado.id"), nullable=False)
    avaliado_id = db.Column(db.Integer, db.ForeignKey("avaliado.id"), nullable=False)
    valor = db.Column(db.Text)

from datetime import datetime

from datetime import datetime

class Questionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    versao = db.Column(db.String(10), nullable=False)
    modo = db.Column(db.String(50), nullable=True)
    documento_referencia = db.Column(db.String(255), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    configuracao_nota_id = db.Column(db.Integer, db.ForeignKey('configuracao_nota.id'))
    configuracao_relatorio_id = db.Column(db.Integer, db.ForeignKey('configuracao_relatorio.id'))
    configuracao_email_id = db.Column(db.Integer, db.ForeignKey('configuracao_email.id'))

    configuracao_nota = db.relationship('ConfiguracaoNota', backref='questionarios', lazy=True)
    configuracao_relatorio = db.relationship('ConfiguracaoRelatorio', backref='questionarios', lazy=True)
    configuracao_email = db.relationship('ConfiguracaoEmail', backref='questionarios', lazy=True)
    restringir_avaliados = db.Column(db.Boolean, default=False)
    reincidencia_ativa = db.Column(db.Boolean, default=False)




class ConfiguracaoNota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    calcular_nota = db.Column(db.Boolean, default=False)
    ocultar_nota = db.Column(db.Boolean, default=False)
    base_calculo = db.Column(db.Integer, default=100)
    casas_decimais = db.Column(db.Integer, default=2)
    modo_configuracao = db.Column(db.String(50), default='Percentual')


class ConfiguracaoRelatorio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exibir_nota_anterior = db.Column(db.Boolean, default=False)
    exibir_tabela_resumo = db.Column(db.Boolean, default=False)
    exibir_limites_aceitaveis = db.Column(db.Boolean, default=False)
    omitir_data_hora = db.Column(db.Boolean, default=False)
    exibir_omitidas = db.Column(db.Boolean, default=False)
    gerar_relatorio_nc = db.Column(db.Boolean, default=False)
    modo_exibicao_nota = db.Column(db.String(50), default='Percentual')
    tipo_agrupamento = db.Column(db.String(50), default='Tópico')
    cor_observacoes = db.Column(db.String(50), default='Cinza')
    cor_relatorio = db.Column(db.String(50), default='Azul CLIQ')
    logotipo_cabecalho = db.Column(db.String(255), nullable=True)
    logotipo_rodape = db.Column(db.String(255), nullable=True)


class ConfiguracaoEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enviar_email = db.Column(db.Boolean, default=False)
    configurar_no_final = db.Column(db.Boolean, default=False)
    exibir_emails_anteriores = db.Column(db.Boolean, default=False)
    idioma = db.Column(db.String(50), default='Português')


class UsuarioAutorizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questionario_id = db.Column(db.Integer, db.ForeignKey('questionario.id'))
    nome = db.Column(db.String(100))
    email = db.Column(db.String(120))


class GrupoQuestionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questionario_id = db.Column(db.Integer, db.ForeignKey('questionario.id'))
    grupo_id = db.Column(db.Integer)


class Topico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    ordem = db.Column(db.Integer, default=0)
    questionario_id = db.Column(db.Integer, db.ForeignKey('questionario.id'), nullable=False)

    questionario = db.relationship('Questionario', backref=db.backref('topicos', lazy=True, order_by="Topico.ordem"))
