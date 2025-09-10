# fix_sistema.py
"""
Script para corrigir rapidamente os erros do sistema
Execute este script para consertar os problemas
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def aplicar_correcoes():
    """Aplica todas as correções necessárias"""
    
    print("🔧 Aplicando correções críticas no sistema...")
    
    # 1. Corrigir app/models.py
    print("📝 Corrigindo models.py...")
    models_content = '''# app/models.py - VERSÃO CORRIGIDA FINAL
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

# ==================== MODELS PARA COMPATIBILIDADE ====================

# Alias para compatibilidade com código antigo
Avaliado = Loja

# ==================== FUNÇÕES AUXILIARES ====================

from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
'''
    
    with open('app/models.py', 'w', encoding='utf-8') as f:
        f.write(models_content)
    
    # 2. Corrigir app/cli/routes.py - adicionar rotas faltando
    print("🛣️  Corrigindo rotas CLI...")
    with open('app/cli/routes.py', 'a', encoding='utf-8') as f:
        f.write('''
# ===================== ROTAS DE COMPATIBILIDADE =====================

@cli_bp.route('/questionarios/novo', methods=['GET', 'POST'])
@login_required
def novo_questionario():
    """Redireciona para criar formulário (compatibilidade)"""
    return redirect(url_for('cli.criar_formulario'))

@cli_bp.route('/questionario/<int:id>/topicos')
@login_required
def gerenciar_topicos(id):
    """Compatibilidade - redireciona para visualizar formulário"""
    return redirect(url_for('cli.visualizar_formulario', formulario_id=id))
''')
    
    # 3. Corrigir app/panorama/routes.py - adicionar rota filtros
    print("📊 Corrigindo rotas Panorama...")
    with open('app/panorama/routes.py', 'a', encoding='utf-8') as f:
        f.write('''
@panorama_bp.route('/filtros')
@login_required
def filtros():
    """Página de filtros (compatibilidade)"""
    return redirect(url_for('panorama.dashboard'))
''')
    
    # 4. Corrigir app/auth/routes.py
    print("🔐 Corrigindo autenticação...")
    auth_content = '''# app/auth/routes.py - VERSÃO CORRIGIDA
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import Usuario, Cliente, TipoUsuario

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# -------- helpers --------
def str_para_tipo_usuario(valor: str) -> TipoUsuario:
    """
    Converte strings legadas de 'perfil' do formulário em TipoUsuario.
    Aceita variações comuns e retorna VISUALIZADOR por padrão.
    """
    if not valor:
        return TipoUsuario.VISUALIZADOR
    v = valor.strip().lower()
    mapa = {
        'super_admin': TipoUsuario.SUPER_ADMIN,
        'superadmin': TipoUsuario.SUPER_ADMIN,
        'root': TipoUsuario.SUPER_ADMIN,
        'admin': TipoUsuario.ADMIN,
        'gestor': TipoUsuario.GESTOR,
        'auditor': TipoUsuario.AUDITOR,
        'usuario': TipoUsuario.VISUALIZADOR,
        'visualizador': TipoUsuario.VISUALIZADOR,
        'viewer': TipoUsuario.VISUALIZADOR,
    }
    return mapa.get(v, TipoUsuario.VISUALIZADOR)

def exige_admin():
    """
    Retorna True se o usuário atual for ADMIN ou SUPER_ADMIN.
    Use para gates simples em rotas.
    """
    if not current_user.is_authenticated:
        return False
    # current_user.tipo é um Enum; compare com os membros existentes
    return current_user.tipo in [TipoUsuario.ADMIN, TipoUsuario.SUPER_ADMIN]

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)

            # Sessão (usar 'tipo' em vez de 'perfil')
            tipo_str = usuario.tipo.name if hasattr(usuario.tipo, "name") else str(usuario.tipo)
            session['tipo'] = tipo_str
            session['nome'] = usuario.nome

            return redirect(url_for('main.painel'))

        flash('E-mail ou senha inválidos.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/cadastrar-usuario', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    # Gate de acesso (ADMIN ou SUPER_ADMIN)
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    clientes = Cliente.query.all()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        perfil_form = request.form.get('perfil')
        usuario.tipo = str_para_tipo_usuario(perfil_form)

        usuario.cliente_id = request.form.get('cliente_id')
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('auth.listar_usuarios'))

    return render_template('auth/editar_usuario.html', usuario=usuario, clientes=clientes)

@auth_bp.route('/usuarios/excluir/<int:usuario_id>')
@login_required
def excluir_usuario(usuario_id):
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuario = Usuario.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('auth.listar_usuarios'))
'''
    
    with open('app/auth/routes.py', 'w', encoding='utf-8') as f:
        f.write(auth_content)
    
    # 5. Criar template de PDF faltando
    print("📄 Criando template PDF...")
    os.makedirs('app/cli/templates/cli', exist_ok=True)
    
    pdf_template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Checklist - {{ checklist.codigo }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .info { margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .qr-code { text-align: center; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ checklist.formulario.nome }}</h1>
        <h2>{{ checklist.loja.nome }}</h2>
    </div>
    
    <div class="info">
        <p><strong>Código:</strong> {{ checklist.codigo }}</p>
        <p><strong>Data:</strong> {{ checklist.data_inicio.strftime('%d/%m/%Y %H:%M') }}</p>
        <p><strong>Auditor:</strong> {{ checklist.usuario.nome }}</p>
        <p><strong>Pontuação:</strong> {{ checklist.percentual }}%</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Pergunta</th>
                <th>Resposta</th>
                <th>Pontuação</th>
            </tr>
        </thead>
        <tbody>
            {% for resposta in checklist.respostas %}
            <tr>
                <td>{{ resposta.pergunta.texto }}</td>
                <td>
                    {% if resposta.valor_opcoes_selecionadas %}
                        {% set opcoes = resposta.valor_opcoes_selecionadas | from_json %}
                        {{ opcoes | join(', ') }}
                    {% elif resposta.valor_texto %}
                        {{ resposta.valor_texto }}
                    {% elif resposta.valor_numero %}
                        {{ resposta.valor_numero }}
                    {% else %}
                        -
                    {% endif %}
                </td>
                <td>{{ resposta.pontuacao_obtida or 0 }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if checklist.observacoes_gerais %}
    <div class="info">
        <h3>Observações Gerais</h3>
        <p>{{ checklist.observacoes_gerais }}</p>
    </div>
    {% endif %}

    <div class="qr-code">
        <img src="data:image/png;base64,{{ qr_base64 }}" width="100">
        <p>{{ data_hoje }}</p>
    </div>
</body>
</html>'''
    
    with open('app/cli/templates/cli/checklist_pdf.html', 'w', encoding='utf-8') as f:
        f.write(pdf_template)
    
    # 6. Criar template selecionar_loja.html
    print("🏪 Criando template selecionar loja...")
    
    selecionar_loja_template = '''{% extends 'base_cliq.html' %}
{% block title %}Selecionar Loja - {{ formulario.nome }}{% endblock %}

{% block content %}
<div class="container py-4">
    <h3 class="mb-4">Selecione uma loja para aplicar: <strong>{{ formulario.nome }}</strong></h3>
    
    <div class="row">
        {% for loja in lojas %}
        <div class="col-md-6 col-lg-4 mb-3">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <h5 class="card-title">{{ loja.nome }}</h5>
                    <p class="card-text">
                        <small class="text-muted">{{ loja.codigo }}</small><br>
                        {{ loja.cidade }}, {{ loja.estado }}
                    </p>
                    <a href="{{ url_for('cli.aplicar_checklist', formulario_id=formulario.id, loja_id=loja.id) }}" 
                       class="btn btn-primary">
                        <i class="fas fa-clipboard-check me-1"></i>
                        Aplicar Checklist
                    </a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    
    <div class="mt-4">
        <a href="{{ url_for('cli.iniciar_aplicacao') }}" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left me-1"></i>
            Voltar
        </a>
    </div>
</div>
{% endblock %}'''
    
    with open('app/cli/templates/cli/selecionar_loja.html', 'w', encoding='utf-8') as f:
        f.write(selecionar_loja_template)
    
    # 7. Corrigir templates base
    print("🎨 Corrigindo templates base...")
    
    # Ler e corrigir base_painel.html
    try:
        with open('app/templates/base_painel.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substituir as referências ao perfil
        content = content.replace("{% if current_user.perfil == 'admin' %}", 
                                "{% if current_user.tipo.name in ['SUPER_ADMIN', 'ADMIN'] %}")
        
        with open('app/templates/base_painel.html', 'w', encoding='utf-8') as f:
            f.write(content)
    except FileNotFoundError:
        print("  ⚠️ base_painel.html não encontrado - OK, será criado depois")
    
    # 8. Criar inicializador corrigido
    print("🚀 Criando inicializador corrigido...")
    
    inicializador_content = '''# inicializar_sistema_corrigido.py
"""
Script corrigido para inicializar o QualiGestor
Execute este após aplicar as correções
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import *
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def criar_dados_basicos():
    """Cria dados básicos para funcionamento"""
    
    print("🚀 Criando dados básicos do sistema...")
    
    app = create_app()
    
    with app.app_context():
        # Limpar e recriar banco
        print("🧹 Recriando banco de dados...")
        db.drop_all()
        db.create_all()
        
        try:
            # 1. Criar Cliente
            print("🏢 Criando cliente...")
            cliente = Cliente(
                nome="Laboratório Demo",
                endereco="Rua das Análises, 123",
                cidade="São Paulo",
                estado="SP",
                telefone="(11) 3456-7890",
                email_contato="contato@labdemo.com",
                ativo=True
            )
            db.session.add(cliente)
            db.session.flush()
            
            # 2. Criar Grupo
            print("📁 Criando grupo...")
            grupo = Grupo(
                nome="São Paulo",
                cliente_id=cliente.id,
                ativo=True
            )
            db.session.add(grupo)
            db.session.flush()
            
            # 3. Criar Lojas
            print("🏪 Criando lojas...")
            lojas = [
                Loja(
                    nome="Lab Centro",
                    codigo="LAB001",
                    endereco="Centro de SP",
                    cidade="São Paulo",
                    estado="SP",
                    cliente_id=cliente.id,
                    grupo_id=grupo.id,
                    ativa=True
                ),
                Loja(
                    nome="Lab Vila Mariana",
                    codigo="LAB002",
                    endereco="Vila Mariana",
                    cidade="São Paulo",
                    estado="SP",
                    cliente_id=cliente.id,
                    grupo_id=grupo.id,
                    ativa=True
                )
            ]
            db.session.add_all(lojas)
            db.session.flush()
            
            # 4. Criar Usuários CORRIGIDOS
            print("👥 Criando usuários...")
            usuarios = [
                Usuario(
                    nome="Admin Sistema",
                    email="admin@admin.com",
                    senha=generate_password_hash("admin123"),
                    tipo=TipoUsuario.SUPER_ADMIN,  # CORRIGIDO
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                ),
                Usuario(
                    nome="Ana Auditora",
                    email="ana@demo.com",
                    senha=generate_password_hash("demo123"),
                    tipo=TipoUsuario.AUDITOR,  # CORRIGIDO
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                )
            ]
            db.session.add_all(usuarios)
            db.session.flush()
            
            # 5. Criar Categoria
            print("📋 Criando categoria...")
            categoria = CategoriaFormulario(
                nome="Higiene",
                icone="fas fa-broom",
                cor="#27ae60",
                ativa=True
            )
            db.session.add(categoria)
            db.session.flush()
            
            # 6. Criar Formulário Simples
            print("📝 Criando formulário...")
            formulario = Formulario(
                nome="Checklist Básico de Higiene",
                cliente_id=cliente.id,
                criado_por_id=usuarios[0].id,
                categoria_id=categoria.id,
                versao='1.0',
                pontuacao_ativa=True,
                ativo=True,
                publicado=True,
                publicado_em=datetime.utcnow()
            )
            db.session.add(formulario)
            db.session.flush()
            
            # 7. Criar Bloco
            bloco = BlocoFormulario(
                nome="Limpeza Geral",
                ordem=1,
                formulario_id=formulario.id
            )
            db.session.add(bloco)
            db.session.flush()
            
            # 8. Criar Perguntas
            print("❓ Criando perguntas...")
            perguntas_data = [
                ("Bancadas estão limpas?", TipoResposta.SIM_NAO, True, 10),
                ("Piso sem resíduos?", TipoResposta.SIM_NAO, True, 10),
                ("Equipamentos limpos?", TipoResposta.SIM_NAO, True, 10),
                ("Nota geral da limpeza", TipoResposta.NOTA, True, 10)
            ]
            
            for ordem, (texto, tipo, obrigatoria, peso) in enumerate(perguntas_data, 1):
                pergunta = Pergunta(
                    texto=texto,
                    tipo_resposta=tipo,
                    obrigatoria=obrigatoria,
                    ordem=ordem,
                    peso=peso,
                    pontuacao_maxima=peso,
                    bloco_id=bloco.id,
                    permite_observacao=True
                )
                db.session.add(pergunta)
                db.session.flush()
                
                # Criar opções para Sim/Não
                if tipo == TipoResposta.SIM_NAO:
                    opcoes = [
                        OpcaoPergunta(texto="Sim", valor="Sim", pontuacao=peso, ordem=1, pergunta_id=pergunta.id),
                        OpcaoPergunta(texto="Não", valor="Não", pontuacao=0, ordem=2, pergunta_id=pergunta.id)
                    ]
                    db.session.add_all(opcoes)
            
            # 9. Criar algumas auditorias de exemplo
            print("📊 Criando auditorias de exemplo...")
            for i in range(5):
                auditoria = Auditoria(
                    codigo=f"AUD-2025-{i+1:03d}",
                    formulario_id=formulario.id,
                    loja_id=lojas[i % 2].id,  # Alterna entre as lojas
                    usuario_id=usuarios[1].id,  # Ana
                    status=StatusAuditoria.CONCLUIDA,
                    data_inicio=datetime.now() - timedelta(days=i*2),
                    data_conclusao=datetime.now() - timedelta(days=i*2),
                    pontuacao_obtida=30 + (i * 5),
                    pontuacao_maxima=40,
                    percentual=75 + (i * 5)
                )
                db.session.add(auditoria)
                db.session.flush()
                
                # Criar respostas simples
                for pergunta in bloco.perguntas:
                    resposta = Resposta(
                        pergunta_id=pergunta.id,
                        auditoria_id=auditoria.id,
                        valor_opcoes_selecionadas='["Sim"]' if pergunta.tipo_resposta == TipoResposta.SIM_NAO else None,
                        valor_numero=8.5 if pergunta.tipo_resposta == TipoResposta.NOTA else None,
                        pontuacao_obtida=pergunta.peso
                    )
                    db.session.add(resposta)
            
            db.session.commit()
            
            print("\\n✅ SISTEMA CORRIGIDO E FUNCIONANDO!")
            print("🔑 LOGIN: admin@admin.com / admin123")
            print("🌐 Execute: python run.py")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    criar_dados_basicos()
'''
    
    with open('inicializar_sistema_corrigido.py', 'w', encoding='utf-8') as f:
        f.write(inicializador_content)
    
    print("\n✅ CORREÇÕES APLICADAS COM SUCESSO!")
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("1. Execute: python inicializar_sistema_corrigido.py")
    print("2. Execute: python run.py")
    print("3. Acesse: http://localhost:5000")
    print("4. Login: admin@admin.com / admin123")
    
    return True

if __name__ == "__main__":
    aplicar_correcoes()
perfil')  # vindo do select legado
        cliente_id = request.form.get('cliente_id')

        # Converte 'perfil' legado para Enum TipoUsuario
        tipo_usuario = str_para_tipo_usuario(perfil_form)

        # Hash da senha
        senha_hash = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_hash,
            tipo=tipo_usuario,
            cliente_id=cliente_id
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('auth.cadastrar_usuario'))

    return render_template('auth/cadastrar_usuario.html', clientes=clientes)

@auth_bp.route('/usuarios')
@login_required
def listar_usuarios():
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuarios = Usuario.query.all()
    return render_template('auth/usuarios.html', usuarios=usuarios)

@auth_bp.route('/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuario = Usuario.query.get_or_404(usuario_id)
    clientes = Cliente.query.all()

    if request.method == 'POST':
        usuario.nome = request.form.get('nome', '').strip()
        usuario.email = request.form.get('email', '').strip()

        perfil_form = request.form.get('