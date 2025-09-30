
# inicializar_banco_novo.py
"""
Inicializa banco de dados do zero com estrutura correta
"""

from app import create_app, db
from app.models import *
import os

def criar_banco_novo():
    """Cria banco novo com todas as tabelas"""
    print("🆕 Criando banco de dados novo...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Remove todas as tabelas se existirem
            db.drop_all()
            print("  ✅ Tabelas antigas removidas")
            
            # Cria todas as tabelas
            db.create_all()
            print("  ✅ Todas as tabelas criadas")
            
            # Cria dados básicos
            from app.models import Cliente, Usuario, TipoUsuario
            from werkzeug.security import generate_password_hash
            
            # Cliente padrão
            cliente = Cliente(
                nome="Cliente Padrão",
                email="cliente@empresa.com",
                ativo=True
            )
            db.session.add(cliente)
            db.session.flush()  # Para pegar o ID
            
            # Usuário admin padrão
            usuario_admin = Usuario(
                nome="Administrador",
                email="admin@admin.com",
                senha=generate_password_hash("admin123"),
                tipo_usuario=TipoUsuario.ADMIN,
                cliente_id=cliente.id,
                ativo=True
            )
            db.session.add(usuario_admin)
            
            db.session.commit()
            print("  ✅ Dados básicos criados")
            print("  📧 Login: admin@admin.com")
            print("  🔑 Senha: admin123")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar banco: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    criar_banco_novo()
