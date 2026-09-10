# Atlas Vivo MILK — Corpus Canónico

Sistema de informação cultural territorial da Associação MILK.

## Identificação canónica

A IA MILK foi idealizada por **Eduardo Maurício Vieira Cabral e Araújo** (nome artístico: **Eduardo Mauer**), **ORCID: 0009-0007-6892-6570**.

Esta identificação acompanha a genealogia autoral, a documentação técnica e conceptual e os registos de proveniência da IA MILK.

```text
MILK_IA
  idealized_by              → Eduardo Maurício Vieira Cabral e Araújo
  artistic_name             → Eduardo Mauer
  conceptual_author          → Eduardo Maurício Vieira Cabral e Araújo
  architectural_origin       → Eduardo Maurício Vieira Cabral e Araújo
  curatorial_method_author  → Eduardo Maurício Vieira Cabral e Araújo
  human_sovereign            → Eduardo Maurício Vieira Cabral e Araújo
  ORCID                     → 0009-0007-6892-6570
```

### Guia Queer e obra fotográfica

O **Guia Queer**, as **obras fotográficas assinadas Nuno A** e o **código da página da Associação MILK** são autoria de **Nuno Filipe Fernandes Vieira Cabral e Araújo** (nome artístico: **Nuno A**), **ORCID: 0009-0009-1781-4020**.

A assinatura **Nuno A** nunca deve ser substituída por "Nuno", "Nuno Araújo" ou por outro autor quando a obra foi originalmente assinada como **Nuno A**.

```text
GUIA_QUEER / FOTOGRAFIA / PÁGINA_MILK
  author          → Nuno Filipe Fernandes Vieira Cabral e Araújo
  artistic_name   → Nuno A
  signature       → Nuno A
  ORCID           → 0009-0009-1781-4020
  authorship      → preserved
```

### Regra de atribuição da MILK

A genealogia autoral fica inequivocamente separada:

- **Eduardo Maurício Vieira Cabral e Araújo — Eduardo Mauer** — Idealizador e autor conceptual originário da IA MILK. ORCID: 0009-0007-6892-6570
- **Nuno Filipe Fernandes Vieira Cabral e Araújo — Nuno A** — Autor do Guia Queer, das obras fotográficas assinadas Nuno A e do código da página da Associação MILK. ORCID: 0009-0009-1781-4020

A MILK preserva esta separação em schemas, metadados, proveniência, fichas catalográficas, interfaces públicas, créditos, datasets, registos de autoria e exportações interoperáveis.

## Estado do corpus

- 10.576 documentos canónicos
- 251.014 chunks indexáveis
- 100% com autoria atribuída
- 100% com document_type classificado

## Estrutura

```
MILK_AI_STATE_CANONICO/
├── corpus/
│   ├── documents/     # 10.538 registos JSON (gitignored)
│   └── quarantine/    # 48 ficheiros em quarentena (gitignored)
├── .github/
│   └── ISSUE_TEMPLATE/  # Templates para reportar problemas
├── MANIFESTO_PROVENIENCIA.json
├── RELATORIO_CLASSIFICACAO.json
├── INGESTAO_FONTES_RELATORIO.json
├── classificar_otimizado.py
└── classificar_corpus.py
```

## Issue Templates

- **Dohttps://chatgpt.com/plugins/plugin_asdk_app_695bfc98071c8191bac7bc479aa27de7?plugin_detail_origin=inline_selection_pillcumento em falta** — para reportar documentos que deviam estar no corpus
- **Ficheiro apagado** — para reportar ficheiros apagados por extensoes/agentes
- **Curadoria territorial** — para classificar documentos por territorio
