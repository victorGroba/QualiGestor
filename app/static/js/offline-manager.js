// =========================================================
// ARQUIVO: app/static/js/offline-manager.js
// VERSÃO: 3.1 (Atualizada com fix para iOS e Blobs)
// =========================================================

// 1. Configuração do Banco de Dados Local (IndexedDB)
const db = new Dexie('QualiGestorDB');

db.version(3).stores({
    respostas_pendentes: 'pergunta_id, aplicacao_id, dados_completos, timestamp',
    fotos_pendentes: 'id, aplicacao_id, pergunta_id, resposta_id, blob, nome, timestamp',
    fila_deletar: 'id_item, tipo, timestamp'
});

const OfflineManager = {
    
    // --- 1. SALVAR TEXTO (A Resposta da Pergunta) ---
    async salvarResposta(aplicacaoId, dados) {
        try {
            await db.respostas_pendentes.put({
                pergunta_id: dados.pergunta_id,
                aplicacao_id: aplicacaoId,
                dados_completos: dados,
                timestamp: Date.now()
            });

            // Tenta enviar imediatamente se tiver internet
            if (navigator.onLine) {
                return await this.sincronizarUma(dados.pergunta_id);
            } else {
                return { status: 'pendente', msg: 'Salvo no dispositivo (Sem internet)' };
            }
        } catch (e) {
            console.error("Erro ao salvar resposta local:", e);
            throw e;
        }
    },

    // --- 2. SINCRONIZAR UMA PERGUNTA (Lógica Sequencial Blindada) ---
    async sincronizarUma(perguntaId) {
        let respostaIdServidor = null;
        let aplicacaoId = null;

        // A) TENTA SINCRONIZAR O TEXTO PRIMEIRO
        const textoItem = await db.respostas_pendentes.get(perguntaId);
        
        if (textoItem) {
            aplicacaoId = textoItem.aplicacao_id;
            try {
                // Recupera CSRF Global ou tenta buscar do DOM
                const csrf = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : 
                             (document.querySelector('input[name="csrf_token"]')?.value || '');

                const response = await fetch(`/cli/aplicacao/${aplicacaoId}/salvar-resposta`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf
                    },
                    body: JSON.stringify(textoItem.dados_completos)
                });

                if (response.ok) {
                    const data = await response.json();
                    respostaIdServidor = data.resposta_id; // GUARDAMOS O ID GERADO
                    
                    // Remove o texto da fila de pendentes
                    await db.respostas_pendentes.delete(perguntaId);
                    
                    // Feedback visual se estiver na tela
                    const icon = document.getElementById(`status-icon-${perguntaId}`);
                    if (icon) {
                        icon.innerHTML = '<i class="fas fa-check text-success"></i>';
                        setTimeout(() => icon.innerHTML = '', 2000);
                    }
                } else {
                    console.warn(`Erro servidor texto (${perguntaId}):`, response.status);
                    return { status: 'erro', msg: 'Servidor rejeitou texto' };
                }
            } catch (e) {
                console.error(`Erro rede texto (${perguntaId}):`, e);
                return { status: 'erro', msg: 'Sem conexão' };
            }
        }

        // B) TENTA SINCRONIZAR AS FOTOS (Usando o ID do passo anterior ou o que já estiver salvo)
        const fotosItems = await db.fotos_pendentes
            .where('pergunta_id')
            .equals(perguntaId.toString())
            .toArray();
        
        if (fotosItems.length > 0) {
            let enviouAlguma = false;

            for (const fotoItem of fotosItems) {
                // Se não temos ID do servidor (nem do passo anterior, nem salvo no item), pulamos
                // (Isso evita tentar enviar foto "orfã")
                let rid = respostaIdServidor || fotoItem.resposta_id;
                
                // Tenta buscar ID do DOM se estivermos na página (Fallback)
                if (!rid && typeof document !== 'undefined') {
                    const inputDom = document.querySelector(`[data-pergunta-id="${perguntaId}"]`);
                    if (inputDom && inputDom.dataset.respostaId) rid = inputDom.dataset.respostaId;
                }

                if (!rid) {
                    console.log(`Foto ${fotoItem.id} aguardando sincronização do texto para obter ID.`);
                    continue; 
                }

                try {
                    const formData = new FormData();
                    
                    // 1. Tratamento do Nome (Segurança)
                    let safeName = fotoItem.nome || `foto_${Date.now()}.jpg`;
                    safeName = safeName.replace(/[^a-zA-Z0-9._-]/g, ''); // Remove caracteres especiais
                    if (!safeName.match(/\.(jpg|jpeg|png|webp)$/i)) safeName += '.jpg'; // Garante extensão

                    // 2. Tratamento do Arquivo (Blob ou Base64)
                    let arquivoParaEnvio;

                    if (fotoItem.tipo === 'base64' || (typeof fotoItem.blob === 'string' && fotoItem.blob.startsWith('data:'))) {
                        // Converte Base64 de volta para Blob
                        const res = await fetch(fotoItem.blob);
                        const blobRecuperado = await res.blob();
                        arquivoParaEnvio = new File([blobRecuperado], safeName, { type: 'image/jpeg' });
                    } else {
                        // Já é um Blob/File
                        arquivoParaEnvio = new File([fotoItem.blob], safeName, { type: fotoItem.blob.type || 'image/jpeg' });
                    }

                    formData.append('foto', arquivoParaEnvio, safeName);

                    // Pega o CSRF novamente para garantir
                    const csrf = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : 
                                 (document.querySelector('input[name="csrf_token"]')?.value || '');

                    const responseFoto = await fetch(`/cli/resposta/${rid}/upload-foto`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrf },
                        body: formData
                    });

                    if (responseFoto.ok) {
                        // SUCESSO: Remove do banco local
                        await db.fotos_pendentes.delete(fotoItem.id);
                        
                        // Atualiza visualmente se possível
                        if (typeof document !== 'undefined') {
                            const elLocal = document.getElementById(`foto-local-${fotoItem.id}`);
                            if (elLocal) elLocal.remove();
                            // Se existir função de criar elemento server, pode chamar aqui (opcional)
                        }
                        enviouAlguma = true;
                    } 
                    else if (responseFoto.status === 400) {
                        // ERRO 400 (Arquivo Inválido): Deleta para não travar a fila
                        console.error("Servidor rejeitou arquivo (400). Removendo da fila.");
                        await db.fotos_pendentes.delete(fotoItem.id);
                        if (typeof document !== 'undefined') {
                            const elLocal = document.getElementById(`foto-local-${fotoItem.id}`);
                            if (elLocal) elLocal.remove();
                        }
                    }
                } catch (error) {
                    console.log(`Erro upload foto ${fotoItem.id}:`, error);
                }
            }
            if (enviouAlguma) return { status: 'sincronizado', msg: 'Fotos enviadas' };
        }

        return { status: 'ok', msg: 'Processo finalizado' };
    },

    // --- 3. SINCRONIZAR TUDO (Batch) ---
    async sincronizarTudo() {
        if (!navigator.onLine) {
            console.log("[OfflineManager] Sem internet. Sincronização cancelada.");
            return;
        }
        
        console.log("[OfflineManager] Iniciando sincronização completa...");

        // Pega todos os IDs únicos que têm pendências (texto ou foto)
        const textos = await db.respostas_pendentes.toArray();
        const fotos = await db.fotos_pendentes.toArray();
        
        const idsParaSincronizar = new Set();
        textos.forEach(t => idsParaSincronizar.add(t.pergunta_id));
        fotos.forEach(f => idsParaSincronizar.add(f.pergunta_id));

        if (idsParaSincronizar.size === 0) {
            console.log("[OfflineManager] Nada pendente.");
            return;
        }

        // Atualiza contador visual se a função existir na página
        if (typeof atualizarContadorPendencias === 'function') atualizarContadorPendencias();

        // Itera e sincroniza um por um
        for (const pId of idsParaSincronizar) {
            await this.sincronizarUma(pId);
        }
        
        // Atualiza contador final
        if (typeof atualizarContadorPendencias === 'function') atualizarContadorPendencias();
        console.log("[OfflineManager] Sincronização em lote concluída.");
    },
    
    // Funções auxiliares
    async temPendente(perguntaId) {
        const t = await db.respostas_pendentes.get(perguntaId);
        const fCount = await db.fotos_pendentes.where('pergunta_id').equals(perguntaId.toString()).count();
        return (t || fCount > 0);
    }
};

// =========================================================
// 4. LISTENERS AUTOMÁTICOS (A "Mágica" do Background)
// =========================================================

// Gatilho 1: Quando a internet cai e volta
window.addEventListener('online', () => {
    console.log("[Auto-Sync] Internet detectada (Evento Online)");
    OfflineManager.sincronizarTudo();
});

// Gatilho 2: Quando o app "acorda" ou volta para a tela (ESSENCIAL PARA IPHONE/IOS)
// Isso resolve o problema de andar com o celular no bolso e ele não sincronizar sozinho
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && navigator.onLine) {
        console.log("[Auto-Sync] App voltou para a tela (Wake Up)");
        OfflineManager.sincronizarTudo();
    }
});

// Gatilho 3: Quando abre o app (Delay para não travar o carregamento inicial)
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => OfflineManager.sincronizarTudo(), 3000);
});