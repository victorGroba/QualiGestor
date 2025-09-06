# test_imports.py
"""
Script para verificar quais modelos estão disponíveis
Execute este da raiz do projeto
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("TESTE DE IMPORTS DO MODELS.PY")
print("=" * 60)

# Tentar importar o app
try:
    from app import create_app, db
    print("✅ App e db importados com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar app: {e}")
    sys.exit(1)

# Listar tudo que está disponível em models
print("\n📋 Verificando o que está disponível em models...")
try:
    import app.models as models
    disponivel = [item for item in dir(models) if not item.startswith('_')]
    
    print("\n✅ Classes/objetos disponíveis em models.py:")
    for item in sorted(disponivel):
        print(f"   • {item}")
        
except Exception as e:
    print(f"❌ Erro ao importar models: {e}")
    sys.exit(1)

# Tentar importar classes específicas
print("\n🔍 Testando imports específicos...")

classes_para_testar = [
    'Usuario',
    'Cliente', 
    'Avaliado',
    'Loja',
    'Formulario',
    'Pergunta',
    'Resposta',
    'Auditoria',
    'Grupo',
    'BlocoFormulario',
    'OpcaoPergunta',
    'Questionario',
    'Topico'
]

classes_encontradas = []
classes_faltando = []

for classe in classes_para_testar:
    try:
        exec(f"from app.models import {classe}")
        print(f"✅ {classe}")
        classes_encontradas.append(classe)
    except ImportError:
        print(f"❌ {classe} - não encontrado")
        classes_faltando.append(classe)
    except Exception as e:
        print(f"⚠️ {classe} - erro: {e}")
        classes_faltando.append(classe)

print("\n" + "=" * 60)
print("RESUMO:")
print(f"✅ Classes encontradas: {len(classes_encontradas)}")
print(f"❌ Classes faltando: {len(classes_faltando)}")

if classes_faltando:
    print("\n⚠️ Classes que precisam ser verificadas no models.py:")
    for classe in classes_faltando:
        print(f"   • {classe}")

print("\n💡 Dica: Se 'Avaliado' está faltando, pode estar com outro nome")
print("   ou precisa ser adicionado ao models.py")