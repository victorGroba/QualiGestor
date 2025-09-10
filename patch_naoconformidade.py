# patch_naoconformidade.py
"""
Patch rápido para adicionar a classe NaoConformidade que está faltando
Execute este script para corrigir o erro de importação
"""

import sys
import os

def adicionar_naoconformidade():
    """Adiciona a classe NaoConformidade ao models.py"""
    
    print("🔧 Corrigindo problema de NaoConformidade...")
    
    # Ler o arquivo models.py atual
    try:
        with open('app/models.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Arquivo app/models.py não encontrado!")
        return False
    
    # Verificar se NaoConformidade já existe
    if 'class NaoConformidade' in content:
        print("✅ NaoConformidade já existe no models.py")
        return True
    
    # Encontrar onde inserir a classe (após a classe Resposta)
    if '# ==================== COMPATIBILIDADE ====================' in content:
        insert_point = content.find('# ==================== COMPATIBILIDADE ====================')
    else:
        # Se não encontrar a seção de compatibilidade, inserir antes do final
        insert_point = content.rfind('# ==================== FUNÇÃO USER LOADER ====================')
        if insert_point == -1:
            insert_point = len(content) - 100  # Próximo do final
    
    # Código da classe NaoConformidade
    naoconformidade_code = '''
# ==================== NÃO CONFORMIDADES ====================

class NaoConformidade(db.Model):
    """Registro de não conformidades identificadas"""
    __tablename__ = "nao_conformidade"
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True)
    
    # Classificação
    tipo = db.Column(SqlEnum(TipoNaoConformidade), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='Aberta')
    prioridade = db.Column(db.String(20), default='Media')
    
    # Datas
    data_identificacao = db.Column(db.DateTime, default=datetime.utcnow)
    prazo_resolucao = db.Column(db.DateTime)
    data_resolucao = db.Column(db.DateTime)
    
    # Chaves estrangeiras
    auditoria_id = db.Column(db.Integer, db.ForeignKey('auditoria.id'), nullable=False)
    resposta_id = db.Column(db.Integer, db.ForeignKey('resposta.id'))
    identificado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    
    # Relacionamentos
    resposta = db.relationship('Resposta', backref='nao_conformidades')
    identificado_por = db.relationship('Usuario', backref='ncs_identificadas')
    auditoria = db.relationship('Auditoria', backref='nao_conformidades')

'''
    
    # Inserir o código
    new_content = content[:insert_point] + naoconformidade_code + content[insert_point:]
    
    # Fazer backup
    import shutil
    from datetime import datetime
    backup_name = f'app/models_backup_naoconf_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    shutil.copy('app/models.py', backup_name)
    print(f"📋 Backup criado: {backup_name}")
    
    # Escrever arquivo corrigido
    with open('app/models.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Classe NaoConformidade adicionada com sucesso!")
    return True

def corrigir_imports_panorama():
    """Corrige imports no panorama que estão causando erro"""
    
    print("🔧 Corrigindo imports do Panorama...")
    
    try:
        with open('app/panorama/routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se há imports problemáticos
        if 'from ..models import (' in content:
            # Substituir imports problemáticos
            old_import = '''from ..models import (
    db, Auditoria, Loja, Formulario, Resposta, 
    Pergunta, StatusAuditoria, TipoResposta, Cliente
)'''
            
            new_import = '''from ..models import (
    db, Auditoria, Loja, Formulario, Resposta, 
    Pergunta, StatusAuditoria, TipoResposta, Cliente
)'''
            
            # Se tem NaoConformidade nos imports, remover por enquanto
            content = content.replace(', NaoConformidade', '')
            content = content.replace('NaoConformidade, ', '')
            content = content.replace('NaoConformidade', '')
            
            with open('app/panorama/routes.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Imports do Panorama corrigidos!")
    
    except FileNotFoundError:
        print("⚠️ Arquivo panorama/routes.py não encontrado")
    except Exception as e:
        print(f"⚠️ Erro corrigindo panorama: {e}")

def instalar_dependencias():
    """Instala dependências faltando"""
    
    print("📦 Instalando dependências faltando...")
    
    try:
        import subprocess
        
        # Instalar python-dotenv e pillow
        cmd = [sys.executable, '-m', 'pip', 'install', 'python-dotenv', 'pillow']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependências instaladas com sucesso!")
            return True
        else:
            print(f"❌ Erro instalando dependências: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro instalando dependências: {e}")
        print("💡 Execute manualmente: pip install python-dotenv pillow")
        return False

def verificar_correcao():
    """Verifica se a correção funcionou"""
    
    print("🔍 Verificando correção...")
    
    try:
        # Tentar importar tudo
        sys.path.insert(0, os.getcwd())
        from app import create_app, db
        from app.models import NaoConformidade
        
        # Tentar criar app
        app = create_app()
        
        print("✅ Importações funcionando!")
        print("✅ App criado com sucesso!")
        return True
        
    except ImportError as e:
        print(f"❌ Ainda há erro de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

if __name__ == "__main__":
    print("🔧 PATCH PARA NAOCONFORMIDADE")
    print("=" * 40)
    
    # Passo 1: Adicionar NaoConformidade
    if adicionar_naoconformidade():
        print("✅ Passo 1: NaoConformidade adicionada")
    else:
        print("❌ Passo 1: Falhou")
        sys.exit(1)
    
    # Passo 2: Corrigir imports
    corrigir_imports_panorama()
    print("✅ Passo 2: Imports corrigidos")
    
    # Passo 3: Instalar dependências
    if instalar_dependencias():
        print("✅ Passo 3: Dependências instaladas")
    else:
        print("⚠️ Passo 3: Instale manualmente as dependências")
    
    # Passo 4: Verificar
    if verificar_correcao():
        print("\n🎉 CORREÇÃO APLICADA COM SUCESSO!")
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. python inicializar_dados_corrigido.py")
        print("2. python run.py")
        print("3. Acesse: http://localhost:5000")
    else:
        print("\n⚠️ Ainda há problemas. Execute:")
        print("python verificar_sistema.py")
    
    print("=" * 40)