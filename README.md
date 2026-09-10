# Atlas Vivo MILK — Corpus Canonico

Sistema de informacao cultural territorial da Associacao MILK.
Curadoria e autoria: **Eduardo Mauricio Vieira Cabral e Araujo** (Eduardo Mauer)

## Estado do corpus

- 10.538 documentos canonicos
- 250.887 chunks indexaveis
- 268 MB de texto
- 100% com autoria atribuida
- 100% com document_type classificado
- 5% com deteccao territorial automatica

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

- **Documento em falta** — para reportar documentos que deviam estar no corpus
- **Ficheiro apagado** — para reportar ficheiros apagados por extensoes/agentes
- **Curadoria territorial** — para classificar documentos por territorio
