"""MILK IA — Motor Relacional Multimodal.

Conecta todos os domínios do Framework Conceptual — dispositivos curatoriais,
conceitos filosóficos/científicos, estratégia de financiamento, projectos
territoriais, bibliografia, framework ético e camada pública — num único
grafo relacional tipado, com arestas multimodais (texto, som, imagem, corpo,
território).

Reutiliza atlas_graph.py (nós + arestas) e provenance.py (autores canónicos).
Nenhuma nova ontologia é criada; os tipos de aresta são os definidos no
Framework Conceptual (biblioteca/milk_framework_conceptual.json).
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_FRAMEWORK_PATH = _ROOT / "biblioteca" / "milk_framework_conceptual.json"

# Modalidades multimodais (texto, som, imagem, corpo, território)
MODALITIES = ("text", "sound", "image", "body", "territory", "code")

# Tipos de aresta do motor relacional (do Framework Conceptual)
EDGE_TYPES = (
    "influência_documentada",
    "afinidade_estrutural",
    "incompatibilidade_importante",
    "coisas_que_parecem_semelhantes_mas_não_são",
    "hipótese_a_investigar",
    "colisão_capaz_de_gerar_dispositivo_novo",
    "conexão_que_falhou_e_portanto_também_informa",
    "coisa_que_emerge_sem_antecedente_evidente",
    "necessidade_pública_atende",
    "dispositivo_aplicável_em",
    "financia",
    "referencia_bibliograficamente",
    "transposição_artística",
    "tensão_produtiva",
    "cadeia_conceptual",
    "retroreferência",
    "distinção_preservada",
    "eixo_investigação",
    "manifesta_se_como",
)


def load_framework() -> dict[str, Any]:
    """Load the canonical Framework Conceptual from biblioteca."""
    if _FRAMEWORK_PATH.exists():
        return json.loads(_FRAMEWORK_PATH.read_text(encoding="utf-8"))
    return {}


class MultimodalRelationalEngine:
    """Motor relacional multimodal — grafo tipado de todos os conceitos MILK.

    Nós: dispositivos curatoriais, conceitos, projectos, fontes de
    financiamento, autores, territórios, modalidades.
    Arestas: tipadas (EDGE_TYPES), com modalidades multimodais e evidência.
    """

    def __init__(self):
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._framework = load_framework()
        self._build()

    def _add_node(self, node_id: str, node_type: str, **props) -> None:
        self._nodes.setdefault(node_id, {"id": node_id, "type": node_type, **props})

    def _add_edge(self, source: str, edge_type: str, target: str,
                  modality: str = "text", evidence: str = "") -> None:
        self._edges.append({
            "source": source, "type": edge_type, "target": target,
            "modality": modality, "evidence": evidence,
        })

    def _build(self) -> None:
        fw = self._framework
        if not fw:
            return

        # --- Documentos fonte ---
        for doc in fw.get("documentos_fonte", []):
            self._add_node(doc["id"], "documento",
                           titulo=doc.get("titulo", ""),
                           classificacao=doc.get("classificacao", ""),
                           necessidade_publica=doc.get("necessidade_publica", ""))
            # documento → necessidade pública
            if doc.get("necessidade_publica"):
                for need in doc["necessidade_publica"].split(";"):
                    need = need.strip()
                    if need:
                        self._add_node(f"need:{need}", "necessidade_publica", nome=need)
                        self._add_edge(doc["id"], "necessidade_pública_atende", f"need:{need}")

        # --- Framework conceptual (nós filosóficos) ---
        fc = fw.get("framework_conceptual", {})
        for node_id, props in fc.get("nos", {}).items():
            self._add_node(node_id, props.get("tipo", "conceito"),
                           campo=props.get("campo", ""),
                           conceitos=props.get("conceitos", []),
                           aviso=props.get("aviso", ""))

        # --- Arestas tipadas do framework conceptual ---
        for edge in fc.get("arestas_tipadas", []):
            self._add_edge(edge["origem"], edge["tipo"], edge["destino"],
                           evidence=edge.get("evidencia", ""))

        # --- Framework ético ---
        fe = fw.get("framework_etico", {})
        for p in fe.get("principios", []):
            self._add_node(f"etica:{p}", "principio_etico", nome=p)
        self._add_edge("etica:não maleficência", "afinidade_estrutural",
                       "etica:autonomia humana",
                       evidence="posso deslocar a tua percepção; não posso retirar a tua autonomia")

        # --- Estratégia de financiamento ---
        ef = fw.get("estrategia_financiamento", {})
        for fonte in ef.get("fontes_financiamento", []):
            fid = f"financ:{fonte['fonte']}"
            self._add_node(fid, "fonte_financiamento",
                           fonte=fonte["fonte"], area=fonte.get("area", ""),
                           prazo=fonte.get("prazo", ""), valor=fonte.get("valor", ""))
            # cada fonte financia necessidades mapeadas
            for need in ef.get("necessidades_publicas_mapeadas", []):
                self._add_node(f"need:{need}", "necessidade_publica", nome=need)
                self._add_edge(fid, "financia", f"need:{need}")

        # --- Projecto Campo do Possível ---
        cp = fw.get("projeto_campo_possivel", {})
        if cp:
            self._add_node("projeto:campo_possivel", "projecto_territorial",
                           nome=cp.get("nome", ""), escola=cp.get("escola", ""),
                           frase_chave=cp.get("frase_chave", ""))
            for disp in cp.get("dispositivos_atlas_aplicaveis", []):
                self._add_node(f"disp:{disp}", "dispositivo_curatorial", nome=disp)
                self._add_edge(f"disp:{disp}", "dispositivo_aplicável_em",
                               "projeto:campo_possivel", modality="territory")
            if cp.get("referencia_arquitectonica"):
                self._add_node("ref:SESC", "referencia_arquitectonica",
                               nome=cp.get("referencia_arquitectonica", ""))
                self._add_edge("ref:SESC", "influência_documentada",
                               "projeto:campo_possivel")

        # --- Camada pública ---
        cpub = fw.get("camada_publica", {})
        if cpub:
            self._add_node("camada:publica", "camada_arquitectura",
                           principio=cpub.get("principio", ""),
                           regra=cpub.get("regra_navegacao", ""))
            for comp, desc in cpub.get("componentes_não_são", {}).items():
                self._add_node(f"comp:{comp}", "componente_publico",
                               nao_e=desc)
                self._add_edge(f"comp:{comp}", "afinidade_estrutural",
                               "camada:publica", modality="text")

        # --- Bibliografia ---
        bib = fw.get("bibliografia_referenciada", {})
        for autor in bib.get("autores_citados", []):
            aid = f"autor:{autor['nome']}"
            self._add_node(aid, "autor_bibliografico",
                           nome=autor["nome"], obra=autor.get("obra", ""),
                           tema=autor.get("tema", ""))
            # ligar autores conceituais aos nós do framework conceptual
            nome_lower = autor["nome"].lower()
            for nid in self._nodes:
                if nid in nome_lower or nome_lower in nid:
                    if self._nodes[nid]["type"] in ("filosofo", "matematico", "fisico",
                                                    "psicologo", "teorico_musical",
                                                    "psicanalista"):
                        self._add_edge(aid, "referencia_bibliograficamente", nid)

        # --- Dispositivos curatoriais do catálogo existente ---
        catalog_path = _ROOT / "deploy" / "atlas-public" / "catalogo-curatorial.json"
        if catalog_path.exists():
            try:
                catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
                for entry in catalog.get("entradas", []):
                    did = f"disp:{entry['nome']}"
                    self._add_node(did, "dispositivo_curatorial",
                                   nome=entry["nome"], mecanica=entry.get("mecanica", ""),
                                   convite=entry.get("convite", ""),
                                   familia=entry.get("familia", ""))
                    self._add_edge(did, "manifesta_se_como", "camada:publica",
                                   modality="body")
            except Exception:
                pass

        # --- Modalidades multimodais nos documentos ---
        doc_modalities = {
            "doc_palavra_ritual": ["text", "body", "sound"],
            "doc_deriva_sentido": ["text", "image", "body", "territory"],
            "doc_sussurro": ["sound", "text", "territory"],
            "doc_toponomastica_qr": ["text", "image", "territory", "code"],
            "doc_dois_joguinhos": ["body", "text", "territory"],
        }
        for did, mods in doc_modalities.items():
            for mod in mods:
                self._add_node(f"mod:{mod}", "modalidade", nome=mod)
                self._add_edge(did, "manifesta_se_como", f"mod:{mod}",
                               modality=mod)

        # --- 7 camadas arquitecturais ---
        for camada in fw.get("camadas_arquitetura", []):
            cid = f"camada:{camada['nome']}"
            self._add_node(cid, "camada_arquitetura",
                           nome=camada["nome"], funcao=camada.get("funcao", ""))
            self._add_edge(cid, "afinidade_estrutural", "camada:publica")

        # --- Dispositivos de interacção ---
        for disp in fw.get("dispositivos_interacao", []):
            did = f"dinter:{disp['id']}"
            self._add_node(did, "dispositivo_interacao",
                           nome=disp["nome"], inspiracao=disp.get("inspiracao", ""),
                           modalidade=disp.get("modalidade", ""))
            self._add_edge(did, "manifesta_se_como",
                           f"mod:{disp.get('modalidade', 'text')}",
                           modality=disp.get("modalidade", "text"))

        # --- Protocolos de confiabilidade ---
        prot = fw.get("protocolos_confiabilidade", {})
        for key, desc in prot.items():
            if isinstance(desc, str):
                self._add_node(f"proto:{key}", "protocolo", nome=key, descricao=desc)
            elif isinstance(desc, list):
                for item in desc:
                    self._add_node(f"proto:{key}:{item[:20]}", "protocolo", nome=item)

        # --- Governança interpretativa ---
        gov = fw.get("governanca_interpretativa", {})
        for camada in gov.get("camadas", []):
            gid = f"gov:{camada['nome']}"
            self._add_node(gid, "camada_governanca",
                           nome=camada["nome"], descricao=camada.get("descricao", ""))

        # --- Ópera Néon ---
        opera = fw.get("opera_neon", {})
        if opera:
            self._add_node("portal:opera_neon", "portal_navegacao",
                           nome="Ópera Néon", funcao=opera.get("funcao", ""))
            self._add_edge("portal:opera_neon", "afinidade_estrutural",
                           "camada:publica")

        # --- Técnicas multimodais ---
        for tec in fw.get("tecnicas_multimodais", []):
            tid = f"tec:{tec['tecnica'][:30]}"
            self._add_node(tid, "tecnica_multimodal",
                           nome=tec["tecnica"], aplicacao=tec.get("aplicacao", ""),
                           modalidade=tec.get("modalidade", "text"))
            self._add_edge(tid, "manifesta_se_como",
                           f"mod:{tec.get('modalidade', 'text')}",
                           modality=tec.get("modalidade", "text"))

        # --- Gestão estratégica (NDIF, LCAFC, DCAN) ---
        for key, val in fw.get("gestao_estrategica", {}).items():
            self._add_node(f"gest:{key}", "modulo_estrategico",
                           nome=val.get("nome", key), funcao=val.get("funcao", ""))

        # --- Motores territoriais (Dossiê I) ---
        for motor in fw.get("motores_territoriais", []):
            mid = f"motor:{motor['id']}"
            self._add_node(mid, "motor_territorial",
                           nome=motor["nome"], definicao=motor.get("definicao", ""),
                           campo_sistema=motor.get("campo_sistema", ""))
            # motor → fontes de dados
            for fonte in motor.get("fontes_primarias", motor.get("fontes_validadas", [])):
                fid = f"dados:{fonte[:30]}"
                self._add_node(fid, "fonte_dados", nome=fonte)
                self._add_edge(mid, "necessidade_pública_atende", fid)

        # --- Tipologias de infraestrutura física ---
        for tipo in fw.get("tipologias_infraestrutura", []):
            tid = f"infra:{tipo['id']}"
            self._add_node(tid, "tipologia_infraestrutura",
                           nome=tipo["nome"], descricao=tipo.get("descricao", ""),
                           modalidade=tipo.get("modalidade", "territory"))
            # tipologia → modalidades
            for mod in tipo.get("modalidade", "").split("+"):
                self._add_edge(tid, "manifesta_se_como", f"mod:{mod}",
                               modality=mod)
            # tipologia → fontes de financiamento
            for fin in tipo.get("financiamento", []):
                finid = f"financ:{fin[:30]}"
                self._add_node(finid, "fonte_financiamento", fonte=fin)
                self._add_edge(finid, "financia", tid)

        # --- Plataformas de referência territorial ---
        for plat in fw.get("plataformas_referencia_territorial", []):
            pid = f"plat:{plat['plataforma']}"
            self._add_node(pid, "plataforma_referencia",
                           nome=plat["plataforma"],
                           mecanicas=plat.get("mecanicas", []),
                           aplicacao=plat.get("aplicacao_atlas", ""))

        # --- Fontes de dados abertas Portugal ---
        for fonte in fw.get("fontes_dados_abertas_portugal", []):
            fid = f"dados:{fonte['fonte'][:30]}"
            self._add_node(fid, "fonte_dados",
                           nome=fonte["fonte"], descricao=fonte.get("descricao", ""))

        # --- Condições territoriais como nós ---
        for cond in ["silencio_territorial", "tensao_territorial",
                     "saturacao_territorial", "vazio_ativo", "vazio_cadastral"]:
            if cond in self._nodes:
                self._add_edge(cond, "manifesta_se_como", "camada:publica",
                               modality="territory")

    # --- Queries relacionais ---

    def nodes_by_type(self, node_type: str) -> list[dict[str, Any]]:
        return [n for n in self._nodes.values() if n["type"] == node_type]

    def edges_by_type(self, edge_type: str) -> list[dict[str, Any]]:
        return [e for e in self._edges if e["type"] == edge_type]

    def neighbors(self, node_id: str) -> list[dict[str, Any]]:
        result = []
        for e in self._edges:
            if e["source"] == node_id:
                t = self._nodes.get(e["target"])
                if t:
                    result.append({"node": t, "edge": e, "direction": "out"})
            elif e["target"] == node_id:
                s = self._nodes.get(e["source"])
                if s:
                    result.append({"node": s, "edge": e, "direction": "in"})
        return result

    def path_between(self, source: str, target: str, max_depth: int = 3) -> list[list[str]]:
        """Find paths between two nodes up to max_depth hops."""
        if source not in self._nodes or target not in self._nodes:
            return []
        paths: list[list[str]] = []
        queue: list[tuple[str, list[str]]] = [(source, [source])]
        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue
            if current == target and len(path) > 1:
                paths.append(path)
                continue
            for e in self._edges:
                nxt = None
                if e["source"] == current and e["target"] not in path:
                    nxt = e["target"]
                elif e["target"] == current and e["source"] not in path:
                    nxt = e["source"]
                if nxt:
                    queue.append((nxt, path + [nxt]))
        return paths[:20]

    def by_modality(self, modality: str) -> list[dict[str, Any]]:
        return [e for e in self._edges if e.get("modality") == modality]

    def graph(self) -> dict[str, Any]:
        return {
            "schema": "ia_milk.motor_relacional_multimodal.v1",
            "nodes": list(self._nodes.values()),
            "edges": self._edges,
            "stats": {
                "nodes": len(self._nodes),
                "edges": len(self._edges),
                "modalities": MODALITIES,
                "edge_types": EDGE_TYPES,
            },
        }

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)
