# QualiGestor - Versão 1.4.0-beta

Data de lançamento: 20/05/2025  
Status: **Em desenvolvimento**

---

## ✨ Visão Geral
Esta versão marca um grande avanço visual e estrutural do sistema QualiGestor, com foco na separação dos módulos, melhoria na responsividade e preparação para funcionalidades dinâmicas mais robustas.

---

## 🔧 Alterações Estruturais
- Reorganização da estrutura de pastas do projeto.
- Realocação do `config.py` para fora da antiga pasta principal.
- Início do controle de versão com Git local (estrutura `.git/`).

---

## 🎨 Melhorias na Interface
- **Novo `base_cliq.html`**:
  - Sidebar responsiva e moderna.
  - Header fixo com tipo de usuário e número da versão.
  - Slider exclusivo para a home do CLIQ.

- **Novo `base_painel.html`**:
  - Layout minimalista com acesso direto aos módulos.
  - Sidebar reduzida com opções: CLIQ, Panorama e Sair.

- Sidebar é fixa no desktop e retraível apenas no mobile.
- Rodapé removido; versão aparece agora no canto superior direito do header.

---

## 🔄 Lógica de Navegação
- A rota `/` verifica se o usuário está logado:
  - Se sim: redireciona para o painel.
  - Se não: redireciona para a tela de login.
- Correção do template carregado ao acessar diretamente via IP.

---

## 📁 Templates e Componentes
- Separados por contexto:
  - `base_cliq.html` para operações internas do módulo CLIQ.
  - `base_painel.html` para a tela inicial de escolha de módulo.
- Layout do slide otimizado para evitar scroll vertical.

---

## 🔍 Arquivos Removidos
- `forms.py` da pasta `app/cli/` removido.
- Arquivos `.pyc` e caches eliminados.

---

## 🔖 Identificação da Versão
```txt
Versão: 1.4.0-beta
Data: 20/05/2025
Status: Em desenvolvimento
```

---

## 🚀 Próximos passos
- Integração de formulários dinâmicos e checklist por bloco.
- Sistema de aplicação de checklist com salvamento de resposta.
- Dashboard para auditorias e relatórios visuais.
