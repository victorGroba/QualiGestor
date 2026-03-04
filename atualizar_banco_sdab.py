import os
from app import create_app, db
from app.models import Treinamento, TreinamentoParticipante, PlanilhaVisita, AcaoCorretiva
from sqlalchemy import text

app = create_app()

def atualizar():
    with app.app_context():
        print("--- Iniciando Atualização de Banco (SDAB) ---")
        
        # 1. Criar novas tabelas (Safe)
        try:
            db.create_all()
            print("[OK] Novas tabelas criadas (se não existiam).")
        except Exception as e:
            print(f"[ERRO] Falha ao criar tabelas: {e}")

        # 2. Adicionar colunas faltantes em aplicacao_questionario
        colunas = [
            ("laudo_alimentos_arquivo", "VARCHAR(255)"),
            ("laudo_ambiental_arquivo", "VARCHAR(255)"),
            ("laudo_materia_prima_arquivo", "VARCHAR(255)"),
            ("checklist_arquivo", "VARCHAR(255)"),
            ("acao_corretiva_arquivo", "VARCHAR(255)"),
            ("manual_boas_praticas_arquivo", "VARCHAR(255)")
        ]

        for nome, tipo in colunas:
            try:
                # PostgreSQL ALTER TABLE
                db.session.execute(text(f"ALTER TABLE aplicacao_questionario ADD COLUMN {nome} {tipo};"))
                db.session.commit()
                print(f"[OK] Coluna {nome} adicionada.")
            except Exception as e:
                db.session.rollback()
                if "already exists" in str(e).lower() or "duplicada" in str(e).lower():
                    print(f"[INFO] Coluna {nome} já existe.")
                else:
                    print(f"[ERRO] Falha ao adicionar {nome}: {e}")

        print("--- Atualização Concluída ---")

if __name__ == "__main__":
    atualizar()
