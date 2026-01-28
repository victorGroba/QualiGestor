// Configuração do Banco de Dados Local (IndexedDB)
const db = new Dexie('QualiGestorDB');

// 1. Atualizamos a estrutura para aceitar FOTOS
db.version(3).stores({
    respostas_pendentes: 'pergunta_id, aplicacao_id, dados_completos, timestamp',
    fotos_pendentes: 'pergunta_id, arquivo_blob, nome_arquivo' // Nova tabela para fotos
    fila_deletar: 'id_item, tipo, timestamp'
});

const OfflineManager = {
    
    // --- FUNÇÃO 1: SALVAR TEXTO (A Resposta da Pergunta) ---
    async salvarResposta(aplicacaoId, dados) {
        try {
            await db.respostas_pendentes.put({
                pergunta_id: dados.pergunta_id,
                aplicacao_id: aplicacaoId,
                dados_completos: dados,
                timestamp: Date.now()
            });

            // Se tiver internet, tenta enviar imediatamente
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

    // --- FUNÇÃO 2: SALVAR FOTO (A Evidência) ---
    async salvarFoto(perguntaId, fileInput) {
        try {
            const file = fileInput.files[0];
            if (!file) return;

            // Salva a foto no banco local (IndexedDB)
            await db.fotos_pendentes.put({
                pergunta_id: perguntaId.toString(), // Garante que é string para bater com a resposta
                arquivo_blob: file,
                nome_arquivo: file.name
            });

            // Se tiver internet, a gente tenta sincronizar TUDO daquela pergunta (Texto + Foto)
            if (navigator.onLine) {
                await this.sincronizarUma(perguntaId);
                return { status: 'sincronizado', msg: 'Foto enviada!' };
            } else {
                return { status: 'pendente', msg: 'Foto salva no dispositivo' };
            }
        } catch (e) {
            console.error("Erro ao salvar foto local:", e);
            throw e;
        }
    },

    // --- FUNÇÃO 3: SINCRONIZAR UMA PERGUNTA (Inteligente: Texto depois Foto) ---
    async sincronizarUma(perguntaId) {
        const respostaItem = await db.respostas_pendentes.get(perguntaId);
        
        // A) Sincronizar o TEXTO primeiro
        let respostaIdServidor = null;

        if (respostaItem) {
            try {
                const response = await fetch(`/aplicacao/${respostaItem.aplicacao_id}/salvar-resposta`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(respostaItem.dados_completos)
                });

                if (response.ok) {
                    const jsonRes = await response.json();
                    respostaIdServidor = jsonRes.resposta_id; // O servidor devolve o ID real da resposta
                    
                    // Remove da fila de pendentes pois já foi
                    await db.respostas_pendentes.delete(perguntaId);
                    console.log(`Texto da pergunta ${perguntaId} sincronizado.`);
                } else {
                    console.warn("Servidor rejeitou o texto.");
                    return { status: 'erro', msg: 'Erro no servidor' };
                }
            } catch (error) {
                console.log("Offline ao tentar enviar texto.");
                return { status: 'offline', msg: 'Sem conexão' };
            }
        }

        // B) Sincronizar a FOTO (Se houver e se tivermos o ID da resposta)
        // Se a resposta já existia no servidor (não estava pendente), precisamos descobrir o ID dela
        // Aqui assumimos que se não tinha texto pendente, a resposta já existe no banco.
        // *Nota: Para simplificar, focamos no fluxo onde o usuário acabou de responder.*
        
        const fotoItem = await db.fotos_pendentes.get(perguntaId);
        
        if (fotoItem && respostaIdServidor) {
            try {
                const formData = new FormData();
                formData.append('foto', fotoItem.arquivo_blob, fotoItem.nome_arquivo);

                const responseFoto = await fetch(`/resposta/${respostaIdServidor}/upload-foto`, {
                    method: 'POST',
                    body: formData // Fetch detecta FormData e ajusta headers automaticamente
                });

                if (responseFoto.ok) {
                    await db.fotos_pendentes.delete(perguntaId);
                    console.log(`Foto da pergunta ${perguntaId} enviada.`);
                    return { status: 'sincronizado', msg: 'Tudo salvo!' };
                }
            } catch (error) {
                console.log("Falha ao enviar foto (mas texto foi).");
            }
        }
        
        return { status: 'parcial', msg: 'Processado' };
    },

    // --- FUNÇÃO 4: SINCRONIZAR TUDO (Quando a internet volta) ---
    async sincronizarTudo() {
        if (!navigator.onLine) return;
        
        // Pega todos os IDs únicos que têm texto OU foto pendente
        const textos = await db.respostas_pendentes.toArray();
        const fotos = await db.fotos_pendentes.toArray();
        
        const idsParaSincronizar = new Set();
        textos.forEach(t => idsParaSincronizar.add(t.pergunta_id));
        fotos.forEach(f => idsParaSincronizar.add(f.pergunta_id));

        if (idsParaSincronizar.size === 0) return;

        console.log(`Sincronizando ${idsParaSincronizar.size} itens...`);
        
        // Itera e sincroniza um por um
        for (const pId of idsParaSincronizar) {
            await this.sincronizarUma(pId);
        }
        
        console.log("Sincronização em lote concluída.");
        // Opcional: Recarregar a página para atualizar ícones
        // location.reload(); 
    },
    
    // Funções auxiliares para verificar status visual
    async temPendente(perguntaId) {
        const t = await db.respostas_pendentes.get(perguntaId);
        const f = await db.fotos_pendentes.get(perguntaId);
        return (t || f);
    }
};

// Listeners Automáticos
window.addEventListener('online', () => OfflineManager.sincronizarTudo());
document.addEventListener('DOMContentLoaded', () => OfflineManager.sincronizarTudo());