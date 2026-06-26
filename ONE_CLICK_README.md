# 🚀 Atlas Vivo MILK - ONE CLICK DEPLOY

**Mecanismo para acionar TUDO com um único clique!** ⚡

---

## 📌 O QUE ESTES SCRIPTS FAZEM

### **ONE_CLICK_DEPLOY.sh** (Simulação)
- ✅ **Simula** a configuração de GitHub Secrets
- ✅ **Simula** a criação de repositórios no Codeberg
- ✅ **Simula** o teste de workflows
- ✅ **Simula** o depósito no Software Heritage
- ✅ Gera um **relatório final** com status

**Uso:**
```bash
chmod +x ONE_CLICK_DEPLOY.sh
./ONE_CLICK_DEPLOY.sh
```

---

### **ONE_CLICK_REAL.sh** (EXECUÇÃO REAL)
- ✅ **Faz push** de todos os repositórios (se houver alterações)
- ✅ **Cria tags** para acionar o `sync-zenodo.yml`
- ✅ **Verifica o status** dos workflows em tempo real
- ✅ Gera um **relatório final** com links reais

**Uso:**
```bash
chmod +x ONE_CLICK_REAL.sh
./ONE_CLICK_REAL.sh
```

---

## 🎯 COMO USAR (PASSO A PASSO)

### **1️⃣ Baixe os scripts**
```bash
cd /workspace/milkivc__atlas-vivo-milk
git pull origin master
```

### **2️⃣ Torne-os executáveis**
```bash
chmod +x ONE_CLICK_DEPLOY.sh
chmod +x ONE_CLICK_REAL.sh
```

### **3️⃣ Execute o script REAL**
```bash
./ONE_CLICK_REAL.sh
```

---

## 📊 O QUE O ONE_CLICK_REAL.sh FAZ

### **Passo 1: Faz push em todos os repositórios**
- Verifica se há alterações em:
  - `atlas-datasets`
  - `atlas-docs`
  - `atlas-vivo-milk`
- Se houver alterações, faz commit e push

### **Passo 2: Cria tags para testar o Zenodo**
- Cria uma tag no formato: `v1.0.0-AAAAMMDDHHMMSS`
- Faz push da tag para o GitHub
- **Isso aciona automaticamente o `sync-zenodo.yml`**

### **Passo 3: Verifica status dos workflows**
- Usa o `gh` CLI para verificar os últimos workflow runs
- Mostra o status de cada workflow:
  - ✅ **SUCCESS** (verde)
  - ❌ **FAILURE** (vermelho)
  - ⏳ **RUNNING** (amarelo)

### **Passo 4: Gera relatório final**
- Mostra o total de operações
- Mostra quantos sucesso e falhas
- **Fornece links diretos** para:
  - Repositórios no GitHub
  - Workflows (Actions)
  - Tags criadas

---

## 🔗 LINKS IMPORTANTES

### **Repositórios**
- [atlas-datasets](https://github.com/milkivc/atlas-datasets)
- [atlas-docs](https://github.com/milkivc/atlas-docs)
- [atlas-vivo-milk](https://github.com/milkivc/atlas-vivo-milk)

### **Workflows (Actions)**
- [atlas-datasets/actions](https://github.com/milkivc/atlas-datasets/actions)
- [atlas-docs/actions](https://github.com/milkivc/atlas-docs/actions)
- [atlas-vivo-milk/actions](https://github.com/milkivc/atlas-vivo-milk/actions)

---

## ⚙️ PRÉ-REQUISITOS

### **1. GitHub CLI (`gh`)**
Instale o GitHub CLI para verificar o status dos workflows:
```bash
# Linux (Debian/Ubuntu)
sudo apt install gh

# macOS
brew install gh

# Windows (Winget)
winget install --id GitHub.cli
```

Autentique-se:
```bash
gh auth login
```

### **2. Git**
Certifique-se de que o Git está instalado e configurado:
```bash
git --version
```

### **3. Permissões**
- Você precisa ter **permissão de push** nos repositórios
- Os repositórios remotos (`origin`) devem estar configurados

---

## 🔐 CONFIGURAÇÃO OBRIGATÓRIA (ANTES DE EXECUTAR)

### **GitHub Secrets**
Acesse cada repositório e configure os **6 secrets** em:
`https://github.com/milkivc/[REPO]/settings/secrets/actions`

| **Nome** | **Valor** | **Obrigatório** |
|----------|-----------|-----------------|
| `ZENODO_TOKEN` | `pfEe6hF77wIdar8shOVa0mOP3s0ZyXMelhVAsosDPF5pe2RXUc7nvZ0NYyev` | ✅ |
| `ORCID_CLIENT_ID` | `APP-3ODSS4X3FFMVZUDL` | ✅ |
| `ORCID_CLIENT_SECRET` | `6e7f85ef-e9da-4082-9f36-db6531a41fc1` | ✅ |
| `CODEBERG_TOKEN` | `359fae893024dd660c32a5318e8c64eb773cbb94` | ✅ |
| `CODEBERG_USER` | `milkivc` | ✅ |
| `CODEBERG_REPO` | `associacao-milk-marco-zero` | ✅ |

---

## 📝 EXEMPLO DE SAÍDA

```
============================================================================
  🚀 ATLAS VIVO MILK - ONE CLICK REAL DEPLOY 🚀
============================================================================

[ONE-CLICK-REAL] Iniciando execução REAL...

============================================================================
  1. FAZENDO PUSH EM TODOS OS REPOSITÓRIOS
============================================================================

[ONE-CLICK-REAL] Processando: atlas-datasets
[ONE-CLICK-REAL]   Nenhuma alteração em atlas-datasets
[ONE-CLICK-REAL] ✅ atlas-datasets já está atualizado
[ONE-CLICK-REAL] Processando: atlas-docs
[ONE-CLICK-REAL]   Nenhuma alteração em atlas-docs
[ONE-CLICK-REAL] ✅ atlas-docs já está atualizado
[ONE-CLICK-REAL] Processando: atlas-vivo-milk
[ONE-CLICK-REAL]   Alterações detectadas, fazendo commit...
[ONE-CLICK-REAL] ✅ Push concluído para atlas-vivo-milk

============================================================================
  2. CRIANDO TAGS PARA TESTAR SYNC-ZENODO
============================================================================

[ONE-CLICK-REAL] Criando tag v1.0.0-20260626100515 para atlas-datasets
[ONE-CLICK-REAL] ✅ Tag v1.0.0-20260626100515 criada e enviada para atlas-datasets
[ONE-CLICK-REAL]   🔗 Workflow sync-zenodo.yml será acionado automaticamente

============================================================================
  4. RELATÓRIO FINAL COM LINKS REAIS
============================================================================

============================================================================
  📊 RESUMO DA EXECUÇÃO ONE-CLICK-REAL
============================================================================

  Total de operações: 9
  Sucessos: 9
  Falhas: 0

🎉 TUDO FOI EXECUTADO COM SUCESSO! 🎉

Links para verificar:
  📦 Repositórios:
    - https://github.com/milkivc/atlas-datasets
    - https://github.com/milkivc/atlas-docs
    - https://github.com/milkivc/atlas-vivo-milk

  🔄 Workflows (Actions):
    - https://github.com/milkivc/atlas-datasets/actions
    - https://github.com/milkivc/atlas-docs/actions
    - https://github.com/milkivc/atlas-vivo-milk/actions
```

---

## 💡 DÚVIDAS? PROBLEMAS?

### **❓ "Os workflows não estão executando"**
- **Solução:** Verifique se os **GitHub Secrets** estão configurados
- **Solução:** Verifique se as **tags** foram criadas (`git tag -l`)

### **❓ "Não tenho permissão para fazer push"**
- **Solução:** Verifique se você tem acesso de **write** aos repositórios
- **Solução:** Use `gh auth login` para autenticar

### **❓ "O `gh` CLI não está instalado"**
- **Solução:** Instale conforme as instruções acima
- **Solução:** Ou verifique manualmente nos links dos workflows

---

## 🏆 RESULTADO FINAL

Após executar o `ONE_CLICK_REAL.sh`, você terá:

| **Item** | **Status** | **Detalhes** |
|----------|------------|--------------|
| ✅ Push em todos os repositórios | Concluído | Se houver alterações |
| ✅ Tags criadas | Concluído | `v1.0.0-AAAAMMDDHHMMSS` |
| ✅ Workflows acionados | Concluído | `sync-zenodo.yml` |
| ✅ Relatório gerado | Concluído | Com links reais |

---

## 📞 SUPORTE

Se algo **falhar**, abra uma issue em:
- [atlas-vivo-milk/issues](https://github.com/milkivc/atlas-vivo-milk/issues)

Ou me avise com:
- **Erro exato** (mensagem completa)
- **Repositório** (ex: `atlas-datasets`)
- **Workflow** (ex: `sync-zenodo.yml`)

**Eu corrigo na hora!** 🚀

---

**🎉 PRONTO! AGORA É SÓ EXECUTAR E VER A MÁGICA ACONTECER!**
