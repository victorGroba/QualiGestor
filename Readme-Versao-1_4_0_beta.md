# QualiGestor - Versão 1.4.0-beta

Data de lançamento: 20/05/2025  
Status: **Em desenvolvimento**

---

## ✨ Visão Geral
Esta versão marca um grande avanço visual e estrutural do sistema QualiGestor, com foco na separação dos módulos, melhoria na responsividade e preparação para funcionalidades dinâmicas mais robustas.

---

---

## 🔧 Alterações Estruturais
- Adicionado suporte ao **Flask-Migrate** para controle de versionamento do banco de dados.
  - Agora é possível gerar e aplicar migrations com os comandos:
    ```bash
    flask db init      # Executar uma única vez
    flask db migrate   # Criar uma nova migration
    flask db upgrade   # Aplicar alterações ao banco
    ```
- Reorganização da estrutura de pastas do projeto.
- Realocação do `config.py` para fora da antiga pasta principal.
- Início do controle de versão com Git local (estrutura `.git/`).

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



---

## 🖼 Capturas de Tela

### Tela de Login (Desktop)
<img src="https://raw.githubusercontent.com/victorGroba/QualiGestor/main/app/static/img/screenshots/login-desktop.png" alt="Login Desktop" width="800"/>

### Tela de Painel (Desktop)
<img src="https://raw.githubusercontent.com/victorGroba/QualiGestor/main/app/static/img/screenshots/painel-desktop.png" alt="Painel Desktop" width="800"/>

### Home do Módulo CLIQ (Desktop)
<img src="https://raw.githubusercontent.com/victorGroba/QualiGestor/main/app/static/img/screenshots/cliq-desktop.png" alt="CLIQ Desktop" width="800"/>

### Painel (Mobile)
<img src="https://raw.githubusercontent.com/victorGroba/QualiGestor/main/app/static/img/screenshots/painel-mobile.png" alt="Painel Mobile" width="400"/>

### Login (Mobile)
<img src="https://raw.githubusercontent.com/victorGroba/QualiGestor/main/app/static/img/screenshots/login-mobile.png" alt="Login Mobile" width="400"/>

### Home CLIQ (Mobile)
<img src="https://raw.githubusercontent.com/victorGroba/QualiGestor/main/app/static/img/screenshots/cliq-mobile.png" alt="CLIQ Mobile" width="400"/>

### Menu CLIQ (Mobile)
<img src="https://raw.githubusercontent.com/victorGroba/QualiGestor/main/app/static/img/screenshots/cliq-sidebar-mobile.png" alt="Sidebar CLIQ Mobile" width="400"/>

### Menu Expandido CLIQ (Mobile)
<img src="https://raw.githubusercontent.com/victorGroba/QualiGestor/main/app/static/img/screenshots/cliq-sidebar-expandido-mobile.png" alt="Sidebar Expandido" width="400"/>
