# corrigir_estrutura_fab.py
from app import create_app, db
from app.models import Cliente, Grupo, Avaliado

app = create_app()

def corrigir_ids():
    with app.app_context():
        print("--- 🛠️ Corrigindo IDs de GAPs e Ranchos ---")
        
        # 1. Busca o Cliente FAB
        cliente_fab = Cliente.query.filter(Cliente.nome.ilike('%Aeronáutica%')).first()
        if not cliente_fab:
            print("❌ ERRO: Cliente Aeronáutica não encontrado.")
            return
        
        fab_id = cliente_fab.id
        print(f"✅ ID da Aeronáutica no banco: {fab_id}")

        # 2. Corrigir GAPs (Grupos)
        gaps = Grupo.query.all()
        gaps_alterados = 0
        for g in gaps:
            if g.cliente_id != fab_id:
                g.cliente_id = fab_id
                db.session.add(g)
                gaps_alterados += 1
        
        # 3. Corrigir Ranchos (Avaliados)
        ranchos = Avaliado.query.all()
        ranchos_alterados = 0
        for r in ranchos:
            if r.cliente_id != fab_id:
                r.cliente_id = fab_id
                db.session.add(r)
                ranchos_alterados += 1

        if gaps_alterados > 0 or ranchos_alterados > 0:
            db.session.commit()
            print(f"🚀 SUCESSO:")
            print(f"   - {gaps_alterados} GAPs movidos para Aeronáutica.")
            print(f"   - {ranchos_alterados} Ranchos movidos para Aeronáutica.")
        else:
            print("👍 Tudo certo: Toda a estrutura já pertence à Aeronáutica.")

if __name__ == "__main__":
    corrigir_ids()