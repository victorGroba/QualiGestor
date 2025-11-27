"""Adiciona CategoriaIndicador e relacionamento em Topico

Revision ID: ff50cdf223c6
Revises: cc3cd0a152fa
Create Date: 2025-11-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'ff50cdf223c6'
down_revision = 'cc3cd0a152fa'
branch_labels = None
depends_on = None


def upgrade():
    # Verifica se a tabela ja existe antes de tentar criar
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'categoria_indicador' not in tables:
        op.create_table('categoria_indicador',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('nome', sa.String(length=100), nullable=False),
            sa.Column('ordem', sa.Integer(), nullable=True),
            sa.Column('cor', sa.String(length=7), nullable=True),
            sa.Column('ativo', sa.Boolean(), nullable=True),
            sa.Column('cliente_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name='fk_categoria_indicador_cliente_id'),
            sa.PrimaryKeyConstraint('id')
        )

    # 2. Adiciona a coluna e a Foreign Key na tabela topico
    # Como a tabela topico ja existia, o create_all geralmente nao adiciona colunas novas,
    # entao esse passo e necessario.
    try:
        with op.batch_alter_table('topico', schema=None) as batch_op:
            batch_op.add_column(sa.Column('categoria_indicador_id', sa.Integer(), nullable=True))
            
            batch_op.create_foreign_key(
                'fk_topico_categoria_indicador',  # Nome da constraint
                'categoria_indicador',            # Tabela referenciada
                ['categoria_indicador_id'],       # Coluna local
                ['id']                            # Coluna remota
            )
    except Exception as e:
        # Se a coluna ja existir (caso raro), apenas imprime o aviso e segue
        if 'duplicate column name' in str(e):
            print("Aviso: Coluna categoria_indicador_id ja existia em Topico.")
        else:
            raise e


def downgrade():
    # Reverte as mudanças
    with op.batch_alter_table('topico', schema=None) as batch_op:
        batch_op.drop_constraint('fk_topico_categoria_indicador', type_='foreignkey')
        batch_op.drop_column('categoria_indicador_id')

    # Nao removemos a tabela categoria_indicador no downgrade se ela ja existia antes,
    # mas para manter a consistencia da migracao, deixamos o drop condicional ou explicito.
    # Aqui vamos tentar remover:
    op.drop_table('categoria_indicador')