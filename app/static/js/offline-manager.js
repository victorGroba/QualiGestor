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
    // ARQUIVO: app/static/js/offline-manager.js

    // ARQUIVO: app/static/js/offline-manager.js

    async sincronizarUma(perguntaId) {
        // ... (código de texto mantém igual) ...

        const fotosItems = await db.fotos_pendentes
            .where('pergunta_id')
            .equals(perguntaId.toString())
            .toArray();
        
        if (fotosItems.length > 0 && respostaIdServidor) {
            let enviouAlguma = false;

            for (const fotoItem of fotosItems) {
                try {
                    const formData = new FormData();
                    
                    // Nome seguro
                    let safeName = fotoItem.nome || 'foto.jpg';
                    safeName = safeName.replace(/[^a-zA-Z0-9._-]/g, '');
                    if (!safeName.toLowerCase().endsWith('.jpg')) safeName += '.jpg';

                    // --- TRATAMENTO INTELIGENTE (TEXTO ou ARQUIVO) ---
                    let arquivoParaEnvio;

                    if (fotoItem.tipo === 'base64' || (typeof fotoItem.blob === 'string' && fotoItem.blob.startsWith('data:'))) {
                        // Se salvou como texto, converte de volta para arquivo
                        const res = await fetch(fotoItem.blob);
                        const blobRecuperado = await res.blob();
                        arquivoParaEnvio = new File([blobRecuperado], safeName, { type: 'image/jpeg' });
                    } else {
                        // Se salvou normal
                        arquivoParaEnvio = new File([fotoItem.blob], safeName, { type: fotoItem.blob.type || 'image/jpeg' });
                    }

                    formData.append('foto', arquivoParaEnvio, safeName);

                    const responseFoto = await fetch(`/resposta/${respostaIdServidor}/upload-foto`, {
                        method: 'POST',
                        body: formData
                    });

                    if (responseFoto.ok) {
                        await db.fotos_pendentes.delete(fotoItem.id);
                        
                        // Remove visualmente se a tela estiver aberta
                        const elLocal = document.getElementById(`foto-local-${fotoItem.id}`);
                        if (elLocal) elLocal.remove();
                        
                        enviouAlguma = true;
                    } 
                    else if (responseFoto.status === 400) {
                        // Se o servidor rejeitou, deleta também
                        await db.fotos_pendentes.delete(fotoItem.id);
                    }
                } catch (error) {
                    console.log(`Erro offline foto ${fotoItem.id}:`, error);
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