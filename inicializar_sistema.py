# inicializar_sistema.py - Script para inicializar sistema do zero
import os
import sys
from datetime import datetime, timedelta
import random
import traceback

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath('.'))

# Imports explícitos (sem wildcard)
from app import create_app, db
import app.models as models
from werkzeug.security import generate_password_hash

def inicializar_sistema():
    """Inicializa o sistema completo do zero"""
    
    print("🚀 INICIALIZANDO SISTEMA QUALIGESTOR")
    print("=" * 50)
    
    try:
        # 1. Criar app
        print("📦 Criando aplicação...")
        app = create_app()
        
        with app.app_context():
            
            # 2. Dropar todas as tabelas (se existirem)
            print("🗑️  Limpando banco de dados...")
            db.drop_all()
            
            # 3. Criar todas as tabelas
            print("🏗️  Criando estrutura do banco...")
            db.create_all()
            
            # 4. Criar cliente padrão
            print("🏢 Criando cliente padrão...")
            cliente_padrao = models.Cliente(
                nome='Empresa Padrão',
                razao_social='Empresa Padrão Ltda',
                email='contato@empresa.com',
                ativo=True
            )
            db.session.add(cliente_padrao)
            db.session.flush()
            
            # 5. Criar grupo padrão
            print("👥 Criando grupo padrão...")
            grupo_padrao = models.Grupo(
                nome='Grupo Padrão',
                descricao='Grupo padrão do sistema',
                cliente_id=cliente_padrao.id,
                ativo=True
            )
            db.session.add(grupo_padrao)
            db.session.flush()
            
            # 6. Criar usuário admin
            print("👤 Criando usuário administrador...")
            admin = models.Usuario(
                nome='Administrador',
                email='admin@admin.com',
                senha_hash=generate_password_hash('admin123'),
                tipo=models.TipoUsuario.ADMIN,
                cliente_id=cliente_padrao.id,
                grupo_id=grupo_padrao.id,
                ativo=True
            )
            db.session.add(admin)
            db.session.flush()
            
            # 7. Criar avaliados de exemplo
            print("🏪 Criando avaliados de exemplo...")
            avaliados_exemplo = [
                models.Avaliado(
                    nome='Loja Centro',
                    codigo='LC001',
                    endereco='Rua das Flores, 123 - Centro',
                    cliente_id=cliente_padrao.id,
                    grupo_id=grupo_padrao.id,
                    ativo=True
                ),
                models.Avaliado(
                    nome='Loja Shopping',
                    codigo='LS002', 
                    endereco='Shopping Center - Loja 45',
                    cliente_id=cliente_padrao.id,
                    grupo_id=grupo_padrao.id,
                    ativo=True
                ),
                models.Avaliado(
                    nome='Unidade Matriz',
                    codigo='UM003',
                    endereco='Av. Principal, 500 - Matriz',
                    cliente_id=cliente_padrao.id,
                    grupo_id=grupo_padrao.id,
                    ativo=True
                )
            ]
            
            for avaliado in avaliados_exemplo:
                db.session.add(avaliado)
            db.session.flush()
            
            # 8. Criar questionário de exemplo
            print("📋 Criando questionário de exemplo...")
            questionario = models.Questionario(
                nome='Avaliação de Qualidade Básica',
                descricao='Questionário básico para avaliar qualidade',
                versao='1.0',
                cliente_id=cliente_padrao.id,
                criado_por_id=admin.id,
                ativo=True,
                publicado=True,
                status=models.StatusQuestionario.PUBLICADO,
                data_publicacao=datetime.now()
            )
            db.session.add(questionario)
            db.session.flush()
            
            # 9. Criar tópico de exemplo
            print("📑 Criando tópico de exemplo...")
            topico = models.Topico(
                nome='Atendimento ao Cliente',
                descricao='Avaliação do atendimento prestado',
                ordem=1,
                questionario_id=questionario.id,
                ativo=True
            )
            db.session.add(topico)
            db.session.flush()
            
            # 10. Criar perguntas de exemplo
            print("❓ Criando perguntas de exemplo...")
            perguntas_exemplo = [
                {
                    'texto': 'O atendente foi cordial e educado?',
                    'tipo': models.TipoResposta.SIM_NAO_NA,
                    'ordem': 1,
                    'peso': 1
                },
                {
                    'texto': 'O tempo de espera foi adequado?',
                    'tipo': models.TipoResposta.SIM_NAO_NA,
                    'ordem': 2,
                    'peso': 1
                },
                {
                    'texto': 'Como você avalia o atendimento geral?',
                    'tipo': models.TipoResposta.MULTIPLA_ESCOLHA,
                    'ordem': 3,
                    'peso': 2
                },
                {
                    'texto': 'Qual a nota geral do atendimento?',
                    'tipo': models.TipoResposta.NOTA,
                    'ordem': 4,
                    'peso': 3
                }
            ]
            
            perguntas_criadas = []
            for p_data in perguntas_exemplo:
                pergunta = models.Pergunta(
                    texto=p_data['texto'],
                    tipo=p_data['tipo'],
                    ordem=p_data['ordem'],
                    peso=p_data['peso'],
                    topico_id=topico.id,
                    obrigatoria=True,
                    ativo=True
                )
                db.session.add(pergunta)
                db.session.flush()
                perguntas_criadas.append(pergunta)
            
            # 11. Criar opções para pergunta de múltipla escolha
            print("🔘 Criando opções de resposta...")
            pergunta_multipla = perguntas_criadas[2]  # "Como você avalia..."
            
            opcoes = [
                {'texto': 'Excelente', 'valor': 10, 'ordem': 1},
                {'texto': 'Bom', 'valor': 8, 'ordem': 2},
                {'texto': 'Regular', 'valor': 6, 'ordem': 3},
                {'texto': 'Ruim', 'valor': 4, 'ordem': 4},
                {'texto': 'Péssimo', 'valor': 2, 'ordem': 5}
            ]
            
            for opcao_data in opcoes:
                opcao = models.OpcaoPergunta(
                    texto=opcao_data['texto'],
                    valor=opcao_data['valor'],
                    ordem=opcao_data['ordem'],
                    pergunta_id=pergunta_multipla.id
                )
                db.session.add(opcao)
            
            # 12. Criar configuração do cliente
            print("⚙️  Criando configuração do sistema...")
            config = models.ConfiguracaoCliente(
                cliente_id=cliente_padrao.id,
                logo_url='',
                cor_primaria='#007bff',
                cor_secundaria='#6c757d',
                mostrar_notas=True,
                permitir_fotos=True,
                obrigar_plano_acao=False
            )
            db.session.add(config)
            
            # 13. Criar algumas aplicações de exemplo para demonstração
            print("📊 Criando aplicações de exemplo...")
            for i in range(10):
                data_aplicacao = datetime.now() - timedelta(days=random.randint(1, 30))
                
                aplicacao = models.AplicacaoQuestionario(
                    questionario_id=questionario.id,
                    avaliado_id=random.choice(avaliados_exemplo).id,
                    aplicador_id=admin.id,
                    data_inicio=data_aplicacao,
                    data_fim=data_aplicacao + timedelta(minutes=random.randint(10, 30)),
                    status=models.StatusAplicacao.FINALIZADA,
                    nota_final=random.uniform(60, 95),
                    observacoes=f'Aplicação de exemplo {i+1}'
                )
                db.session.add(aplicacao)
                db.session.flush()
                
                # Criar respostas para esta aplicação
                for j, pergunta in enumerate(perguntas_criadas):
                    if pergunta.tipo == models.TipoResposta.SIM_NAO_NA:
                        resposta_texto = random.choice(['Sim', 'Não', 'N.A.'])
                        pontos = 1 if resposta_texto == 'Sim' else 0 if resposta_texto == 'Não' else None
                    elif pergunta.tipo == models.TipoResposta.MULTIPLA_ESCOLHA:
                        opcao_escolhida = random.choice(opcoes)
                        resposta_texto = opcao_escolhida['texto']
                        pontos = opcao_escolhida['valor']
                    elif pergunta.tipo == models.TipoResposta.NOTA:
                        nota = random.randint(6, 10)
                        resposta_texto = str(nota)
                        pontos = nota
                    else:
                        resposta_texto = f'Resposta exemplo {j+1}'
                        pontos = random.randint(5, 10)
                    
                    resposta = models.RespostaPergunta(
                        aplicacao_id=aplicacao.id,
                        pergunta_id=pergunta.id,
                        resposta=resposta_texto,
                        pontos=pontos,
                        data_resposta=data_aplicacao
                    )
                    db.session.add(resposta)
            
            # 14. Commit final
            print("💾 Salvando dados...")
            db.session.commit()
            
            print("\n" + "=" * 50)
            print("✅ SISTEMA INICIALIZADO COM SUCESSO!")
            print("=" * 50)
            print("\n📋 INFORMAÇÕES DE ACESSO:")
            print(f"   🌐 URL: http://localhost:5000")
            print(f"   👤 Email: admin@admin.com")
            print(f"   🔑 Senha: admin123")
            
            print(f"\n📊 DADOS CRIADOS:")
            print(f"   • 1 Cliente: {cliente_padrao.nome}")
            print(f"   • 1 Grupo: {grupo_padrao.nome}")
            print(f"   • 1 Administrador: {admin.nome}")
            print(f"   • {len(avaliados_exemplo)} Avaliados de exemplo")
            print(f"   • 1 Questionário: {questionario.nome}")
            print(f"   • 1 Tópico: {topico.nome}")
            print(f"   • {len(perguntas_criadas)} Perguntas")
            print(f"   • 10 Aplicações de exemplo com dados")
            
            print(f"\n🚀 PRÓXIMOS PASSOS:")
            print(f"   1. Execute: python run.py")
            print(f"   2. Acesse: http://localhost:5000")
            print(f"   3. Faça login com as credenciais acima")
            print(f"   4. Teste os módulos CLI e Panorama")
            
            return True
            
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if inicializar_sistema():
        print("\n🎉 SISTEMA PRONTO PARA USO!")
    else:
        print("\n💥 FALHA NA INICIALIZAÇÃO!")
        sys.exit(1)
