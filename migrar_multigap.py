from app import create_app, db
from app.models import Usuario, Grupo, usuario_grupos
from sqlalchemy import text

app = create_app()

def migrar_dados():
    with app.app_context():
        print("=== INICIANDO MIGRAÇÃO SEGURA (POSTGRESQL) ===")
        
        # 1. Criar a tabela nova
        print("1. Verificando/Criando tabela 'usuario_grupos'...")
        try:
            usuario_grupos.create(db.engine)
            print("   -> Tabela criada com sucesso.")
        except Exception as e:
            print(f"   -> Aviso (pode já existir): {e}")

        # 2. Migrar dados antigos (grupo_id) para a nova lista
        print("2. Migrando vínculos existentes...")
        usuarios = Usuario.query.all()
        contador = 0
        
        for u in usuarios:
            if u.grupo_id:
                grupo = Grupo.query.get(u.grupo_id)
                if grupo and grupo not in u.grupos_acesso:
                    u.grupos_acesso.append(grupo)
                    contador += 1
                    print(f"   -> Migrado: {u.nome} + GAP {grupo.nome}")
        
        # 3. Commit
        try:
            db.session.commit()
            print(f"=== SUCESSO! {contador} vínculos migrados. ===")
        except Exception as e:
            db.session.rollback()
            print(f"=== ERRO: {e} ===")

if __name__ == "__main__":
    migrar_dados()