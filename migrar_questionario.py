# migrar_questionario.py
from app import create_app, db
from app.models import Questionario, Cliente, Topico, Pergunta

app = create_app()

def migrar():
    with app.app_context():
        # 1. Busca o ID da Aeronáutica
        cliente_fab = Cliente.query.filter(Cliente.nome.ilike('%Aeronáutica%')).first()
        if not cliente_fab:
            print("Erro: Cliente Aeronáutica não encontrado.")
            return

        # 2. Busca TODOS os questionários que estão no cliente antigo (ID 1)
        # Se não souberes o ID, podemos buscar todos que não são da FAB
        questionarios = Questionario.query.filter(Questionario.cliente_id != cliente_fab.id).all()

        if not questionarios:
            print("Nenhum questionário encontrado para migrar.")
            return

        print(f"Migrando {len(questionarios)} questionários para {cliente_fab.nome}...")

        for q in questionarios:
            print(f" -> Migrando: {q.nome}")
            q.cliente_id = cliente_fab.id
            db.session.add(q)

        db.session.commit()
        print("\n🚀 SUCESSO! Agora os questionários pertencem à Aeronáutica e vão aparecer para ti.")

if __name__ == "__main__":
    migrar()