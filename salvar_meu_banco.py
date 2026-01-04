import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join('instance', 'banco.db')

print(f"🔌 Conectando ao banco em: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Tenta adicionar a coluna nova na tabela 'pergunta'
    try:
        print("🛠️  Tentando adicionar coluna 'criterio_foto'...")
        cursor.execute("ALTER TABLE pergunta ADD COLUMN criterio_foto VARCHAR(20) DEFAULT 'nenhuma'")
        print("✅ Coluna 'criterio_foto' adicionada com sucesso!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️  A coluna 'criterio_foto' já existe. Ignorando.")
        else:
            print(f"❌ Erro ao adicionar coluna: {e}")

    # 2. Limpa a tabela de controle de versão (alembic_version)
    # Isso remove o erro "Can't locate revision..."
    try:
        print("🧹 Limpando histórico de versão bugado...")
        cursor.execute("DROP TABLE IF EXISTS alembic_version")
        print("✅ Histórico de versão resetado. O banco está livre!")
    except Exception as e:
        print(f"❌ Erro ao limpar versão: {e}")

    conn.commit()
    conn.close()
    print("\n🎉 PROCEDIMENTO CONCLUÍDO! Seus dados foram preservados.")

except Exception as e:
    print(f"\n❌ Erro geral ao acessar o banco: {e}")