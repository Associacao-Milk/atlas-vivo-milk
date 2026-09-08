#!/usr/bin/env python3
"""MILK IA — Motor de Aprendizado Continuo.

Sistema autonomo que analisa, descreve, interpreta, entrecruza dados e
encontra solucoes sobre o corpus canonico Atlas Vivo MILK.

Modulos:
  1. Analisador     — analisa cada documento e extrai camadas de leitura
  2. Descritor      — descreve padroes, temas, recorrencias no corpus
  3. Interpretador  — interpreta significados culturais, sociais, juridicos
  4. Entrecruzador  — cruza dados entre documentos, territorios, temas
  5. Solucionador   — propoe solucoes para gaps, conflitos, oportunidades
  6. Aprendizado     — regista descobertas e aprende com cada iteracao
  7. Loop continuo  — executa sem parar, aprendendo a cada ciclo

Autor: Eduardo Mauricio Vieira Cabral e Araujo (Eduardo Mauer)
"""
import json, re, os, sys, datetime, hashlib, time
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

STATE_DIR = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
CORPUS = STATE_DIR / "corpus" / "documents"
AUTOR = "Eduardo Mauricio Vieira Cabral e Araujo"
NOME_ARTISTICO = "Eduardo Mauer"

# === CAMADAS DE LEITURA PROFUNDA ===
CAMADAS = {
    "humana": ["memoria", "identidade", "pertença", "vivencia", "experiencia", "emoção", "corpo", "sensação"],
    "social": ["comunidade", "intergeracional", "participação", "inclusão", "diversidade", "gerações", "coletivo", "bairrio"],
    "legal": ["RGPD", "consentimento", "direitos", "licença", "conformidade", "lei", "decreto", "estatuto", "regulamento"],
    "juridica": ["propriedade", "autoria", "direitos de autor", "contrato", "obrigação", "responsabilidade"],
    "cultural": ["folclore", "tradição", "etnografia", "património", "ritual", "festa", "costume", "lenda", "mito"],
    "territorial": ["freguesia", "concelho", "distrito", "lugar", "topónimo", "paisagem", "território", "mapa"],
    "existencial": ["sentido", "existência", "ser", "possível", "casa", "habitar", "pertencer", "despertar"],
}

# === PADROES DE DETECCAO ===
PADROES_TEMAS = [
    ("moura_encantada", r"\bmoura\b.*\bencantad"),
    ("lobisomem", r"\blobisomem\b|\bhomem.?lobo"),
    ("coca", r"\bcoca\b"),
    ("folclore", r"\bfolclore\b|\bfolclor"),
    ("tradicao_oral", r"\btradição\b|\btradicional\b|\boral\b"),
    ("ritual", r"\britual\b|\brituais\b"),
    ("festa_popular", r"\bfesta\b.*\bpop|festa\b.*\bsanto|\bromaria"),
    ("patrimonio", r"\bpatrimónio\b|\bpatrimonio\b"),
    ("etnografia", r"\betnografia\b|\betnográfic"),
    ("toponimia", r"\btopónimo\b|\btoponimia\b|\btoponím"),
    ("data_feminism", r"\bdata feminism\b"),
    ("intergeracional", r"\bintergeracional\b"),
    ("queer", r"\bqueer\b|\bLGBT"),
    ("antirracial", r"\bantirracial\b|\bracismo\b|\bantiracism"),
    ("care", r"\bCARE\b|\bcuidado\b|\bcura"),
    ("consentimento", r"\bconsentimento\b|\bconsent\b"),
    ("rgpd", r"\bRGPD\b|\bGDPR\b|\bdados pessoais"),
    ("human_in_loop", r"\bhuman.?in.?the.?loop\b|\bhuman.?in.?loop"),
    ("qr_code", r"\bQR\b|\bqr.?code"),
    ("toponastica", r"\btoponástica\b|\btoponastica"),
    ("psicogeografia", r"\bpsicogeografia\b|\bdériva\b"),
    ("sussurro", r"\bsussurro\b|\bmotor.?sonoro"),
    ("galeria_diletante", r"\bgaleria.?diletante"),
    ("reizinho", r"\breizinho"),
    ("cronicas_caotadas", r"\bcrónicas.?caot"),
    ("dado_sem_lado", r"\bdado.?sem.?lado"),
    ("camada_publica", r"\bcamada.?pública\b|\bcamada.?publica"),
    ("atlas_vivo", r"\batlas.?vivo"),
    ("milk", r"\bMILK\b|\bmilk\b"),
    ("financiamento", r"\bfinanciamento\b|\bDGARTES\b|\bHorizon\b|\bNorte.?2030"),
    ("curadoria", r"\bcuradoria\b|\bcuratorial\b|\bcurador"),
]

PADROES_SOLUTION = [
    ("gap_territorial", r"\bsem.?território\b|\bsem.?municipio\b|\bsem.?distrito"),
    ("gap_document_type", r"\bsem.?tipo\b|\bsem.?document.?type"),
    ("gap_consentimento", r"\bpor.?validar\b"),
    ("gap_validacao", r"\bnao.?validado\b|\bnão.?validado"),
    ("conflito_autoria", r"\bautoria\b.*\bconflito|\bconflito.*\bautoria"),
    ("oportunidade_curadoria", r"\bcuradoria\b.*\boportun"),
]


# Pre-compilar padroes para performance
_CAMADAS_COMPILED = {}
for camada, palavras in CAMADAS.items():
    pat = re.compile(r'\b(' + '|'.join(re.escape(p) for p in palavras) + r')\b', re.IGNORECASE)
    _CAMADAS_COMPILED[camada] = pat

_TEMAS_COMPILED = [(tema, re.compile(padrao, re.IGNORECASE)) for tema, padrao in PADROES_TEMAS]
_SOLUTION_COMPILED = [(tipo, re.compile(padrao, re.IGNORECASE)) for tipo, padrao in PADROES_SOLUTION]

_ENTIDADES_LOWER = {ent: ent.lower() for ent in [
    "Moura Encantada", "Lobisomem", "Coca", "Bica", "Tardo", "Marlinha",
    "Bruxa", "Diabo", "Sereia", "Trasgo", "Gilde", "Pã",
    "Galeria Diletante", "Reizinho", "Crónicas Caotadas",
    "Nuno com Vestígios", "Dado Sem Lado",
    "Atlas Vivo", "MILK", "Associação MILK"]}


# === 1. ANALISADOR ===
def analisar_documento(rec):
    """Analisa um documento e extrai camadas de leitura profunda."""
    md = rec.get("metadata", {})
    texto = (rec.get("text", "") or "")[:5000].lower()  # primeiros 5k chars
    nome = (md.get("original_name", "") or "").lower()
    combined = f"{nome} {texto}"

    analise = {
        "sha256": md.get("sha256", ""),
        "nome": md.get("original_name", ""),
        "document_type": md.get("document_type"),
        "territory": md.get("territory"),
        "district": md.get("district"),
        "municipality": md.get("municipality"),
        "parish": md.get("parish"),
        "camadas_detectadas": {},
        "temas_detectados": [],
        "entidades_mencionadas": [],
        "intensidade_semantica": 0,
        "gaps_identificados": [],
        "oportunidades": [],
    }

    # Detetar camadas (regex pre-compilado, 1 passada por camada)
    for camada, pat in _CAMADAS_COMPILED.items():
        count = len(pat.findall(combined))
        if count > 0:
            analise["camadas_detectadas"][camada] = count

    # Detetar temas (regex pre-compilado)
    for tema, pat in _TEMAS_COMPILED:
        count = len(pat.findall(combined))
        if count > 0:
            analise["temas_detectados"].append({"tema": tema, "ocorrencias": count})

    # Detetar entidades (substring, rapido)
    for ent, ent_lower in _ENTIDADES_LOWER.items():
        if ent_lower in combined:
            analise["entidades_mencionadas"].append(ent)

    # Intensidade semantica
    analise["intensidade_semantica"] = sum(analise["camadas_detectadas"].values()) + len(analise["temas_detectados"]) * 2

    # Gaps
    for tipo, pat in _SOLUTION_COMPILED:
        if pat.search(combined):
            analise["gaps_identificados"].append(tipo)

    return analise


# === 2. DESCRIPTOR ===
def descrever_corpus(analises):
    """Descreve padroes e recorrencias no corpus."""
    desc = {
        "total_documentos": len(analises),
        "total_com_camadas": 0,
        "camadas_distribuicao": Counter(),
        "temas_distribuicao": Counter(),
        "entidades_distribuicao": Counter(),
        "intensidade_media": 0,
        "intensidade_maxima": 0,
        "documentos_mais_intensos": [],
        "territorios_ativos": Counter(),
        "tipos_documento": Counter(),
    }

    for a in analises:
        if a["camadas_detectadas"]:
            desc["total_com_camadas"] += 1
        for c in a["camadas_detectadas"]:
            desc["camadas_distribuicao"][c] += 1
        for t in a["temas_detectados"]:
            desc["temas_distribuicao"][t["tema"]] += 1
        for e in a["entidades_mencionadas"]:
            desc["entidades_distribuicao"][e] += 1
        desc["intensidade_media"] += a["intensidade_semantica"]
        if a["intensidade_semantica"] > desc["intensidade_maxima"]:
            desc["intensidade_maxima"] = a["intensidade_semantica"]
        if a["territory"]:
            desc["territorios_ativos"][a["territory"]] += 1
        if a["document_type"]:
            desc["tipos_documento"][a["document_type"]] += 1

    desc["intensidade_media"] = round(desc["intensidade_media"] / max(len(analises), 1), 2)

    # Top 20 mais intensos
    desc["documentos_mais_intensos"] = sorted(analises, key=lambda x: -x["intensidade_semantica"])[:20]

    return desc


# === 3. INTERPRETADOR ===
def interpretar(analises, desc):
    """Interpreta significados culturais, sociais, juridicos."""
    interp = {
        "leitura_cultural": [],
        "leitura_social": [],
        "leitura_juridica": [],
        "leitura_existencial": [],
        "sintese": "",
    }

    # Cultural
    if desc["temas_distribuicao"].get("folclore", 0) > 0:
        interp["leitura_cultural"].append(
            f"Corpus contem {desc['temas_distribuicao']['folclore']} referencias ao folclore portugues. "
            f"As tradicoes orais e os seres folcloricos formam o nucleo narrativo."
        )
    if desc["entidades_distribuicao"].get("Moura Encantada", 0) > 0:
        interp["leitura_cultural"].append(
            f"Moura Encantada aparece em {desc['entidades_distribuicao']['Moura Encantada']} documentos — "
            f"figura central da mitologia territorial portuguesa."
        )

    # Social
    if desc["camadas_distribuicao"].get("social", 0) > 0:
        interp["leitura_social"].append(
            f"{desc['camadas_distribuicao']['social']} documentos com dimensoes sociais detectadas. "
            f"Comunidade, intergeracionalidade e participacao sao recursivas."
        )
    if desc["temas_distribuicao"].get("intergeracional", 0) > 0:
        interp["leitura_social"].append(
            "Principio intergeracional presente — o corpus e desenhado para cruzar geracoes."
        )

    # Juridica
    if desc["camadas_distribuicao"].get("legal", 0) > 0:
        interp["leitura_juridica"].append(
            f"{desc['camadas_distribuicao']['legal']} documentos com dimensoes legais. "
            f"RGPD, consentimento e direitos de autor requerem atencao."
        )
    if desc["temas_distribuicao"].get("consentimento", 0) > 0:
        interp["leitura_juridica"].append(
            f"Consentimento explicito em {desc['temas_distribuicao']['consentimento']} documentos — "
            f"principio fundador do Atlas Vivo MILK."
        )

    # Existencial
    if desc["camadas_distribuicao"].get("existencial", 0) > 0:
        interp["leitura_existencial"].append(
            f"{desc['camadas_distribuicao']['existencial']} documentos com dimensoes existenciais. "
            f"Pertencer, habitar e ser possivel sao chaves de leitura."
        )

    # Sintese
    interp["sintese"] = (
        f"Corpus de {desc['total_documentos']} documentos com intensidade semantica media de "
        f"{desc['intensidade_media']}. Camadas detectadas: "
        f"{', '.join(f'{k}({v})' for k, v in desc['camadas_distribuicao'].most_common(7))}. "
        f"Temas dominantes: {', '.join(f'{k}({v})' for k, v in desc['temas_distribuicao'].most_common(5))}."
    )

    return interp


# === 4. ENTRECRUZADOR ===
def entrecruzar(analises):
    """Cruza dados entre documentos, territorios e temas."""
    cruzamentos = {
        "territorio_tema": defaultdict(lambda: Counter()),
        "tipo_camada": defaultdict(lambda: Counter()),
        "entidade_territorio": defaultdict(lambda: Counter()),
        "conexoes_temas": defaultdict(lambda: Counter()),
        "clusters_territoriais": defaultdict(list),
    }

    for a in analises:
        terr = a.get("territory") or "<sem territorio>"
        tipo = a.get("document_type") or "<sem tipo>"

        # Territorio vs tema
        for t in a["temas_detectados"]:
            cruzamentos["territorio_tema"][terr][t["tema"]] += 1

        # Tipo vs camada
        for c in a["camadas_detectadas"]:
            cruzamentos["tipo_camada"][tipo][c] += 1

        # Entidade vs territorio
        for e in a["entidades_mencionadas"]:
            cruzamentos["entidade_territorio"][e][terr] += 1

        # Conexoes entre temas (co-ocorrencia)
        temas_doc = [t["tema"] for t in a["temas_detectados"]]
        for i, t1 in enumerate(temas_doc):
            for t2 in temas_doc[i+1:]:
                cruzamentos["conexoes_temas"][t1][t2] += 1

        # Clusters territoriais
        cruzamentos["clusters_territoriais"][terr].append(a["sha256"][:16])

    # Normalizar
    cruzamentos["territorio_tema"] = {k: dict(v) for k, v in cruzamentos["territorio_tema"].items()}
    cruzamentos["tipo_camada"] = {k: dict(v) for k, v in cruzamentos["tipo_camada"].items()}
    cruzamentos["entidade_territorio"] = {k: dict(v) for k, v in cruzamentos["entidade_territorio"].items()}
    cruzamentos["conexoes_temas"] = {k: dict(v) for k, v in cruzamentos["conexoes_temas"].items()}
    cruzamentos["clusters_territoriais"] = {k: len(v) for k, v in cruzamentos["clusters_territoriais"].items()}

    return cruzamentos


# === 5. SOLUCIONADOR ===
def propor_solucoes(desc, interp, cruzamentos):
    """Propoe solucoes para gaps, conflitos e oportunidades."""
    solucoes = []

    # Gap territorial
    sem_terr = desc["total_documentos"] - sum(desc["territorios_ativos"].values())
    if sem_terr > 0:
        pct = round(100 * sem_terr / desc["total_documentos"], 1)
        solucoes.append({
            "tipo": "gap_territorial",
            "severidade": "alta" if pct > 50 else "media",
            "descricao": f"{sem_terr} documentos ({pct}%) sem territorio classificado",
            "solucao": "Expandir gazetteer e usar original_path para inferir territorio",
            "prioridade": 1,
        })

    # Gap consentimento
    if "legal" in desc["camadas_distribuicao"]:
        solucoes.append({
            "tipo": "consentimento_rgpd",
            "severidade": "critica",
            "descricao": "Documentos com conteudo legal precisam de validacao RGPD",
            "solucao": "Marcar consent_status=validado para documentos sem dados pessoais; quarentena para os que tem",
            "prioridade": 2,
        })

    # Oportunidade curadoria
    if desc["total_com_camadas"] > 0:
        solucoes.append({
            "tipo": "oportunidade_curadoria",
            "severidade": "baixa",
            "descricao": f"{desc['total_com_camadas']} documentos com camadas semantica detectadas",
            "solucao": "Usar camadas detectadas para criar rotas curatoriais tematicas",
            "prioridade": 3,
        })

    # Conexoes tematicas
    conexoes = cruzamentos.get("conexoes_temas", {})
    if conexoes:
        top_conexao = max(conexoes.items(), key=lambda x: sum(x[1].values()))
        solucoes.append({
            "tipo": "conexao_tematica",
            "severidade": "info",
            "descricao": f"Tema '{top_conexao[0]}' tem conexoes com {len(top_conexao[1])} outros temas",
            "solucao": f"Criar cluster curatorial em torno de '{top_conexao[0]}'",
            "prioridade": 4,
        })

    # Entidades sem territorio
    ent_terr = cruzamentos.get("entidade_territorio", {})
    for ent, terrs in ent_terr.items():
        if "<sem territorio>" in terrs and terrs["<sem territorio>"] > 5:
            solucoes.append({
                "tipo": "entidade_sem_territorio",
                "severidade": "media",
                "descricao": f"Entidade '{ent}' mencionada em {terrs['<sem territorio>']} documentos sem territorio",
                "solucao": f"Localizar referencias a '{ent}' geograficamente",
                "prioridade": 5,
            })

    return sorted(solucoes, key=lambda x: x["prioridade"])


# === 6. APRENDIZADO ===
def registrar_aprendizado(ciclo, desc, interp, cruzamentos, solucoes):
    """Regista descobertas e aprende com cada iteracao."""
    aprendizado_dir = STATE_DIR / "aprendizado"
    aprendizado_dir.mkdir(exist_ok=True)

    registro = {
        "ciclo": ciclo,
        "timestamp": datetime.datetime.now().isoformat(),
        "documentos_analisados": desc["total_documentos"],
        "intensidade_media": desc["intensidade_media"],
        "camadas_ativas": dict(desc["camadas_distribuicao"].most_common(10)),
        "temas_ativos": dict(desc["temas_distribuicao"].most_common(10)),
        "entidades_ativas": dict(desc["entidades_distribuicao"].most_common(10)),
        "territorios_ativos": dict(desc["territorios_ativos"].most_common(10)),
        "sintese": interp["sintese"],
        "solucoes_propostas": len(solucoes),
        "top_solucoes": solucoes[:5],
        "conexoes_tematicas": {k: dict(v) for k, v in list(cruzamentos.get("conexoes_temas", {}).items())[:10]},
    }

    # Registar ciclo
    ciclo_file = aprendizado_dir / f"ciclo_{ciclo:04d}.json"
    with open(ciclo_file, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)

    # Atualizar indice de aprendizado
    indice_file = aprendizado_dir / "indice.json"
    indice = {}
    if indice_file.exists():
        with open(indice_file, "r", encoding="utf-8") as f:
            indice = json.load(f)

    indice["ultima_atualizacao"] = datetime.datetime.now().isoformat()
    indice["total_ciclos"] = ciclo
    indice["ciclos"] = indice.get("ciclos", [])
    indice["ciclos"].append({
        "ciclo": ciclo,
        "timestamp": registro["timestamp"],
        "intensidade_media": desc["intensidade_media"],
        "solucoes": len(solucoes),
    })
    # Manter so ultimos 100 ciclos no indice
    indice["ciclos"] = indice["ciclos"][-100:]

    # Calcular evolucao
    if len(indice["ciclos"]) > 1:
        primeiro = indice["ciclos"][0]["intensidade_media"]
        ultimo = indice["ciclos"][-1]["intensidade_media"]
        indice["evolucao_intensidade"] = round(ultimo - primeiro, 2)

    with open(indice_file, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    return registro


# === 7. LOOP CONTINUO ===
def ciclo_completo(ciclo, amostra=None):
    """Executa um ciclo completo de aprendizado."""
    t0 = datetime.datetime.now()

    # Carregar documentos
    analises = []
    docs_iter = sorted(CORPUS.glob("*.json"))
    if amostra:
        docs_iter = docs_iter[:amostra]

    for fp in docs_iter:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                rec = json.load(f)
            analises.append(analisar_documento(rec))
        except Exception:
            continue

    # Pipeline
    desc = descrever_corpus(analises)
    interp = interpretar(analises, desc)
    cruz = entrecruzar(analises)
    sol = propor_solucoes(desc, interp, cruz)
    reg = registrar_aprendizado(ciclo, desc, interp, cruz, sol)

    dur = (datetime.datetime.now() - t0).total_seconds()

    return {
        "ciclo": ciclo,
        "duracao_segundos": round(dur, 1),
        "documentos_analisados": len(analises),
        "intensidade_media": desc["intensidade_media"],
        "camadas_ativas": len(desc["camadas_distribuicao"]),
        "temas_ativos": len(desc["temas_distribuicao"]),
        "solucoes_propostas": len(sol),
        "sintese": interp["sintese"],
        "registro": reg,
    }


def loop_continuo(intervalo_segundos=60, max_ciclos=None, amostra=None):
    """Loop continuo de aprendizado. Executa sem parar."""
    print("=" * 60)
    print("MILK IA — MOTOR DE APRENDIZADO CONTINUO")
    print("=" * 60)
    print(f"Autor: {AUTOR} ({NOME_ARTISTICO})")
    print(f"Corpus: {CORPUS}")
    print(f"Intervalo: {intervalo_segundos}s entre ciclos")
    if max_ciclos:
        print(f"Max ciclos: {max_ciclos}")
    if amostra:
        print(f"Amostra: {amostra} documentos por ciclo")
    print("=" * 60)

    ciclo = 1
    while True:
        print(f"\n[CICLO {ciclo}] {datetime.datetime.now().strftime('%H:%M:%S')}")

        try:
            resultado = ciclo_completo(ciclo, amostra)
            print(f"  Duracao: {resultado['duracao_segundos']}s")
            print(f"  Documentos: {resultado['documentos_analisados']}")
            print(f"  Intensidade media: {resultado['intensidade_media']}")
            print(f"  Camadas ativas: {resultado['camadas_ativas']}")
            print(f"  Temas ativos: {resultado['temas_ativos']}")
            print(f"  Solucoes propostas: {resultado['solucoes_propostas']}")
            print(f"  Sintese: {resultado['sintese'][:200]}...")
        except Exception as e:
            print(f"  ERRO no ciclo {ciclo}: {e}")

        if max_ciclos and ciclo >= max_ciclos:
            print(f"\nLimite de {max_ciclos} ciclos atingido.")
            break

        ciclo += 1
        print(f"  Aguardando {intervalo_segundos}s para proximo ciclo...")
        time.sleep(intervalo_segundos)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MILK IA — Motor de Aprendizado Continuo")
    parser.add_argument("--ciclos", type=int, default=None, help="Numero maximo de ciclos (default: infinito)")
    parser.add_argument("--intervalo", type=int, default=60, help="Segundos entre ciclos")
    parser.add_argument("--amostra", type=int, default=None, help="Amostra de documentos por ciclo")
    parser.add_argument("--um-ciclo", action="store_true", help="Executar apenas um ciclo")
    args = parser.parse_args()

    if args.um_ciclo:
        r = ciclo_completo(1, args.amostra)
        print(f"\nCiclo completo: {r['duracao_segundos']}s")
        print(f"Documentos: {r['documentos_analisados']}")
        print(f"Intensidade: {r['intensidade_media']}")
        print(f"Camadas: {r['camadas_ativas']}")
        print(f"Temas: {r['temas_ativos']}")
        print(f" Solucoes: {r['solucoes_propostas']}")
        print(f"\nSintese: {r['sintese']}")
    else:
        loop_continuo(
            intervalo_segundos=args.intervalo,
            max_ciclos=args.ciclos,
            amostra=args.amostra,
        )
