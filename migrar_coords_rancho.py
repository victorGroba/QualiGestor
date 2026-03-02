import os
import sys

# Adiciona o diretório atual ao path para poder importar o app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app import create_app, db
from app.models import Avaliado
from sqlalchemy import text

app = create_app()

with app.app_context():
    # 1. Tentar adicionar as colunas diretamente usando SQL puro pra evitar problemas de migração bloqueada
    print("Verificando colunas latitude/longitude em Avaliado...")
    try:
        db.session.execute(text('ALTER TABLE avaliado ADD COLUMN latitude VARCHAR(50);'))
        db.session.execute(text('ALTER TABLE avaliado ADD COLUMN longitude VARCHAR(50);'))
        db.session.commit()
        print("-> Colunas criadas com sucesso no PostgreSQL.")
    except Exception as e:
        db.session.rollback()
        print("-> Colunas ja existem ou ocorreu um erro (isso é normal se ja rodou antes):", e)

    # 2. Popular os dados existentes com um valor default só pra não quebrar (opcional)
    avaliados_sem_coord = Avaliado.query.filter((Avaliado.latitude == None) | (Avaliado.latitude == '')).all()
    
    print(f"\nEncontrados {len(avaliados_sem_coord)} avaliados sem coordenadas.")
    
    # Exemplo: Seta pro centro do BR temporariamente '-15.7801, -47.9292' (Brasilia) se estiver vazio apenas pra teste do mapa
    for avaliado in avaliados_sem_coord:
        avaliado.latitude = '-15.7801'
        avaliado.longitude = '-47.9292'
        
    db.session.commit()
    print("-> Coordenadas iniciais preenchidas (Centro do BR) para ranchos existentes.")
