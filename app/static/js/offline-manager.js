// =========================================================
// ARQUIVO: app/static/js/offline-manager.js
// VERSÃO: 3.2 (BLINDADO CONTRA CRASH IOS + DETECÇÃO DE CONFLITO)
// =========================================================

const db = new Dexie('QualiGestorDB');

db.version(3).stores({
    respostas_pendentes: 'pergunta_id, aplicacao_id, dados_completos, timestamp',
    fotos_pendentes: 'id, aplicacao_id, pergunta_id, resposta_id, blob, nome, timestamp',
    fila_deletar: 'id_item, tipo, timestamp'
});

const OfflineManager = {
    
    // --- 1. SALVAR TEXTO ---
    async salvarResposta(aplicacaoId, dados) {
        try {
            await db.respostas_pendentes.put({
                pergunta_id: dados.pergunta_id,
                aplicacao_id: aplicacaoId,
                dados_completos: dados,
                timestamp: Date.now()
            });

            if (navigator.onLine) {
                return await this.sincronizarUma(dados.pergunta_id);
            } else {
                return { status: 'pendente', msg: 'Salvo localmente' };
            }
        } catch (e) {
            console.error("Erro Dexie:", e);
            throw e;
        }
    },

    // --- 2. SINCRONIZAR UMA PERGUNTA (Unitário) ---
    async sincronizarUma(perguntaId) {
        let respostaIdServidor = null;
        let aplicacaoId = null;

        // A) TEXTO
        const textoItem = await db.respostas_pendentes.get(perguntaId);
        if (textoItem) {
            aplicacaoId = textoItem.aplicacao_id;
            try {
                const csrf = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : 
                             (document.querySelector('input[name="csrf_token"]')?.value || '');

                const response = await fetch(`/cli/aplicacao/${aplicacaoId}/salvar-resposta`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                    body: JSON.stringify(textoItem.dados_completos)
                });

                if (response.ok) {
                    const data = await response.json();
                    respostaIdServidor = data.resposta_id;
                    await db.respostas_pendentes.delete(perguntaId);
                }
            } catch (e) {
                return { status: 'erro', msg: 'Sem conexão' };
            }
        }

        // B) FOTOS (Unitário e Seguro)
        // Aqui usamos primaryKeys para não carregar blobs pesados se houver muitas fotos
        const chavesFotos = await db.fotos_pendentes
            .where('pergunta_id').equals(perguntaId.toString())
            .primaryKeys();
        
        if (chavesFotos.length > 0) {
            for (const chave of chavesFotos) {
                const fotoItem = await db.fotos_pendentes.get(chave);
                if (!fotoItem) continue;

                let rid = respostaIdServidor || fotoItem.resposta_id;
                
                // Fallback: Tenta achar ID no DOM se estivermos na página
                if (!rid && typeof document !== 'undefined') {
                    const el = document.querySelector(`[data-pergunta-id="${perguntaId}"]`);
                    if (el && el.dataset.respostaId) rid = el.dataset.respostaId;
                }

                if (!rid) continue; // Sem ID, não dá pra enviar

                try {
                    const fd = new FormData();
                    let safeName = (fotoItem.nome || `foto_${Date.now()}.jpg`).replace(/[^a-zA-Z0-9._-]/g, '');
                    if (!safeName.match(/\.(jpg|jpeg|png|webp)$/i)) safeName += '.jpg';

                    // Recupera Blob
                    let arquivo;
                    if (fotoItem.tipo === 'base64' || (typeof fotoItem.blob === 'string')) {
                        const r = await fetch(fotoItem.blob);
                        const b = await r.blob();
                        arquivo = new File([b], safeName, { type: 'image/jpeg' });
                    } else {
                        arquivo = new File([fotoItem.blob], safeName, { type: fotoItem.blob.type || 'image/jpeg' });
                    }

                    fd.append('foto', arquivo, safeName);
                    
                    const csrf = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : 
                                 (document.querySelector('input[name="csrf_token"]')?.value || '');

                    const resFoto = await fetch(`/cli/resposta/${rid}/upload-foto`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrf },
                        body: fd
                    });

                    if (resFoto.ok || resFoto.status === 400) {
                        await db.fotos_pendentes.delete(fotoItem.id);
                        // Atualiza UI se existir
                        if (typeof document !== 'undefined') {
                            const localEl = document.getElementById(`foto-local-${fotoItem.id}`);
                            if (localEl) localEl.remove();
                        }
                    }
                } catch (err) {
                    console.log(`Erro foto ${fotoItem.id}:`, err);
                }
            }
        }
        return { status: 'ok' };
    },

    // --- 3. SINCRONIZAR TUDO (Modo Seguro v2) ---
    async sincronizarTudo() {
        if (!navigator.onLine) return;
        
        // [TRAVA DE SEGURANÇA]
        // Se estivermos na página de responder, deixamos o script da página lidar com isso
        // para evitar conflito de dois scripts enviando a mesma foto e travando o celular.
        if (document.getElementById('form-finalizar') || document.querySelector('.question-card')) {
            console.log("[OfflineManager] Página de resposta detectada. Passando a bola para o script local.");
            return; 
        }

        console.log("[OfflineManager] Iniciando Sync Global...");

        // 1. Textos
        const textos = await db.respostas_pendentes.toArray();
        const idsUnicos = new Set(textos.map(t => t.pergunta_id));
        
        for (const pid of idsUnicos) {
            await this.sincronizarUma(pid);
        }

        // 2. Fotos (Correção Crítica para iOS)
        // NUNCA usar .toArray() em fotos_pendentes globalmente
        const totalFotos = await db.fotos_pendentes.count();
        
        if (totalFotos > 0) {
            // Pegamos apenas IDs para iterar um a um
            const chaves = await db.fotos_pendentes.primaryKeys();
            for (const chave of chaves) {
                const foto = await db.fotos_pendentes.get(chave);
                if (foto) {
                    // Reutiliza a lógica unitária segura
                    await this.sincronizarUma(foto.pergunta_id);
                }
                // Memória limpa a cada iteração
            }
        }
        
        console.log("[OfflineManager] Sync Global Finalizado.");
    }
};

// =========================================================
// 4. LISTENERS (Só ativa se NÃO estiver na página de responder)
// =========================================================

function triggerSync() {
    // Verificação dupla de segurança
    if (!document.getElementById('form-finalizar')) {
        OfflineManager.sincronizarTudo();
    }
}

window.addEventListener('online', triggerSync);

document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && navigator.onLine) {
        triggerSync();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(triggerSync, 5000); // Delay maior para não competir com load inicial
});