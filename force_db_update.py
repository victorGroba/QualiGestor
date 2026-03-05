import os
import sys

# Garante que o diretório root do projeto está no sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import PlanilhaVisita, AplicacaoQuestionario, Treinamento, TreinamentoParticipante
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

app = create_app()

def add_column_if_not_exists(table_name, column_name, column_type):
    try:
        with db.engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            conn.commit()
            print(f"Coluna {column_name} adicionada na tabela {table_name}.")
    except Exception as e:
        if "already exists" in str(e) or "Duplicate column name" in str(e):
            print(f"Coluna {column_name} já existe na tabela {table_name}.")
        else:
            print(f"Erro ao adicionar {column_name}: {e}")

with app.app_context():
    print("Criando tabelas que não existem (ex: planilha_visita, treinamento, treinamento_participante)...")
    db.create_all()
    print("Tabelas verificadas/criadas.")

    print("\nAdicionando colunas de arquivos na aplicacao_questionario...")
    novas_colunas = [
        # Antigas/Legado
        ('fluxograma_arquivo', 'VARCHAR(255)'),
        ('relatorio_mensal_arquivo', 'VARCHAR(255)'),
        ('laudo_laboratorio_arquivo', 'VARCHAR(255)'),
        ('laudo_materia_prima_arquivo', 'VARCHAR(255)'),
        ('checklist_arquivo', 'VARCHAR(255)'),
        ('acao_corretiva_arquivo', 'VARCHAR(255)'),
        # Novas - Laudos
        ('laudo_alimentos_arquivo', 'VARCHAR(255)'),
        ('laudo_ambiental_arquivo', 'VARCHAR(255)'),
        ('laudo_materia_prima_micro_arquivo', 'VARCHAR(255)'),
        ('laudo_materia_prima_fq_arquivo', 'VARCHAR(255)'),
        # Novas - SDAB/Doc
        ('relatorio_monitoramento_arquivo', 'VARCHAR(255)'),
        ('avaliacao_cardapio_arquivo', 'VARCHAR(255)'),
        ('ordem_servico_1_arquivo', 'VARCHAR(255)'),
        ('ordem_servico_2_arquivo', 'VARCHAR(255)'),
        ('plano_capacitacao_arquivo', 'VARCHAR(255)'),
        ('manual_boas_praticas_arquivo', 'VARCHAR(255)')
    ]

    for col_name, col_type in novas_colunas:
        add_column_if_not_exists('aplicacao_questionario', col_name, col_type)

    print("\nProcesso finalizado!")
