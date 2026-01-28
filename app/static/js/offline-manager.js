// Configuração do Banco de Dados Local (IndexedDB)
const db = new Dexie('QualiGestorDB');

// 1. ATUALIZADO: Estrutura idêntica ao HTML para evitar conflitos (Versão 3)
db.version(3).stores({
    respostas_pendentes: 'pergunta_id, aplicacao_id, dados_completos, timestamp',
    // Agora a chave primária é 'id' (auto-incremento ou timestamp), não mais 'pergunta_id'
    fotos_pendentes: 'id, aplicacao_id, pergunta_id, resposta_id, blob, nome, timestamp',
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
    async salvarFoto(perguntaId, fileInput, aplicacaoId = null) {
        try {
            const file = fileInput.files[0];
            if (!file) return;

            // Gera um ID único para a foto
            const fotoId = Date.now();

            // Salva a foto no banco local (IndexedDB) com a estrutura NOVA
            await db.fotos_pendentes.add({
                id: fotoId,
                aplicacao_id: aplicacaoId, // Idealmente deve ser passado, ou null se não tiver
                pergunta_id: perguntaId.toString(),
                resposta_id: null, // Será preenchido após sincronizar o texto
                blob: file,        // Nome padronizado: 'blob'
                nome: file.name,   // Nome padronizado: 'nome'
                timestamp: Date.now()
            });

            // Se tiver internet, a gente tenta sincronizar TUDO daquela pergunta
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

    // --- FUNÇÃO 3: SINCRONIZAR UMA PERGUNTA (Inteligente: Texto depois Fotos) ---
    async sincronizarUma(perguntaId) {
        const respostaItem = await db.respostas_pendentes.get(perguntaId);
        
        // A) Sincronizar o TEXTO primeiro
        let respostaIdServidor = null;

        // Tenta recuperar ID se já existir no HTML (caso a resposta já tenha ido, mas a foto não)
        // Como o OfflineManager roda isolado, ele depende do retorno do servidor ou da resposta pendente.

        if (respostaItem) {
            try {
                const response = await fetch(`/aplicacao/${respostaItem.aplicacao_id}/salvar-resposta`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(respostaItem.dados_completos)
                });

                if (response.ok) {
                    const jsonRes = await response.json();
                    respostaIdServidor = jsonRes.resposta_id; // O servidor devolve o ID real
                    
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

        // B) Sincronizar FOTOS (Agora suporta múltiplas fotos por pergunta)
        // Busca todas as fotos pendentes vinculadas a esta pergunta
        // Nota: Precisamos converter perguntaId para string pois no banco salvamos como string
        const fotosItems = await db.fotos_pendentes
            .where('pergunta_id')
            .equals(perguntaId.toString())
            .toArray();
        
        // Se não temos o ID da resposta vindo do texto, não conseguimos enviar a foto.
        // (A menos que a gente busque no DOM, mas este script roda separado).
        // Aqui assumimos: se enviou o texto agora, temos o ID. Se não tinha texto pendente, 
        // talvez a resposta já existisse. *Melhoria: Se respostaIdServidor for null, tentar buscar a resposta no servidor antes*
        
        if (fotosItems.length > 0 && respostaIdServidor) {
            let enviouAlguma = false;

            for (const fotoItem of fotosItems) {
                try {
                    const formData = new FormData();
                    // Garante a extensão do arquivo para evitar erro 400 no Python
                    let nomeFinal = fotoItem.nome || 'foto.jpg';
                    if (!nomeFinal.toLowerCase().match(/\.(jpg|jpeg|png|webp)$/)) {
                        nomeFinal += '.jpg';
                    }

                    // Recria o arquivo para garantir integridade
                    const arquivoParaEnvio = new File([fotoItem.blob], nomeFinal, { type: fotoItem.blob.type || 'image/jpeg' });
                    formData.append('foto', arquivoParaEnvio, nomeFinal);

                    const responseFoto = await fetch(`/resposta/${respostaIdServidor}/upload-foto`, {
                        method: 'POST',
                        body: formData
                    });

                    if (responseFoto.ok) {
                        // Remove especificamente esta foto pelo seu ID único
                        await db.fotos_pendentes.delete(fotoItem.id);
                        console.log(`Foto ${fotoItem.id} da pergunta ${perguntaId} enviada.`);
                        enviouAlguma = true;
                    }
                } catch (error) {
                    console.log(`Falha ao enviar foto ${fotoItem.id}.`);
                }
            }
            
            if (enviouAlguma) return { status: 'sincronizado', msg: 'Fotos processadas' };
        }
        
        return { status: 'parcial', msg: 'Processado' };
    },

    // --- FUNÇÃO 4: SINCRONIZAR TUDO (Quando a internet volta) ---
    async sincronizarTudo() {
        if (!navigator.onLine) return;
        
        // Pega todos os IDs únicos que têm texto pendente
        const textos = await db.respostas_pendentes.toArray();
        const fotos = await db.fotos_pendentes.toArray();
        
        const idsParaSincronizar = new Set();
        textos.forEach(t => idsParaSincronizar.add(t.pergunta_id));
        fotos.forEach(f => idsParaSincronizar.add(f.pergunta_id));

        if (idsParaSincronizar.size === 0) return;

        console.log(`[OfflineManager] Sincronizando itens de ${idsParaSincronizar.size} perguntas...`);
        
        // Itera e sincroniza um por um
        for (const pId of idsParaSincronizar) {
            await this.sincronizarUma(pId);
        }
        
        console.log("[OfflineManager] Sincronização em lote concluída.");
    },
    
    // Funções auxiliares para verificar status visual
    async temPendente(perguntaId) {
        const t = await db.respostas_pendentes.get(perguntaId);
        // Verifica se existe alguma foto com este pergunta_id
        const fCount = await db.fotos_pendentes.where('pergunta_id').equals(perguntaId.toString()).count();
        return (t || fCount > 0);
    }
};

// Listeners Automáticos
window.addEventListener('online', () => OfflineManager.sincronizarTudo());
document.addEventListener('DOMContentLoaded', () => {
    // Aguarda um pouco para não competir com o carregamento principal da página
    setTimeout(() => OfflineManager.sincronizarTudo(), 3000);
});