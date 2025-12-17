#!/usr/bin/env python3
# run.py - Servidor QualiGestor

import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    
    app = create_app()
    
    # LER A CONFIGURAÇÃO DO ARQUIVO .ENV
    # Se não achar nada, assume False por segurança
    modo_debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    if __name__ == '__main__':
        if modo_debug:
            print("🚀 Iniciando QualiGestor em MODO DESENVOLVIMENTO (Windows)...")
            print("📍 Acesse: http://localhost:5000")
        else:
            print("🔒 Iniciando QualiGestor em MODO PRODUÇÃO (Linux/VPS)...")
            
        print("=" * 50)
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=modo_debug,  # <--- AQUI MUDOU! Agora usa a variável
            use_reloader=modo_debug # <--- O reloader só liga se for debug
        )
        
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("\n💡 Verifique se executou:")
    print("  1. python inicializar_dados_corrigido.py")
    print("  2. pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()
