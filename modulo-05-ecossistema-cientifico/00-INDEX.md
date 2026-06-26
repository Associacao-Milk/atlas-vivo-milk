# MÓDULO 05 — ECOSSISTEMA CIENTÍFICO, DATACITE, UNIVERSIDADES

## 🎯 **OBJETIVO PRINCIPAL**
Preparar, estruturar, ligar e manter relações técnicas e documentais com identificadores persistentes, universidades, centros de investigação, repositórios científicos, infraestruturas de preservação digital, bases de conhecimento, programas de financiamento e redes de colaboração para a **Associação MILK – Movimento de Intervenções e Linguagens Kulturais e Arte**.

---

## 📁 **ESTRUTURA COMPLETA DO MÓDULO**

```
modulo-05-ecossistema-cientifico/
├── 00-INDEX.md                          ← Este documento
├── 01-identificadores-persistentes/
│   ├── orcid/
│   │   ├── README.md
│   │   ├── orcid-mappings-completo.json  ← Mapeamento ORCID de todos os colaboradores
│   │   ├── orcid-validation-report.md    ← Relatório de validação ORCID
│   │   └── orcid-api-integration.md       ← Integração com API ORCID
│   ├── doi/
│   │   ├── README.md
│   │   ├── doi-registry.md                ← Registro de DOIs
│   │   ├── zenodo-doi-mapping.json        ← Mapeamento DOI-Zenodo
│   │   └── datacite-doi-template.json    ← Template DataCite para DOI
│   ├── datacite/
│   │   ├── README.md
│   │   ├── datacite-metadata-schema.json  ← Schema DataCite 4.4
│   │   ├── datacite-validation-rules.md   ← Regras de validação DataCite
│   │   └── datacite-examples/             ← Exemplos de metadados
│   ├── ror/
│   │   ├── README.md
│   │   ├── ror-institutions.json          ← Instituições com ROR
│   │   └── ror-validation.md              ← Validação ROR
│   ├── swhid/
│   │   ├── README.md
│   │   ├── swhid-registry.md              ← Registro SWHID
│   │   └── swhid-mapping.json             ← Mapeamento SWHID
│   └── crossref/
│       ├── README.md
│       └── crossref-mapping.json          ← Mapeamento Crossref
├── 02-repositorios-preservacao/
│   ├── zenodo/
│   │   ├── README.md
│   │   ├── zenodo-deposits.json           ← Depósitos Zenodo
│   │   └── zenodo-communities.md          ← Comunidades Zenodo
│   ├── software-heritage/
│   │   ├── README.md
│   │   ├── swh-archive-status.md          ← Status de arquivo no SWH
│   │   └── swh-mapping.json               ← Mapeamento SWH
│   └── codeberg/
│       ├── README.md
│       └── codeberg-mirror-config.yml     ← Configuração de mirror
├── 03-universidades-nucleos/
│   ├── README.md
│   ├── matriz-institucional.json           ← Matriz de instituições
│   ├── matriz-institucional.md            ← Documentação da matriz
│   ├── contactos/
│   │   ├── universidades-portuguesas.json
│   │   ├── centros-investigacao.json
│   │   └── contactos-validados.json
│   └── parcerias/
│       ├── propostas-parceria/
│       ├── memorandos-entendimento/
│       └── protocolos-cooperacao/
├── 04-redes-conhecimento/
│   ├── README.md
│   ├── openaire/
│   │   ├── README.md
│   │   ├── openaire-compliance.md         ← Conformidade OpenAIRE
│   │   └── openaire-mapping.json           ← Mapeamento OpenAIRE
│   ├── cordis/
│   │   ├── README.md
│   │   └── cordis-projects.json           ← Projetos CORDIS
│   ├── wikidata/
│   │   ├── README.md
│   │   ├── wikidata-entities.json         ← Entidades Wikidata
│   │   └── wikidata-mapping.md             ← Mapeamento Wikidata
│   └── europeana/
│       ├── README.md
│       └── europeana-mapping.json          ← Mapeamento Europeana
└── 05-financiabilidade/
    ├── README.md
    ├── programas/
    │   ├── portugal-2030.json
    │   ├── fct.json
    │   ├── dgartes.json
    │   ├── europa-criativa.json
    │   ├── erasmus-plus.json
    │   ├── cerv.json
    │   ├── horizonte-europa.json
    │   ├── interreg.json
    │   ├── eea-grants.json
    │   └── todos-programas.json
    ├── matriz-elegibilidade.json
    └── matriz-elegibilidade.md
```

---

## 📊 **RESUMO EXECUTIVO**

### ✅ **O QUE JÁ ESTÁ PRONTO**

1. **Identificadores Persistentes**
   - ✅ ORCID: 2 colaboradores validados
     - Nuno Filipe: `0009-0009-1781-4020`
     - Eduardo Maurício: `0009-0007-6892-6570`
   - ✅ ROR: Associação MILK (`https://ror.org/05ma71t58`)
   - ✅ DOI: Template DataCite pronto
   - ✅ SWHID: Integração com Software Heritage

2. **Repositórios e Preservação**
   - ✅ Zenodo: Metadados completos (`.zenodo.json`)
   - ✅ GitHub: 8 repositórios ativos
   - ✅ Codeberg: Workflows de sincronização configurados
   - ✅ Software Heritage: APIs de integração

3. **APIs de Integração** (atlas-vivo-milk)
   - ✅ `zenodo_api_integration.js`
   - ✅ `orcid_api_integration.js`
   - ✅ `github_api_integration.js`
   - ✅ `index.js` (interface unificada)

4. **Automação**
   - ✅ 6+ workflows GitHub Actions
   - ✅ 5 consoles HTML para acesso fácil
   - ✅ Validação automática de ORCIDs

---

## 🎯 **PRÓXIMOS PASSOS (TURBINAMENTO)**

### **Fase 1: Identificadores Persistentes (PRIORIDADE 1)**
- [ ] Completar mapeamento ORCID para todos os colaboradores
- [ ] Gerar DOI para datasets existentes via Zenodo
- [ ] Registrar prefixo DataCite para Associação MILK
- [ ] Criar SWHID para todos os repositórios de código
- [ ] Validar ROR para todas as instituições parceiras

### **Fase 2: Repositórios e Preservação (PRIORIDADE 2)**
- [ ] Configurar mirror automático para Codeberg
- [ ] Submeter datasets para Zenodo com DOI
- [ ] Configurar preservação no Software Heritage
- [ ] Criar repositórios universitários (se aplicável)

### **Fase 3: Universidades e Núcleos (PRIORIDADE 3)**
- [ ] Criar matriz institucional completa
- [ ] Identificar núcleos de investigação afins
- [ ] Preparar propostas de parceria
- [ ] Estabelecer contactos iniciais

### **Fase 4: Redes de Conhecimento (PRIORIDADE 4)**
- [ ] Mapear integração com OpenAIRE
- [ ] Pesquisar projetos semelhantes no CORDIS
- [ ] Criar entidades no Wikidata
- [ ] Preparar integração com Europeana

### **Fase 5: Financiabilidade (PRIORIDADE 5)**
- [ ] Atualizar matriz de elegibilidade
- [ ] Preparar candidaturas para programas prioritários
- [ ] Identificar parceiros necessários
- [ ] Criar calendarização de submissões

---

## 📞 **CONTACTOS E RESPONSÁVEIS**

| Área | Responsável | Email | ORCID |
|------|-------------|-------|-------|
| Coordenação Geral | Nuno Filipe | nuno@associacaomilk.pt | [0009-0009-1781-4020](https://orcid.org/0009-0009-1781-4020) |
| Técnico | Eduardo Maurício | eduardo@associacaomilk.pt | [0009-0007-6892-6570](https://orcid.org/0009-0007-6892-6570) |
| Associação MILK | - | milk@associacaomilk.pt | - |

---

## 🔗 **LINKS IMPORTANTES**

- **GitHub**: [https://github.com/milkivc](https://github.com/milkivc)
- **Codeberg**: [https://codeberg.org/milkivc](https://codeberg.org/milkivc)
- **ORCID Nuno**: [https://orcid.org/0009-0009-1781-4020](https://orcid.org/0009-0009-1781-4020)
- **ORCID Eduardo**: [https://orcid.org/0009-0007-6892-6570](https://orcid.org/0009-0007-6892-6570)
- **ROR MILK**: [https://ror.org/05ma71t58](https://ror.org/05ma71t58)
- **Zenodo**: [https://zenodo.org](https://zenodo.org)
- **Software Heritage**: [https://archive.softwareheritage.org](https://archive.softwareheritage.org)

---

## 📝 **NOTAS IMPORTANTES**

1. **Regra Central**: Todas as alterações externas requerem:
   - API ou conector disponível
   - Token/OAuth válido
   - Escopo de permissão compatível
   - Pré-visualização da alteração
   - Confirmação humana explícita
   - Registo da ação executada

2. **Modos de Execução**:
   - **Modo 1**: Preparação sem acesso (documentação, metadados)
   - **Modo 2**: Leitura autorizada (informação pública)
   - **Modo 3**: Escrita assistida (preparar + confirmar)
   - **Modo 4**: Execução controlada (token limitado + confirmação)
   - **Modo 5**: Publicação/depósito (validação explícita)

3. **Nunca afirmar**: DOI, SWHID, afiliação, parceria, financiamento, submissão ou publicação sem evidência real.

---

## 🚀 **COMO COMEÇAR A USAR**

1. **Navegue pela estrutura**: Use os links acima para explorar cada camada
2. **Consulte os JSONs**: Todos os dados estruturados estão em formato JSON
3. **Use os templates**: Modelos prontos para candidaturas, emails e memorandos
4. **Valide os dados**: Checklists de validação disponíveis
5. **Integre com APIs**: Use as APIs de integração para automação

---

**📌 Status**: Em desenvolvimento ativo  
**📅 Última atualização**: 2026-06-26  
**👤 Responsável**: Vibe Code Agent + Associação MILK
