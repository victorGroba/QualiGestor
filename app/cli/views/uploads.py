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
from ..utils import allowed_file

# Importa Modelos
from ...models import db, RespostaPergunta, FotoResposta, AplicacaoQuestionario

# ===================== UPLOAD DE FOTOS (CORRIGIDO) =====================

@cli_bp.route('/resposta/<int:resposta_id>/upload-foto', methods=['POST'])
@login_required
@csrf.exempt
def upload_foto_por_id(resposta_id):
    """
    Recebe upload vinculado diretamente ao ID da Resposta.
    URL usada pelo JS: /cli/resposta/<id>/upload-foto
    """
    try:
        # 1. Busca a Resposta no Banco (Para saber quem é o "pai" da foto)
        resp = RespostaPergunta.query.get(resposta_id)
        if not resp:
            # Se não achou a resposta, retorna erro para o JS tentar de novo
            return jsonify({'erro': 'Resposta ainda não sincronizada. Tente novamente.'}), 404

        # 2. Segurança: Verifica se a aplicação pertence ao cliente logado
        app = AplicacaoQuestionario.query.get(resp.aplicacao_id)
        if not app or app.avaliado.cliente_id != current_user.cliente_id:
            return jsonify({'erro': 'Acesso negado à aplicação.'}), 403

        # 3. Validação do Arquivo
        if 'foto' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['foto']
        if not file or file.filename == '':
            return jsonify({'erro': 'Arquivo vazio'}), 400
        
        # Aceita jpg, png, jpeg, gif, webp
        if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
            return jsonify({'erro': 'Formato inválido (apenas imagens).'}), 400

        # 4. Preparação para Salvar
        # Recuperamos IDs do objeto 'resp' para manter o padrão de nomeação
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        new_filename = f"{resp.aplicacao_id}_{resp.pergunta_id}_{uuid.uuid4().hex[:8]}.{ext}"

        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # 5. Salva no Disco
        caminho_completo = os.path.join(upload_folder, new_filename)
        file.save(caminho_completo)

        # 6. Atualiza Banco de Dados
        # a) Atualiza a "capa" da resposta (para compatibilidade com relatórios antigos)
        resp.caminho_foto = new_filename
        
        # b) Insere na tabela de múltiplas fotos (FotoResposta)
        nova_foto = FotoResposta(
            caminho=new_filename,
            resposta_id=resp.id,
            data_upload=db.func.now()
        )
        db.session.add(nova_foto)
        
        # Commit da transação (Aqui que pode dar erro se o banco estiver travado)
        db.session.commit()

        # Retorna SUCESSO com IDs (Essencial para o botão de deletar funcionar no JS)
        return jsonify({
            'sucesso': True, 
            'arquivo': new_filename,
            'resposta_id': resp.id,
            'foto_id': nova_foto.id 
        })

    except Exception as e:
        db.session.rollback()
        # Log do erro real no terminal
        current_app.logger.error(f"ERRO FATAL UPLOAD: {str(e)}")
        # Retorna 500 para o App saber que deve manter a foto na fila
        return jsonify({'erro': f"Erro no servidor: {str(e)}"}), 500

# ===================== REMOÇÃO DE FOTOS =====================

@cli_bp.route('/foto/<int:foto_id>/deletar', methods=['DELETE'])
@login_required
@csrf.exempt
def deletar_foto_por_id(foto_id):
    """Rota de deleção via ID da foto (Segura)."""
    try:
        foto = FotoResposta.query.get(foto_id)
        if not foto:
            return jsonify({'erro': 'Foto não encontrada'}), 404
        
        # Validação de Segurança
        resp = RespostaPergunta.query.get(foto.resposta_id)
        app = AplicacaoQuestionario.query.get(resp.aplicacao_id)
        if app.avaliado.cliente_id != current_user.cliente_id:
            return jsonify({'erro': 'Acesso negado'}), 403

        nome_arquivo = foto.caminho

        # Remove do Banco
        db.session.delete(foto)
        
        # Se essa era a foto de capa, limpa a referência na resposta
        if resp.caminho_foto == nome_arquivo:
            resp.caminho_foto = None
            
        db.session.commit()

        # Remove do Disco (Opcional, mas recomendado para limpar espaço)
        try:
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Erro ao deletar arquivo físico: {e}")

        return jsonify({'sucesso': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===================== SERVIR ARQUIVOS =====================

from werkzeug.exceptions import NotFound # Adicione este import no topo se não tiver, ou use try/except genérico

# ... (restante do código) ...

@cli_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    """
    Rota Inteligente:
    1. Tenta buscar na pasta de Uploads (Fotos novas).
    2. Se não achar, busca na pasta Static/img (Fotos antigas/legado).
    """
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    static_folder = os.path.join(current_app.static_folder, 'img')
    
    # Tentativa 1: Pasta de Uploads (Padrão Novo)
    try:
        return send_from_directory(upload_folder, filename)
    except Exception:
        # Tentativa 2: Pasta Static (Legado)
        try:
            return send_from_directory(static_folder, filename)
        except Exception:
            # Se não achar em nenhum dos dois, aí sim é 404
            abort(404)