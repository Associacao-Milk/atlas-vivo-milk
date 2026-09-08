# Auditoria pública do repositório — Atlas Vivo MILK

Data: 2026-08-28  
Repositório: `milkivc/atlas-vivo-milk`  
Estado: saneamento em curso.

## Resultado executivo

O repositório contém uma mistura de vitrine institucional, código de integração, documentação científica e workflows de migração/automação. Essa mistura não deve ser apagada sem triagem, mas precisa de classificação para preservar financiabilidade, segurança e credibilidade pública.

## Achados principais

| Área | Achado | Acção recomendada |
|---|---|---|
| Metadados | ORCIDs de Nuno e Eduardo presentes; estado de DOI/SWHID precisava distinção | Corrigido em `metadata.json`: DOI não declarado, SWHID local não arquivado |
| Workflows | Muitos workflows Mistral/Drive/FTPS/Nextcloud coexistem | Manter sem executar automaticamente; migrar lógica sensível para Forgejo privado |
| Segredos | Foram encontradas referências a nomes de segredos, não valores | Aceitável; continuar sem imprimir ou copiar credenciais |
| Codeberg | Conteúdo com agentes/LLM deve ser tratado com cautela | Enviar apenas repositórios limpos e documentação pública |
| Zenodo | Depósito só deve ocorrer após release validada | Preparar metadados; não publicar DOI antes da validação humana |
| Software Heritage | SWHID local existe, mas não equivale a arquivo público | Submeter Save Code Now apenas após origem pública aprovada |
| Conformidade | Termos como RGPD, AI Act, ISO 42001 podem soar como certificação | Usar “alinhamento”, “preparação” e “governação” até haver auditoria externa |

## Classificação dos workflows existentes

| Categoria | Exemplos | Destino |
|---|---|---|
| Validação segura | `validate-opaque-credentials.yml`, `validate-metadata.yml`, `validate-orcid.yml` | Pode permanecer público se não revelar valores |
| Publicação/release | `release.yml`, `atlas-public-release.yml`, `sync-zenodo.yml` | Exigir revisão humana antes de publicar |
| Migração privada | `mistral-nextcloud-private-migration.yml`, `mistral-drive-ftps-filewise.yml`, `mistral-cpanel-nextcloud-operator.yml` | Migrar para Forgejo privado ou manter desactivado até revisão |
| Espelho/Codeberg | `mirror-to-codeberg.yml` | Não executar sem revisão linha a linha e confirmação humana |
| Histórico experimental | workflows Mistral/Drive/FTPS antigos | Arquivar ou mover para área privada após triagem |

## Política de saneamento

1. Não remover ficheiros sem confirmação específica.
2. Não executar workflows de migração destrutiva.
3. Não expor valores de segredos.
4. Não publicar corpus, dumps ou dados sensíveis.
5. Não declarar certificação, DOI ou SWHID arquivado sem evidência externa.
6. Separar vitrine pública, trabalho privado e acervo canónico.

## Próxima intervenção segura

- Criar ou actualizar descrições públicas curtas dos repositórios.
- Preparar um pacote privado Forgejo com agentes e operadores.
- Gerar release candidate público mínimo antes de Zenodo/SWH.
- Submeter ao Software Heritage apenas uma origem pública limpa.
