# Governação de migração — Atlas Vivo MILK

Data: 2026-08-28  
Estado: em saneamento, sem declaração de produção, DOI público ou arquivo Software Heritage concluído.

## Objectivo

Este documento separa a vitrine pública da Associação MILK dos materiais internos de automação, agentes e migração. A intenção é permitir financiabilidade, preservação e interoperabilidade sem expor segredos, dados sensíveis ou reivindicações ainda não verificadas.

## Camadas de publicação

| Camada | Destino preferencial | Conteúdo permitido | Bloqueios |
|---|---|---|---|
| Vitrine pública | GitHub público, Codeberg público, páginas institucionais | README, metadados, documentação, esquemas públicos, exemplos aprovados | segredos, credenciais, dados pessoais não justificados, dumps, corpus interno |
| Trabalho técnico privado | Forgejo privado / servidor institucional | agentes, scripts de migração, logs saneados, recibos técnicos | publicação automática, credenciais em texto, artefactos sem triagem |
| Arquivo científico | Zenodo, ORCID, Software Heritage | releases aprovadas, CITATION.cff, codemeta, SWHID confirmado, DOI confirmado | DOI antes de release validada, SWHID antes de confirmação pública |
| Acervo canónico | Nextcloud/PTServidor ou repositório documental controlado | corpus, fichas, anexos, matrizes curatoriais | exposição pública sem direitos e consentimentos |

## Metadados obrigatórios antes de depósito

- Autores com ORCID:
  - Nuno Filipe Fernandes Vieira Cabral e Araújo — `0009-0009-1781-4020`.
  - Eduardo Maurício Vieira Cabral e Araújo — `0009-0007-6892-6570`.
- Licença explícita do software.
- Licença explícita dos dados quando existirem dados publicados.
- `CITATION.cff` e `metadata.json` coerentes.
- Ausência de chaves, palavras-passe, tokens, cookies ou ficheiros `.env`.
- Ausência de afirmações de conformidade não auditadas.

## Vocabulário de conformidade

Usar:

- “alinhamento com RGPD / EU AI Act / EIF / ISO/IEC 42001”.
- “preparação de governação”.
- “validação humana necessária”.
- “SWHID local preparado”.

Não usar até haver evidência externa:

- “certificado”.
- “compliance garantida”.
- “produção completa”.
- “DOI emitido”.
- “SWHID arquivado”.

## Tags técnicas de interoperabilidade

As tags úteis para financiabilidade e indexação são:

- EIF — European Interoperability Framework.
- EU AI Act — governação de risco e transparência.
- ISO/IEC 42001 — sistema de gestão de IA, apenas como alinhamento.
- FIWARE / NGSI-LD — interoperabilidade de entidades e contexto.
- IIIF — imagens, manuscritos e materiais culturais digitalizados.
- W3C WCAG — acessibilidade Web.
- Cultural Probes — metodologia participativa e curatorial.
- SAMHSA trauma-informed approach — cuidado em materiais sensíveis.
- ORCID — autoria e identidade académica.
- Zenodo / DataCite — depósito e DOI após validação.
- Software Heritage — preservação de código após origem pública aprovada.

## Regra para agentes Mistral e automações

Agentes, prompts operacionais, scripts de varredura e workflows que usam segredos devem ficar numa camada privada. Em repositórios públicos, só devem aparecer:

- interfaces documentadas;
- políticas de segurança;
- descrições de arquitectura;
- recibos saneados;
- referências opacas a segredos, nunca valores.

## Software Heritage

Um SWHID calculado localmente ajuda a preparar o depósito, mas só se torna evidência pública depois de:

1. origem Git pública e aprovada;
2. release/tag imutável;
3. submissão Save Code Now;
4. confirmação de ingestão;
5. qualificação do SWHID exacto de revisão/directório.

## Decisão actual

- GitHub fica como área de saneamento público e histórico de trabalho.
- Codeberg público deve receber apenas repos limpos, sem dependência de agentes LLM.
- Forgejo privado deve receber automações Mistral, operadores de migração e materiais sensíveis.
- Zenodo e Software Heritage só entram depois da triagem pública final.
