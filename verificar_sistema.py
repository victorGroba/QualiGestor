# verificar_sistema.py
"""
Script para verificar se o QualiGestor está funcionando corretamente
Execute após aplicar as correções
"""

import sys
import os
import subprocess
import importlib.util

def verificar_sistema():
    """Verifica todos os componentes do sistema"""
    
    print("🔍 VERIFICAÇÃO DO SISTEMA QUALIGESTOR")
    print("=" * 50)
    
    problemas = []
    sucessos = []
    
    # 1. Verificar arquivos essenciais
    print("\n📁 Verificando arquivos essenciais...")
    
    arquivos_essenciais = [
        'app/__init__.py',
        'app/models.py',
        'app/auth/routes.py',
        'app/cli/routes.py',
        'app/panorama/routes.py',
        'app/main/routes.py',
        'run.py',
        'requirements.txt'
    ]
    
    for arquivo in arquivos_essenciais:
        if os.path.exists(arquivo):
            print(f"  ✅ {arquivo}")
            sucessos.append(f"Arquivo {arquivo} existe")
        else:
            print(f"  ❌ {arquivo} - FALTANDO")
            problemas.append(f"Arquivo {arquivo} não encontrado")
    
    # 2. Verificar imports críticos
    print("\n🐍 Verificando imports...")
    
    try:
        # Testar import do app
        sys.path.insert(0, os.getcwd())
        from app import create_app, db
        print("  ✅ App principal importado")
        sucessos.append("App principal funciona")
        
        # Testar modelos
        from app.models import Usuario, Cliente, Loja, Formulario, Auditoria
        print("  ✅ Modelos principais importados")
        sucessos.append("Modelos principais funcionam")
        
        # Testar enums
        from app.models import TipoUsuario, TipoResposta, StatusAuditoria
        print("  ✅ Enums importados")
        sucessos.append("Enums funcionam")
        
    except ImportError as e:
        print(f"  ❌ Erro de import: {e}")
        problemas.append(f"Erro de import: {e}")
    except Exception as e:
        print(f"  ❌ Erro inesperado: {e}")
        problemas.append(f"Erro inesperado: {e}")
    
    # 3. Verificar criação do app
    print("\n🚀 Verificando criação do app...")
    
    try:
        app = create_app()
        print("  ✅ App criado com sucesso")
        sucessos.append("App Flask funciona")
        
        with app.app_context():
            # Testar conexão com banco
            try:
                db.create_all()
                print("  ✅ Banco de dados OK")
                sucessos.append("Banco de dados funciona")
            except Exception as e:
                print(f"  ❌ Erro no banco: {e}")
                problemas.append(f"Erro no banco: {e}")
                
    except Exception as e:
        print(f"  ❌ Erro criando app: {e}")
        problemas.append(f"Erro criando app: {e}")
    
    # 4. Verificar blueprints
    print("\n🗺️ Verificando blueprints...")
    
    try:
        from app.auth.routes import auth_bp
        print("  ✅ Blueprint auth")
        
        from app.main.routes import main_bp
        print("  ✅ Blueprint main")
        
        from app.cli.routes import cli_bp
        print("  ✅ Blueprint cli")
        
        from app.panorama.routes import panorama_bp
        print("  ✅ Blueprint panorama")
        
        sucessos.append("Todos os blueprints funcionam")
        
    except ImportError as e:
        print(f"  ❌ Erro nos blueprints: {e}")
        problemas.append(f"Erro nos blueprints: {e}")
    
    # 5. Verificar templates
    print("\n🎨 Verificando templates...")
    
    templates_importantes = [
        'app/templates/base_cliq.html',
        'app/templates/base_painel.html',
        'app/auth/templates/auth/login.html',
        'app/cli/templates/cli/index.html',
        'app/panorama/templates/panorama/index.html'
    ]
    
    for template in templates_importantes:
        if os.path.exists(template):
            print(f"  ✅ {template}")
        else:
            print(f"  ⚠️ {template} - pode ser criado depois")
    
    # 6. Verificar dependências Python
    print("\n📦 Verificando dependências...")
    
    dependencias = [
        'flask',
        'flask_sqlalchemy', 
        'flask_login',
        'werkzeug'
    ]
    
    for dep in dependencias:
        try:
            spec = importlib.util.find_spec(dep)
            if spec is not None:
                print(f"  ✅ {dep}")
            else:
                print(f"  ❌ {dep} - não instalado")
                problemas.append(f"Dependência {dep} não encontrada")
        except Exception:
            print(f"  ❌ {dep} - erro na verificação")
            problemas.append(f"Erro verificando {dep}")
    
    # 7. Resultado final
    print("\n" + "=" * 50)
    print("📊 RESULTADO DA VERIFICAÇÃO")
    print("=" * 50)
    
    print(f"\n✅ SUCESSOS: {len(sucessos)}")
    for sucesso in sucessos:
        print(f"  • {sucesso}")
    
    if problemas:
        print(f"\n❌ PROBLEMAS: {len(problemas)}")
        for problema in problemas:
            print(f"  • {problema}")
        
        print("\n🛠️ AÇÕES RECOMENDADAS:")
        
        if any("import" in p for p in problemas):
            print("  1. Execute: pip install -r requirements.txt")
        
        if any("arquivo" in p.lower() for p in problemas):
            print("  2. Execute: python fix_qualigestor_completo.py")
        
        if any("banco" in p.lower() for p in problemas):
            print("  3. Delete a pasta 'instance' e execute o inicializador")
        
        return False
    else:
        print("\n🎉 SISTEMA VERIFICADO COM SUCESSO!")
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("  1. python inicializar_dados_corrigido.py")
        print("  2. python run.py")
        print("  3. Acesse: http://localhost:5000")
        return True

def testar_rotas_basicas():
    """Testa se as rotas básicas funcionam"""
    
    print("\n🌐 TESTANDO ROTAS...")
    
    try:
        from app import create_app
        app = create_app()
        
        with app.test_client() as client:
            # Testar rota de login
            response = client.get('/login')
            if response.status_code == 200:
                print("  ✅ Rota /login funciona")
            else:
                print(f"  ❌ Rota /login retornou {response.status_code}")
            
            # Testar redirecionamento da home
            response = client.get('/')
            if response.status_code in [200, 302]:  # 302 = redirect
                print("  ✅ Rota / funciona")
            else:
                print(f"  ❌ Rota / retornou {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro testando rotas: {e}")
        return False

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    
    print("\n📦 VERIFICANDO DEPENDÊNCIAS DETALHADAS...")
    
    dependencias_necessarias = [
        ('flask', '2.0.0'),
        ('flask-sqlalchemy', '3.0.0'),
        ('flask-login', '0.6.0'),
        ('flask-migrate', '4.0.0'),
        ('werkzeug', '2.0.0'),
        ('python-dotenv', '1.0.0'),
        ('qrcode', '7.0.0'),
        ('pillow', '10.0.0')
    ]
    
    faltando = []
    
    for dep, versao_min in dependencias_necessarias:
        try:
            module = __import__(dep.replace('-', '_'))
            if hasattr(module, '__version__'):
                print(f"  ✅ {dep} v{module.__version__}")
            else:
                print(f"  ✅ {dep} (versão não detectada)")
        except ImportError:
            print(f"  ❌ {dep} - NÃO INSTALADO")
            faltando.append(dep)
    
    if faltando:
        print(f"\n📋 INSTALE AS DEPENDÊNCIAS FALTANDO:")
        print(f"pip install {' '.join(faltando)}")
        return False
    
    return True

if __name__ == "__main__":
    print("Iniciando verificação completa do sistema...\n")
    
    # Verificar sistema
    sistema_ok = verificar_sistema()
    
    # Verificar dependências
    deps_ok = verificar_dependencias()
    
    # Testar rotas (só se sistema estiver OK)
    if sistema_ok:
        rotas_ok = testar_rotas_basicas()
    else:
        rotas_ok = False
    
    # Resultado final
    print("\n" + "=" * 50)
    if sistema_ok and deps_ok and rotas_ok:
        print("🎉 SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("Execute: python inicializar_dados_corrigido.py")
    else:
        print("⚠️ SISTEMA PRECISA DE AJUSTES")
        print("Execute: python fix_qualigestor_completo.py")
    print("=" * 50)