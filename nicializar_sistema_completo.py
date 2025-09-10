# inicializar_sistema_completo.py
"""
Script final para inicializar o QualiGestor com dados de demonstração
Execute este script para ter o sistema funcionando completamente
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import *
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def criar_dados_completos():
    """Cria um conjunto completo de dados para demonstração"""
    
    print("🚀 Inicializando Sistema QualiGestor - Dados Completos")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # Limpar e recriar banco
        print("🧹 Limpando banco de dados...")
        db.drop_all()
        db.create_all()
        
        try:
            # 1. Criar Categorias
            print("\n📋 Criando categorias...")
            categorias = [
                CategoriaFormulario(nome="Higiene e Limpeza", icone="fas fa-broom", cor="#27ae60", ordem=1),
                CategoriaFormulario(nome="Segurança", icone="fas fa-shield-alt", cor="#e74c3c", ordem=2),
                CategoriaFormulario(nome="Atendimento", icone="fas fa-smile", cor="#f39c12", ordem=3),
                CategoriaFormulario(nome="Processos", icone="fas fa-cogs", cor="#3498db", ordem=4)
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
                ativo=True,
                data_cadastro=datetime.utcnow()
            )
            db.session.add(cliente)
            db.session.flush()
            
            # 3. Criar Grupos
            print("📁 Criando grupos...")
            grupos = [
                Grupo(nome="São Paulo", cliente_id=cliente.id),
                Grupo(nome="Rio de Janeiro", cliente_id=cliente.id),
                Grupo(nome="Minas Gerais", cliente_id=cliente.id)
            ]
            db.session.add_all(grupos)
            db.session.flush()
            
            # 4. Criar Lojas
            print("🏪 Criando lojas...")
            lojas_data = [
                ("Lab Centro SP", "SP001", grupos[0].id, "São Paulo", "SP"),
                ("Lab Vila Mariana", "SP002", grupos[0].id, "São Paulo", "SP"),
                ("Lab Copacabana", "RJ001", grupos[1].id, "Rio de Janeiro", "RJ"),
                ("Lab Ipanema", "RJ002", grupos[1].id, "Rio de Janeiro", "RJ"),
                ("Lab BH Centro", "MG001", grupos[2].id, "Belo Horizonte", "MG"),
                ("Lab Savassi", "MG002", grupos[2].id, "Belo Horizonte", "MG")
            ]
            
            lojas = []
            for nome, codigo, grupo_id, cidade, estado in lojas_data:
                loja = Loja(
                    nome=nome,
                    codigo=codigo,
                    endereco=f"Endereço da {nome}",
                    cidade=cidade,
                    estado=estado,
                    telefone="(11) 3456-7890",
                    email=f"{codigo.lower()}@labdemo.com",
                    gerente_nome=f"Gerente {nome.split()[-1]}",
                    cliente_id=cliente.id,
                    grupo_id=grupo_id,
                    ativa=True
                )
                lojas.append(loja)
            
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
                    email="ana@labdemo.com",
                    senha=generate_password_hash("demo123"),
                    tipo=TipoUsuario.AUDITOR,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                ),
                Usuario(
                    nome="Bruno Gestor",
                    email="bruno@labdemo.com",
                    senha=generate_password_hash("demo123"),
                    tipo=TipoUsuario.GESTOR,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                ),
                Usuario(
                    nome="Carlos Visualizador",
                    email="carlos@labdemo.com",
                    senha=generate_password_hash("demo123"),
                    tipo=TipoUsuario.VISUALIZADOR,
                    cliente_id=cliente.id,
                    ativo=True,
                    primeiro_acesso=False
                )
            ]
            db.session.add_all(usuarios)
            db.session.flush()
            
            # 6. Criar Formulários
            print("📝 Criando formulários...")
            formularios_data = [
                {
                    'nome': 'Checklist de Higiene Laboratorial',
                    'categoria_id': categorias[0].id,
                    'blocos': [
                        {
                            'nome': 'Limpeza do Ambiente',
                            'perguntas': [
                                ('Bancadas estão limpas e organizadas?', TipoResposta.SIM_NAO, True, 10),
                                ('Piso sem resíduos ou contaminantes?', TipoResposta.SIM_NAO, True, 10),
                                ('Equipamentos limpos e calibrados?', TipoResposta.SIM_NAO, True, 15),
                                ('Nota geral da limpeza (0-10)', TipoResposta.NOTA, True, 10)
                            ]
                        },
                        {
                            'nome': 'Descarte de Materiais',
                            'perguntas': [
                                ('Lixeiras identificadas corretamente?', TipoResposta.SIM_NAO, True, 10),
                                ('Materiais perfurocortantes descartados adequadamente?', TipoResposta.SIM_NAO, True, 15),
                                ('Resíduos químicos segregados?', TipoResposta.SIM_NAO, True, 15)
                            ]
                        }
                    ]
                },
                {
                    'nome': 'Auditoria de Segurança',
                    'categoria_id': categorias[1].id,
                    'blocos': [
                        {
                            'nome': 'Equipamentos de Proteção',
                            'perguntas': [
                                ('Todos usando EPIs obrigatórios?', TipoResposta.SIM_NAO, True, 20),
                                ('EPIs em bom estado de conservação?', TipoResposta.SIM_NAO, True, 15),
                                ('Chuveiro de emergência funcionando?', TipoResposta.SIM_NAO, True, 15),
                                ('Extintores dentro da validade?', TipoResposta.SIM_NAO, True, 10)
                            ]
                        }
                    ]
                },
                {
                    'nome': 'Avaliação de Atendimento',
                    'categoria_id': categorias[2].id,
                    'blocos': [
                        {
                            'nome': 'Atendimento ao Cliente',
                            'perguntas': [
                                ('Recepção organizada e limpa?', TipoResposta.SIM_NAO, True, 10),
                                ('Funcionários uniformizados?', TipoResposta.SIM_NAO, True, 10),
                                ('Tempo de espera adequado?', TipoResposta.SIM_NAO, True, 15),
                                ('Nota do atendimento (0-10)', TipoResposta.NOTA, True, 15),
                                ('Observações sobre atendimento', TipoResposta.TEXTO_LONGO, False, 5)
                            ]
                        }
                    ]
                }
            ]
            
            formularios = []
            for form_data in formularios_data:
                # Criar formulário
                formulario = Formulario(
                    nome=form_data['nome'],
                    cliente_id=cliente.id,
                    criado_por_id=usuarios[1].id,  # Ana
                    categoria_id=form_data['categoria_id'],
                    versao='1.0',
                    pontuacao_ativa=True,
                    ativo=True,
                    publicado=True,
                    publicado_em=datetime.utcnow()
                )
                db.session.add(formulario)
                db.session.flush()
                
                # Criar blocos e perguntas
                for ordem_bloco, bloco_data in enumerate(form_data['blocos'], 1):
                    bloco = BlocoFormulario(
                        nome=bloco_data['nome'],
                        ordem=ordem_bloco,
                        formulario_id=formulario.id
                    )
                    db.session.add(bloco)
                    db.session.flush()
                    
                    for ordem_pergunta, (texto, tipo, obrigatoria, peso) in enumerate(bloco_data['perguntas'], 1):
                        pergunta = Pergunta(
                            texto=texto,
                            tipo_resposta=tipo,
                            obrigatoria=obrigatoria,
                            ordem=ordem_pergunta,
                            peso=peso,
                            pontuacao_maxima=peso,
                            bloco_id=bloco.id,
                            permite_observacao=True,
                            permite_foto=(tipo == TipoResposta.SIM_NAO)
                        )
                        db.session.add(pergunta)
                        db.session.flush()
                        
                        # Criar opções para Sim/Não
                        if tipo == TipoResposta.SIM_NAO:
                            opcoes = [
                                OpcaoPergunta(texto="Sim", valor="Sim", pontuacao=peso, ordem=1, pergunta_id=pergunta.id),
                                OpcaoPergunta(texto="Não", valor="Não", pontuacao=0, ordem=2, pergunta_id=pergunta.id, gera_nc=True)
                            ]
                            db.session.add_all(opcoes)
                
                formularios.append(formulario)
            
            # 7. Criar Auditorias com Respostas
            print("📊 Criando auditorias de demonstração...")
            
            # Criar auditorias dos últimos 90 dias
            for i in range(50):  # 50 auditorias de exemplo
                # Data aleatória nos últimos 90 dias
                dias_atras = random.randint(1, 90)
                data_auditoria = datetime.now() - timedelta(days=dias_atras)
                
                # Escolher loja e formulário aleatórios
                loja = random.choice(lojas)
                formulario = random.choice(formularios)
                usuario = random.choice([usuarios[1], usuarios[2]])  # Ana ou Bruno
                
                # Criar auditoria
                auditoria = Auditoria(
                    codigo=f"AUD-2025-{i+1:05d}",
                    formulario_id=formulario.id,
                    loja_id=loja.id,
                    usuario_id=usuario.id,
                    status=StatusAuditoria.CONCLUIDA,
                    data_inicio=data_auditoria,
                    data_conclusao=data_auditoria + timedelta(minutes=random.randint(15, 60)),
                    observacoes_gerais=f"Auditoria realizada em {data_auditoria.strftime('%d/%m/%Y')}"
                )
                db.session.add(auditoria)
                db.session.flush()
                
                # Criar respostas para todas as perguntas
                pontuacao_total = 0
                pontuacao_maxima = 0
                
                for bloco in formulario.blocos:
                    for pergunta in bloco.perguntas:
                        pontuacao_maxima += pergunta.peso
                        
                        # Simular resposta baseada no tipo
                        resposta = Resposta(
                            pergunta_id=pergunta.id,
                            auditoria_id=auditoria.id
                        )
                        
                        if pergunta.tipo_resposta == TipoResposta.SIM_NAO:
                            # 80% de chance de ser "Sim"
                            valor = "Sim" if random.random() < 0.8 else "Não"
                            resposta.valor_opcoes_selecionadas = f'["{valor}"]'
                            resposta.pontuacao_obtida = pergunta.peso if valor == "Sim" else 0
                            
                        elif pergunta.tipo_resposta == TipoResposta.NOTA:
                            # Nota aleatória entre 6 e 10
                            nota = random.uniform(6, 10)
                            resposta.valor_numero = nota
                            resposta.pontuacao_obtida = (nota / 10) * pergunta.peso
                            
                        elif pergunta.tipo_resposta == TipoResposta.TEXTO_LONGO:
                            resposta.valor_texto = "Observação da auditoria..."
                            resposta.pontuacao_obtida = pergunta.peso
                        
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
            print(f"  • Auditora: ana@labdemo.com / demo123")
            print(f"  • Gestor: bruno@labdemo.com / demo123")
            print(f"  • Visualizador: carlos@labdemo.com / demo123")