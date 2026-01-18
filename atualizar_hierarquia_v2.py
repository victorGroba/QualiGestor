from app import create_app, db
from app.models import Grupo, Avaliado, Usuario, AplicacaoQuestionario, RespostaPergunta

app = create_app()
app.app_context().push()

print("--- INICIANDO ATUALIZAÇÃO HIERÁRQUICA V2 (LIMPEZA PROFUNDA) ---")

# 1. Identificar o Cliente
user = Usuario.query.filter_by(email='ti@labmattos.com.br').first()
if user:
    cid = user.cliente_id
    print(f"-> Cliente identificado: {user.nome} (ID: {cid})")
else:
    cid = 2
    print(f"-> AVISO: Usuário não encontrado. Usando Cliente ID padrão: {cid}")

# 2. LIMPEZA TOTAL DE DEPENDÊNCIAS
print("-> Iniciando limpeza de dados vinculados...")

# A. Desvincular Usuários (para não travar a exclusão dos Ranchos)
print("   ... Desvinculando usuários de GAPs/Ranchos antigos")
usuarios = Usuario.query.filter_by(cliente_id=cid).all()
for u in usuarios:
    u.grupo_id = None
    u.avaliado_id = None
db.session.commit()

# B. Apagar Aplicações e Respostas (O motivo do seu erro)
print("   ... Apagando histórico de aplicações antigas (necessário para recriar a estrutura)")
# Primeiro, pegamos todos os IDs de avaliados deste cliente
avaliados_ids = [a.id for a in Avaliado.query.filter_by(cliente_id=cid).all()]

if avaliados_ids:
    # Busca aplicações vinculadas a esses avaliados
    aplicacoes = AplicacaoQuestionario.query.filter(AplicacaoQuestionario.avaliado_id.in_(avaliados_ids)).all()
    for app_q in aplicacoes:
        # Apagar respostas vinculadas (se o cascade não estiver automático)
        RespostaPergunta.query.filter_by(aplicacao_id=app_q.id).delete()
        db.session.delete(app_q)
    db.session.commit()

# C. Agora sim, apagar Ranchos e Grupos
print("   ... Apagando Ranchos e Grupos antigos")
Avaliado.query.filter_by(cliente_id=cid).delete()
Grupo.query.filter_by(cliente_id=cid).delete()
db.session.commit()

# 3. ESTRUTURA DE DADOS COMPLETA
dados_sistema = {
    "GAP-RJ — Grupamento de Apoio do Rio de Janeiro": [
        ("Rancho Castelo", "Praça Marechal Âncora, 77 – Castelo", "Rio de Janeiro", "RJ"),
        ("Rancho Afonsos", "Av. Marechal Fontenelle, 1000 – Campo dos Afonsos", "Rio de Janeiro", "RJ")
    ],
    "GAP-GL — Grupamento de Apoio do Galeão": [
        ("Rancho Galeão", "Estrada do Galeão, s/n – Galeão", "Rio de Janeiro", "RJ"),
        ("HFAG", "Estrada do Galeão, 4101 – Ilha do Governador", "Rio de Janeiro", "RJ"),
        ("CEMAL", "Estrada do Galeão, 3737 – Galeão", "Rio de Janeiro", "RJ"),
        ("PAMB", "Estrada do Galeão, 4700 – Ilha do Governador", "Rio de Janeiro", "RJ"),
        ("CGABEG", "Praça do Avião – Galeão", "Rio de Janeiro", "RJ")
    ],
    "GAP-AF — Grupamento de Apoio dos Afonsos": [
        ("Rancho Afonsos (GAP-AF)", "Av. Marechal Fontenelle, 1000 – Campo dos Afonsos", "Rio de Janeiro", "RJ"),
        ("CPA - Central de Produção", "Campo dos Afonsos", "Rio de Janeiro", "RJ"),
        ("UNIFA", "Campo dos Afonsos", "Rio de Janeiro", "RJ"),
        ("HAAF - Hospital dos Afonsos", "Campo dos Afonsos", "Rio de Janeiro", "RJ")
    ],
    "GAP-SP — Grupamento de Apoio de São Paulo": [
        ("Rancho GAP-SP (Santana)", "Av. Olavo Fontoura, 1300 – Santana", "São Paulo", "SP"),
        ("PAMA-SP", "Av. Braz Leme, 3258 – Santana", "São Paulo", "SP"),
        ("Rancho Cambuci", "Av. Dom Pedro I, 100 – Cambuci", "São Paulo", "SP"),
        ("BASP / GRU Airport", "Av. Monteiro Lobato, 6335 – Guarulhos", "Guarulhos", "SP")
    ],
    "GAP-SJ — Grupamento de Apoio de São José dos Campos": [
        ("Rancho GAP-SJ", "Praça Mal. do Ar Eduardo Gomes, 50", "São José dos Campos", "SP"),
        ("IEAV", "Putim", "São José dos Campos", "SP")
    ],
    "GAP-LS — Grupamento de Apoio de Lagoa Santa": [
        ("Rancho GAP-LS", "Av. Brigadeiro Eduardo Gomes, s/n", "Lagoa Santa", "MG"),
        ("Esquadrão de Saúde GAP-LS", "Lagoa Santa", "Lagoa Santa", "MG")
    ],
    "GAP-CO — Grupamento de Apoio de Canoas": [
        ("Rancho Augusto Severo", "Rua Augusto Severo, 1700", "Canoas", "RS"),
        ("Rancho Guilherme Schell", "Av. Guilherme Schell, 3950", "Canoas", "RS"),
        ("Rancho Vila Ícaro", "Av. A, nº 100 – Vila Ícaro", "Canoas", "RS"),
        ("BACO - Base Aérea", "Canoas", "Canoas", "RS"),
        ("HACO - Hospital de Canoas", "Canoas", "Canoas", "RS")
    ],
    "GAP-BE — Grupamento de Apoio de Belém": [
        ("Rancho Júlio César", "Av. Júlio César, s/n", "Belém", "PA"),
        ("Rancho Almirante Barroso", "Av. Almirante Barroso, 3492", "Belém", "PA"),
        ("COMARA", "Av. Pedro Álvares Cabral, 7115", "Belém", "PA")
    ],
    "GAP-MN — Grupamento de Apoio de Manaus": [
        ("Rancho Rodrigo Otávio", "Av. Rodrigo Otávio, 430", "Manaus", "AM"),
        ("HAMN - Hospital de Manaus", "Av. Rodrigo Otávio, 430", "Manaus", "AM"),
        ("DACO-MN", "Rua Guamá, 1", "Manaus", "AM")
    ],
    "GAP-RF — Grupamento de Apoio de Recife": [
        ("Rancho GAP-RF", "Av. Armindo Moura, 500", "Recife", "PE"),
        ("HARF - Hospital de Recife", "Av. Armindo Moura, 500", "Recife", "PE")
    ],
    "GAP-DF — Grupamento de Apoio do Distrito Federal": [
        ("Rancho Lago Sul", "SHIS QI 05 – Área Especial 12 – Lago Sul", "Brasília", "DF"),
        ("Rancho Ministérios", "Esplanada dos Ministérios – Bloco M", "Brasília", "DF"),
        ("HFAB", "Área Militar do Aeroporto", "Brasília", "DF"),
        ("BABR - Base Aérea", "Área Militar do Aeroporto", "Brasília", "DF"),
        ("GABAER", "Esplanada dos Ministérios", "Brasília", "DF")
    ]
}

demais_oms = [
    ("EPCAR", "Rua Santos Dumont, 149", "Barbacena", "MG"),
    ("CIAAR", "Av. Santa Rosa, 10", "Belo Horizonte", "MG"),
    ("AFA", "Estrada de Aguaí, s/n", "Pirassununga", "SP"),
    ("FAYS", "Rod. Faria Lima, Km 7", "Pirassununga", "SP"),
    ("BASM", "Rod. RSC 287, Km 240", "Santa Maria", "RS"),
    ("BAFL", "Av. Santos Dumont, s/n", "Florianópolis", "SC"),
    ("CINDACTA II", "Av. Pref. Erasto Gaertner, 1000", "Curitiba", "PR"),
    ("CINDACTA III", "Av. Maria Irene, s/n", "Recife", "PE"),
    ("CLA", "Rod. MA-106, Km 7", "Alcântara", "MA"),
    ("BAFZ", "Av. Borges de Melo, 205", "Fortaleza", "CE"),
    ("BANT", "Estrada da BANT, s/n", "Parnamirim", "RN"),
    ("CLBI", "Rod. RN-063, Km 11", "Parnamirim", "RN"),
    ("BASV", "Aeroporto Luís Eduardo Magalhães", "Salvador", "BA"),
    ("BAAN", "BR-414 Km 4", "Anápolis", "GO"),
    ("BABV", "Rua Valdemar Ferreira da Silva, s/n", "Boa Vista", "RR"),
    ("BAPV", "Av. Lauro Sodré, s/n", "Porto Velho", "RO")
]

# 4. EXECUÇÃO DA INSERÇÃO
count_grupos = 0
count_ranchos = 0

print("-> Inserindo nova hierarquia...")

# GAPs
for nome_grupo, lista_ranchos in dados_sistema.items():
    gap = Grupo(nome=nome_grupo, cliente_id=cid, ativo=True)
    db.session.add(gap)
    db.session.flush()
    count_grupos += 1
    
    for r_nome, r_end, r_cid, r_uf in lista_ranchos:
        rancho = Avaliado(
            nome=r_nome,
            grupo_id=gap.id,
            cliente_id=cid,
            ativo=True,
            endereco=r_end,
            cidade=r_cid,
            estado=r_uf
        )
        db.session.add(rancho)
        count_ranchos += 1

# OMs Individuais
for om_nome, om_end, om_cid, om_uf in demais_oms:
    grupo_om = Grupo(nome=om_nome, cliente_id=cid, ativo=True)
    db.session.add(grupo_om)
    db.session.flush()
    count_grupos += 1
    
    rancho_om = Avaliado(
        nome=om_nome,
        grupo_id=grupo_om.id,
        cliente_id=cid,
        ativo=True,
        endereco=om_end,
        cidade=om_cid,
        estado=om_uf
    )
    db.session.add(rancho_om)
    count_ranchos += 1

db.session.commit()

print("="*50)
print("ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
print(f"Total de Grupos: {count_grupos}")
print(f"Total de Ranchos: {count_ranchos}")
print("="*50)
