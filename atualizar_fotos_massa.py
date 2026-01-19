import sys
from app import create_app, db
from app.models import Questionario, Pergunta, Topico

# Cria a aplicação para acessar o banco de dados
app = create_app()

def atualizar_fotos_para_opcional(nome_questionario):
    with app.app_context():
        print(f"--- Iniciando atualização para: '{nome_questionario}' ---")
        
        # 1. Busca o questionário pelo nome (ou parte dele)
        questionario = Questionario.query.filter(
            Questionario.nome.ilike(f"%{nome_questionario}%")
        ).first()
        
        if not questionario:
            print(f"❌ ERRO: Questionário contendo '{nome_questionario}' não encontrado.")
            return

        print(f"✅ Questionário encontrado: {questionario.nome} (ID: {questionario.id})")
        
        # 2. Busca todas as perguntas desse questionário
        perguntas = Pergunta.query.join(Topico).filter(
            Topico.questionario_id == questionario.id,
            Pergunta.ativo == True
        ).all()
        
        total = len(perguntas)
        print(f"📋 Total de perguntas encontradas: {total}")
        
        if total == 0:
            print("Nenhuma pergunta ativa encontrada para atualizar.")
            return

        # 3. Atualiza o campo criterio_foto
        count_atualizadas = 0
        for p in perguntas:
            # Só atualiza se for diferente para evitar writes desnecessários
            if p.criterio_foto != 'opcional':
                p.criterio_foto = 'opcional'
                count_atualizadas += 1
        
        # 4. Salva no banco
        try:
            db.session.commit()
            print(f"🚀 SUCESSO! {count_atualizadas} perguntas foram atualizadas para 'Foto Opcional'.")
            print(f"Obs: {total - count_atualizadas} perguntas já estavam configuradas corretamente.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar no banco: {str(e)}")

if __name__ == "__main__":
    # Nome exato ou parte única do nome do seu checklist
    NOME_DO_CHECKLIST = "Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026"
    
    # CORREÇÃO AQUI: Chamando a função com o nome correto
    atualizar_fotos_para_opcional(NOME_DO_CHECKLIST)
