# Atlas Vivo MILK — integração web e orquestração cloud

## 1. Estado factual

- O `API_ROR_MILK` localizado no Drive contém `document.json` com
  `https://api.ror.org/v2/organizations`.
- O inventário integral conhecido contém 4 870 ficheiros, 397 pastas e
  16 011 662 239 bytes.
- Descobertos: 4 870; transferidos: 0; verificados: 0; já existentes: 0;
  falhados: 0; bytes transferidos: 0.
- A migração só termina quando todos os objetos forem transferidos e verificados,
  com zero falhas. Preparação, publicação do migrador ou lote parcial não é conclusão.

## 2. Fronteiras obrigatórias

| Zona | Conteúdo | Regra |
|---|---|---|
| GitHub/Forgejo público | código, schemas e documentação sem segredos | nunca recebe arquivo Drive, tokens ou dados pessoais |
| `atlas.associacaomilk.pt` | web app validada e conteúdos públicos aprovados | substituição atómica com rollback |
| fora da webroot PTServidor | arquivo migrado, checkpoints, auditoria, agentes e configuração | acesso mínimo; sem URL pública |
| `associacaomilk.pt` | site institucional | intocável |
| Google Drive | fonte original | apenas leitura; não apagar, mover ou alterar |

## 3. Orquestração Mistral

O núcleo usa `MistralOrchestrator` e dez papéis encadeados:

1. arquitetura;
2. ontologia e protocolos;
3. RGPD/AI Act/soberania;
4. codificação;
5. revisão;
6. testes;
7. migração preservativa;
8. publicação interoperável;
9. documentação e memória;
10. monitorização e financiabilidade.

Cada tarefa circula num `AgentEnvelope`. O processamento cloud bloqueia
`confidencial` e `dados_pessoais`; remove segredos, emails e identificadores
numéricos prováveis antes do envio. A resposta é pedida em JSON e fica associada
a `task_id`, `request_hash`, `source_refs` e `log_ref`.

### Exemplo seguro

```python
from atlas_integrations.mistral import EngineeringWorkflow, MistralOrchestrator

plan = EngineeringWorkflow().plan(
    "atlas-integracao-001",
    "validar contratos de interoperabilidade",
    ["drive:API_ROR_MILK/document.json"],
    {"endpoint": "https://api.ror.org/v2/organizations"},
    classification="interno",
)

orchestrator = MistralOrchestrator()
for task in plan:
    print(orchestrator.run(task, execute=False))  # dry-run por omissão
```

Para execução real, definir `MISTRAL_API_KEY` apenas no servidor e chamar
`run(envelope, execute=True)`. Uma chave inválida ou ausente é um bloqueio factual.

## 4. Conectores e autoridade

| Sistema | Leitura | Escrita | Porta de controlo |
|---|---:|---:|---|
| ROR v2 | imediata | não aplicável | seleção humana para afiliação institucional |
| Forgejo/Codeberg | repositório/metadados | opcional | token limitado ao repositório |
| GitHub | repositório público seguro | aditiva | nunca dados privados; Codeberg continua fonte canónica |
| Zenodo | pesquisa | rascunho/depósito | sandbox primeiro; publicação só após validação |
| ORCID 3.0 | público/autorizado | obras/afiliações | OAuth individual; consentimento do titular |
| DataCite REST | consulta | DOI | conta Repository e prefixo; começar em `draft` |
| Software Heritage | consulta | pedido de arquivo | apenas origem pública e versão estabilizada |
| FIWARE NGSI-LD | consulta | entidade JSON-LD | broker configurado; dry-run por omissão |
| Nextcloud | WebDAV/OCS | ficheiros/equipas | app password/OIDC; área privada |
| IGAC/WIPO | informação pública | submissão institucional | dossiê e intervenção humana; nenhum número inventado |

## 5. Ontologia lógica mínima

`AtlasRecord` separa identidade, conteúdo, classificação, aprovação, consentimento,
licença, identificadores e proveniência. Um registo `publico` é inválido sem:

- `approval=APROVADO`;
- `consent_public=true`;
- licença explícita;
- proveniência e hash.

A projeção FIWARE usa `Entity`, `Property`, URN e contexto NGSI-LD. ROR, ORCID,
DOI e SWHID são identificadores associados, nunca substitutos da autoria ou da
validação humana.

## 6. Migração total do Drive

Fluxo preservativo:

1. inventariar IDs, caminhos, MIME, tamanho e modificação;
2. criar diretórios privados no destino;
3. transferir para ficheiro temporário;
4. calcular SHA-256;
5. comparar tamanho/hash e promover atomicamente;
6. registar `transferido`, `verificado`, `já existente` ou `falhado`;
7. retomar por checkpoint sem repetir objetos verificados;
8. validar contagens e bytes finais;
9. só então declarar conclusão.

O processo não toca na origem nem nos domínios durante a transferência.

## 7. Passkeys e credenciais

Passkeys são criadas pelo autenticador do titular (Windows Hello, iCloud,
Android ou chave FIDO2). O servidor guarda apenas credenciais de serviço em
variáveis de ambiente. Nunca guardar tokens no repositório, HTML, JavaScript do
navegador, logs ou pedidos aos agentes.

## 8. Execução e testes

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -v
atlas-integrations migration-status ../migration_stage/DRIVE_TOTAL_MANIFEST.json
atlas-integrations ror-search "Associação MILK"
```

Critério mínimo: todos os testes passam; hash canónico é determinístico; dados
pessoais são bloqueados no cloud; ações externas ficam em dry-run sem `execute`;
contagens da migração são lidas do manifesto, nunca inferidas.

## 9. Fontes técnicas oficiais

- ROR REST API v2: https://ror.readme.io/docs/rest-api
- Zenodo REST API: https://developers.zenodo.org/
- ORCID Integration Guide: https://info.orcid.org/documentation/integration-guide/
- DataCite DOI API: https://support.datacite.org/docs/api-create-dois
- Forgejo API: https://forgejo.org/docs/latest/user/api/
- Nextcloud WebDAV: https://docs.nextcloud.com/server/stable/developer_manual/client_apis/WebDAV/
- Nextcloud OCS: https://docs.nextcloud.com/server/stable/developer_manual/client_apis/OCS/
- FIWARE NGSI-LD: https://fiware.github.io/data-models/specs/ngsi-ld_howto.html

