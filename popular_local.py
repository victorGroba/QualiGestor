# popular_local.py
import os
import sys
from pathlib import Path

# --- 1. CONFIGURAÇÃO FORÇADA PARA SQLITE LOCAL ---
# Obtém o diretório atual
basedir = Path(__file__).resolve().parent
# Caminho para o banco local
db_path = basedir / "instance" / "banco.db"
sqlite_uri = f"sqlite:///{db_path.as_posix()}"

# FORÇA a variável de ambiente ANTES de importar o app.
# Isso impede que o create_app() pegue a configuração do PostgreSQL do .env
os.environ["SQLALCHEMY_DATABASE_URI"] = sqlite_uri

print(f"--- MODO FORÇADO SQLITE ---")
print(f"Alvo: {sqlite_uri}")
print("-" * 30)

# Agora importamos o app (ele vai ler a variável que acabamos de definir)
try:
    from app import create_app, db
    from app.models import Cliente, Grupo, Avaliado
except ImportError as e:
    print("ERRO DE IMPORTAÇÃO: Verifique se está na raiz do projeto.")
    print(f"Detalhe: {e}")
    sys.exit(1)

app = create_app()

# Estrutura FAB (Mesma do script anterior)
ESTRUTURA_FAB = {
    "GAP-RJ (Rio de Janeiro)": [
        ("HCA - Hospital Central da Aeronáutica", "Rua Barão de Itapagipe, 167 - Rio Comprido"),
        ("GAP-RJ (DECEA)", "Praça Marechal Ancora, 77 - Castelo"),
        ("PAME-RJ", "Rua General Gurjão, 4 - Caju"),
        ("DIRAD", "Rua Coronel Laurênio Lago, S/N - Marechal Hermes")
    ],
    "GAP-AF (Afonsos)": [
        ("BAAF - Base Aérea dos Afonsos", "Av. Marechal Fontenelle, 1000"),
        ("CPA - Central de Produção de Alimentação", "Av. Mal. Fontenelle, 1000"),
        ("HAAF - Hospital de Aeronáutica dos Afonsos", "Av. Marechal Fontenelle, 1000"),
        ("UNIFA", "Av. Marechal Fontenelle, 1000")
    ],
    "GAP-GL (Galeão)": [
        ("GAP-GL (Base Aérea)", "Estrada do Galeão, S/N"),
        ("CGABEG - Casa Gerontológica", "Rua Major Aviador Carlos Biavati S/N"),
        ("HFAG - Hospital de Força Aérea do Galeão", "Estrada do Galeão 4101"),
        ("CEMAL", "Estrada do Galeão, 3737"),
        ("PAMB - Parque de Material Bélico", "Estrada do Galeão, 4.700")
    ],
    "GAP-SC (Santa Cruz)": [
        ("BASC - Base Aérea de Santa Cruz", "Rua do Império, S/N, Santa Cruz")
    ],
    "GAP-SP (São Paulo)": [
        ("BASP - Base Aérea de São Paulo", "Av. Monteiro Lobato, 6335 - Guarulhos"),
        ("PAMA-SP", "Avenida Braz Leme, 3258 - Santana"),
        ("GAP-SP", "Av. Olavo Fontoura, 1300 - Santana"),
        ("HFASP", "Av. Olavo Fontoura, 1400 - Santana"),
        ("BAST - Base Aérea de Santos", "Av. Presidente Castelo Branco, s/n - Guarujá"),
        ("COMGAP", "Av. Dom Pedro I, 100 - Cambuci")
    ],
    "AFA (Pirassununga)": [
        ("AFA / FAYS", "Rodovia Faria Lima, Km 07 - Pirassununga")
    ],
    "GAP-SJ (São José dos Campos)": [
        ("EEAR", "Av. Brig. Adhemar Lyrio, s/n - Guaratinguetá"),
        ("IEAV / DCTA", "Trevo Cel Av José Alberto Albano - São José dos Campos"),
        ("GAP-SJ", "Praça Mal. Eduardo Gomes, 50 - Vila das Acácias")
    ],
    "EPCAR (Barbacena)": [
        ("EPCAR", "Rua Santos Dumont, 149 - Barbacena")
    ],
    "GAP-LS (Lagoa Santa)": [
        ("CIAAR", "Av. Santa Rosa 10 - Pampulha"),
        ("GAP-LS / PAMA-LS", "Av. Brig. Eduardo Gomes s/n - Vila Asas"),
        ("Esquadrão de Saúde GAP-LS", "Av. Brig. Eduardo Gomes s/n - Vila Asas")
    ],
    "GAP-SM (Santa Maria)": [
        ("BASM", "Rodovia RSC 287, Km 240 - Santa Maria")
    ],
    "GAP-CO (Canoas)": [
        ("BACO", "Rua Augusto Severo, 1700 - Canoas"),
        ("GAP-CO", "Av. Guilherme Schell, 3950 - Canoas"),
        ("HACO", "Av. A, 100 - Vila Icaro - Canoas")
    ],
    "GAP-FL (Florianópolis)": [
        ("BAFL", "Av. Santos-Dumont, s/n - Tapera")
    ],
    "CINDACTA II (Curitiba)": [
        ("CINDACTA II", "Av. Pref. Erasto Gaertner, 1000 - Bacacheri")
    ],
    "GAP-BE (Belém)": [
        ("BABE", "Rod Arthur Bernardes S/N - Val-de-Cans"),
        ("GAP-BE", "Av. Júlio César, s/n - Souza"),
        ("HABE", "Av. Almirante Barroso 3492 - Souza"),
        ("COMARA", "Av. Pedro Alvares Cabral, 7115")
    ],
    "GAP-MN (Manaus)": [
        ("DACO-MN", "Rua Guama, 1 - Colônia Oliveira Machado"),
        ("GAP-MN (BAMN)", "Avenida Rodrigo Otávio, 430 - Crespo"),
        ("HAMN", "Av. do Contorno, 780 - Crespo")
    ],
    "GAP-BV (Boa Vista)": [
        ("BABV", "Rua Valdemar Bastos de Oliveira, 2990 - Aeroporto")
    ],
    "GAP-PV (Porto Velho)": [
        ("BAPV", "Avenida Lauro Sodré, s/n - Aeroporto")
    ],
    "CLA (Alcântara)": [
        ("CLA - Centro de Lançamento", "ROD. MA-106 Km 7 - Alcântara")
    ],
    "GAP-FZ (Fortaleza)": [
        ("BAFZ", "Av Borges de Melo, 205 - Fortaleza")
    ],
    "GAP-NT (Natal)": [
        ("BANT", "Estrada da BANT s/n - Emaús"),
        ("CLBI", "Rodovia RN 063 Km 11 - Parnamirim")
    ],
    "GAP-RF (Recife)": [
        ("CINDACTA III", "Av. Maria Irene, s/n - Jordão"),
        ("GAP-RF", "Av. Armindo Moura, 500 - Boa Viagem"),
        ("HARF", "Av. Senador Sérgio Guerra, 606 - Piedade")
    ],
    "GAP-SV (Salvador)": [
        ("BASV", "Av. Ten. Frederico Gustavo dos Santos, s/n"),
        ("CEMCOHA", "Av. Oceânica - Ondina")
    ],
    "GAP-DF (Brasília)": [
        ("BABR", "Área Militar do Aeroporto Internacional"),
        ("HFAB", "Área Militar do Aeroporto Internacional"),
        ("GAP-DF / VI COMAR", "SHIS QI 05 - Lago Sul"),
        ("GAP-BR / GABAER", "Esplanada dos Ministérios Bloco M")
    ],
    "GAP-AN (Anápolis)": [
        ("BAAN", "BR 414 KM 4 - Anápolis")
    ],
    "GAP-CG (Campo Grande)": [
        ("BACG", "Av. Duque de Caxias, 2905")
    ]
}

def popular():
    with app.app_context():
        # Confirmação visual
        print(f"Conectado a: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Garante que as tabelas existem no SQLite
        db.create_all()
        print("Tabelas verificadas/criadas no SQLite.")

        # 1. Garante que existe o Cliente "FAB" ou "SDAB"
        cliente = Cliente.query.filter_by(nome="FAB - SDAB").first()
        if not cliente:
            cliente = Cliente(
                nome="FAB - SDAB",
                razao_social="Comando da Aeronáutica",
                email="sdab@fab.mil.br"
            )
            db.session.add(cliente)
            db.session.commit()
            print(f"-> Cliente FAB criado com ID: {cliente.id}")
        else:
            print(f"-> Cliente FAB já existe (ID: {cliente.id})")

        # 2. Loop para criar Grupos e Ranchos
        count_gaps = 0
        count_ranchos = 0

        for nome_gap, lista_ranchos in ESTRUTURA_FAB.items():
            # Busca GAP
            grupo = Grupo.query.filter_by(nome=nome_gap, cliente_id=cliente.id).first()
            if not grupo:
                grupo = Grupo(
                    nome=nome_gap,
                    descricao="Grupamento de Apoio",
                    cliente_id=cliente.id,
                    ativo=True
                )
                db.session.add(grupo)
                db.session.flush()
                count_gaps += 1
                print(f"   [Novo GAP] {nome_gap}")
            
            # Busca/Cria Ranchos
            for nome_rancho, endereco in lista_ranchos:
                avaliado = Avaliado.query.filter_by(
                    nome=nome_rancho, 
                    cliente_id=cliente.id
                ).first()
                
                if not avaliado:
                    avaliado = Avaliado(
                        nome=nome_rancho,
                        endereco=endereco,
                        grupo_id=grupo.id,
                        cliente_id=cliente.id,
                        ativo=True
                    )
                    db.session.add(avaliado)
                    count_ranchos += 1
                    print(f"      + Rancho criado: {nome_rancho}")
                else:
                    # Se já existe, garante o vínculo correto com o Grupo
                    if avaliado.grupo_id != grupo.id:
                        avaliado.grupo_id = grupo.id
                        print(f"      ~ Rancho atualizado (Grupo): {nome_rancho}")

        db.session.commit()
        print("\n=== RESUMO ===")
        print(f"GAPs Novos: {count_gaps}")
        print(f"Ranchos Novos: {count_ranchos}")
        print(f"Banco Populado: {db_path}")

if __name__ == "__main__":
    popular()