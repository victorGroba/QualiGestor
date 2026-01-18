from app import create_app, db
from app.models import Grupo, Avaliado, Usuario, AplicacaoQuestionario, RespostaPergunta

app = create_app()
app.app_context().push()

print("--- INICIANDO ATUALIZAÇÃO HIERÁRQUICA V3 (29 GAPs/OMs -> 60 RANCHOS) ---")

# 1. Identificar o Cliente
user = Usuario.query.filter_by(email='ti@labmattos.com.br').first()
if user:
    cid = user.cliente_id
    print(f"-> Cliente identificado: {user.nome} (ID: {cid})")
else:
    cid = 2
    print(f"-> AVISO: Usuário não encontrado. Usando Cliente ID padrão: {cid}")

# 2. LIMPEZA PROFUNDA (Necessária para corrigir a estrutura)
print("-> Iniciando limpeza de dados vinculados...")

# A. Desvincular Usuários
usuarios = Usuario.query.filter_by(cliente_id=cid).all()
for u in usuarios:
    u.grupo_id = None
    u.avaliado_id = None
db.session.commit()

# B. Apagar Aplicações e Respostas antigas
avaliados_ids = [a.id for a in Avaliado.query.filter_by(cliente_id=cid).all()]
if avaliados_ids:
    aplicacoes = AplicacaoQuestionario.query.filter(AplicacaoQuestionario.avaliado_id.in_(avaliados_ids)).all()
    for app_q in aplicacoes:
        RespostaPergunta.query.filter_by(aplicacao_id=app_q.id).delete()
        db.session.delete(app_q)
    db.session.commit()

# C. Apagar Ranchos e Grupos antigos
Avaliado.query.filter_by(cliente_id=cid).delete()
Grupo.query.filter_by(cliente_id=cid).delete()
db.session.commit()

# 3. ESTRUTURA DE DADOS FINAL (Baseada no PDF Anexo IV)
# Formato: "NOME DO GRUPO": [ (Nome Rancho, Endereço, Cidade, UF) ]

estrutura_pdf = {
    # --- GAPs (AGRUPADORES) ---
    
    "GAP-RJ — Grupamento de Apoio do Rio de Janeiro": [
        ("Rancho HCA", "Rua Barão de Itapagipe, 167 - Rio Comprido", "Rio de Janeiro", "RJ"),
        ("Rancho GAP-RJ (DECEA)", "Praça Marechal Âncora, 77 – Castelo", "Rio de Janeiro", "RJ"),
        ("Rancho PAME-RJ", "Rua General Gurjão, 4 – Caju", "Rio de Janeiro", "RJ"),
        ("Rancho DIRAD", "Rua Coronel Laurênio Lago, S/N - Marechal Hermes", "Rio de Janeiro", "RJ")
    ],

    "GAP-AF — Grupamento de Apoio dos Afonsos": [
        ("Rancho BAAF", "Av. Marechal Fontenelle, 1000 - Campo dos Afonsos", "Rio de Janeiro", "RJ"),
        ("Rancho CPA dos Afonsos", "Av. Mal. Fontenelle, 1000 - Campo dos Afonsos", "Rio de Janeiro", "RJ"),
        ("Rancho HAAF", "Av. Marechal Fontenelle, n°1000 - Campo dos Afonsos", "Rio de Janeiro", "RJ"),
        ("Rancho UNIFA", "Av. Marechal Fontenelle, 1000 - Campo dos Afonsos", "Rio de Janeiro", "RJ")
    ],

    "GAP-GL — Grupamento de Apoio do Galeão": [
        ("Rancho GAP-GL", "Estrada do Galeão, S/N - Galeão", "Rio de Janeiro", "RJ"),
        ("Rancho CGABEG", "Rua Major Aviador Carlos Biavati S/Nº - Praça do Avião", "Rio de Janeiro", "RJ"),
        ("Rancho HFAG", "Estrada do Galeão 4101 - Ilha do Governador", "Rio de Janeiro", "RJ"),
        ("Rancho CEMAL", "Estrada do Galeão, 3737 - Galeão", "Rio de Janeiro", "RJ"),
        ("Rancho PAMB", "Estrada do Galeão, 4.700 - Ilha do Governador", "Rio de Janeiro", "RJ")
    ],

    "GAP-SP — Grupamento de Apoio de São Paulo": [
        ("Rancho BASP", "Av. Monteiro Lobato, 6335 - Guarulhos", "Guarulhos", "SP"),
        ("Rancho PAMA-SP", "Avenida Braz Leme, 3258 - Santana", "São Paulo", "SP"),
        ("Rancho GAP-SP", "Av. Olavo Fontoura, 1300 - Santana", "São Paulo", "SP"),
        ("Rancho HFASP", "Av. Olavo Fontoura, 1400 - Santana", "São Paulo", "SP"),
        ("Rancho BAST", "Av. Presidente Castelo Branco, s/n°", "Guarujá", "SP"),
        ("Rancho COMGAP", "Av. Dom Pedro I, 100 - Cambuci", "São Paulo", "SP")
    ],

    "GAP-SJ — Grupamento de Apoio de São José dos Campos": [
        ("Rancho IEAV", "Trevo Cel. Av. José Alberto Albano do Amarante, 1 - Putim", "São José dos Campos", "SP"),
        ("Rancho GAP-SJ", "Praça Marechal do Ar Eduardo Gomes, nº 50", "São José dos Campos", "SP")
    ],

    "GAP-LS — Grupamento de Apoio de Lagoa Santa": [
        ("Rancho GAP-LS", "Av. Brigadeiro Eduardo Gomes s/nº - Vila Asas", "Lagoa Santa", "MG"),
        ("Rancho Esquadrão de Saúde", "Av. Brigadeiro Eduardo Gomes s/nº - Vila Asas", "Lagoa Santa", "MG")
    ],

    "GAP-CO — Grupamento de Apoio de Canoas": [
        ("Rancho BACO", "Rua Augusto Severo, nº 1700 - N. Sra. das Graças", "Canoas", "RS"),
        ("Rancho GAP-CO", "Av. Guilherme Schell, 3950 - Fátima", "Canoas", "RS"),
        ("Rancho HACO (Vila Ícaro)", "Av. A, nº 100 - Vila Ícaro", "Canoas", "RS")
    ],

    "GAP-BE — Grupamento de Apoio de Belém": [
        ("Rancho BABE", "Rod Arthur Bernardes S/N – Val-de-Cans", "Belém", "PA"),
        ("Rancho GAP-BE", "Av. Júlio César, s/n° - Souza", "Belém", "PA"),
        ("Rancho HABE", "Av. Almirante Barroso 3492 - Souza", "Belém", "PA"),
        ("Rancho COMARA", "Av. Pedro Alvares Cabral, 7115", "Belém", "PA")
    ],

    "GAP-MN — Grupamento de Apoio de Manaus": [
        ("Rancho DACO-MN", "Rua Guama, 1 - Colônia Oliveira Machado", "Manaus", "AM"),
        ("Rancho GAP-MN (BAMN)", "Avenida Rodrigo Otávio, 430 - Crespo", "Manaus", "AM"),
        ("Rancho HAMN", "Av. do Contorno, 780 - Crespo", "Manaus", "AM")
    ],

    "GAP-RF — Grupamento de Apoio de Recife": [
        ("Rancho GAP-RF", "Av. Armindo Moura, 500 - Boa Viagem", "Recife", "PE"),
        ("Rancho HARF", "Av. Senador Sérgio Guerra, nº 606 - Piedade", "Recife", "PE")
    ],

    "GAP-DF — Grupamento de Apoio do Distrito Federal": [
        ("Rancho BABR", "Área Militar do Aeroporto Internacional", "Brasília", "DF"),
        ("Rancho HFAB", "Área Militar do Aeroporto - Lago Sul", "Brasília", "DF"),
        ("Rancho GAP-DF (VI COMAR)", "SHIS QI 05 - Área Especial 12 - Lago Sul", "Brasília", "DF"),
        ("Rancho GAP-BR", "Esplanada dos Ministérios Bloco M - Anexo A/B", "Brasília", "DF"),
        ("Rancho GABAER", "Esplanada dos Ministérios Bloco M - 8º Andar", "Brasília", "DF")
    ],
    
    "GAP-CG — Grupamento de Apoio de Campo Grande": [
        ("Rancho BACG", "Av. Duque de Caxias, 2905 - Santo Antônio", "Campo Grande", "MS")
    ],

    # --- OMs INDEPENDENTES (1 Grupo = 1 Rancho) ---

    "BASC — Base Aérea de Santa Cruz": [
        ("Rancho BASC", "Rua do Império, S/N° - Santa Cruz", "Rio de Janeiro", "RJ")
    ],

    "AFA — Academia da Força Aérea": [
        ("Rancho FAYS", "Rodovia Faria Lima, Km 07", "Pirassununga", "SP"),
        ("Rancho AFA", "Estrada de Aguaí, s/nº - Jd. Bandeirantes", "Pirassununga", "SP")
    ],

    "EEAR — Escola de Especialistas de Aeronáutica": [
        ("Rancho EEAR", "Av. Brig. Adhemar Lyrio, s/nº", "Guaratinguetá", "SP")
    ],

    "EPCAR — Escola Preparatória de Cadetes do Ar": [
        ("Rancho EPCAR", "Rua Santos Dumont, nº 149", "Barbacena", "MG")
    ],

    "CIAAR — Centro de Instrução e Adaptação": [
        ("Rancho CIAAR", "Av. Santa Rosa nº 10 - Pampulha", "Belo Horizonte", "MG")
    ],

    "BASM — Base Aérea de Santa Maria": [
        ("Rancho BASM", "Rodovia RSC 287, Km 240", "Santa Maria", "RS")
    ],

    "BAFL — Base Aérea de Florianópolis": [
        ("Rancho BAFL", "Av. Santos-Dumont, s/n° - Tapera", "Florianópolis", "SC")
    ],

    "CINDACTA II": [
        ("Rancho CINDACTA II", "Av. Pref. Erasto Gaertner, 1000 - Bacacheri", "Curitiba", "PR")
    ],

    "BABV — Base Aérea de Boa Vista": [
        ("Rancho BABV", "Rua Valdemar Bastos de Oliveira, 2990", "Boa Vista", "RR")
    ],

    "BAPV — Base Aérea de Porto Velho": [
        ("Rancho BAPV", "Avenida Lauro Sodré, s/n - Aeroporto", "Porto Velho", "RO")
    ],

    "CLA — Centro de Lançamento de Alcântara": [
        ("Rancho CLA", "Rod. MA-106 - Km 7", "Alcântara", "MA")
    ],

    "BAFZ — Base Aérea de Fortaleza": [
        ("Rancho BAFZ", "Av Borges de Melo, 205", "Fortaleza", "CE")
    ],

    "BANT — Base Aérea de Natal": [
        ("Rancho BANT", "Estrada da BANT s/n° - Emaús", "Parnamirim", "RN")
    ],

    "CLBI — Centro de Lançamento da Barreira do Inferno": [
        ("Rancho CLBI", "Rodovia RN 063 - Km 11", "Parnamirim", "RN")
    ],

    "CINDACTA III": [
        ("Rancho CINDACTA III", "Av. Maria Irene, s/n° - Jordão", "Recife", "PE")
    ],

    "BASV — Base Aérea de Salvador": [
        ("Rancho BASV", "Av. Tenente Frederico Gustavo dos Santos, s/nº", "Salvador", "BA"),
        ("Rancho CEMCOHA", "Av. Oceânica - Ondina", "Salvador", "BA")
    ],

    "BAAN — Base Aérea de Anápolis": [
        ("Rancho BAAN", "BR 414 KM 4 - Zona Rural", "Anápolis", "GO")
    ]
}

# 4. EXECUÇÃO DA INSERÇÃO
count_grupos = 0
count_ranchos = 0

print(f"-> Inserindo {len(estrutura_pdf)} Grupos (OMs) e seus Ranchos...")

for nome_grupo, lista_ranchos in estrutura_pdf.items():
    # Cria o Grupo
    gap = Grupo(nome=nome_grupo, cliente_id=cid, ativo=True)
    db.session.add(gap)
    db.session.flush()
    count_grupos += 1
    
    # Cria os Ranchos
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

db.session.commit()

print("="*50)
print("ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
print(f"Total de Grupos (GAPs/OMs): {count_grupos}")
print(f"Total de Ranchos (Unidades): {count_ranchos}")
print("="*50)
