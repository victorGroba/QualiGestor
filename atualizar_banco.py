import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join('instance', 'banco.db')

if not os.path.exists(db_path):
    print(f"ERRO: Banco de dados não encontrado em {db_path}")
else:
    print(f"Conectando ao banco em: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Tenta adicionar a coluna 'avaliado_id' na tabela 'usuario'
        print("Tentando adicionar a coluna 'avaliado_id'...")
        cursor.execute("ALTER TABLE usuario ADD COLUMN avaliado_id INTEGER REFERENCES avaliado(id)")
        conn.commit()
        print("SUCESSO: Coluna 'avaliado_id' adicionada! Seus dados estão salvos.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("AVISO: A coluna 'avaliado_id' já existe. Nenhuma alteração necessária.")
        else:
            print(f"ERRO ao alterar o banco: {e}")
    finally:
        conn.close()