# init_sistema.py
"""
Script para inicializar o sistema QualiGestor com o NOVO MODELO
Compatível com Loja ao invés de Avaliado
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Usuario, Cliente, Loja, Grupo,
    Formulario, BlocoFormulario, Pergunta, OpcaoPergunta,
    CategoriaFormulario, TipoResposta, TipoUsuario,
    PlanoSaaS, StatusAuditoria
)
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def limpar_banco():
    """Limpa o banco de dados"""
    print("🧹 Limpando banco de dados...")
    try:
        db.drop_all()
        db.create_all()
        print("✅ Banco limpo e recriado")
        return True
    except Exception as e:
        print(f"❌ Erro ao limpar banco: {e}")
        return False

def criar_planos():
    """Cria planos SaaS"""
    print("\n💳 Criando planos SaaS...")
    
    planos = [
        PlanoSaaS(
            nome_plano="Básico",
            descricao="Plano ideal para pequenas empresas",
            preco_mensal=299.90,
            limite_usuarios=5,
            limite_lojas=3,
            limite_formularios=10,
            limite_auditorias_mes=50,
            ativo=True
        ),
        PlanoSaaS(
            nome_plano="Profissional",
            descricao="Plano completo para médias empresas",
            preco_mensal=799.90,
            limite_usuarios=20,
            limite_lojas=10,
            limite_formularios=50,
            limite_auditorias_mes=200,
            ativo=True
        ),
        PlanoSaaS(
            nome_plano="Enterprise",
            descricao="Plano ilimitado para grandes corporações",
            preco_mensal=1999.90,
            limite_usuarios=999,
            limite_lojas=999,
            limite_formularios=999,
            limite_auditorias_mes=9999,
            ativo=True
        )
    ]
    
    db.session.add_all(planos)
    db.session.flush()
    print(f"✅ {len(planos)} planos criados")
    return planos[1]  # Retorna o plano Profissional

def criar_cliente(plano):
    """Cria cliente principal"""
    print("\n🏢 Criando cliente...")
    
    cliente = Cliente(
        nome="Empresa Demo LTDA",
        nome_fantasia="Demo Store",
        cnpj="12.345.678/0001-90",
        inscricao_estadual="123.456.789.012",
        endereco="Rua Exemplo, 123",
        cidade="São Paulo",
        estado="SP",
        cep="01234-567",
        telefone="(11) 3456-7890",
        email_contato="contato@demo.com",
        website="www.demo.com",
        logo_url="/static/img/logo-demo.png",
        cor_primaria="#2c3e50",
        cor_secundaria="#3498db",
        ativo=True,
        data_cadastro=datetime.utcnow(),
        data_expiracao=datetime.utcnow() + timedelta(days=365),
        plano_saas_id=plano.id
    )
    
    db.session.add(cliente)
    db.session.flush()
    print("✅ Cliente criado")
    return cliente

def criar_grupos(cliente):
    """Cria grupos de lojas"""
    print("\n📁 Criando grupos...")
    
    grupos = [
        Grupo(
            nome="São Paulo - Capital",
            descricao="Lojas da capital paulista",
            cliente_id=cliente.id,
            ativo=True
        ),
        Grupo(
            nome="São Paulo - Interior",
            descricao="Lojas do interior de SP",
            cliente_id=cliente.id,
            ativo=True
        ),
        Grupo(
            nome="Rio de Janeiro",
            descricao="Lojas do estado do RJ",
            cliente_id=cliente.id,
            ativo=True
        )
    ]
    
    db.session.add_all(grupos)
    db.session.flush()
    print(f"✅ {len(grupos)} grupos criados")
    return grupos

def criar_lojas(cliente, grupos):
    """Cria lojas"""
    print("\n🏪 Criando lojas...")
    
    lojas = [
        Loja(
            codigo="SP001",
            nome="Loja Centro SP",
            tipo="Loja",
            endereco="Av. Paulista, 1000",
            cidade="São Paulo",
            estado="SP",
            cep="01310-100",
            latitude=-23.5505,
            longitude=-46.6333,
            telefone="(11) 3456-0001",
            email="centro.sp@demo.com",
            gerente_nome="João Silva",
            gerente_telefone="(11) 98765-4321",
            gerente_email="joao.silva@demo.com",
            horario_funcionamento="Seg-Sex: 9h-18h, Sab: 9h-13h",
            ativa=True,
            cliente_id=cliente.id,
            grupo_id=grupos[0].id
        ),
        Loja(
            codigo="SP002",
            nome="Loja Vila Mariana",
            tipo="Loja",
            endereco="Rua Domingos de Morais, 500",
            cidade="São Paulo",
            estado="SP",
            cep="04010-100",
            telefone="(11) 3456-0002",
            email="vila.mariana@demo.com",
            gerente_nome="Maria Santos",
            gerente_telefone="(11) 98765-4322",
            gerente_email="maria.santos@demo.com",
            ativa=True,
            cliente_id=cliente.id,
            grupo_id=grupos[0].id
        ),
        Loja(
            codigo="SP003",
            nome="Loja Campinas",
            tipo="Loja",
            endereco="Av. Francisco Glicério, 300",
            cidade="Campinas",
            estado="SP",
            cep="13012-100",
            telefone="(19) 3456-0001",
            email="campinas@demo.com",
            gerente_nome="Carlos Mendes",
            gerente_telefone="(19) 98765-4321",
            gerente_email="carlos.mendes@demo.com",
            ativa=True,
            cliente_id=cliente.id,
            grupo_id=grupos[1].id
        ),
        Loja(
            codigo="RJ001",
            nome="Loja Copacabana",
            tipo="Loja",
            endereco="Av. N. S. de Copacabana, 800",
            cidade="Rio de Janeiro",
            estado="RJ",
            cep="22050-001",
            latitude=-22.9668,
            longitude=-43.1876,
            telefone="(21) 3456-0001",
            email="copacabana@demo.com",
            gerente_nome="Ana Costa",
            gerente_telefone="(21) 98765-4321",
            gerente_email="ana.costa@demo.com",
            ativa=True,
            cliente_id=cliente.id,
            grupo_id=grupos[2].id
        ),
        Loja(
            codigo="CD001",
            nome="Centro de Distribuição",
            tipo="Centro de Distribuição",
            endereco="Rod. Presidente Dutra, KM 50",
            cidade="Guarulhos",
            estado="SP",
            cep="07034-000",
            telefone="(11) 3456-9999",
            email="cd@demo.com",
            gerente_nome="Roberto Alves",
            gerente_telefone="(11) 98765-9999",
            gerente_email="roberto.alves@demo.com",
            ativa=True,
            cliente_id=cliente.id,
            grupo_id=grupos[0].id
        )
    ]
    
    db.session.add_all(lojas)
    db.session.flush()
    print(f"✅ {len(lojas)} lojas criadas")
    return lojas

def criar_usuarios(cliente):
    """Cria usuários do sistema"""
    print("\n👥 Criando usuários...")
    
    usuarios = [
        Usuario(
            nome="Administrador Sistema",
            email="admin@admin.com",
            senha=generate_password_hash("admin123"),
            cpf="111.111.111-11",
            telefone="(11) 99999-9999",
            tipo=TipoUsuario.SUPER_ADMIN,
            ativo=True,
            primeiro_acesso=False,
            cliente_id=cliente.id
        ),
        Usuario(
            nome="Gestor Demo",
            email="gestor@demo.com",
            senha=generate_password_hash("demo123"),
            cpf="222.222.222-22",
            telefone="(11) 98888-8888",
            tipo=TipoUsuario.ADMIN_CLIENTE,
            ativo=True,
            primeiro_acesso=False,
            cliente_id=cliente.id
        ),
        Usuario(
            nome="Ana Auditora",
            email="ana@demo.com",
            senha=generate_password_hash("demo123"),
            cpf="333.333.333-33",
            telefone="(11) 97777-7777",
            tipo=TipoUsuario.AUDITOR,
            ativo=True,
            primeiro_acesso=False,
            cliente_id=cliente.id
        ),
        Usuario(
            nome="Bruno Auditor",
            email="bruno@demo.com",
            senha=generate_password_hash("demo123"),
            cpf="444.444.444-44",
            telefone="(11) 96666-6666",
            tipo=TipoUsuario.AUDITOR,
            ativo=True,
            primeiro_acesso=False,
            cliente_id=cliente.id
        ),
        Usuario(
            nome="João Gestor Loja",
            email="joao@demo.com",
            senha=generate_password_hash("demo123"),
            cpf="555.555.555-55",
            telefone="(11) 95555-5555",
            tipo=TipoUsuario.GESTOR_LOJA,
            ativo=True,
            primeiro_acesso=False,
            cliente_id=cliente.id
        )
    ]
    
    db.session.add_all(usuarios)
    db.session.flush()
    print(f"✅ {len(usuarios)} usuários criados")
    return usuarios

def criar_categorias():
    """Cria categorias de formulários"""
    print("\n📋 Criando categorias de formulários...")
    
    categorias = [
        CategoriaFormulario(
            nome="Higiene e Limpeza",
            descricao="Checklists relacionados a higiene e limpeza",
            icone="fas fa-broom",
            cor="#27ae60",
            ordem=1,
            ativa=True
        ),
        CategoriaFormulario(
            nome="Segurança",
            descricao="Checklists de segurança e prevenção",
            icone="fas fa-shield-alt",
            cor="#e74c3c",
            ordem=2,
            ativa=True
        ),
        CategoriaFormulario(
            nome="Qualidade",
            descricao="Controle de qualidade e processos",
            icone="fas fa-check-circle",
            cor="#3498db",
            ordem=3,
            ativa=True
        ),
        CategoriaFormulario(
            nome="Atendimento",
            descricao="Avaliação de atendimento ao cliente",
            icone="fas fa-smile",
            cor="#f39c12",
            ordem=4,
            ativa=True
        )
    ]
    
    db.session.add_all(categorias)
    db.session.flush()
    print(f"✅ {len(categorias)} categorias criadas")
    return categorias

def criar_formularios(cliente, usuarios, categorias):
    """Cria formulários de exemplo"""
    print("\n📝 Criando formulários...")
    
    formularios = []
    
    # FORMULÁRIO 1: Abertura de Loja
    form1 = Formulario(
        codigo="CHK001",
        nome="Checklist de Abertura de Loja",
        descricao="Verificação completa para abertura diária",
        versao="1.0",
        pontuacao_ativa=True,
        pontuacao_maxima=100,
        peso_total=100,
        formula_calculo="PERCENTUAL",
        exibir_pontuacao=True,
        exibir_observacoes=True,
        obrigar_foto=False,
        obrigar_plano_acao=True,
        permitir_na=True,
        gerar_relatorio_pdf=True,
        enviar_email_conclusao=False,
        ativo=True,
        publicado=True,
        cliente_id=cliente.id,
        criado_por_id=usuarios[1].id,  # Gestor
        categoria_id=categorias[0].id,  # Higiene
        publicado_em=datetime.utcnow()
    )
    db.session.add(form1)
    db.session.flush()
    
    # Blocos do Formulário 1
    bloco1_1 = BlocoFormulario(
        nome="Limpeza e Organização",
        descricao="Verificação de limpeza",
        ordem=1,
        peso=40,
        expansivel=True,
        obrigatorio=True,
        formulario_id=form1.id
    )
    
    bloco1_2 = BlocoFormulario(
        nome="Equipamentos e Sistemas",
        descricao="Funcionamento dos equipamentos",
        ordem=2,
        peso=35,
        expansivel=True,
        obrigatorio=True,
        formulario_id=form1.id
    )
    
    bloco1_3 = BlocoFormulario(
        nome="Equipe",
        descricao="Verificação da equipe",
        ordem=3,
        peso=25,
        expansivel=True,
        obrigatorio=True,
        formulario_id=form1.id
    )
    
    db.session.add_all([bloco1_1, bloco1_2, bloco1_3])
    db.session.flush()
    
    # Perguntas do Bloco 1
    perguntas_bloco1 = [
        Pergunta(
            codigo="B1P1",
            texto="O piso está limpo e sem manchas?",
            descricao="Verificar toda a área de vendas",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            permite_observacao=True,
            permite_foto=True,
            ordem=1,
            peso=10,
            pontuacao_maxima=10,
            valor_esperado="Sim",
            bloco_id=bloco1_1.id
        ),
        Pergunta(
            codigo="B1P2",
            texto="As vitrines estão limpas?",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            permite_observacao=True,
            ordem=2,
            peso=10,
            pontuacao_maxima=10,
            valor_esperado="Sim",
            bloco_id=bloco1_1.id
        ),
        Pergunta(
            codigo="B1P3",
            texto="Banheiros limpos e abastecidos?",
            tipo_resposta=TipoResposta.SIM_NAO_NA,
            obrigatoria=True,
            permite_observacao=True,
            permite_foto=True,
            ordem=3,
            peso=10,
            pontuacao_maxima=10,
            critica=True,  # Pergunta crítica
            gera_nc_automatica=True,
            valor_esperado="Sim",
            bloco_id=bloco1_1.id
        ),
        Pergunta(
            codigo="B1P4",
            texto="Nota geral da limpeza (0-10)",
            tipo_resposta=TipoResposta.NOTA,
            obrigatoria=True,
            ordem=4,
            peso=10,
            pontuacao_maxima=10,
            limite_minimo=0,
            limite_maximo=10,
            bloco_id=bloco1_1.id
        )
    ]
    
    # Perguntas do Bloco 2
    perguntas_bloco2 = [
        Pergunta(
            codigo="B2P1",
            texto="Sistema de ar condicionado funcionando?",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            permite_observacao=True,
            ordem=1,
            peso=15,
            pontuacao_maxima=15,
            critica=True,
            gera_nc_automatica=True,
            valor_esperado="Sim",
            bloco_id=bloco1_2.id
        ),
        Pergunta(
            codigo="B2P2",
            texto="Sistema PDV/Caixa operacional?",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            permite_observacao=True,
            ordem=2,
            peso=15,
            pontuacao_maxima=15,
            critica=True,
            gera_nc_automatica=True,
            valor_esperado="Sim",
            bloco_id=bloco1_2.id
        ),
        Pergunta(
            codigo="B2P3",
            texto="Iluminação adequada?",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            ordem=3,
            peso=5,
            pontuacao_maxima=5,
            valor_esperado="Sim",
            bloco_id=bloco1_2.id
        )
    ]
    
    # Perguntas do Bloco 3
    perguntas_bloco3 = [
        Pergunta(
            codigo="B3P1",
            texto="Quantidade de funcionários presentes",
            tipo_resposta=TipoResposta.NUMERO,
            obrigatoria=True,
            ordem=1,
            peso=5,
            pontuacao_maxima=5,
            limite_minimo=1,
            limite_maximo=50,
            bloco_id=bloco1_3.id
        ),
        Pergunta(
            codigo="B3P2",
            texto="Todos uniformizados?",
            tipo_resposta=TipoResposta.SIM_NAO_NA,
            obrigatoria=True,
            permite_observacao=True,
            permite_foto=True,
            ordem=2,
            peso=10,
            pontuacao_maxima=10,
            valor_esperado="Sim",
            bloco_id=bloco1_3.id
        ),
        Pergunta(
            codigo="B3P3",
            texto="Observações gerais",
            tipo_resposta=TipoResposta.TEXTO_LONGO,
            obrigatoria=False,
            ordem=3,
            peso=10,
            pontuacao_maxima=10,
            bloco_id=bloco1_3.id
        )
    ]
    
    db.session.add_all(perguntas_bloco1 + perguntas_bloco2 + perguntas_bloco3)
    formularios.append(form1)
    
    # FORMULÁRIO 2: Segurança
    form2 = Formulario(
        codigo="CHK002",
        nome="Checklist de Segurança",
        descricao="Verificação de itens de segurança",
        versao="1.0",
        pontuacao_ativa=True,
        pontuacao_maxima=100,
        ativo=True,
        publicado=True,
        cliente_id=cliente.id,
        criado_por_id=usuarios[1].id,
        categoria_id=categorias[1].id,
        publicado_em=datetime.utcnow()
    )
    db.session.add(form2)
    db.session.flush()
    
    bloco2_1 = BlocoFormulario(
        nome="Equipamentos de Segurança",
        ordem=1,
        peso=100,
        formulario_id=form2.id
    )
    db.session.add(bloco2_1)
    db.session.flush()
    
    perguntas_form2 = [
        Pergunta(
            codigo="SEG001",
            texto="Câmeras funcionando?",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            ordem=1,
            peso=25,
            pontuacao_maxima=25,
            critica=True,
            bloco_id=bloco2_1.id
        ),
        Pergunta(
            codigo="SEG002",
            texto="Alarme testado?",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            ordem=2,
            peso=25,
            pontuacao_maxima=25,
            critica=True,
            bloco_id=bloco2_1.id
        ),
        Pergunta(
            codigo="SEG003",
            texto="Extintores na validade?",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            ordem=3,
            peso=25,
            pontuacao_maxima=25,
            critica=True,
            bloco_id=bloco2_1.id
        ),
        Pergunta(
            codigo="SEG004",
            texto="Saídas de emergência livres?",
            tipo_resposta=TipoResposta.SIM_NAO,
            obrigatoria=True,
            ordem=4,
            peso=25,
            pontuacao_maxima=25,
            critica=True,
            gera_nc_automatica=True,
            bloco_id=bloco2_1.id
        )
    ]
    db.session.add_all(perguntas_form2)
    formularios.append(form2)
    
    db.session.commit()
    print(f"✅ {len(formularios)} formulários criados com perguntas")
    return formularios

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 INICIALIZADOR DO SISTEMA QUALIGESTOR - NOVO MODELO")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        print("\n⚠️  ATENÇÃO: Isso apagará todos os dados existentes!")
        resposta = input("Deseja continuar? (s/n): ").lower()
        
        if resposta != 's':
            print("❌ Operação cancelada")
            return
        
        # Limpar banco
        if not limpar_banco():
            return
        
        try:
            # Criar estrutura
            plano = criar_planos()
            cliente = criar_cliente(plano)
            grupos = criar_grupos(cliente)
            lojas = criar_lojas(cliente, grupos)
            usuarios = criar_usuarios(cliente)
            categorias = criar_categorias()
            formularios = criar_formularios(cliente, usuarios, categorias)
            
            # Associar gestores às lojas
            lojas[0].usuarios_responsaveis.append(usuarios[4])  # João na Loja Centro
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro durante a criação: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Resumo
        print("\n" + "=" * 60)
        print("🎉 SISTEMA INICIALIZADO COM SUCESSO!")
        print("=" * 60)
        print("\n📊 RESUMO DOS DADOS CRIADOS:")
        print(f"  • Planos SaaS: {PlanoSaaS.query.count()}")
        print(f"  • Clientes: {Cliente.query.count()}")
        print(f"  • Grupos: {Grupo.query.count()}")
        print(f"  • Lojas: {Loja.query.count()}")
        print(f"  • Usuários: {Usuario.query.count()}")
        print(f"  • Categorias: {CategoriaFormulario.query.count()}")
        print(f"  • Formulários: {Formulario.query.count()}")
        print(f"  • Blocos: {BlocoFormulario.query.count()}")
        print(f"  • Perguntas: {Pergunta.query.count()}")
        
        print("\n🔑 CREDENCIAIS DE ACESSO:")
        print("  • Admin: admin@admin.com / admin123")
        print("  • Gestor: gestor@demo.com / demo123")
        print("  • Auditor Ana: ana@demo.com / demo123")
        print("  • Auditor Bruno: bruno@demo.com / demo123")
        print("  • Gestor Loja: joao@demo.com / demo123")
        
        print("\n✨ Execute 'python run.py' para iniciar o sistema")
        print("💡 Acesse http://localhost:5000 no navegador")

if __name__ == "__main__":
    main()