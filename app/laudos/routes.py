import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from ..models import db, LaudoMicrobiologico  # ✅ Importa o db e o modelo

laudos_bp = Blueprint('laudos', __name__, template_folder='templates')

UPLOAD_FOLDER = 'static/uploads/laudos'

@laudos_bp.route('/laudos', methods=['GET', 'POST'])
def cadastrar_laudo():
    if request.method == 'POST':
        data_coleta = request.form['data_coleta']
        tipo_amostra = request.form['tipo_amostra']
        local = request.form['local']
        resultado = request.form['resultado']
        observacoes = request.form.get('observacoes')
        responsavel = request.form['responsavel']
        arquivo = request.files.get('arquivo')

        nome_arquivo = None
        if arquivo and arquivo.filename:
            nome_arquivo = secure_filename(arquivo.filename)
            caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            arquivo.save(caminho)

        laudo = LaudoMicrobiologico(
            data_coleta=datetime.strptime(data_coleta, '%Y-%m-%d'),
            tipo_amostra=tipo_amostra,
            local=local,
            resultado=resultado,
            observacoes=observacoes,
            responsavel=responsavel,
            arquivo=nome_arquivo
        )

        db.session.add(laudo)
        db.session.commit()
        flash('Laudo registrado com sucesso.', 'success')
        return redirect(url_for('laudos.cadastrar_laudo'))

    laudos = LaudoMicrobiologico.query.order_by(LaudoMicrobiologico.data_coleta.desc()).all()
    return render_template('laudos/lista.html', laudos=laudos)
