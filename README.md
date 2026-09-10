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
