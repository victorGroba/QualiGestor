from app import create_app, db
from app.models import Grupo, Avaliado, Usuario

app = create_app()
app.app_context().push()

# 1. Tenta identificar o cliente (mesma lógica do script anterior)
user = Usuario.query.filter_by(email='ti@labmattos.com.br').first()
if user:
    cid = user.cliente_id
    print(f"Listando dados do Cliente: {user.nome} (ID: {cid})")
else:
    cid = 2
    print(f"Usuário não encontrado. Listando para Cliente ID padrão: {cid}")

print("=" * 80)
print(f"{'GAP / OM':<50} | {'RANCHO (Avaliado)':<30}")
print("=" * 80)

# 2. Busca todos os Grupos (GAPs)
grupos = Grupo.query.filter_by(cliente_id=cid).order_by(Grupo.nome).all()

total_ranchos = 0
sem_grupo = Avaliado.query.filter_by(cliente_id=cid, grupo_id=None).all()

# 3. Lista GAPs e seus Ranchos
for gap in grupos:
    # Busca os ranchos deste GAP
    ranchos = Avaliado.query.filter_by(grupo_id=gap.id, cliente_id=cid).all()
    
    if not ranchos:
        print(f"{gap.nome:<50} | (Nenhum rancho vinculado)")
    
    for rancho in ranchos:
        print(f"{gap.nome:<50} | {rancho.nome}")
        total_ranchos += 1

# 4. Lista Ranchos órfãos (se houver algum erro)
if sem_grupo:
    print("-" * 80)
    print("ALERTA: RANCHOS SEM GAP VINCULADO:")
    for rancho in sem_grupo:
        print(f"{'SEM GRUPO':<50} | {rancho.nome}")
        total_ranchos += 1

print("=" * 80)
print(f"RESUMO FINAL:")
print(f"Total de GAPs encontrados: {len(grupos)}")
print(f"Total de Ranchos encontrados: {total_ranchos}")
print("=" * 80)
