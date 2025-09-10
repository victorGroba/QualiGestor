#!/usr/bin/env python3
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
    print("\n💡 Verifique se executou:")
    print("  1. python inicializar_dados_corrigido.py")
    print("  2. pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()
