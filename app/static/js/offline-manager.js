// =========================================================
// ARQUIVO: app/static/js/offline-manager.js
// VERSÃO: 3.5 (CORREÇÃO TOTAL: RACE CONDITION + DELEÇÃO OFFLINE)
// =========================================================

const db = new Dexie('QualiGestorDB');

// Definição do Banco de Dados Local
db.version(3).stores({
    respostas_pendentes: 'pergunta_id, aplicacao_id, dados_completos, timestamp',
    fotos_pendentes: 'id, aplicacao_id, pergunta_id, resposta_id, blob, nome, timestamp',
    fila_deletar: 'id_item, tipo, timestamp'
});

const OfflineManager = {
    
    // --- 1. SALVAR TEXTO (Chamado pelo HTML) ---
    async salvarResposta(aplicacaoId, dados) {
        try {
            await db.respostas_pendentes.put({
                pergunta_id: dados.pergunta_id,
                aplicacao_id: aplicacaoId,
                dados_completos: dados,
                timestamp: Date.now()
            });

            if (navigator.onLine) {
                // Tenta sincronizar imediatamente se tiver internet
                return await this.sincronizarUma(dados.pergunta_id);
            } else {
                return { status: 'pendente', msg: 'Salvo localmente' };
            }
        } catch (e) {
            console.error("Erro Dexie ao salvar resposta:", e);
            throw e;
        }
    },

    // --- 2. SINCRONIZAR UMA PERGUNTA (Núcleo da Lógica) ---
    async sincronizarUma(perguntaId) {
        let respostaIdServidor = null;
        let aplicacaoId = null;

        // =================================================================
        // PASSO A: TEXTO E OBSERVAÇÕES
        // (Prioridade Total: Precisamos gerar o ID da resposta primeiro)
        // =================================================================
        const textoItem = await db.respostas_pendentes.get(perguntaId);
        
        if (textoItem) {
            aplicacaoId = textoItem.aplicacao_id;
            try {
                const csrf = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : 
                             (document.querySelector('input[name="csrf_token"]')?.value || '');

                // Envia o texto para o servidor
                const response = await fetch(`/cli/aplicacao/${aplicacaoId}/salvar-resposta`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                    body: JSON.stringify(textoItem.dados_completos)
                });

                if (response.ok) {
                    const data = await response.json();
                    respostaIdServidor = data.resposta_id; // ID REAL DO SERVIDOR
                    
                    // Remove da fila de pendentes pois já salvou
                    await db.respostas_pendentes.delete(perguntaId);
                    
                    // [CORREÇÃO CRÍTICA]
                    // Se gerou um ID novo, avisa imediatamente as fotos pendentes dessa pergunta!
                    // Isso impede que a foto suba "sem dono" e corrompa.
                    if (respostaIdServidor) {
                        await this.atualizarIdFotosPendentes(perguntaId, respostaIdServidor);
                    }
                }
            } catch (e) {
                // Se falhar o texto, não adianta tentar enviar fotos agora (vão dar erro 404)
                return { status: 'erro', msg: 'Sem conexão para texto' };
            }
        }

        // =================================================================
        // PASSO B: FOTOS
        // (Só executa se tivermos um ID de resposta válido)
        // =================================================================
        const chavesFotos = await db.fotos_pendentes
            .where('pergunta_id').equals(perguntaId.toString())
            .primaryKeys();
        
        if (chavesFotos.length > 0) {
            for (const chave of chavesFotos) {
                const fotoItem = await db.fotos_pendentes.get(chave);
                if (!fotoItem) continue;

                // Tenta descobrir o ID da resposta:
                // 1. Veio do servidor agora (respostaIdServidor)?
                // 2. Já estava salvo no item (fotoItem.resposta_id)?
                // 3. Está no HTML da página (dataset)?
                let rid = respostaIdServidor || fotoItem.resposta_id;
                
                if (!rid && typeof document !== 'undefined') {
                    const el = document.querySelector(`[data-pergunta-id="${perguntaId}"]`);
                    if (el && el.dataset.respostaId) rid = el.dataset.respostaId;
                }

                // Se depois de tudo isso não tem ID, pula essa foto e mantém na fila
                if (!rid) continue; 

                try {
                    await this.enviarFotoUnica(fotoItem, rid);
                } catch (err) {
                    console.log(`Erro ao processar foto ${fotoItem.id}:`, err);
                }
            }
        }
        return { status: 'ok' };
    },

    // --- AUXILIAR 1: ATUALIZA IDS ORFÃOS (A Mágica da Correção) ---
    async atualizarIdFotosPendentes(perguntaId, novoRespostaId) {
        // Busca todas as fotos presas no celular para esta pergunta
        const fotos = await db.fotos_pendentes.where('pergunta_id').equals(String(perguntaId)).toArray();
        
        for (const f of fotos) {
            // Se a foto não tem ID ou está com ID errado, atualiza!
            if (!f.resposta_id || f.resposta_id != novoRespostaId) {
                f.resposta_id = novoRespostaId;
                await db.fotos_pendentes.put(f);
                console.log(`[Sync] Foto ${f.id} vinculada com sucesso à resposta ${novoRespostaId}`);
            }
        }

        // Atualiza também o HTML para o usuário ver que está tudo certo
        if (typeof document !== 'undefined') {
            const inputs = document.querySelectorAll(`[data-pergunta-id="${perguntaId}"]`);
            inputs.forEach(el => el.dataset.respostaId = novoRespostaId);
        }
    },

    // --- AUXILIAR 2: ENVIO REAL DA FOTO (Rota Atualizada) ---
    async enviarFotoUnica(fotoItem, rid) {
        const fd = new FormData();
        // Higieniza o nome do arquivo
        let safeName = (fotoItem.nome || `foto_${Date.now()}.jpg`).replace(/[^a-zA-Z0-9._-]/g, '');
        if (!safeName.match(/\.(jpg|jpeg|png|webp)$/i)) safeName += '.jpg';

        let arquivo;
        
        // Lógica para converter Base64 (se foi salvo como texto) ou Blob (se arquivo)
        if (fotoItem.tipo === 'base64' || (typeof fotoItem.blob === 'string')) {
            try {
                const base64Data = fotoItem.blob.includes(',') ? fotoItem.blob.split(',')[1] : fotoItem.blob;
                const byteCharacters = atob(base64Data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                arquivo = new File([byteArray], safeName, { type: 'image/jpeg' });
            } catch (errConv) {
                console.error("Arquivo corrompido (base64 inválido), removendo da fila:", errConv);
                await db.fotos_pendentes.delete(fotoItem.id); 
                return;
            }
        } else {
            // Arquivo normal (Blob)
            arquivo = new File([fotoItem.blob], safeName, { type: fotoItem.blob.type || 'image/jpeg' });
        }

        fd.append('foto', arquivo, safeName);
        
        const csrf = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : 
                     (document.querySelector('input[name="csrf_token"]')?.value || '');

        // --- ROTA NOVA (VINCULADA AO ID DA RESPOSTA) ---
        const resFoto = await fetch(`/cli/resposta/${rid}/upload-foto`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrf },
            body: fd
        });

        if (resFoto.ok) {
            const data = await resFoto.json();
            // Sucesso: Remove do banco local
            await db.fotos_pendentes.delete(fotoItem.id);
            
            // Atualiza Visual (Troca Borda Amarela por Verde)
            if (typeof document !== 'undefined') {
                const localEl = document.getElementById(`foto-local-${fotoItem.id}`);
                if (localEl) {
                    localEl.outerHTML = `
                        <div class="position-relative d-inline-block flex-shrink-0 me-2" id="foto-server-${data.foto_id}" style="width: 70px; height: 70px;">
                            <img src="${URL.createObjectURL(arquivo)}" class="rounded w-100 h-100 border border-success" style="object-fit: cover; cursor: pointer;" onclick="window.open(this.src)">
                            <button type="button" class="btn btn-danger btn-sm p-0 position-absolute top-0 end-0 translate-middle rounded-circle shadow-sm" style="width: 20px; height: 20px; font-size: 10px; z-index: 10;" onclick="deletarFotoServidor(${data.foto_id})">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>`;
                }
            }
        } else if (resFoto.status === 400) {
            // Erro Fatal (Arquivo Inválido): Remove para não travar a fila
            console.error("Servidor rejeitou arquivo (Erro 400). Removendo.");
            await db.fotos_pendentes.delete(fotoItem.id);
        } else {
            // Outros erros (500, Conexão): Mantém na fila para tentar depois
            console.warn(`Erro servidor ${resFoto.status}. Tentaremos novamente.`);
        }
    },

    // --- 3. SINCRONIZAR TUDO (Loop Global) ---
    async sincronizarTudo() {
        if (!navigator.onLine) return;
        
        // Se estiver respondendo, não interfere (evita travamentos na UI)
        if (document.getElementById('form-finalizar') || document.querySelector('.question-card')) {
            return; 
        }

        console.log("[OfflineManager] Iniciando Sync Global (Background)...");

        // 1. Textos
        const textos = await db.respostas_pendentes.toArray();
        const idsUnicos = new Set(textos.map(t => t.pergunta_id));
        for (const pid of idsUnicos) {
            await this.sincronizarUma(pid);
        }

        // 2. Fotos (Itera chave por chave para economizar memória)
        const totalFotos = await db.fotos_pendentes.count();
        if (totalFotos > 0) {
            const chaves = await db.fotos_pendentes.primaryKeys();
            for (const chave of chaves) {
                const foto = await db.fotos_pendentes.get(chave);
                if (foto) await this.sincronizarUma(foto.pergunta_id);
            }
        }
        
        // 3. Fila de Deleção (Processa itens excluídos offline)
        const deletes = await db.fila_deletar.toArray();
        for (const del of deletes) {
            if (del.tipo === 'foto') {
                try {
                    const csrf = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : '';
                    await fetch(`/cli/foto/${del.id_item}/deletar`, { 
                        method: 'DELETE',
                        headers: { 'X-CSRFToken': csrf }
                    });
                    await db.fila_deletar.delete(del.id_item); 
                } catch (e) { 
                    console.log("Erro sync delete:", e); 
                }
            }
        }
    }
};

// =========================================================
// 4. LISTENERS (Gatilhos Automáticos)
// =========================================================

function triggerSync() {
    // Só roda o sync global se NÃO estivermos na tela de responder (para não competir com o salvamento em tempo real)
    if (!document.getElementById('form-finalizar')) {
        OfflineManager.sincronizarTudo();
    }
}

// Tenta sincronizar quando a internet volta
window.addEventListener('online', triggerSync);

// Tenta sincronizar quando o usuário volta para a aba do navegador
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && navigator.onLine) {
        triggerSync();
    }
});

// Tenta sincronizar pouco depois de abrir o app
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(triggerSync, 5000); 
});

// =========================================================
// 5. FUNÇÃO GLOBAL DELETAR (SEGURA E OFFLINE)
// =========================================================
window.deletarFotoServidor = async (id) => {
    if (!confirm('Apagar esta foto do servidor?')) return;
    
    const el = document.getElementById(`foto-server-${id}`);
    
    // TENTATIVA 1: MODO ONLINE
    if (navigator.onLine) {
        try {
            const csrf = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : 
                         (document.querySelector('input[name="csrf_token"]')?.value || '');
            
            const res = await fetch(`/cli/foto/${id}/deletar`, { 
                method: 'DELETE', 
                headers: { 'X-CSRFToken': csrf } 
            });
            
            if (res.ok) {
                if (el) el.remove(); // Sucesso: some da tela
                return;
            }
        }
        catch (e) { 
            console.warn("Falha ao deletar online (Rede instável). Agendando...", e);
        }
    }

    // TENTATIVA 2: MODO OFFLINE (Se falhou acima ou sem net)
    alert("Sem conexão. A foto será apagada assim que possível.");

    // Marca visualmente como "Lixeira"
    if (el) {
        el.style.opacity = '0.5';
        el.style.border = '2px dashed red';
        el.innerHTML += '<span class="position-absolute top-50 start-50 translate-middle badge bg-danger">LIXEIRA</span>';
    }
    
    // Agenda no banco local para apagar depois
    try {
        await db.fila_deletar.put({ 
            id_item: id, 
            tipo: 'foto', 
            timestamp: Date.now() 
        });
    } catch (e) {
        console.error("Erro ao agendar deleção:", e);
    }
};