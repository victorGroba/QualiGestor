# inicializar_dados_corrigido.py
"""
Script para inicializar o QualiGestor com dados de demonstração
Execute este script após aplicar as correções
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import *
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def criar_dados_demonstracao():
    """Cria dados básicos para demonstração"""
    
    print("🚀 Inicializando QualiGestor com dados de demonstração")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # Limpar e recriar banco
        print("🧹 Recriando banco de dados...")
        db.drop_all()
        db.create_all()
        
        try:
            # 1. Criar Categorias
            print("📋 Criando categorias...")
            categorias = [
                CategoriaFormulario(nome="Higiene", icone="fas fa-broom", cor="#27ae60", ordem=1),
                CategoriaFormulario(nome="Segurança", icone="fas fa-shield-alt", cor="#e74c3c", ordem=2),
                CategoriaFormulario(nome="Atendimento", icone="fas fa-smile", cor="#f39c12", ordem=3)
            ]
            db.session.add_all(categorias)
            db.session.flush()
            
            # 2. Criar Cliente
            print("🏢 Criando cliente...")
            cliente = Cliente(
                nome="Laboratório Demo LTDA",
                nome_fantasia="Lab Demo",
                cnpj="12.345.678/0001-90",
                endereco="Rua das Análises, 123",
                cidade="São Paulo",
                estado="SP",
                cep="01234-567",
                telefone="(11) 3456-7890",
                email_contato="contato@labdemo.com",
                ativo=True
            )
            db.session.add(cliente)
            db.session.flush()
            
            # 3. Criar Grupos
            print("📁 Criando grupos...")
            grupos = [
                Grupo(nome="São Paulo", cliente_id=cliente.id),
                Grupo(nome="Rio de Janeiro", cliente_id=cliente.id)
            ]
            db.session.add_all(grupos)
            db.session.flush()
            
            # 4. Criar Lojas
            print("🏪 Criando lojas...")
            lojas = [
                Loja(
                    nome="Lab Centro SP",
                    codigo="SP001",
                    endereco="Centro de São Paulo",
                    cidade="São Paulo",
                    estado="SP",
                    cliente_id=cliente.id,
                    grupo_id=grupos[0].id,
                    ativa=True
                ),
                Loja(
                    nome="Lab Vila Mariana",
                    codigo="SP002",
                    endereco="Vila Mariana",
                    cidade="São Paulo",
                    estado="SP",
                    cliente_id=cliente.id,
                    grupo_id=grupos[0].id,
                    ativa=True
                ),
                Loja(
                    nome="Lab Copacabana",
                    codigo="RJ001",
                    endereco="Copacabana",
                    cidade="Rio de Janeiro",
                    estado="RJ",
                    cliente_id=cliente.id,
                    grupo_id=grupos[1].id,
                    ativa=True
                )
            ]
            db.session.add_all(lojas)
            db.session.flush()
            
            # 5. Criar Usuários
            print("👥 Criando usuários...")
            usuarios = [
                Usuario(
                    nome="Administrador Sistema",
                    email="admin@admin.com",
                    senha=generate_password_hash("admin123"),
                    tipo=TipoUsuario.SUPER_ADMIN,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                ),
                Usuario(
                    nome="Ana Auditora",
                    email="ana@demo.com",
                    senha=generate_password_hash("demo123"),
                    tipo=TipoUsuario.AUDITOR,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                ),
                Usuario(
                    nome="Bruno Gestor",
                    email="bruno@demo.com",
                    senha=generate_password_hash("demo123"),
                    tipo=TipoUsuario.GESTOR,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                )
            ]
            db.session.add_all(usuarios)
            db.session.flush()
            
            # 6. Criar Formulários
            print("📝 Criando formulários...")
            
            # Formulário 1: Higiene
            formulario1 = Formulario(
                nome="Checklist de Higiene Laboratorial",
                cliente_id=cliente.id,
                criado_por_id=usuarios[1].id,
                categoria_id=categorias[0].id,
                versao='1.0',
                pontuacao_ativa=True,
                ativo=True,
                publicado=True,
                publicado_em=datetime.utcnow()
            )
            db.session.add(formulario1)
            db.session.flush()
            
            # Bloco 1
            bloco1 = BlocoFormulario(
                nome="Limpeza do Ambiente",
                ordem=1,
                formulario_id=formulario1.id
            )
            db.session.add(bloco1)
            db.session.flush()
            
            # Perguntas do bloco 1
            perguntas1 = [
                ("Bancadas estão limpas e organizadas?", TipoResposta.SIM_NAO, True, 10),
                ("Piso sem resíduos ou contaminantes?", TipoResposta.SIM_NAO, True, 10),
                ("Equipamentos limpos e calibrados?", TipoResposta.SIM_NAO, True, 15),
                ("Nota geral da limpeza (0-10)", TipoResposta.NOTA, True, 10)
            ]
            
            for ordem, (texto, tipo, obrigatoria, peso) in enumerate(perguntas1, 1):
                pergunta = Pergunta(
                    texto=texto,
                    tipo_resposta=tipo,
                    obrigatoria=obrigatoria,
                    ordem=ordem,
                    peso=peso,
                    pontuacao_maxima=peso,
                    bloco_id=bloco1.id,
                    permite_observacao=True
                )
                db.session.add(pergunta)
                db.session.flush()
                
                # Criar opções para Sim/Não
                if tipo == TipoResposta.SIM_NAO:
                    opcoes = [
                        OpcaoPergunta(texto="Sim", valor="Sim", pontuacao=peso, ordem=1, pergunta_id=pergunta.id),
                        OpcaoPergunta(texto="Não", valor="Não", pontuacao=0, ordem=2, pergunta_id=pergunta.id)
                    ]
                    db.session.add_all(opcoes)
            
            # Formulário 2: Segurança
            formulario2 = Formulario(
                nome="Auditoria de Segurança",
                cliente_id=cliente.id,
                criado_por_id=usuarios[1].id,
                categoria_id=categorias[1].id,
                versao='1.0',
                pontuacao_ativa=True,
                ativo=True,
                publicado=True,
                publicado_em=datetime.utcnow()
            )
            db.session.add(formulario2)
            db.session.flush()
            
            # Bloco 2
            bloco2 = BlocoFormulario(
                nome="Equipamentos de Proteção",
                ordem=1,
                formulario_id=formulario2.id
            )
            db.session.add(bloco2)
            db.session.flush()
            
            # Perguntas do bloco 2
            perguntas2 = [
                ("Todos usando EPIs obrigatórios?", TipoResposta.SIM_NAO, True, 20),
                ("EPIs em bom estado de conservação?", TipoResposta.SIM_NAO, True, 15),
                ("Chuveiro de emergência funcionando?", TipoResposta.SIM_NAO, True, 15),
                ("Extintores dentro da validade?", TipoResposta.SIM_NAO, True, 10)
            ]
            
            for ordem, (texto, tipo, obrigatoria, peso) in enumerate(perguntas2, 1):
                pergunta = Pergunta(
                    texto=texto,
                    tipo_resposta=tipo,
                    obrigatoria=obrigatoria,
                    ordem=ordem,
                    peso=peso,
                    pontuacao_maxima=peso,
                    bloco_id=bloco2.id,
                    permite_observacao=True
                )
                db.session.add(pergunta)
                db.session.flush()
                
                # Criar opções para Sim/Não
                if tipo == TipoResposta.SIM_NAO:
                    opcoes = [
                        OpcaoPergunta(texto="Sim", valor="Sim", pontuacao=peso, ordem=1, pergunta_id=pergunta.id),
                        OpcaoPergunta(texto="Não", valor="Não", pontuacao=0, ordem=2, pergunta_id=pergunta.id)
                    ]
                    db.session.add_all(opcoes)
            
            # 7. Criar Auditorias de Demonstração
            print("📊 Criando auditorias de demonstração...")
            
            formularios = [formulario1, formulario2]
            
            for i in range(20):  # 20 auditorias de exemplo
                # Data aleatória nos últimos 60 dias
                dias_atras = random.randint(1, 60)
                data_auditoria = datetime.now() - timedelta(days=dias_atras)
                
                # Escolher loja e formulário aleatórios
                loja = random.choice(lojas)
                formulario = random.choice(formularios)
                usuario = random.choice([usuarios[1], usuarios[2]])  # Ana ou Bruno
                
                # Criar auditoria
                auditoria = Auditoria(
                    codigo=f"AUD-2025-{i+1:03d}",
                    formulario_id=formulario.id,
                    loja_id=loja.id,
                    usuario_id=usuario.id,
                    status=StatusAuditoria.CONCLUIDA,
                    data_inicio=data_auditoria,
                    data_conclusao=data_auditoria + timedelta(minutes=random.randint(15, 45)),
                    observacoes_gerais=f"Auditoria realizada em {data_auditoria.strftime('%d/%m/%Y')}"
                )
                db.session.add(auditoria)
                db.session.flush()
                
                # Criar respostas
                pontuacao_total = 0
                pontuacao_maxima = 0
                
                for bloco in formulario.blocos:
                    for pergunta in bloco.perguntas:
                        pontuacao_maxima += pergunta.peso
                        
                        resposta = Resposta(
                            pergunta_id=pergunta.id,
                            auditoria_id=auditoria.id
                        )
                        
                        if pergunta.tipo_resposta == TipoResposta.SIM_NAO:
                            # 75% de chance de ser "Sim"
                            valor = "Sim" if random.random() < 0.75 else "Não"
                            resposta.valor_opcoes_selecionadas = f'["{valor}"]'
                            resposta.pontuacao_obtida = pergunta.peso if valor == "Sim" else 0
                            
                        elif pergunta.tipo_resposta == TipoResposta.NOTA:
                            # Nota aleatória entre 6 e 10
                            nota = random.uniform(6, 10)
                            resposta.valor_numero = nota
                            resposta.pontuacao_obtida = (nota / 10) * pergunta.peso
                        
                        pontuacao_total += resposta.pontuacao_obtida
                        db.session.add(resposta)
                
                # Atualizar pontuação da auditoria
                auditoria.pontuacao_obtida = pontuacao_total
                auditoria.pontuacao_maxima = pontuacao_maxima
                auditoria.percentual = (pontuacao_total / pontuacao_maxima * 100) if pontuacao_maxima > 0 else 0
            
            db.session.commit()
            
            # Relatório final
            print("\n" + "=" * 60)
            print("🎉 SISTEMA INICIALIZADO COM SUCESSO!")
            print("=" * 60)
            
            print(f"\n📊 DADOS CRIADOS:")
            print(f"  • Categorias: {CategoriaFormulario.query.count()}")
            print(f"  • Clientes: {Cliente.query.count()}")
            print(f"  • Grupos: {Grupo.query.count()}")
            print(f"  • Lojas: {Loja.query.count()}")
            print(f"  • Usuários: {Usuario.query.count()}")
            print(f"  • Formulários: {Formulario.query.count()}")
            print(f"  • Blocos: {BlocoFormulario.query.count()}")
            print(f"  • Perguntas: {Pergunta.query.count()}")
            print(f"  • Auditorias: {Auditoria.query.count()}")
            print(f"  • Respostas: {Resposta.query.count()}")
            
            print(f"\n🔑 CREDENCIAIS DE ACESSO:")
            print(f"  • Super Admin: admin@admin.com / admin123")
            print(f"  • Auditora: ana@demo.com / demo123")
            print(f"  • Gestor: bruno@demo.com / demo123")
            
            print(f"\n🚀 COMO USAR:")
            print(f"  1. Execute: python run.py")
            print(f"  2. Acesse: http://localhost:5000")
            print(f"  3. Faça login com as credenciais acima")
            print(f"  4. Navegue pelos módulos CLIQ e Panorama")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = criar_dados_demonstracao()
    if sucesso:
        print("\n✅ Inicialização concluída com sucesso!")
    else:
        print("\n❌ Falha na inicialização!")
