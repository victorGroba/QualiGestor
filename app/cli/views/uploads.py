# app/cli/views/uploads.py
import os
import uuid
from pathlib import Path
from flask import request, jsonify, current_app, send_from_directory, abort
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

# Importa Blueprint e CSRF
from .. import cli_bp, csrf

# Importa Utilitários
from ..utils import allowed_file, log_acao

# Importa Modelos
from ...models import db, RespostaPergunta, FotoResposta, AplicacaoQuestionario

# ===================== UPLOAD DE FOTOS (AJAX) =====================

@cli_bp.route('/upload/foto_resposta', methods=['POST'])
@login_required
@csrf.exempt
def upload_foto_resposta():
    """Recebe upload via AJAX (Dropzone ou Input File)."""
    try:
        # Verifica dados básicos
        if 'foto' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['foto']
        pergunta_id = request.form.get('pergunta_id')
        aplicacao_id = request.form.get('aplicacao_id')

        if not file or file.filename == '':
            return jsonify({'erro': 'Arquivo vazio'}), 400
        
        if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            return jsonify({'erro': 'Formato não permitido (apenas imagens).'}), 400

        # Verifica permissão na Aplicação
        app = AplicacaoQuestionario.query.get(aplicacao_id)
        if not app or app.avaliado.cliente_id != current_user.cliente_id:
            return jsonify({'erro': 'Acesso negado à aplicação.'}), 403

        # Gera nome seguro e único
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
        new_filename = f"{aplicacao_id}_{pergunta_id}_{uuid.uuid4().hex[:8]}.{ext}"

        # Garante diretório
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Salva arquivo
        file.save(os.path.join(upload_folder, new_filename))

        # Atualiza Banco de Dados
        # Lógica Híbrida: Suporta tanto campo único (Legado) quanto Multi-fotos
        resp = RespostaPergunta.query.filter_by(aplicacao_id=aplicacao_id, pergunta_id=pergunta_id).first()
        
        if not resp:
            # Se a resposta ainda não existe, cria (comportamento de upload antes de responder texto)
            resp = RespostaPergunta(aplicacao_id=aplicacao_id, pergunta_id=pergunta_id)
            db.session.add(resp)
            db.session.flush() # Para ter ID

        # 1. Atualiza campo principal (para exibir a 'capa' ou compatibilidade)
        resp.caminho_foto = new_filename
        
        # 2. Adiciona na tabela de múltiplas fotos (se existir no modelo)
        try:
            nova_foto = FotoResposta(
                caminho=new_filename,
                resposta_id=resp.id,
                data_upload=db.func.now()
            )
            db.session.add(nova_foto)
        except Exception:
            # Se a tabela FotoResposta não existir ou der erro, ignoramos (fallback legacy)
            pass

        db.session.commit()

        return jsonify({
            'sucesso': True, 
            'arquivo': new_filename,
            'resposta_id': resp.id
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro Upload: {e}")
        return jsonify({'erro': str(e)}), 500

# ===================== REMOÇÃO DE FOTOS =====================

@cli_bp.route('/deletar/foto_resposta', methods=['POST'])
@login_required
@csrf.exempt
def deletar_foto():
    """Remove foto do banco e (opcionalmente) do disco."""
    try:
        data = request.get_json()
        nome_arquivo = data.get('filename')
        resposta_id = data.get('resposta_id')

        if not nome_arquivo:
            return jsonify({'erro': 'Nome do arquivo necessário'}), 400

        # Busca a resposta para validar permissão
        resp = RespostaPergunta.query.get(resposta_id)
        if resp:
            app = AplicacaoQuestionario.query.get(resp.aplicacao_id)
            if app.avaliado.cliente_id != current_user.cliente_id:
                return jsonify({'erro': 'Acesso negado'}), 403

            # Limpa referência no campo principal
            if resp.caminho_foto == nome_arquivo:
                resp.caminho_foto = None

            # Remove da tabela FotoResposta
            FotoResposta.query.filter_by(caminho=nome_arquivo).delete()

            db.session.commit()

            # Remove do disco (Opcional - alguns sistemas preferem soft delete)
            try:
                path = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Erro ao deletar arquivo físico: {e}")

            return jsonify({'sucesso': True})

        return jsonify({'erro': 'Resposta não encontrada'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===================== SERVIR ARQUIVOS (SEGURANÇA) =====================

@cli_bp.route('/uploads/<path:filename>')
@login_required
def get_foto_resposta(filename):
    """
    Rota segura para exibir imagens. 
    Verifica se o usuário tem acesso à aplicação dona da foto.
    """
    try:
        # Tenta descobrir de quem é essa foto através do nome ou busca no banco
        # Formato esperado do nome: {app_id}_{perg_id}_{hash}.ext
        
        parts = filename.split('_')
        app_id = None
        
        if len(parts) >= 3 and parts[0].isdigit():
            app_id = int(parts[0])
        else:
            # Fallback: Tenta achar no banco pelo nome do arquivo
            foto_db = FotoResposta.query.filter_by(caminho=filename).first()
            if foto_db:
                app_id = foto_db.resposta.aplicacao_id
            else:
                resp_db = RespostaPergunta.query.filter_by(caminho_foto=filename).first()
                if resp_db:
                    app_id = resp_db.aplicacao_id

        # Se identificamos a App, verificamos segurança
        if app_id:
            app = AplicacaoQuestionario.query.get(app_id)
            if app and app.avaliado.cliente_id != current_user.cliente_id:
                abort(403) # Pertence a outro cliente
        
        # Se não achou app_id (arquivo antigo ou nome fora do padrão), 
        # deixamos passar SE o usuário for logado (risco menor, mas existente)
        # Idealmente, todo arquivo deveria ter rastreio.

        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        
        # Tenta servir do Upload Folder
        try:
            return send_from_directory(upload_folder, filename)
        except:
            # Fallback para Static (caso seja imagem padrão ou antiga)
            return send_from_directory(os.path.join(current_app.static_folder, 'img'), filename)

    except Exception as e:
        current_app.logger.error(f"Erro ao servir imagem: {e}")
        abort(404)