# Nextcloud — interoperabilidade, financiabilidade e treino da IA MILK

Estado: arquitetura executável e portas de ativação. Este documento não afirma que o Nextcloud esteja instalado.
Voz externa: MILK. Executor de fluxos: Mistral. Coordenação: Atlas Vivo MILK.

## Limite arquitetónico obrigatório

| Camada | Função | Domínio/armazenamento | Regra |
|---|---|---|---|
| Pública | brinca e ativa dinâmicas curatoriais | `atlas.associacaomilk.pt` | Montserrat; sem documentos privados, segredos ou explicações administrativas |
| Invisível | trabalha, documenta, classifica, valida e governa | `nuvem.associacaomilk.pt` + dados fora da webroot | acesso autenticado; trilho de auditoria; não publica por si |
| Origem | corpus canónico | Google Drive | somente leitura; IDs e datas preservados |
| Execução | fluxos técnicos | Mistral | não assume a voz pública e não decide aprovação |
| Voz | interação cultural | IA MILK | só recebe contexto autorizado e aprovado |

Webroot proposta da aplicação: `/home/associ16/nuvem.associacaomilk.pt`.
Dados obrigatoriamente fora de qualquer webroot: `/home/associ16/.nextcloud-data` ou caminho privado equivalente confirmado pelo instalador.
Nunca usar `/home/associ16/public_html` para dados.

## Potencialidades aplicáveis

| Capacidade | Uso Atlas | Interface | Camada | Evidência/financiabilidade | Porta |
|---|---|---|---|---|---|
| WebDAV | ingestão privada retomável | RFC 4918 / SabreDAV | invisível | recibos por ficheiro, ETag, FileId, mtime | HTTPS, conta técnica e app password |
| Upload em blocos v2 | ficheiros grandes | DAV uploads | invisível | retomada e contagem por lote | compatibilidade confirmada |
| Bulk upload | muitos ficheiros pequenos | DAV bulk | invisível | menos falhas e lotes reproduzíveis | teste canário |
| OCS Share API | partilha mínima e temporária | OCS | invisível | prova de destinatário, permissão e expiração | política aprovada |
| File requests | recolha sem expor pastas | OCS Share | invisível | submissões atribuídas e isoladas | consentimento e retenção |
| Versions + comments | revisão curatorial | WebDAV/OCS | invisível | histórico de versões e parecer humano | app ativa |
| Flow + etiquetas | classificação automática | Workflow Engine | invisível | estados `privado`, `consentido`, `publicável` | regras testadas |
| Files Access Control | negar acesso por grupo/IP/tag | Flow | invisível | separação RGPD e privilégio mínimo | teste negativo obrigatório |
| Activity + admin_audit | acontecimentos e auditoria | logs/apps | invisível | trilho verificável para candidaturas e prestação de contas | retenção definida |
| FullTextSearch | recuperação autorizada | OCS Collections | invisível | pesquisa do corpus com proveniência | conta de índice estritamente limitada |
| TaskProcessing | tarefas de IA assíncronas | OCS / webhooks | invisível | estado, progresso, erro e resultado por tarefa | Nextcloud >= 30; compatibilidade real |
| Assistant API | agendamento/consulta de tarefas IA | OCS | invisível | ligação MILK–Mistral auditável | API versionada e testada |
| AppAPI / ExApps | microserviço Mistral em linguagem externa | AppAPI OCS | invisível | isolamento do executor e eventos | runtime suportado; não presumir Docker em shared hosting |
| OIDC | identidade federada | OpenID Connect | invisível | utilizadores e acessos atribuíveis | IdP e política de identidade |
| CalDAV/CardDAV | programas, calendário e contactos | DAV | invisível | cronogramas e parceiros exportáveis | necessidade confirmada |
| Federation | colaboração entre nuvens | OCS federation | invisível | cooperação interinstitucional | acordo, confiança e proteção de dados |
| Object storage | escala futura | S3/Swift compatível | invisível | capacidade e custo mensuráveis | decidir antes da importação; bucket exclusivo |
| Antivirus | verificar novos uploads | ClamAV app | invisível | controlo de risco documental | ClamAV disponível no alojamento |
| Encriptação | proteger storage/Team Folders | servidor/occ | invisível | controlo de confidencialidade | chaves, recuperação e backup testados |

## Estrutura toponímica e curatorial

A estrutura é criada apenas depois da instalação e do teste de permissões:

- `00_ENTRADA_READONLY`
- `10_CURADORIAS`
- `20_FESTAS`
- `30_BRINCADEIRAS_JOGOS`
- `40_FOLCLORE_GIRIAS`
- `50_TOPONIMIA`
- `60_EVIDENCIAS_FINANCIAMENTO`
- `70_TREINO_IA_MILK`
- `80_APROVACAO_HUMANA`
- `90_PUBLICAVEL`

Cada objeto deve ligar freguesia, município, distrito/região, fonte, direitos, consentimento, versão, hash e decisão humana. A pasta não substitui o modelo de dados: o Atlas gera manifestos JSON/GeoJSON e relações explícitas.

## Fluxo de treino fundamentado

1. Ingestão somente leitura do corpus e recibo SHA-256.
2. Classificação de dados pessoais, direitos, consentimento e proveniência.
3. Extração de texto e metadados; segmentação sem perder o identificador da fonte.
4. Indexação de recuperação respeitando grupos e permissões.
5. Mistral executa classificação, extração e TaskProcessing.
6. IA MILK responde com a voz cultural apenas sobre contexto autorizado.
7. Validação humana regista decisão, comentário, versão e hash.
8. Apenas um manifesto aprovado alimenta a Web App pública.

`Treino`, `RAG` e `indexação` são estados distintos. Nenhum fine-tuning é declarado sem dataset aprovado, job executado, versão de modelo, métricas e recibo.

## Dossiers de financiabilidade

O Nextcloud funciona como sala de dados e workflow de evidências; não concede nem garante financiamento. Para cada proposta:

- diagnóstico e necessidade territorial;
- fonte e proveniência;
- curadoria/dinâmica associada;
- titularidade, consentimento e base legal;
- parceiros, calendário e orçamento;
- entregáveis e indicadores de resultado;
- versão, SHA-256, responsável e aprovação;
- exportações interoperáveis: DCAT-AP, GeoJSON, IIIF e Web Annotation quando aplicáveis.

DCAT-AP/IIIF/GeoJSON são produzidos pelo Atlas ou por ExApp validada e guardados/versionados no Nextcloud; não são capacidades nativas presumidas do servidor.

## Portas de ativação

| Porta | Verificação | Saída factual |
|---|---|---|
| G0 | quota, versão Nextcloud, PHP, base de dados, Cron, SSL e apps | inventário sem segredos |
| G1 | subdomínio privado + diretório de dados fora da webroot | caminhos confirmados |
| G2 | instalação, HTTPS, app password, hardening e backup | health check |
| G3 | canário WebDAV com upload/download/hash/mtime | recibo do canário |
| G4 | importação privada por lotes | descobertos, transferidos, verificados, existentes, falhados, bytes, SHA-256 |
| G5 | Team Folders, grupos, etiquetas, Flow e acesso | testes positivos e negativos |
| G6 | FullTextSearch + TaskProcessing/AppAPI | consulta autorizada e tarefa rastreável |
| G7 | dossier de financiamento | pacote versionado e aprovado |
| G8 | projeção pública | manifesto aprovado; camada privada não exposta |

## Decisões técnicas

- Cron do sistema a cada cinco minutos; AJAX não serve para execução fiável.
- Primary object storage é decisão anterior à importação: ativá-lo depois pode tornar ficheiros existentes inacessíveis.
- Retenção automática não é ativada no corpus original; primeiro backup, classificação e teste de recuperação.
- A conta do índice FullTextSearch não recebe acesso transversal.
- AppAPI/ExApps em alojamento partilhado dependem do runtime permitido; não expor Docker socket.
- A versão documentada como estável pode diferir da versão Softaculous; o inventário G0 governa todas as ativações.

## Fontes oficiais

- Instalação: https://docs.nextcloud.com/server/latest/admin_manual/installation/source_installation.html
- Cron: https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/background_jobs_configuration.html
- WebDAV: https://docs.nextcloud.com/server/stable/developer_manual/client_apis/WebDAV/index.html
- OCS Share API: https://docs.nextcloud.com/server/stable/developer_manual/client_apis/OCS/ocs-share-api.html
- OIDC: https://docs.nextcloud.com/server/latest/admin_manual/configuration_user/user_auth_oidc.html
- FullTextSearch: https://docs.nextcloud.com/server/stable/developer_manual/client_apis/OCS/ocs-fulltextsearch-collections-api.html
- TaskProcessing: https://docs.nextcloud.com/server/stable/developer_manual/client_apis/OCS/ocs-taskprocessing-api.html
- Assistant API: https://docs.nextcloud.com/server/stable/developer_manual/client_apis/OCS/ocs-assistant-api.html
- Flow e acesso: https://docs.nextcloud.com/server/stable/admin_manual/file_workflows/index.html
- Activity: https://docs.nextcloud.com/server/stable/admin_manual/configuration_server/activity_configuration.html
- Logging/auditoria: https://docs.nextcloud.com/server/stable/admin_manual/configuration_server/logging_configuration.html
- AppAPI/ExApps: https://docs.nextcloud.com/server/stable/developer_manual/exapp_development/index.html
- Object storage: https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/primary_storage.html
- Antivirus: https://docs.nextcloud.com/server/stable/admin_manual/configuration_server/antivirus_configuration.html
- Encriptação: https://docs.nextcloud.com/server/stable/admin_manual/configuration_files/encryption_configuration.html
