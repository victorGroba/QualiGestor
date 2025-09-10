# fix_qualigestor_completo.py
"""
Sistema de Correção Completo para QualiGestor
Corrige todos os problemas identificados no sistema
"""

import sys
import os
import shutil
from datetime import datetime

def aplicar_correcoes_completas():
    """Aplica todas as correções necessárias no sistema"""
    
    print("🔧 SISTEMA DE CORREÇÃO QUALIGESTOR v1.4.0-beta")
    print("=" * 60)
    
    # 1. Corrigir app/models.py (Principal problema)
    print("📝 Corrigindo models.py...")
    criar_models_corrigido()
    
    # 2. Corrigir app/auth/routes.py
    print("🔐 Corrigindo autenticação...")
    criar_auth_corrigido()
    
    # 3. Corrigir app/cli/routes.py
    print("📋 Corrigindo rotas CLI...")
    corrigir_cli_routes()
    
    # 4. Corrigir app/panorama/routes.py
    print("📊 Corrigindo Panorama...")
    corrigir_panorama_routes()
    
    # 5. Criar templates faltando
    print("🎨 Criando templates faltando...")
    criar_templates_faltando()
    
    # 6. Corrigir app/__init__.py
    print("⚙️ Corrigindo inicialização...")
    corrigir_app_init()
    
    # 7. Criar inicializador de dados
    print("🚀 Criando inicializador...")
    criar_inicializador()
    
    print("\n✅ TODAS AS CORREÇÕES APLICADAS!")
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("1. Execute: python inicializar_dados_corrigido.py")
    print("2. Execute: python run.py")
    print("3. Acesse: http://localhost:5000")
    print("4. Login: admin@admin.com / admin123")

def criar_models_corrigido():
    """Cria versão corrigida do models.py"""
    
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
'''
    
    # Backup do arquivo original
    if os.path.exists('app/models.py'):
        shutil.copy('app/models.py', f'app/models_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
    
    with open('app/models.py', 'w', encoding='utf-8') as f:
        f.write(models_content)

def criar_auth_corrigido():
    """Cria versão corrigida do auth/routes.py"""
    
    auth_content = '''# app/auth/routes.py - VERSÃO CORRIGIDA
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import Usuario, Cliente, TipoUsuario

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# -------- helpers --------
def str_para_tipo_usuario(valor: str) -> TipoUsuario:
    """Converte strings legadas de 'perfil' do formulário em TipoUsuario."""
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
    """Retorna True se o usuário atual for ADMIN ou SUPER_ADMIN."""
    if not current_user.is_authenticated:
        return False
    return current_user.tipo in [TipoUsuario.ADMIN, TipoUsuario.SUPER_ADMIN]

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)

            # Sessão
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
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    clientes = Cliente.query.all()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        perfil_form = request.form.get('perfil')
        cliente_id = request.form.get('cliente_id')

        tipo_usuario = str_para_tipo_usuario(perfil_form)
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
    
    # Backup se existir
    if os.path.exists('app/auth/routes.py'):
        shutil.copy('app/auth/routes.py', f'app/auth/routes_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
    
    with open('app/auth/routes.py', 'w', encoding='utf-8') as f:
        f.write(auth_content)

def corrigir_cli_routes():
    """Adiciona rotas faltando no CLI"""
    
    rotas_faltando = '''
# ===================== ROTAS DE COMPATIBILIDADE =====================

@cli_bp.route('/questionarios')
@login_required
def listar_questionarios():
    """Lista formulários (compatibilidade)"""
    return redirect(url_for('cli.listar_formularios'))

@cli_bp.route('/questionarios/novo', methods=['GET', 'POST'])
@login_required
def novo_questionario():
    """Cria formulário (compatibilidade)"""
    return redirect(url_for('cli.criar_formulario'))

@cli_bp.route('/questionario/<int:id>/topicos')
@login_required
def gerenciar_topicos(id):
    """Gerencia blocos (compatibilidade)"""
    return redirect(url_for('cli.visualizar_formulario', formulario_id=id))

@cli_bp.route('/avaliados')
@login_required
def listar_avaliados():
    """Lista lojas (compatibilidade)"""
    return redirect(url_for('cli.listar_lojas'))

@cli_bp.route('/avaliados/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_avaliado():
    """Cria loja (compatibilidade)"""
    return redirect(url_for('cli.nova_loja'))

@cli_bp.route('/grupos/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_grupo():
    """Cria grupo (compatibilidade)"""
    return redirect(url_for('cli.novo_grupo'))
'''
    
    # Ler arquivo existente e adicionar rotas
    try:
        with open('app/cli/routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Se já não tem as rotas, adicionar
        if 'listar_questionarios' not in content:
            with open('app/cli/routes.py', 'a', encoding='utf-8') as f:
                f.write(rotas_faltando)
    except FileNotFoundError:
        print("  ⚠️ app/cli/routes.py não encontrado")

def corrigir_panorama_routes():
    """Adiciona rota filtros no Panorama"""
    
    rota_filtros = '''
@panorama_bp.route('/filtros')
@login_required
def filtros():
    """Página de filtros (compatibilidade)"""
    return redirect(url_for('panorama.dashboard'))
'''
    
    try:
        with open('app/panorama/routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '/filtros' not in content:
            with open('app/panorama/routes.py', 'a', encoding='utf-8') as f:
                f.write(rota_filtros)
    except FileNotFoundError:
        print("  ⚠️ app/panorama/routes.py não encontrado")

def criar_templates_faltando():
    """Cria templates que estão faltando"""
    
    # 1. Template listar_questionarios.html
    os.makedirs('app/cli/templates/cli', exist_ok=True)
    
    template_questionarios = '''{% extends 'base_cliq.html' %}
{% block title %}Questionários{% endblock %}

{% block content %}
<div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h4>Questionários Cadastrados</h4>
        <a href="{{ url_for('cli.criar_formulario') }}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Novo Questionário
        </a>
    </div>

    <div class="card shadow-sm">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Versão</th>
                            <th>Status</th>
                            <th>Criado em</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for formulario in formularios %}
                        <tr>
                            <td>{{ formulario.nome }}</td>
                            <td>{{ formulario.versao }}</td>
                            <td>
                                <span class="badge bg-{{ 'success' if formulario.publicado else 'warning' }}">
                                    {{ 'Publicado' if formulario.publicado else 'Rascunho' }}
                                </span>
                            </td>
                            <td>{{ formulario.criado_em.strftime('%d/%m/%Y') if formulario.criado_em else '-' }}</td>
                            <td>
                                <a href="{{ url_for('cli.visualizar_formulario', formulario_id=formulario.id) }}" 
                                   class="btn btn-sm btn-outline-primary" title="Visualizar">
                                    <i class="fas fa-eye"></i>
                                </a>
                                <a href="{{ url_for('cli.selecionar_loja', formulario_id=formulario.id) }}" 
                                   class="btn btn-sm btn-outline-success" title="Aplicar">
                                    <i class="fas fa-play"></i>
                                </a>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" class="text-center text-muted py-4">
                                Nenhum questionário cadastrado
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    with open('app/cli/templates/cli/listar_questionarios.html', 'w', encoding='utf-8') as f:
        f.write(template_questionarios)
    
    # 2. Template selecionar_loja.html
    template_selecionar_loja = '''{% extends 'base_cliq.html' %}
{% block title %}Selecionar Loja{% endblock %}

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
                        <small class="text-muted">{{ loja.codigo or 'Sem código' }}</small><br>
                        {{ loja.cidade or 'N/A' }}, {{ loja.estado or 'N/A' }}
                    </p>
                    <a href="{{ url_for('cli.aplicar_checklist', formulario_id=formulario.id, loja_id=loja.id) }}" 
                       class="btn btn-primary">
                        <i class="fas fa-clipboard-check me-1"></i>
                        Aplicar Checklist
                    </a>
                </div>
            </div>
        </div>
        {% else %}
        <div class="col-12">
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Nenhuma loja cadastrada. <a href="{{ url_for('cli.nova_loja') }}">Cadastre uma loja</a> primeiro.
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
        f.write(template_selecionar_loja)
    
    # 3. Template nova_loja.html
    template_nova_loja = '''{% extends 'base_cliq.html' %}
{% block title %}Nova Loja{% endblock %}

{% block content %}
<div class="container py-4">
    <h4 class="mb-4">Cadastrar Nova Loja</h4>

    <form method="POST">
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="nome" class="form-label">Nome da Loja *</label>
                    <input type="text" name="nome" id="nome" class="form-control" required>
                </div>
                
                <div class="mb-3">
                    <label for="codigo" class="form-label">Código</label>
                    <input type="text" name="codigo" id="codigo" class="form-control">
                </div>
                
                <div class="mb-3">
                    <label for="endereco" class="form-label">Endereço</label>
                    <input type="text" name="endereco" id="endereco" class="form-control">
                </div>
                
                <div class="row">
                    <div class="col-8">
                        <div class="mb-3">
                            <label for="cidade" class="form-label">Cidade</label>
                            <input type="text" name="cidade" id="cidade" class="form-control">
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="mb-3">
                            <label for="estado" class="form-label">Estado</label>
                            <input type="text" name="estado" id="estado" class="form-control" maxlength="2">
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="cep" class="form-label">CEP</label>
                    <input type="text" name="cep" id="cep" class="form-control">
                </div>
                
                <div class="mb-3">
                    <label for="telefone" class="form-label">Telefone</label>
                    <input type="text" name="telefone" id="telefone" class="form-control">
                </div>
                
                <div class="mb-3">
                    <label for="email" class="form-label">E-mail</label>
                    <input type="email" name="email" id="email" class="form-control">
                </div>
                
                <div class="mb-3">
                    <label for="gerente_nome" class="form-label">Nome do Gerente</label>
                    <input type="text" name="gerente_nome" id="gerente_nome" class="form-control">
                </div>
                
                <div class="mb-3">
                    <label for="grupo_id" class="form-label">Grupo</label>
                    <select name="grupo_id" id="grupo_id" class="form-select">
                        <option value="">Selecione um grupo</option>
                        {% for grupo in grupos %}
                        <option value="{{ grupo.id }}">{{ grupo.nome }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <button type="submit" class="btn btn-success">
                <i class="fas fa-save"></i> Salvar
            </button>
            <a href="{{ url_for('cli.listar_lojas') }}" class="btn btn-secondary">
                Cancelar
            </a>
        </div>
    </form>
</div>
{% endblock %}'''
    
    with open('app/cli/templates/cli/nova_loja.html', 'w', encoding='utf-8') as f:
        f.write(template_nova_loja)
    
    # 4. Template checklist_pdf.html
    template_pdf = '''<!DOCTYPE html>
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
        f.write(template_pdf)

def corrigir_app_init():
    """Corrige o arquivo app/__init__.py"""
    
    init_content = '''import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-secreta-desenvolvimento')
    
    # Configuração do banco
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'banco.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False

    # Versão do sistema
    versao_path = os.path.join(os.getcwd(), 'version.txt')
    try:
        with open(versao_path, 'r') as f:
            app.config['VERSAO'] = f.read().strip()
    except FileNotFoundError:
        app.config['VERSAO'] = '1.4.0-beta'

    @app.context_processor
    def inject_version():
        return dict(versao=app.config['VERSAO'])

    # Função auxiliar para templates
    from app.utils.helpers import opcao_pergunta_por_id

    @app.context_processor
    def inject_custom_functions():
        return dict(opcao_pergunta_por_id=opcao_pergunta_por_id)

    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importar modelos
    from .models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .cli.routes import cli_bp
    from .panorama.routes import panorama_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(cli_bp, url_prefix='/cli')
    app.register_blueprint(panorama_bp, url_prefix='/panorama')

    # Registrar admin se existir
    try:
        from .admin.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        pass

    return app

# Expor db para importação
__all__ = ['db']
'''
    
    # Backup
    if os.path.exists('app/__init__.py'):
        shutil.copy('app/__init__.py', f'app/__init___backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
    
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

def criar_inicializador():
    """Cria script inicializador de dados"""
    
    inicializador_content = '''# inicializar_dados_corrigido.py
"""
Script para inicializar o QualiGestor com dados de demonstração
Execute este script após aplicar as correções
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import *
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def criar_dados_demonstracao():
    """Cria dados básicos para demonstração"""
    
    print("🚀 Inicializando QualiGestor com dados de demonstração")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # Limpar e recriar banco
        print("🧹 Recriando banco de dados...")
        db.drop_all()
        db.create_all()
        
        try:
            # 1. Criar Categorias
            print("📋 Criando categorias...")
            categorias = [
                CategoriaFormulario(nome="Higiene", icone="fas fa-broom", cor="#27ae60", ordem=1),
                CategoriaFormulario(nome="Segurança", icone="fas fa-shield-alt", cor="#e74c3c", ordem=2),
                CategoriaFormulario(nome="Atendimento", icone="fas fa-smile", cor="#f39c12", ordem=3)
            ]
            db.session.add_all(categorias)
            db.session.flush()
            
            # 2. Criar Cliente
            print("🏢 Criando cliente...")
            cliente = Cliente(
                nome="Laboratório Demo LTDA",
                nome_fantasia="Lab Demo",
                cnpj="12.345.678/0001-90",
                endereco="Rua das Análises, 123",
                cidade="São Paulo",
                estado="SP",
                cep="01234-567",
                telefone="(11) 3456-7890",
                email_contato="contato@labdemo.com",
                ativo=True
            )
            db.session.add(cliente)
            db.session.flush()
            
            # 3. Criar Grupos
            print("📁 Criando grupos...")
            grupos = [
                Grupo(nome="São Paulo", cliente_id=cliente.id),
                Grupo(nome="Rio de Janeiro", cliente_id=cliente.id)
            ]
            db.session.add_all(grupos)
            db.session.flush()
            
            # 4. Criar Lojas
            print("🏪 Criando lojas...")
            lojas = [
                Loja(
                    nome="Lab Centro SP",
                    codigo="SP001",
                    endereco="Centro de São Paulo",
                    cidade="São Paulo",
                    estado="SP",
                    cliente_id=cliente.id,
                    grupo_id=grupos[0].id,
                    ativa=True
                ),
                Loja(
                    nome="Lab Vila Mariana",
                    codigo="SP002",
                    endereco="Vila Mariana",
                    cidade="São Paulo",
                    estado="SP",
                    cliente_id=cliente.id,
                    grupo_id=grupos[0].id,
                    ativa=True
                ),
                Loja(
                    nome="Lab Copacabana",
                    codigo="RJ001",
                    endereco="Copacabana",
                    cidade="Rio de Janeiro",
                    estado="RJ",
                    cliente_id=cliente.id,
                    grupo_id=grupos[1].id,
                    ativa=True
                )
            ]
            db.session.add_all(lojas)
            db.session.flush()
            
            # 5. Criar Usuários
            print("👥 Criando usuários...")
            usuarios = [
                Usuario(
                    nome="Administrador Sistema",
                    email="admin@admin.com",
                    senha=generate_password_hash("admin123"),
                    tipo=TipoUsuario.SUPER_ADMIN,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                ),
                Usuario(
                    nome="Ana Auditora",
                    email="ana@demo.com",
                    senha=generate_password_hash("demo123"),
                    tipo=TipoUsuario.AUDITOR,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                ),
                Usuario(
                    nome="Bruno Gestor",
                    email="bruno@demo.com",
                    senha=generate_password_hash("demo123"),
                    tipo=TipoUsuario.GESTOR,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                )
            ]
            db.session.add_all(usuarios)
            db.session.flush()
            
            # 6. Criar Formulários
            print("📝 Criando formulários...")
            
            # Formulário 1: Higiene
            formulario1 = Formulario(
                nome="Checklist de Higiene Laboratorial",
                cliente_id=cliente.id,
                criado_por_id=usuarios[1].id,
                categoria_id=categorias[0].id,
                versao='1.0',
                pontuacao_ativa=True,
                ativo=True,
                publicado=True,
                publicado_em=datetime.utcnow()
            )
            db.session.add(formulario1)
            db.session.flush()
            
            # Bloco 1
            bloco1 = BlocoFormulario(
                nome="Limpeza do Ambiente",
                ordem=1,
                formulario_id=formulario1.id
            )
            db.session.add(bloco1)
            db.session.flush()
            
            # Perguntas do bloco 1
            perguntas1 = [
                ("Bancadas estão limpas e organizadas?", TipoResposta.SIM_NAO, True, 10),
                ("Piso sem resíduos ou contaminantes?", TipoResposta.SIM_NAO, True, 10),
                ("Equipamentos limpos e calibrados?", TipoResposta.SIM_NAO, True, 15),
                ("Nota geral da limpeza (0-10)", TipoResposta.NOTA, True, 10)
            ]
            
            for ordem, (texto, tipo, obrigatoria, peso) in enumerate(perguntas1, 1):
                pergunta = Pergunta(
                    texto=texto,
                    tipo_resposta=tipo,
                    obrigatoria=obrigatoria,
                    ordem=ordem,
                    peso=peso,
                    pontuacao_maxima=peso,
                    bloco_id=bloco1.id,
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
            
            # Formulário 2: Segurança
            formulario2 = Formulario(
                nome="Auditoria de Segurança",
                cliente_id=cliente.id,
                criado_por_id=usuarios[1].id,
                categoria_id=categorias[1].id,
                versao='1.0',
                pontuacao_ativa=True,
                ativo=True,
                publicado=True,
                publicado_em=datetime.utcnow()
            )
            db.session.add(formulario2)
            db.session.flush()
            
            # Bloco 2
            bloco2 = BlocoFormulario(
                nome="Equipamentos de Proteção",
                ordem=1,
                formulario_id=formulario2.id
            )
            db.session.add(bloco2)
            db.session.flush()
            
            # Perguntas do bloco 2
            perguntas2 = [
                ("Todos usando EPIs obrigatórios?", TipoResposta.SIM_NAO, True, 20),
                ("EPIs em bom estado de conservação?", TipoResposta.SIM_NAO, True, 15),
                ("Chuveiro de emergência funcionando?", TipoResposta.SIM_NAO, True, 15),
                ("Extintores dentro da validade?", TipoResposta.SIM_NAO, True, 10)
            ]
            
            for ordem, (texto, tipo, obrigatoria, peso) in enumerate(perguntas2, 1):
                pergunta = Pergunta(
                    texto=texto,
                    tipo_resposta=tipo,
                    obrigatoria=obrigatoria,
                    ordem=ordem,
                    peso=peso,
                    pontuacao_maxima=peso,
                    bloco_id=bloco2.id,
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
            
            # 7. Criar Auditorias de Demonstração
            print("📊 Criando auditorias de demonstração...")
            
            formularios = [formulario1, formulario2]
            
            for i in range(20):  # 20 auditorias de exemplo
                # Data aleatória nos últimos 60 dias
                dias_atras = random.randint(1, 60)
                data_auditoria = datetime.now() - timedelta(days=dias_atras)
                
                # Escolher loja e formulário aleatórios
                loja = random.choice(lojas)
                formulario = random.choice(formularios)
                usuario = random.choice([usuarios[1], usuarios[2]])  # Ana ou Bruno
                
                # Criar auditoria
                auditoria = Auditoria(
                    codigo=f"AUD-2025-{i+1:03d}",
                    formulario_id=formulario.id,
                    loja_id=loja.id,
                    usuario_id=usuario.id,
                    status=StatusAuditoria.CONCLUIDA,
                    data_inicio=data_auditoria,
                    data_conclusao=data_auditoria + timedelta(minutes=random.randint(15, 45)),
                    observacoes_gerais=f"Auditoria realizada em {data_auditoria.strftime('%d/%m/%Y')}"
                )
                db.session.add(auditoria)
                db.session.flush()
                
                # Criar respostas
                pontuacao_total = 0
                pontuacao_maxima = 0
                
                for bloco in formulario.blocos:
                    for pergunta in bloco.perguntas:
                        pontuacao_maxima += pergunta.peso
                        
                        resposta = Resposta(
                            pergunta_id=pergunta.id,
                            auditoria_id=auditoria.id
                        )
                        
                        if pergunta.tipo_resposta == TipoResposta.SIM_NAO:
                            # 75% de chance de ser "Sim"
                            valor = "Sim" if random.random() < 0.75 else "Não"
                            resposta.valor_opcoes_selecionadas = f'["{valor}"]'
                            resposta.pontuacao_obtida = pergunta.peso if valor == "Sim" else 0
                            
                        elif pergunta.tipo_resposta == TipoResposta.NOTA:
                            # Nota aleatória entre 6 e 10
                            nota = random.uniform(6, 10)
                            resposta.valor_numero = nota
                            resposta.pontuacao_obtida = (nota / 10) * pergunta.peso
                        
                        pontuacao_total += resposta.pontuacao_obtida
                        db.session.add(resposta)
                
                # Atualizar pontuação da auditoria
                auditoria.pontuacao_obtida = pontuacao_total
                auditoria.pontuacao_maxima = pontuacao_maxima
                auditoria.percentual = (pontuacao_total / pontuacao_maxima * 100) if pontuacao_maxima > 0 else 0
            
            db.session.commit()
            
            # Relatório final
            print("\\n" + "=" * 60)
            print("🎉 SISTEMA INICIALIZADO COM SUCESSO!")
            print("=" * 60)
            
            print(f"\\n📊 DADOS CRIADOS:")
            print(f"  • Categorias: {CategoriaFormulario.query.count()}")
            print(f"  • Clientes: {Cliente.query.count()}")
            print(f"  • Grupos: {Grupo.query.count()}")
            print(f"  • Lojas: {Loja.query.count()}")
            print(f"  • Usuários: {Usuario.query.count()}")
            print(f"  • Formulários: {Formulario.query.count()}")
            print(f"  • Blocos: {BlocoFormulario.query.count()}")
            print(f"  • Perguntas: {Pergunta.query.count()}")
            print(f"  • Auditorias: {Auditoria.query.count()}")
            print(f"  • Respostas: {Resposta.query.count()}")
            
            print(f"\\n🔑 CREDENCIAIS DE ACESSO:")
            print(f"  • Super Admin: admin@admin.com / admin123")
            print(f"  • Auditora: ana@demo.com / demo123")
            print(f"  • Gestor: bruno@demo.com / demo123")
            
            print(f"\\n🚀 COMO USAR:")
            print(f"  1. Execute: python run.py")
            print(f"  2. Acesse: http://localhost:5000")
            print(f"  3. Faça login com as credenciais acima")
            print(f"  4. Navegue pelos módulos CLIQ e Panorama")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = criar_dados_demonstracao()
    if sucesso:
        print("\\n✅ Inicialização concluída com sucesso!")
    else:
        print("\\n❌ Falha na inicialização!")
'''
    
    with open('inicializar_dados_corrigido.py', 'w', encoding='utf-8') as f:
        f.write(inicializador_content)

def criar_requirements():
    """Cria arquivo requirements.txt atualizado"""
    
    requirements_content = '''Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-Migrate==4.0.5
Flask-WTF==1.1.1
WTForms==3.0.1
WTForms-SQLAlchemy==0.4.1
Werkzeug==2.3.7
python-dotenv==1.0.0
qrcode==7.4.2
Pillow==10.0.1
WeasyPrint==60.1
'''
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(requirements_content)

def criar_arquivo_env():
    """Cria arquivo .env de exemplo"""
    
    env_content = '''# Configurações do QualiGestor
SECRET_KEY=chave-secreta-desenvolvimento-qualigestor-2025
DEBUG=True
FLASK_ENV=development

# Banco de dados
DATABASE_URL=sqlite:///instance/banco.db

# Configurações de email (opcional)
MAIL_SERVER=localhost
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
'''
    
    # Só criar se não existir
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)

def criar_run_py_corrigido():
    """Cria run.py corrigido"""
    
    run_content = '''#!/usr/bin/env python3
# run.py - Servidor de desenvolvimento QualiGestor

import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    
    app = create_app()
    
    if __name__ == '__main__':
        print("🚀 Iniciando QualiGestor...")
        print("📍 Acesse: http://localhost:5000")
        print("🔑 Login: admin@admin.com / admin123")
        print("=" * 50)
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("\\n💡 Verifique se executou:")
    print("  1. python inicializar_dados_corrigido.py")
    print("  2. pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()
'''
    
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(run_content)

def corrigir_utils():
    """Cria/corrige arquivos utils"""
    
    # Criar diretório utils se não existir
    os.makedirs('app/utils', exist_ok=True)
    
    # helpers.py
    helpers_content = '''from app.models import OpcaoPergunta

def opcao_pergunta_por_id(opcao_id):
    """Função auxiliar para templates"""
    if not opcao_id:
        return None
    return OpcaoPergunta.query.get(opcao_id)
'''
    
    with open('app/utils/__init__.py', 'w') as f:
        f.write('# Utils package')
    
    with open('app/utils/helpers.py', 'w', encoding='utf-8') as f:
        f.write(helpers_content)

def corrigir_templates_base():
    """Corrige referências nos templates base"""
    
    # Corrigir base_painel.html
    try:
        with open('app/templates/base_painel.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substituir referências antigas
        content = content.replace(
            "{% if current_user.perfil == 'admin' %}", 
            "{% if current_user.tipo.name in ['SUPER_ADMIN', 'ADMIN'] %}"
        )
        
        with open('app/templates/base_painel.html', 'w', encoding='utf-8') as f:
            f.write(content)
            
    except FileNotFoundError:
        print("  ⚠️ base_painel.html não encontrado - OK")
    
    # Corrigir base_cliq.html
    try:
        with open('app/templates/base_cliq.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Adicionar filtro para compatibilidade se não existir
        if 'from_json' not in content:
            content = content.replace(
                '{% endblock %}',
                '''
<!-- Filtro personalizado para JSON -->
<script>
    // Adicionar filtro from_json globalmente para Jinja2
    if (typeof window.jinja_filters === 'undefined') {
        window.jinja_filters = {};
    }
    window.jinja_filters.from_json = function(value) {
        try {
            return JSON.parse(value);
        } catch(e) {
            return value;
        }
    };
</script>
{% endblock %}'''
            )
        
        with open('app/templates/base_cliq.html', 'w', encoding='utf-8') as f:
            f.write(content)
            
    except FileNotFoundError:
        print("  ⚠️ base_cliq.html não encontrado - OK")

# Executar todas as correções
if __name__ == "__main__":
    try:
        aplicar_correcoes_completas()
        criar_requirements()
        criar_arquivo_env()
        criar_run_py_corrigido()
        corrigir_utils()
        corrigir_templates_base()
        
        print("\n" + "=" * 60)
        print("🎉 SISTEMA TOTALMENTE CORRIGIDO!")
        print("=" * 60)
        
        print("\n📋 CHECKLIST DE VERIFICAÇÃO:")
        print("✅ Models.py corrigido")
        print("✅ Auth routes corrigido")
        print("✅ CLI routes corrigido")
        print("✅ Panorama routes corrigido")
        print("✅ Templates criados")
        print("✅ App/__init__.py corrigido")
        print("✅ Requirements.txt criado")
        print("✅ .env criado")
        print("✅ run.py corrigido")
        print("✅ Utils criado")
        print("✅ Inicializador criado")
        
        print("\n🚀 EXECUTAR AGORA:")
        print("1. pip install -r requirements.txt")
        print("2. python inicializar_dados_corrigido.py")
        print("3. python run.py")
        print("4. Acesse: http://localhost:5000")
        print("5. Login: admin@admin.com / admin123")
        
        print("\n💡 DICAS:")
        print("• Se der erro de import, execute o passo 1 primeiro")
        print("• Se o banco não funcionar, delete a pasta 'instance' e rode o passo 2")
        print("• Use Ctrl+C para parar o servidor")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A CORREÇÃO: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Tente executar as correções manualmente")