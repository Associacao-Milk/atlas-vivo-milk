# ATLAS VIVO MILK — Integrações e Preservação

**Versão documental:** 2.0.0-review  
**Responsável institucional:** Associação MILK  
**Estado:** integração em consolidação; sem declaração de produção, DOI ou conformidade sem evidência verificável

---

## Governação actual da migração

Este repositório está em saneamento público. A camada de vitrine, os metadados de preservação e os workflows de migração devem ser tratados separadamente.

Documentos activos:

- [Governação de migração — Atlas Vivo MILK](docs/MIGRATION_GOVERNANCE_2026-08-28.md)
- [Auditoria pública do repositório — Atlas Vivo MILK](docs/PUBLIC_REPOSITORY_AUDIT_2026-08-28.md)

Pontos de controlo:

- SWHID local preparado, ainda não arquivado publicamente pelo Software Heritage.
- DOI/Zenodo preparado, ainda não publicado.
- ORCID de Nuno e Eduardo registados nos metadados.
- Workflows Mistral/Drive/FTPS/Nextcloud em revisão antes de qualquer execução.
- Sem publicação de corpus, segredos ou dados sensíveis neste repositório público.

---

## 📋 Overview

Este repositório reúne clientes JavaScript e Python para integrar componentes do Atlas Vivo MILK. Cada integração exige credenciais próprias, teste controlado, revisão humana e confirmação de direitos antes de qualquer operação externa.

| API | File | Description | Status |
|-----|------|-------------|--------|
| **Zenodo API** | `zenodo_api_integration.js` | DOI minting, deposit management | Em revisão |
| **ORCID API** | `orcid_api_integration.js` | Researcher identification, work linking | Em revisão |
| **GitHub API** | `github_api_integration.js` | Repository management, workflows | Em revisão |
| **Codeberg API** | `github_api_integration.js` | Codeberg repository management | Em revisão |
| **Unified API** | `index.js` | Single interface for all APIs | Em revisão |

---

## 🎯 Features

### **Zenodo API** 📚
- Em revisão: create and manage deposits
- Em revisão: upload files to deposits
- Em revisão: publish deposits with DOI minting
- Em revisão: link deposits to ORCID records
- Em revisão: search and retrieve deposit information
- Em revisão: manage Zenodo communities
- Em revisão: repository synchronization
- Em revisão: metadata template generation

### **ORCID API** 👤
- Em revisão: OAuth2 authentication
- Em revisão: get researcher information
- Em revisão: add/update/delete works
- Em revisão: link works to ORCID records
- Em revisão: search researchers
- Em revisão: manage affiliations
- Em revisão: work payload creation
- Em revisão: multiple ORCID linking
- Em revisão: ORCID validation

### **GitHub API** 🐙
- Em revisão: repository management
- Em revisão: file operations
- Em revisão: workflow management
- Em revisão: trigger workflow runs
- Em revisão: issue and PR management
- Em revisão: metadata synchronization
- Em revisão: cross-repository operations

### **Codeberg API** 🐙
- Em revisão: Codeberg repository management
- Em revisão: compatible interface

### **Unified API** 🔗
- Em revisão: single interface for all platforms
- Em revisão: deposit creation with DOI
- Em revisão: automatic ORCID linking
- Em revisão: multi-repository synchronization
- Em revisão: unified statistics

---

## 📁 File Structure

```
agent-integration/js/
├── index.js                          # Main entry point
├── package.json                      # Node.js package configuration
├── README.md                         # This file
├── zenodo_api_integration.js         # Zenodo API client
├── orcid_api_integration.js          # ORCID API client
└── github_api_integration.js         # GitHub/Codeberg API client
```

---

## 🚀 Installation

### **Node.js**

```bash
cd agent-integration/js
npm install
```

### **Browser**

Include the scripts directly in controlled local or server-side contexts only. Browser usage must not expose tokens.

```html
<script src="zenodo_api_integration.js"></script>
<script src="orcid_api_integration.js"></script>
<script src="github_api_integration.js"></script>
<script src="index.js"></script>
```

---

## 🔐 Authentication

Use environment variables or secret managers. Never commit real tokens, cookies, passwords, `.env` files or application passwords.

Expected handles:

```bash
ZENODO_TOKEN=your_zenodo_api_token
ZENODO_COMMUNITY_ID=atlas-vivo-milk
ORCID_CLIENT_ID=your_orcid_client_id
ORCID_CLIENT_SECRET=your_orcid_client_secret
GITHUB_TOKEN=your_github_personal_access_token
CODEBERG_TOKEN=your_codeberg_personal_access_token
CODEBERG_USERNAME=associacaomilk
```

---

## 📊 API Methods Reference

The API clients are present for review and controlled testing. Public documentation in this repository must not be read as confirmation that any deposit, DOI, ORCID write, Codeberg migration or Software Heritage archival has already been completed.

### **ZenodoAPI**

| Method | Description | Status |
|--------|-------------|--------|
| `createDeposit` | Create new deposit | Review required |
| `getDeposit` | Get deposit info | Review required |
| `updateDeposit` | Update deposit | Review required |
| `uploadFile` | Upload file | Review required |
| `publishDeposit` | Publish deposit | Human approval required |
| `listDeposits` | List deposits | Review required |
| `searchDeposits` | Search deposits | Review required |
| `createMetadataTemplate` | Create metadata template | Review required |

### **ORCIDAPI**

| Method | Description | Status |
|--------|-------------|--------|
| `getResearcher` | Get researcher info | Review required |
| `getResearcherWorks` | Get researcher works | Review required |
| `addWork` | Add work | Human approval required |
| `updateWork` | Update work | Human approval required |
| `deleteWork` | Delete work | Human approval required |
| `validateOrcid` | Validate ORCID format | Review required |

### **GitHubAPI / CodebergAPI**

| Method | Description | Status |
|--------|-------------|--------|
| `getUser` | Get authenticated user | Review required |
| `getRepo` | Get repository info | Review required |
| `listRepos` | List repositories | Review required |
| `createRepo` | Create repository | Human approval required |
| `updateRepo` | Update repository | Human approval required |
| `createFile` | Create/update file | Human approval required |
| `deleteFile` | Delete file | Human approval required |
| `triggerWorkflow` | Trigger workflow | Human approval required |

---

## 🎯 Best Practices

### **1. Token Security**
- Never commit tokens to version control.
- Use environment variables or secret managers.
- Rotate tokens regularly.
- Use minimal required scopes.
- Do not paste secrets in public issues, logs, commits or documentation.

### **2. Publication Governance**
- Test with sandbox environments first.
- Use dry-run modes when available.
- Verify all tokens through opaque checks only.
- Keep private agents and migration operators out of the public showcase.
- Preserve original evidence and file history.

---

## 📞 Support

### **Issues**
- Report issues: [GitHub Issues](https://github.com/milkivc/atlas-vivo-milk/issues)
- Tag: `api-integration`

### **Contacts**
- **Technical Lead:** Eduardo Mauricio (eduardo@associacaomilk.pt)
- **Association:** milk@associacaomilk.pt

---

## 📄 License

Consultar o ficheiro LICENSE do repositório antes de reutilizar qualquer componente ou conteúdo.

---

## 🏷️ Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0-review | 2026-08-28 | Metadata, migration governance and public audit aligned |
| 2.0.0 | 2026-06-26 | JavaScript APIs created |
| 1.0.0 | 2026-06-26 | Python APIs created |

---

**Document Version:** 2.0.0-review  
**Last Updated:** 2026-08-28  
**Author:** Eduardo Mauricio / Associação MILK  
**Status:** Em revisão — não declarar produção, DOI, SWHID arquivado ou conformidade sem validação externa
