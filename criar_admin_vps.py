import sys
import os

# Garante que o Python encontre a pasta 'app'
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Usuario, TipoUsuario, Cliente

# Inicia a aplicação para ter acesso ao banco
app = create_app()

with app.app_context():
    print("Conectando ao banco de dados...")

    # 1. GARANTIR QUE EXISTA UM CLIENTE (EMPRESA)
    cliente = Cliente.query.first()
    if not cliente:
        print("Criando Empresa Padrão...")
        cliente = Cliente(
            nome='Minha Empresa',
            razao_social='Minha Empresa Ltda',
            email='contato@empresa.com',
            ativo=True
        )
        db.session.add(cliente)
        db.session.commit()
        print(f"Empresa criada com ID: {cliente.id}")
    else:
        print(f"Usando Empresa existente ID: {cliente.id}")

    # 2. CRIAR O USUÁRIO ADMIN
    admin_existente = Usuario.query.filter_by(email="admin@admin.com").first()
    
    if admin_existente:
        print("AVISO: O usuario admin@admin.com JA EXISTE.")
        # CORREÇÃO AQUI: set_password
        admin_existente.set_password("123456") 
        admin_existente.tipo = TipoUsuario.ADMIN
        admin_existente.ativo = True
        db.session.commit()
        print("Senha redefinida para 123456 e permissões atualizadas.")
    else:
        print("Criando novo usuario admin...")
        u = Usuario(
            nome="Administrador", 
            email="admin@admin.com", 
            tipo=TipoUsuario.ADMIN,
            cliente_id=cliente.id,
            ativo=True
        )
        # CORREÇÃO AQUI: set_password
        u.set_password("123456")
        
        db.session.add(u)
        db.session.commit()
        print("SUCESSO: Usuario admin@admin.com criado!")

print("Fim.")
