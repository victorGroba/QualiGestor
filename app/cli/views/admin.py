# app/cli/views/admin.py
from flask import request, redirect, url_for, flash, current_app, render_template
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

# Importa o Blueprint da pasta pai (app/cli/__init__.py)
from .. import cli_bp

# Importa os utilitários criados no passo anterior
from ..utils import (
    admin_required, log_acao, render_template_safe, get_avaliados_usuario
)

# Importa os modelos (ajuste o caminho se necessário)
from ...models import (
    db, Usuario, Cliente, Grupo, Avaliado,
    CategoriaIndicador, Topico, ConfiguracaoCliente, 
    TipoUsuario, usuario_grupos
)

# ===================== GESTÃO DE AVALIADOS (RANCHOS) =====================

@cli_bp.route('/avaliados', endpoint='listar_avaliados')
@login_required
def listar_avaliados():
    """Lista avaliados com filtro por Grupo (GAP)."""
    try:
        grupos = Grupo.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        ).order_by(Grupo.nome).all()

        query = Avaliado.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        )

        grupo_id = request.args.get('grupo_id')
        if grupo_id:
            query = query.filter_by(grupo_id=grupo_id)
        
        avaliados = query.order_by(Avaliado.nome).all()
        
        return render_template_safe('cli/listar_avaliados.html', 
                                  avaliados=avaliados, 
                                  grupos=grupos,
                                  grupo_selecionado=grupo_id)
    except Exception as e:
        flash(f"Erro ao carregar avaliados: {str(e)}", "danger")
        return redirect(url_for('cli.index'))

@cli_bp.route('/avaliados/novo', methods=['GET', 'POST'])
@cli_bp.route('/avaliados/cadastrar', methods=['GET', 'POST'], endpoint='cadastrar_avaliado')
@login_required
def novo_avaliado():
    """Cadastra um novo avaliado."""
    # Verifica se é admin (para selecionar cliente, se multi-cliente)
    is_admin = False
    try:
        is_admin = (current_user.tipo == TipoUsuario.ADMIN)
    except:
        is_admin = (str(getattr(current_user, 'tipo', '')).upper() == 'ADMIN')

    if request.method == 'POST':
        try:
            nome = (request.form.get('nome') or '').strip()
            codigo = (request.form.get('codigo') or '').strip()
            endereco = (request.form.get('endereco') or '').strip()
            email = (request.form.get('email') or '').strip()
            idioma = (request.form.get('idioma') or '').strip()
            cliente_id_raw = request.form.get('cliente_id')
            grupo_id_raw = request.form.get('grupo_id')

            if not nome:
                flash("Nome do avaliado é obrigatório.", "danger")
                return redirect(url_for('cli.cadastrar_avaliado'))

            # Define cliente_id
            if is_admin and cliente_id_raw:
                cliente_id = int(cliente_id_raw)
            else:
                cliente_id = current_user.cliente_id

            # Valida grupo
            grupo_id = None
            if grupo_id_raw:
                grupo_id = int(grupo_id_raw)

            # Valida código único
            if codigo:
                ja_existe = Avaliado.query.filter_by(codigo=codigo, cliente_id=cliente_id).first()
                if ja_existe:
                    flash("Já existe um avaliado com este código.", "warning")
                    return redirect(url_for('cli.cadastrar_avaliado'))

            avaliado = Avaliado(
                nome=nome,
                codigo=codigo or None,
                endereco=endereco or None,
                grupo_id=grupo_id,
                cliente_id=cliente_id,
                ativo=True,
                email=email or None,
                idioma=idioma or None
            )

            db.session.add(avaliado)
            db.session.commit()

            log_acao("Criou avaliado", {"nome": nome, "codigo": codigo}, "Avaliado", avaliado.id)
            flash(f"Avaliado '{nome}' criado com sucesso!", "success")
            return redirect(url_for('cli.listar_avaliados'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar avaliado: {str(e)}", "danger")
            return redirect(url_for('cli.cadastrar_avaliado'))

    # GET
    grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome).all()
    clientes = []
    if is_admin:
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()

    return render_template_safe(
        'cli/cadastrar_avaliado.html',
        clientes=clientes,
        grupos=grupos,
        is_admin=is_admin
    )

@cli_bp.route('/avaliado/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_avaliado(id):
    """Edita um avaliado existente."""
    avaliado = Avaliado.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            endereco = request.form.get('endereco', '').strip()
            email = request.form.get('email', '').strip()
            grupo_id = request.form.get('grupo_id')
            codigo = request.form.get('codigo', '').strip()

            if not nome or not grupo_id:
                flash("Nome e GAP são obrigatórios.", "warning")
            else:
                avaliado.nome = nome
                avaliado.grupo_id = int(grupo_id)
                avaliado.endereco = endereco if endereco else None
                avaliado.email = email if email else None
                if codigo:
                    avaliado.codigo = codigo

                db.session.commit()
                flash(f"Rancho '{nome}' atualizado com sucesso!", "success")
                return redirect(url_for('cli.listar_avaliados'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {str(e)}", "danger")

    grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome).all()
    return render_template_safe('cli/editar_avaliado.html', avaliado=avaliado, grupos=grupos)

@cli_bp.route('/avaliado/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_avaliado(id):
    """Inativa um avaliado."""
    try:
        avaliado = Avaliado.query.get_or_404(id)
        if avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "danger")
            return redirect(url_for('cli.listar_avaliados'))

        avaliado.ativo = False
        db.session.commit()

        log_acao("Excluiu avaliado", {"id": id, "nome": avaliado.nome}, "Avaliado", id)
        flash("Avaliado excluído (inativado) com sucesso.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir avaliado: {str(e)}", "danger")

    return redirect(url_for('cli.listar_avaliados'))

# ===================== GESTÃO DE GRUPOS (GAPS) =====================

@cli_bp.route('/grupos', endpoint='listar_grupos')
@login_required
@admin_required
def listar_grupos():
    """Lista grupos (GAPs)."""
    try:
        grupos = Grupo.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).order_by(Grupo.nome).all()
        
        for grupo in grupos:
            grupo.total_avaliados = Avaliado.query.filter_by(
                grupo_id=grupo.id,
                ativo=True
            ).count()
        
        return render_template_safe('cli/listar_grupos.html', grupos=grupos)
    except Exception as e:
        flash(f"Erro ao carregar grupos: {str(e)}", "danger")
        return redirect(url_for('cli.index'))

@cli_bp.route('/grupo/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_grupo():
    """Cria novo grupo."""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            
            if not nome:
                flash('Nome do grupo é obrigatório.', 'error')
                return render_template_safe('cli/grupo_form.html')
            
            grupo = Grupo(
                nome=nome,
                descricao=descricao,
                cliente_id=current_user.cliente_id,
                ativo=True
            )
            
            db.session.add(grupo)
            db.session.commit()
            
            log_acao(f"Criou grupo: {nome}", None, "Grupo", grupo.id)
            flash(f'Grupo "{nome}" criado com sucesso!', 'success')
            return redirect(url_for('cli.listar_grupos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar grupo: {str(e)}', 'error')
    
    return render_template_safe('cli/grupo_form.html')

@cli_bp.route('/grupo/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_grupo(id):
    """Edita grupo."""
    grupo = Grupo.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()

            if not nome:
                flash("O nome do GAP é obrigatório.", "warning")
            else:
                grupo.nome = nome
                grupo.descricao = descricao if descricao else None
                db.session.commit()
                flash(f"GAP '{nome}' atualizado!", "success")
                return redirect(url_for('cli.listar_grupos'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao editar GAP: {str(e)}", "danger")

    return render_template_safe('cli/grupo_form.html', grupo=grupo)

@cli_bp.route('/grupo/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_grupo(id):
    """Exclui (inativa) grupo."""
    grupo = Grupo.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()
    
    ranchos_vinculados = Avaliado.query.filter_by(grupo_id=grupo.id, ativo=True).count()
    if ranchos_vinculados > 0:
        flash(f"Não é possível excluir: Existem {ranchos_vinculados} ranchos vinculados.", "danger")
    else:
        try:
            grupo.ativo = False
            db.session.commit()
            flash(f"GAP '{grupo.nome}' removido.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao excluir: {str(e)}", "danger")
            
    return redirect(url_for('cli.listar_grupos'))

# ===================== GESTÃO DE USUÁRIOS =====================

@cli_bp.route('/usuarios', endpoint='gerenciar_usuarios')
@login_required
@admin_required
def gerenciar_usuarios():
    """Gestão de usuários com Filtro por GAP."""
    try:
        grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome).all()
        query = Usuario.query.filter_by(cliente_id=current_user.cliente_id)

        filtro_grupo_id = request.args.get('grupo_id')
        if filtro_grupo_id and filtro_grupo_id.isdigit():
            gid = int(filtro_grupo_id)
            query = query.join(usuario_grupos, isouter=True).join(Avaliado, isouter=True).filter(
                or_(usuario_grupos.c.grupo_id == gid, Avaliado.grupo_id == gid)
            ).distinct()

        usuarios = query.order_by(Usuario.nome).all()
        
        stats = {
            'total': len(usuarios),
            'ativos': len([u for u in usuarios if u.ativo]),
            'admins': len([u for u in usuarios if u.tipo.name in ['SUPER_ADMIN', 'ADMIN']]),
            'operacional': len([u for u in usuarios if u.tipo.name not in ['SUPER_ADMIN', 'ADMIN']])
        }
        
        return render_template_safe('cli/gerenciar_usuarios.html',
                             usuarios=usuarios,
                             grupos=grupos,
                             filtro_grupo_id=filtro_grupo_id,
                             stats=stats)
    except Exception as e:
        flash(f"Erro ao carregar usuários: {str(e)}", "danger")
        return render_template_safe('cli/index.html')

@cli_bp.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    """Cria novo usuário com Multi-GAP."""
    if request.method == 'GET':
        gaps = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome).all()
        ranchos = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Avaliado.nome).all()
        return render_template_safe('cli/usuario_form.html', grupos=gaps, ranchos=ranchos)

    try:
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        tipo_str = request.form.get('tipo')
        gaps_ids = request.form.getlist('grupos_acesso')
        avaliado_id = request.form.get('avaliado_id')

        if not all([nome, email, tipo_str]):
            flash('Nome, Email e Tipo são obrigatórios.', 'warning')
            return redirect(url_for('cli.novo_usuario'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está em uso.', 'warning')
            return redirect(url_for('cli.novo_usuario'))

        # Validações de Vínculo
        if tipo_str in ['auditor', 'gestor'] and not gaps_ids:
            flash('Consultoras e Gestores precisam de pelo menos um GAP.', 'warning')
            return redirect(url_for('cli.novo_usuario'))
        if tipo_str == 'usuario' and not avaliado_id:
            flash('Usuários Locais precisam de um Rancho.', 'warning')
            return redirect(url_for('cli.novo_usuario'))

        # Enum
        try:
            tipo_enum = TipoUsuario[tipo_str.upper()]
        except KeyError:
            flash(f"Tipo inválido: {tipo_str}", "error")
            return redirect(url_for('cli.novo_usuario'))

        usuario = Usuario(
            nome=nome,
            email=email,
            tipo=tipo_enum,
            cliente_id=current_user.cliente_id,
            avaliado_id=int(avaliado_id) if avaliado_id else None,
            senha_hash=generate_password_hash('123456'),
            ativo=True
        )

        # Processar GAPs
        if usuario.tipo in [TipoUsuario.GESTOR, TipoUsuario.AUDITOR]:
            if gaps_ids:
                primeiro = True
                for gid in gaps_ids:
                    gap = Grupo.query.get(int(gid))
                    if gap:
                        usuario.grupos_acesso.append(gap)
                        if primeiro:
                            usuario.grupo_id = gap.id # Legado
                            primeiro = False
        elif usuario.tipo == TipoUsuario.USUARIO:
            if usuario.avaliado_id:
                rancho = Avaliado.query.get(usuario.avaliado_id)
                if rancho and rancho.grupo_id:
                    usuario.grupo_id = rancho.grupo_id
                    gap_rancho = Grupo.query.get(rancho.grupo_id)
                    if gap_rancho:
                        usuario.grupos_acesso.append(gap_rancho)

        db.session.add(usuario)
        db.session.commit()
        log_acao(f"Criou usuário: {nome}", None, "Usuario", usuario.id)
        flash(f'Usuário {nome} criado! Senha padrão: 123456', 'success')
        return redirect(url_for('cli.gerenciar_usuarios'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar usuário: {str(e)}', 'danger')
        return redirect(url_for('cli.novo_usuario'))

@cli_bp.route('/usuario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    """Edita usuário."""
    usuario = Usuario.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()
    
    gaps = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Grupo.nome).all()
    ranchos = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Avaliado.nome).all()

    if request.method == 'POST':
        try:
            usuario.nome = request.form.get('nome')
            usuario.email = request.form.get('email')
            tipo_str = request.form.get('tipo')
            senha = request.form.get('senha')
            gaps_ids = request.form.getlist('grupos_acesso')
            avaliado_id = request.form.get('avaliado_id')

            if tipo_str:
                try:
                    usuario.tipo = TipoUsuario[tipo_str.upper()]
                except KeyError: pass

            # Refazer vínculos
            usuario.grupos_acesso = []
            
            if usuario.tipo in [TipoUsuario.GESTOR, TipoUsuario.AUDITOR]:
                usuario.avaliado_id = None
                if gaps_ids:
                    primeiro = True
                    for gid in gaps_ids:
                        gap = Grupo.query.get(int(gid))
                        if gap:
                            usuario.grupos_acesso.append(gap)
                            if primeiro:
                                usuario.grupo_id = gap.id
                                primeiro = False
                else:
                    usuario.grupo_id = None
                    
            elif usuario.tipo == TipoUsuario.USUARIO:
                usuario.avaliado_id = int(avaliado_id) if avaliado_id else None
                if usuario.avaliado_id:
                    rancho = Avaliado.query.get(usuario.avaliado_id)
                    if rancho and rancho.grupo_id:
                        usuario.grupo_id = rancho.grupo_id
                        gap_rancho = Grupo.query.get(rancho.grupo_id)
                        if gap_rancho:
                            usuario.grupos_acesso.append(gap_rancho)
                else:
                    usuario.grupo_id = None
            else:
                usuario.grupo_id = None
                usuario.avaliado_id = None

            if senha and len(senha.strip()) > 0:
                usuario.senha_hash = generate_password_hash(senha)

            db.session.commit()
            flash('Usuário atualizado.', 'success')
            return redirect(url_for('cli.gerenciar_usuarios'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'error')

    return render_template_safe('cli/usuario_editar.html', usuario=usuario, gaps=gaps, ranchos=ranchos)

@cli_bp.route('/usuario/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_usuario(id):
    """Exclui usuário."""
    if id == current_user.id:
        flash("Você não pode excluir a si mesmo!", "warning")
        return redirect(url_for('cli.gerenciar_usuarios'))
        
    usuario = Usuario.query.filter_by(id=id, cliente_id=current_user.cliente_id).first_or_404()
    
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash(f'Usuário {usuario.nome} removido.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'error')
        
    return redirect(url_for('cli.gerenciar_usuarios'))

# ===================== CONFIGURAÇÕES E CATEGORIAS =====================

@cli_bp.route('/configuracoes')
@login_required
@admin_required
def configuracoes():
    """Configurações do sistema."""
    try:
        config = ConfiguracaoCliente.query.filter_by(cliente_id=current_user.cliente_id).first()
        if not config:
            config = ConfiguracaoCliente(
                cliente_id=current_user.cliente_id,
                logo_url='', cor_primaria='#007bff', cor_secundaria='#6c757d',
                mostrar_notas=True, permitir_fotos=True, obrigar_plano_acao=True
            )
            db.session.add(config)
            db.session.commit()
        
        return render_template_safe('cli/configuracoes.html', config=config)
    except Exception as e:
        flash(f"Erro ao carregar configurações: {str(e)}", "danger")
        return redirect(url_for('cli.index'))

@cli_bp.route('/configuracoes/categorias', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_categorias():
    """Gestão de categorias SDAB."""
    try:
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            cor = request.form.get('cor', '#4e73df')
            ordem = int(request.form.get('ordem', 0))
            
            if nome:
                nova_cat = CategoriaIndicador(
                    nome=nome, cor=cor, ordem=ordem,
                    cliente_id=current_user.cliente_id, ativo=True
                )
                db.session.add(nova_cat)
                db.session.commit()
                flash(f"Categoria '{nome}' criada!", "success")
            else:
                flash("Nome obrigatório.", "warning")
            return redirect(url_for('cli.gerenciar_categorias'))

        categorias = CategoriaIndicador.query.filter_by(
            cliente_id=current_user.cliente_id, ativo=True
        ).order_by(CategoriaIndicador.ordem).all()
        
        return render_template_safe('cli/gerenciar_categorias.html', categorias=categorias)
    except Exception as e:
        flash(f"Erro: {str(e)}", "danger")
        return redirect(url_for('cli.configuracoes'))

@cli_bp.route('/configuracoes/categoria/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_categoria(id):
    """Exclui categoria."""
    try:
        cat = CategoriaIndicador.query.get_or_404(id)
        if cat.cliente_id != current_user.cliente_id:
            flash("Acesso negado", "error")
            return redirect(url_for('cli.gerenciar_categorias'))
            
        # Desvincula tópicos
        topicos = Topico.query.filter_by(categoria_indicador_id=id).all()
        for t in topicos:
            t.categoria_indicador_id = None
            
        db.session.delete(cat)
        db.session.commit()
        flash("Categoria removida.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir: {str(e)}", "danger")
        
    return redirect(url_for('cli.gerenciar_categorias'))

# ===================== PERFIL DO USUÁRIO =====================

@cli_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Alteração de dados do próprio usuário."""
    usuario_db = Usuario.query.get(current_user.id)
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            senha_atual = request.form.get('senha_atual')
            nova_senha = request.form.get('nova_senha')
            confirma_senha = request.form.get('confirma_senha')

            if nome: 
                usuario_db.nome = nome
            
            if nova_senha and nova_senha.strip():
                if nova_senha == '123456':
                    flash("Senha padrão não permitida. Escolha outra.", "warning")
                    return redirect(url_for('cli.perfil'))
                
                if len(nova_senha) < 6:
                    flash("Mínimo de 6 caracteres.", "warning")
                    return redirect(url_for('cli.perfil'))

                if not senha_atual or not check_password_hash(usuario_db.senha_hash, senha_atual):
                    flash("Senha atual incorreta.", "danger")
                    return redirect(url_for('cli.perfil'))
                
                if nova_senha != confirma_senha:
                    flash("Senhas não conferem.", "warning")
                    return redirect(url_for('cli.perfil'))
                
                usuario_db.senha_hash = generate_password_hash(nova_senha)
                flash("Senha alterada! Faça login novamente.", "success")
            else:
                flash("Perfil atualizado!", "success")

            db.session.commit()
            return redirect(url_for('cli.perfil'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {str(e)}", "danger")

    return render_template_safe('cli/perfil.html', usuario=usuario_db)