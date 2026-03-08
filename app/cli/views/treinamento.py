# app/cli/views/treinamento.py
import os
from datetime import datetime
from flask import request, redirect, url_for, flash, current_app, render_template
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

# Importa o Blueprint da pasta pai (app/cli/__init__.py)
from .. import cli_bp
from ..utils import admin_required, log_acao, render_template_safe
from ...models import db, Treinamento, Avaliado, Grupo, TipoUsuario

# Configurações de upload
UPLOAD_FOLDER_TREINAMENTOS = os.path.join('app', 'static', 'uploads', 'treinamentos')
ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@cli_bp.route('/treinamentos/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_treinamento():
    if request.method == 'POST':
        try:
            tema = request.form.get('tema')
            data_str = request.form.get('data')
            avaliado_id = request.form.get('avaliado_id')

            if not all([tema, data_str, avaliado_id]):
                flash("Todos os campos de texto são obrigatórios.", "danger")
                return redirect(url_for('cli.novo_treinamento'))

            # Parse data
            try:
                data_treinamento = datetime.strptime(data_str, "%Y-%m-%d")
            except ValueError:
                flash("Formato de data inválido.", "danger")
                return redirect(url_for('cli.novo_treinamento'))

            avaliado = Avaliado.query.get(avaliado_id)
            if not avaliado or avaliado.cliente_id != current_user.cliente_id:
                flash("Unidade inválida.", "danger")
                return redirect(url_for('cli.novo_treinamento'))

            # Processa arquivos
            arquivo_ppt = request.files.get('arquivo_ppt')
            arquivo_lista = request.files.get('arquivo_lista')

            ppt_path = None
            lista_path = None

            os.makedirs(UPLOAD_FOLDER_TREINAMENTOS, exist_ok=True)

            if arquivo_ppt and arquivo_ppt.filename != '' and allowed_file(arquivo_ppt.filename):
                filename = secure_filename(f"ppt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{arquivo_ppt.filename}")
                filepath = os.path.join(UPLOAD_FOLDER_TREINAMENTOS, filename)
                arquivo_ppt.save(filepath)
                ppt_path = f"uploads/treinamentos/{filename}"

            if arquivo_lista and arquivo_lista.filename != '' and allowed_file(arquivo_lista.filename):
                filename = secure_filename(f"lista_{avaliado_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{arquivo_lista.filename}")
                filepath = os.path.join(UPLOAD_FOLDER_TREINAMENTOS, filename)
                arquivo_lista.save(filepath)
                lista_path = f"uploads/treinamentos/{filename}"

            novo_treinamento = Treinamento(
                tema=tema,
                data=data_treinamento,
                avaliado_id=int(avaliado_id),
                grupo_id=avaliado.grupo_id,
                cliente_id=current_user.cliente_id,
                criado_por_id=current_user.id,
                materiais_arquivo=ppt_path,
                lista_presenca_arquivo=lista_path
            )

            db.session.add(novo_treinamento)
            db.session.commit()

            log_acao("Criou Treinamento", {"tema": tema, "avaliado_id": avaliado_id}, "Treinamento", novo_treinamento.id)
            flash("Treinamento registrado com sucesso!", "success")
            return redirect(url_for('cli.index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar treinamento: {str(e)}", "danger")

    # Para exibir o form (GET)
    ranchos = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Avaliado.nome).all()
    return render_template_safe('cli/treinamento_form.html', ranchos=ranchos)
