# app/config_transicao.py
"""
Arquivo de configuração para gerenciar a transição entre o modelo antigo e o novo.
Permite alternar entre os modelos sem quebrar o sistema.
"""

import os

# ========== CONFIGURAÇÃO PRINCIPAL ==========
# Defina como True para usar o novo modelo completo
# Defina como False para manter compatibilidade com modelo antigo
USAR_NOVO_MODELO = os.environ.get('USAR_NOVO_MODELO', 'False').lower() == 'true'

# ========== MAPEAMENTO DE ENTIDADES ==========

def get_config():
    """Retorna a configuração atual do sistema"""
    return {
        'novo_modelo': USAR_NOVO_MODELO,
        'versao': '1.5.0-transicao' if not USAR_NOVO_MODELO else '2.0.0-novo',
        'features': get_features_disponiveis()
    }

def get_features_disponiveis():
    """Retorna as funcionalidades disponíveis baseado no modelo"""
    if USAR_NOVO_MODELO:
        return {
            'lojas': True,
            'blocos_formulario': True,
            'nao_conformidades': True,
            'planos_acao': True,
            'categorias_formulario': True,
            'anexos': True,
            'perguntas_condicionais': True,
            'auditoria_sistema': True,
            'tipos_usuario_avancados': True,
            'pontuacao_avancada': True,
            'status_auditoria': True,
            'codigo_auditoria': True
        }
    else:
        return {
            'lojas': False,  # Usa Avaliados
            'blocos_formulario': False,
            'nao_conformidades': False,
            'planos_acao': False,
            'categorias_formulario': False,
            'anexos': False,
            'perguntas_condicionais': False,
            'auditoria_sistema': False,
            'tipos_usuario_avancados': False,
            'pontuacao_avancada': False,
            'status_auditoria': False,
            'codigo_auditoria': False
        }

def get_entity_name(plural=False):
    """Retorna o nome da entidade principal (Loja ou Avaliado)"""
    if USAR_NOVO_MODELO:
        return 'Lojas' if plural else 'Loja'
    else:
        return 'Avaliados' if plural else 'Avaliado'

def get_entity_field():
    """Retorna o nome do campo da entidade na tabela Auditoria"""
    return 'loja_id' if USAR_NOVO_MODELO else 'avaliado_id'

def get_date_field():
    """Retorna o nome do campo de data na tabela Auditoria"""
    return 'data_inicio' if USAR_NOVO_MODELO else 'data'

def get_user_type_field():
    """Retorna o nome do campo de tipo de usuário"""
    return 'tipo' if USAR_NOVO_MODELO else 'perfil'

# ========== MAPEAMENTO DE TEMPLATES ==========

def get_template_mapping():
    """Retorna o mapeamento de templates baseado no modelo"""
    if USAR_NOVO_MODELO:
        return {
            'home': 'cli/home_novo.html',
            'aplicar': 'cli/aplicar_novo.html',
            'listar': 'cli/listar_novo.html',
            'formulario': 'cli/formulario_novo.html'
        }
    else:
        return {
            'home': 'cli/home.html',
            'aplicar': 'cli/aplicar_checklist.html',
            'listar': 'cli/listar_checklists.html',
            'formulario': 'cli/formulario_visualizacao.html'
        }

# ========== HELPERS PARA QUERIES ==========

def get_audit_query_filters(query, current_user):
    """Aplica filtros apropriados na query de auditorias"""
    if USAR_NOVO_MODELO:
        from ..models import Loja
        return query.join(Loja).filter(
            Loja.cliente_id == current_user.cliente_id
        )
    else:
        # No modelo antigo, pode não ter restrição por cliente
        if hasattr(current_user, 'cliente_id'):
            return query.filter_by(usuario_id=current_user.id)
        return query

def format_audit_code(audit_id, date=None):
    """Formata o código da auditoria"""
    if USAR_NOVO_MODELO:
        year = date.year if date else datetime.now().year
        return f"AUD-{year}-{audit_id:05d}"
    else:
        return f"CHK-{audit_id:04d}"

# ========== VALIDAÇÃO DE MIGRAÇÃO ==========

def check_migration_ready():
    """Verifica se o sistema está pronto para migração"""
    checks = {
        'database': check_database_schema(),
        'files': check_required_files(),
        'data': check_data_compatibility()
    }
    
    return all(checks.values()), checks

def check_database_schema():
    """Verifica se o schema do banco suporta o novo modelo"""
    try:
        from ..models import db
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if USAR_NOVO_MODELO:
            required_tables = ['loja', 'bloco_formulario', 'nao_conformidade', 'plano_acao']
            return all(table in tables for table in required_tables)
        else:
            required_tables = ['avaliado', 'formulario', 'pergunta', 'auditoria']
            return all(table in tables for table in required_tables)
    except:
        return False

def check_required_files():
    """Verifica se os arquivos necessários existem"""
    import os
    base_path = os.path.dirname(os.path.dirname(__file__))
    
    if USAR_NOVO_MODELO:
        required_files = [
            'templates/cli/home_novo.html',
            'templates/cli/aplicar_novo.html'
        ]
    else:
        required_files = [
            'templates/cli/home.html',
            'templates/cli/aplicar_checklist.html'
        ]
    
    return all(
        os.path.exists(os.path.join(base_path, f)) 
        for f in required_files
    )

def check_data_compatibility():
    """Verifica se os dados existentes são compatíveis"""
    # Implementar verificações de compatibilidade de dados
    return True

# ========== FUNÇÃO DE MIGRAÇÃO ==========

def migrate_to_new_model():
    """Migra dados do modelo antigo para o novo"""
    from ..models import db, Cliente, Formulario, Pergunta, Auditoria, Resposta
    
    if not USAR_NOVO_MODELO:
        print("⚠️ Configuração atual usa modelo antigo. Configure USAR_NOVO_MODELO=True primeiro.")
        return False
    
    try:
        # Importar modelos antigos e novos
        from ..models import Avaliado, Loja, BlocoFormulario
        
        print("🔄 Iniciando migração...")
        
        # 1. Migrar Avaliados para Lojas
        avaliados = Avaliado.query.all()
        for avaliado in avaliados:
            # Verificar se já existe
            loja_existente = Loja.query.filter_by(nome=avaliado.nome).first()
            if not loja_existente:
                loja = Loja(
                    codigo=f"LJ{avaliado.id:04d}",
                    nome=avaliado.nome,
                    tipo='Loja',
                    endereco=avaliado.endereco,
                    email=avaliado.email,
                    cliente_id=avaliado.cliente_id,
                    grupo_id=avaliado.grupo_id if hasattr(avaliado, 'grupo_id') else None,
                    ativa=True
                )
                db.session.add(loja)
        
        db.session.flush()
        print(f"✅ {len(avaliados)} avaliados migrados para lojas")
        
        # 2. Adicionar blocos aos formulários existentes
        formularios = Formulario.query.all()
        for form in formularios:
            if not form.blocos.first():
                bloco = BlocoFormulario(
                    nome="Bloco Principal",
                    ordem=1,
                    formulario_id=form.id
                )
                db.session.add(bloco)
                db.session.flush()
                
                # Associar perguntas ao bloco
                for idx, pergunta in enumerate(form.perguntas):
                    pergunta.bloco_id = bloco.id
                    pergunta.ordem = idx + 1
        
        print(f"✅ {len(formularios)} formulários atualizados com blocos")
        
        # 3. Atualizar auditorias
        auditorias = Auditoria.query.all()
        for aud in auditorias:
            if hasattr(aud, 'avaliado_id') and aud.avaliado_id:
                # Encontrar loja correspondente
                avaliado = Avaliado.query.get(aud.avaliado_id)
                if avaliado:
                    loja = Loja.query.filter_by(nome=avaliado.nome).first()
                    if loja:
                        aud.loja_id = loja.id
                        
            # Adicionar campos novos
            if not hasattr(aud, 'codigo') or not aud.codigo:
                aud.codigo = format_audit_code(aud.id, aud.data if hasattr(aud, 'data') else None)
            
            if not hasattr(aud, 'status') or not aud.status:
                aud.status = 'CONCLUIDA'
            
            if hasattr(aud, 'data') and not hasattr(aud, 'data_inicio'):
                aud.data_inicio = aud.data
                aud.data_conclusao = aud.data
        
        print(f"✅ {len(auditorias)} auditorias migradas")
        
        db.session.commit()
        print("🎉 Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro na migração: {str(e)}")
        return False

# ========== FUNÇÃO PARA REVERTER ==========

def rollback_to_old_model():
    """Reverte para o modelo antigo (use com cuidado!)"""
    if USAR_NOVO_MODELO:
        print("⚠️ Configure USAR_NOVO_MODELO=False para usar o modelo antigo")
        return False
    
    print("✅ Sistema configurado para usar modelo antigo")
    return True