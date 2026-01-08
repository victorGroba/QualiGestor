# criar_estrutura_fab.py
from app import create_app, db
from app.models import Cliente, Grupo, Avaliado

app = create_app()

def popular_fab():
    with app.app_context():
        print(">>> Iniciando Carga de Dados da FAB...")

        # 1. Verifica/Cria Cliente FAB
        # Procura por 'Aeronáutica' ou cria se não existir
        cliente = Cliente.query.filter(Cliente.nome.ilike('%Aeronáutica%')).first()
        if not cliente:
            cliente = Cliente(nome="Aeronáutica (FAB)", razao_social="Comando da Aeronáutica", email="sdab@fab.mil.br")
            db.session.add(cliente)
            db.session.commit()
            print("  [+] Cliente 'Aeronáutica (FAB)' criado.")
        else:
            print(f"  [i] Cliente '{cliente.nome}' já existe (ID: {cliente.id}).")

        # DADOS EXTRAÍDOS DO PDF (OM APOIADORA -> RANCHO)
        estrutura = {
            "GAP-RJ": [
                {"nome": "Hospital Central da Aeronáutica - HCA", "codigo": "HCA", "endereco": "Rua Barão de Itapagipe, 167 - Rio Comprido, RJ"},
                {"nome": "GAP-RJ (DECEA)", "codigo": "GAPRJ", "endereco": "Praça Marechal Ancora, 77 - Castelo, RJ"},
                {"nome": "Parque de Material Eletrônico - PAME-RJ", "codigo": "PAMERJ", "endereco": "Rua General Gurjão, 4 - Caju, RJ"},
                {"nome": "Diretoria de Administração - DIRAD", "codigo": "DIRAD", "endereco": "Rua Coronel Laurênio Lago, S/N - Marechal Hermes, RJ"},
                {"nome": "Base Aérea dos Afonsos - BAAF", "codigo": "BAAF", "endereco": "Av. Marechal Fontenelle, 1000 - Campo dos Afonsos, RJ"},
                {"nome": "Central de Produção de Alimentação - CPA Afonsos", "codigo": "CPA", "endereco": "Av. Mal. Fontenelle, 1000 - Campo dos Afonsos, RJ"},
            ],
            "GAP-DF": [
                {"nome": "Hospital de Força Aérea de Brasília - HFAB", "codigo": "HFAB", "endereco": "Área Militar do Aeroporto - Lago Sul, DF"},
                {"nome": "GAP-DF / VI COMAR", "codigo": "GAPDF", "endereco": "SHIS QI 05 - Área Especial 12 - Lago Sul, DF"},
            ],
            "GAP-BR": [
                {"nome": "GAP-BR / GABAER", "codigo": "GAPBR", "endereco": "Esplanada dos Ministérios Bloco M, DF"},
                {"nome": "Base Aérea de Brasília - BABR", "codigo": "BABR", "endereco": "Área Militar do Aeroporto Internacional de Brasília, DF"},
            ],
            "GAP-RF (Recife)": [
                {"nome": "Hospital de Aeronáutica de Recife - HARF", "codigo": "HARF", "endereco": "Av. Senador Sérgio Guerra, 606 - Piedade, PE"},
            ],
            "GAP-SV (Salvador)": [
                {"nome": "Base Aérea de Salvador - BASV", "codigo": "BASV", "endereco": "Av. Tenente Frederico Gustavo dos Santos, s/n - Salvador, BA"},
                {"nome": "CEMSONA - Centro Militar de Convenções", "codigo": "CEMSONA", "endereco": "Av. Oceânica Ondina - Salvador, BA"},
            ]
        }

        # 2. Cria GAPs e Ranchos
        for nome_gap, ranchos in estrutura.items():
            # Tenta encontrar o GAP pelo nome e cliente
            gap = Grupo.query.filter_by(nome=nome_gap, cliente_id=cliente.id).first()
            
            if not gap:
                gap = Grupo(nome=nome_gap, descricao=f"Grupamento de Apoio - {nome_gap}", cliente_id=cliente.id, ativo=True)
                db.session.add(gap)
                db.session.flush() # Garante que o GAP ganhe um ID antes de prosseguir
                print(f"  [+] GAP criado: {nome_gap}")
            else:
                print(f"  [i] GAP existente: {nome_gap}")

            for r_data in ranchos:
                # Tenta encontrar o Rancho (Avaliado)
                rancho = Avaliado.query.filter_by(nome=r_data['nome'], cliente_id=cliente.id).first()
                
                if not rancho:
                    rancho = Avaliado(
                        nome=r_data['nome'],
                        codigo=r_data['codigo'],
                        endereco=r_data['endereco'],
                        grupo_id=gap.id, # Vincula ao ID do GAP
                        cliente_id=cliente.id,
                        ativo=True
                    )
                    db.session.add(rancho)
                    print(f"    -> Rancho criado: {r_data['codigo']}")
                else:
                    # Se já existe, atualiza o vínculo do GAP se estiver errado
                    if rancho.grupo_id != gap.id:
                        rancho.grupo_id = gap.id
                        print(f"    -> ATUALIZADO: Rancho {r_data['codigo']} movido para {nome_gap}")

        db.session.commit()
        print(">>> Carga Completa! Todos os GAPs e Ranchos foram cadastrados.")

if __name__ == "__main__":
    popular_fab()