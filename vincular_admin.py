# vincular_admin.py
from app import create_app, db
from app.models import Usuario, Cliente, Grupo

app = create_app()

def corrigir_vinculos():
    with app.app_context():
        print("--- 🕵️‍♂️ Diagnóstico e Correção de Vínculos ---")
        
        # 1. Busca o Cliente FAB (Onde os dados estão)
        cliente_fab = Cliente.query.filter(Cliente.nome.ilike('%Aeronáutica%')).first()
        
        if not cliente_fab:
            print("❌ ERRO: Cliente 'Aeronáutica' não achado. Rode o 'criar_estrutura_fab.py' primeiro.")
            return

        print(f"✅ Cliente Alvo: {cliente_fab.nome} (ID: {cliente_fab.id})")
        
        # 2. Confere se os GAPs estão lá mesmo
        gaps_fab = Grupo.query.filter_by(cliente_id=cliente_fab.id).count()
        print(f"📊 Total de GAPs neste cliente: {gaps_fab}")

        if gaps_fab == 0:
            print("⚠️ AVISO: Não há GAPs neste cliente. Algo errado com a carga anterior.")
        
        # 3. Busca e Corrige os Usuários
        usuarios = Usuario.query.all()
        print(f"\n👥 Verificando {len(usuarios)} usuários...")

        alterados = 0
        for u in usuarios:
            status = "✅ OK"
            if u.cliente_id != cliente_fab.id:
                # AQUI É A MÁGICA: Atualiza o ID do cliente do usuário
                u.cliente_id = cliente_fab.id
                db.session.add(u)
                status = "🔄 CORRIGIDO PARA FAB"
                alterados += 1
            
            print(f"   - {u.nome} ({u.email}): {status}")

        if alterados > 0:
            db.session.commit()
            print(f"\n🚀 SUCESSO: {alterados} usuários foram movidos para a Aeronáutica.")
        else:
            print("\n👍 Tudo certo: Todos os usuários já pertencem à Aeronáutica.")

if __name__ == "__main__":
    corrigir_vinculos()