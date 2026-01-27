from app import create_app, db
from app.models import usuario_grupos, Usuario, Grupo
from sqlalchemy import text

app = create_app()

def verificar_e_corrigir():
    with app.app_context():
        print("=== DIAGNÓSTICO DO BANCO DE DADOS ===")
        
        # 1. Tenta verificar se a tabela existe
        try:
            # Comando SQL direto para verificar existência (Postgres)
            result = db.session.execute(text("SELECT to_regclass('public.usuario_grupos');"))
            tabela_existe = result.scalar() is not None
            
            if tabela_existe:
                print("✅ Tabela 'usuario_grupos' JÁ EXISTE no banco.")
            else:
                print("❌ Tabela 'usuario_grupos' NÃO ENCONTRADA.")
                print("🔨 Criando tabela agora...")
                usuario_grupos.create(db.engine)
                print("✅ Tabela criada com sucesso!")
                
        except Exception as e:
            print(f"⚠️ Erro ao verificar tabela (tentando criar mesmo assim): {e}")
            try:
                usuario_grupos.create(db.engine)
            except:
                pass

        # 2. Teste de Vínculo (Simulação)
        print("\n=== TESTE DE VÍNCULO ===")
        usuario = Usuario.query.filter_by(email='victorgroba2@gmail.com').first() # Tenta pegar seu user
        if not usuario:
            usuario = Usuario.query.first()
            
        grupos = Grupo.query.limit(2).all()
        
        if usuario and len(grupos) >= 2:
            print(f"Testando com usuário: {usuario.nome}")
            print(f"Tentando vincular GAPs: {[g.nome for g in grupos]}")
            
            # Limpa e adiciona
            usuario.grupos_acesso = []
            for g in grupos:
                usuario.grupos_acesso.append(g)
            
            try:
                db.session.commit()
                print("✅ SUCESSO! Vínculos salvos no banco. O sistema está funcionando.")
                print(f"GAPs atuais do usuário: {usuario.grupos_acesso}")
            except Exception as e:
                db.session.rollback()
                print(f"❌ ERRO AO SALVAR NO BANCO: {e}")
        else:
            print("⚠️ Não foi possível testar (falta usuário ou grupos cadastrados).")

if __name__ == "__main__":
    verificar_e_corrigir()