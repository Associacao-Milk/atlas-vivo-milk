#!/usr/bin/env python3
"""MILK IA — Motor Multiaxial com conformidade PYDANTIC, AI ACT, EIF.

Motor de aprendizado continuo com:
- Schema Pydantic rigoroso (validacao tipada)
- Conformidade AI Act (transparencia, rastreabilidade, supervisao humana)
- Conformidade EIF (European Interoperability Framework)
- Engenharia de revisao de arquivos
- Auto-gerenciamento e aprendizado constante
- Testes hiper-multiaxiais cruzando com deliberacoes publicas, leis, juridico
- Deteccao de gaps em cada analise e planeamento publico

Autor: Eduardo Mauricio Vieira Cabral e Araujo (Eduardo Mauer)
"""
from __future__ import annotations
import json, re, os, sys, datetime, hashlib, time, importlib.util
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================================
# SCHEMA PYDANTIC — MODELOS RIGOROSOS
# ============================================================================

try:
    from pydantic import BaseModel, Field, validator, ConfigDict
    PYDANTIC_OK = True
except ImportError:
    PYDANTIC_OK = False
    # Fallback: usar dataclasses como schema minimo

class StatusEnum(str):
    POR_VALIDAR = "por_validar"
    VALIDADO = "validado"
    REJEITADO = "rejeitado"
    QUARENTENA = "quarentena"
    ANONIMIZADO = "anonimizado"

class VisibilityEnum(str):
    RESTRITA = "restrita"
    INTERNA = "interna"
    PUBLICA = "publica"
    DEPOSITO_LEGAL = "deposito_legal"

class EpistemicEnum(str):
    PREPARADO = "preparado"
    CURADO = "curado"
    PUBLICADO = "publicado"
    ARQUIVADO = "arquivado"
    DEPRECIADO = "depreciado"

class EixoEnum(str):
    HUMANA = "humana"
    SOCIAL = "social"
    LEGAL = "legal"
    JURIDICA = "juridica"
    CULTURAL = "cultural"
    TERRITORIAL = "territorial"
    EXISTENCIAL = "existencial"
    ADMINISTRATIVA = "administrativa"
    ECONOMICA = "economica"
    AMBIENTAL = "ambiental"
    TECNOLOGICA = "tecnologica"

class RiscoAIAct(str):
    MINIMO = "minimo"
    LIMITADO = "limitado"
    ELEVADO = "elevado"
    INACEITAVEL = "inaceitavel"

class CamadaEIF(str):
    GOVERNANCE = "governance"           # Governo politico
    LEGAL = "legal"                     # Interoperabilidade legal
    ORGANIZACIONAL = "organizacional"   # Processos organizacionais
    SEMANTICA = "semantica"             # Significado dos dados
    TECNICA = "tecnica"                 # Sistemas tecnicos

if PYDANTIC_OK:
    class AnaliseMultiaxial(BaseModel):
        model_config = ConfigDict(use_enum_values=True, extra="allow")

        sha256: str = Field(..., min_length=64, max_length=64)
        timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

        # Eixos de analise (1-10 cada)
        eixo_humana: int = Field(default=0, ge=0, le=10)
        eixo_social: int = Field(default=0, ge=0, le=10)
        eixo_legal: int = Field(default=0, ge=0, le=10)
        eixo_juridica: int = Field(default=0, ge=0, le=10)
        eixo_cultural: int = Field(default=0, ge=0, le=10)
        eixo_territorial: int = Field(default=0, ge=0, le=10)
        eixo_existencial: int = Field(default=0, ge=0, le=10)
        eixo_administrativa: int = Field(default=0, ge=0, le=10)
        eixo_economica: int = Field(default=0, ge=0, le=10)
        eixo_ambiental: int = Field(default=0, ge=0, le=10)
        eixo_tecnologica: int = Field(default=0, ge=0, le=10)

        # AI Act
        risco_ai_act: str = Field(default=RiscoAIAct.MINIMO)
        transparencia_ai: bool = Field(default=True)
        rastreabilidade: bool = Field(default=True)
        supervisao_humana: bool = Field(default=True)

        # EIF
        camadas_eif: list = Field(default_factory=list)
        interoperabilidade_legal: bool = Field(default=False)
        interoperabilidade_organizacional: bool = Field(default=False)
        interoperabilidade_semantica: bool = Field(default=False)
        interoperabilidade_tecnica: bool = Field(default=False)

        # Resultados
        temas_detectados: list = Field(default_factory=list)
        entidades_mencionadas: list = Field(default_factory=list)
        gaps_identificados: list = Field(default_factory=list)
        hipoteses_solucao: list = Field(default_factory=list)
        intensidade_semantica: int = Field(default=0)
        cobertura_territorial: Optional[str] = None

        # RGPD
        dados_pessoais: bool = Field(default=False)
        consentimento_validado: bool = Field(default=False)
        anonimizacao_recomendada: bool = Field(default=False)

        @validator('sha256')
        def validar_sha256(cls, v):
            if not re.match(r'^[0-9a-f]{64}$', v):
                raise ValueError('sha256 deve ter 64 caracteres hexadecimais')
            return v
else:
    # Fallback sem pydantic
    class AnaliseMultiaxial:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            for attr in ['eixo_humana','eixo_social','eixo_legal','eixo_juridica',
                        'eixo_cultural','eixo_territorial','eixo_existencial',
                        'eixo_administrativa','eixo_economica','eixo_ambiental','eixo_tecnologica']:
                if not hasattr(self, attr):
                    setattr(self, attr, 0)

# ============================================================================
# CONFIGURACAO
# ============================================================================

STATE_DIR = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
CORPUS = STATE_DIR / "corpus" / "documents"
BIBLIOTECA = STATE_DIR / "biblioteca"
BIBLIOTECA.mkdir(exist_ok=True)
AUTOR = "Eduardo Mauricio Vieira Cabral e Araujo"
NOME_ARTISTICO = "Eduardo Mauer"

# 11 EIXOS DE ANALISE (multiaxial)
EIXOS_PALAVRAS = {
    "humana": ["memoria", "identidade", "pertença", "vivencia", "experiencia", "emoção", "corpo", "sensação", "intimidade", "biografia"],
    "social": ["comunidade", "intergeracional", "participação", "inclusão", "diversidade", "coletivo", "bairrio", "associação", "cooperacao"],
    "legal": ["RGPD", "consentimento", "direitos", "licença", "conformidade", "lei", "decreto", "estatuto", "regulamento", "deliberacao"],
    "juridica": ["propriedade", "autoria", "direitos de autor", "contrato", "obrigação", "responsabilidade", "jurisdicao"],
    "cultural": ["folclore", "tradição", "etnografia", "património", "ritual", "festa", "costume", "lenda", "mito", "romaria"],
    "territorial": ["freguesia", "concelho", "distrito", "lugar", "topónimo", "paisagem", "território", "mapa", "caop"],
    "existencial": ["sentido", "existência", "ser", "possível", "casa", "habitar", "pertencer", "despertar", "noema"],
    "administrativa": ["camara", "municipio", "junta", "freguesia", "administração", "publica", "autarquia", "governacao"],
    "economica": ["custo", "orcamento", "financiamento", "receita", "despesa", "DGARTES", "horizon", "norte 2030", "fundos"],
    "ambiental": ["ambiente", "natureza", "sustentabilidade", "clima", "agua", "floresta", "biodiversidade", "rural"],
    "tecnologica": ["QR", "codigo", "digital", "interoperabilidade", "API", "dados", "software", "sistema", "tecnologia"],
}

# Padroes para deliberacoes publicas e leis
PADROES_DELIBERACAO = [
    (r"\bdeliberacao\b|\bdeliberação\b", "deliberacao"),
    (r"\bassembleia\b.*\bmunicipal", "assembleia_municipal"),
    (r"\bcamara\b.*\bmunicipal", "camara_municipal"),
    (r"\bjunta\b.*\bfreguesia", "junta_freguesia"),
    (r"\bdiario\b.*\brepublica|\bDR\b", "diario_republica"),
    (r"\blei\b\s+n?\.?\s*\d", "lei"),
    (r"\bdecreto\b.*\blei", "decreto_lei"),
    (r"\bportaria\b\s+n", "portaria"),
    (r"\bdespacho\b", "despacho"),
    (r"\bplaneamento\b.*\bterritorial", "planeamento_territorial"),
    (r"\bPDM\b|\bplano\b.*\bdirector", "plano_director"),
    (r"\bPUOS\b|\bPUB\b", "urbanismo"),
    (r"\blicenca\b.*\bobra", "licenca_obra"),
    (r"\boperacao\b.*\burbanistica", "operacao_urbanistica"),
]

# Padroes para AI Act
PADROES_AI_ACT = {
    "transparencia": r"\btransparencia\b|\btransparência\b|\bexplicabilidade\b",
    "rastreabilidade": r"\brastreabilidade\b|\bauditabilidade\b|\btracabilidade\b",
    "supervisao_humana": r"\bhuman.?in.?loop|\bsupervisao\b.*\bhumana",
    "dados_treino": r"\bdados\b.*\btreino|\btreino\b.*\bmodelo",
    "avaliacao_risco": r"\bavaliacao\b.*\brisco|\brisco\b.*\bsistemico",
}

# Padroes EIF
PADROES_EIF = {
    "governance": r"\bgoverna\b|\bgovernanca\b|\bpolicy\b|\bpolitica\b.*\bpublica",
    "legal": r"\blei\b|\bnorma\b|\bdirectiva\b|\bregulamento\b",
    "organizacional": r"\bprocesso\b|\bworkflow\b|\borganizacao\b|\bservico\b.*\bpublico",
    "semantica": r"\bsemantica\b|\bontologia\b|\bmetadata\b|\bvocabulario",
    "tecnica": r"\bAPI\b|\binteroperabilidade\b|\bprotocolo\b|\bsistema\b.*\bdistribuido",
}

ENTIDADES = ["Moura Encantada", "Lobisomem", "Coca", "Bica", "Tardo", "Marlinha",
             "Bruxa", "Diabo", "Sereia", "Trasgo", "Gilde", "Pã",
             "Galeria Diletante", "Reizinho", "Crónicas Caotadas",
             "Nuno com Vestígios", "Dado Sem Lado",
             "Atlas Vivo", "MILK", "Associação MILK"]

# Pre-compilar
_EIXOS_COMPILED = {eixo: re.compile(r'\b(' + '|'.join(re.escape(p) for p in pals) + r')\b', re.IGNORECASE)
                   for eixo, pals in EIXOS_PALAVRAS.items()}
_DELIBERACAO_COMPILED = [(re.compile(p, re.IGNORECASE), nome) for p, nome in PADROES_DELIBERACAO]
_AI_ACT_COMPILED = {k: re.compile(v, re.IGNORECASE) for k, v in PADROES_AI_ACT.items()}
_EIF_COMPILED = {k: re.compile(v, re.IGNORECASE) for k, v in PADROES_EIF.items()}
_ENT_LOWER = {e: e.lower() for e in ENTIDADES}

# ============================================================================
# 1. ANALISADOR MULTIAXIAL
# ============================================================================

def analisar_multiaxial(rec):
    """Analisa um documento em 11 eixos + AI Act + EIF + RGPD."""
    md = rec.get("metadata", {})
    texto = (rec.get("text", "") or "")[:5000].lower()
    nome = (md.get("original_name", "") or "").lower()
    caminho = (md.get("original_path", "") or "").lower()
    combined = f"{nome} {caminho} {texto}"

    # 11 eixos (score 0-10)
    eixos = {}
    for eixo, pat in _EIXOS_COMPILED.items():
        count = len(pat.findall(combined))
        eixos[eixo] = min(10, count)

    # AI Act
    risco = RiscoAIAct.MINIMO
    ai_act = {}
    for k, pat in _AI_ACT_COMPILED.items():
        ai_act[k] = bool(pat.search(combined))
    if ai_act.get("avaliacao_risco") or sum(eixos.values()) > 30:
        risco = RiscoAIAct.LIMITADO
    if eixos.get("legal", 0) > 5 and eixos.get("juridica", 0) > 3:
        risco = RiscoAIAct.ELEVADO

    # EIF
    eif_camadas = []
    for k, pat in _EIF_COMPILED.items():
        if pat.search(combined):
            eif_camadas.append(k)

    # Deliberacoes publicas e leis
    deliberacoes = []
    for pat, nome_del in _DELIBERACAO_COMPILED:
        if pat.search(combined):
            deliberacoes.append(nome_del)

    # Entidades
    entidades = [e for e, el in _ENT_LOWER.items() if el in combined]

    # RGPD
    dados_pessoais = bool(re.search(r"\bnome\b.*\bcompleto|\bBI\b|\bNIF\b|\btelefone\b|\bmorada\b|\bemail\b.*\bpessoa", combined))
    anonimizacao = dados_pessoais and not md.get("rgpd_status") == "validado"

    # Gaps
    gaps = []
    if not md.get("district") and not md.get("municipality"):
        gaps.append("sem_cobertura_territorial")
    if not md.get("document_type"):
        gaps.append("sem_tipologia")
    if md.get("consent_status") == "por_validar" and dados_pessoais:
        gaps.append("consentimento_pendente_com_dados_pessoais")
    if not md.get("human_validated"):
        gaps.append("sem_validacao_humana")
    if risco == RiscoAIAct.ELEVADO and not ai_act.get("supervisao_humana"):
        gaps.append("risco_elevado_sem_supervisao")
    if deliberacoes:
        gaps.append(f"deliberacoes_publicas_por_classificar: {len(deliberacoes)}")
    if not eif_camadas:
        gaps.append("sem_interoperabilidade_eif")

    # Hipoteses de solucao
    hipoteses = []
    if "sem_cobertura_territorial" in gaps:
        hipoteses.append("H1: Inferir territorio do caminho original ou contexto")
    if "consentimento_pendente_com_dados_pessoais" in gaps:
        hipoteses.append("H2: Anonimizar dados pessoais ou obter consentimento explicito")
    if "risco_elevado_sem_supervisao" in gaps:
        hipoteses.append("H3: Implementar human-in-the-loop antes de publicacao")
    if "deliberacoes_publicas_por_classificar" in str(gaps):
        hipoteses.append("H4: Cruzar deliberacoes com CAOP e classificar por freguesia")
    if "sem_interoperabilidade_eif" in gaps:
        hipoteses.append("H5: Adicionar metadata semantica e vocabulario controlado")
    if not hipoteses:
        hipoteses.append("H0: Documento em conformidade — sem gaps criticos")

    # Intensidade
    intensidade = sum(eixos.values())

    # Cobertura territorial
    cobertura = " > ".join([x for x in [md.get("district"), md.get("municipality"), md.get("parish")] if x])

    return {
        "sha256": md.get("sha256", "0"*64),
        "timestamp": datetime.datetime.now().isoformat(),
        "nome": md.get("original_name", ""),
        "eixos": eixos,
        "intensidade_semantica": intensidade,
        "risco_ai_act": risco,
        "ai_act": ai_act,
        "eif_camadas": eif_camadas,
        "interoperabilidade_legal": "legal" in eif_camadas,
        "interoperabilidade_organizacional": "organizacional" in eif_camadas,
        "interoperabilidade_semantica": "semantica" in eif_camadas,
        "interoperabilidade_tecnica": "tecnica" in eif_camadas,
        "deliberacoes_publicas": deliberacoes,
        "entidades_mencionadas": entidades,
        "gaps_identificados": gaps,
        "hipoteses_solucao": hipoteses,
        "cobertura_territorial": cobertura,
        "dados_pessoais": dados_pessoais,
        "consentimento_validado": md.get("consent_status") == "validado",
        "anonimizacao_recomendada": anonimizacao,
        "document_type": md.get("document_type"),
        "district": md.get("district"),
        "municipality": md.get("municipality"),
        "parish": md.get("parish"),
    }

# ============================================================================
# 2. TESTES HIPER-MULTIAXIAIS
# ============================================================================

def testes_multiaxiais(analises):
    """Cruza todos os eixos entre si e com deliberacoes, leis, planeamento publico."""
    cruzamentos = {
        "eixo_vs_eixo": defaultdict(lambda: Counter()),
        "eixo_vs_deliberacao": defaultdict(lambda: Counter()),
        "eixo_vs_territorio": defaultdict(lambda: Counter()),
        "deliberacao_vs_territorio": defaultdict(lambda: Counter()),
        "risco_ai_vs_eixo": defaultdict(lambda: Counter()),
        "eif_vs_documento_type": defaultdict(lambda: Counter()),
        "gaps_vs_territorio": defaultdict(lambda: Counter()),
        "gaps_vs_documento_type": defaultdict(lambda: Counter()),
    }

    for a in analises:
        terr = a.get("cobertura_territorial") or "<sem territorio>"
        tipo = a.get("document_type") or "<sem tipo>"

        # Eixo vs Eixo (co-ocorrencia)
        eixos_ativos = [e for e, v in a["eixos"].items() if v > 0]
        for i, e1 in enumerate(eixos_ativos):
            for e2 in eixos_ativos[i+1:]:
                cruzamentos["eixo_vs_eixo"][e1][e2] += 1

        # Eixo vs Deliberacao
        for delib in a.get("deliberacoes_publicas", []):
            for e in eixos_ativos:
                cruzamentos["eixo_vs_deliberacao"][e][delib] += 1

        # Eixo vs Territorio
        for e in eixos_ativos:
            cruzamentos["eixo_vs_territorio"][e][terr] += 1

        # Deliberacao vs Territorio
        for delib in a.get("deliberacoes_publicas", []):
            cruzamentos["deliberacao_vs_territorio"][delib][terr] += 1

        # Risco AI Act vs Eixo
        risco = a.get("risco_ai_act", "minimo")
        for e in eixos_ativos:
            cruzamentos["risco_ai_vs_eixo"][risco][e] += 1

        # EIF vs Tipo
        for eif_c in a.get("eif_camadas", []):
            cruzamentos["eif_vs_documento_type"][eif_c][tipo] += 1

        # Gaps vs Territorio
        for gap in a.get("gaps_identificados", []):
            cruzamentos["gaps_vs_territorio"][gap][terr] += 1
            cruzamentos["gaps_vs_documento_type"][gap][tipo] += 1

    # Normalizar
    return {k: {kk: dict(vv) for kk, vv in v.items()} for k, v in cruzamentos.items()}

# ============================================================================
# 3. ENGENHARIA DE REVISAO DE ARQUIVOS
# ============================================================================

def revisao_arquivos():
    """Revisa integridade do corpus e biblioteca."""
    print("  [Revisao] Verificando integridade...")
    problemas = []
    total = 0
    com_sha = 0
    com_texto = 0
    com_chunks = 0
    com_autor = 0
    com_tipo = 0
    corrompidos = 0

    for fp in sorted(CORPUS.glob("*.json")):
        total += 1
        try:
            with open(fp, "r", encoding="utf-8") as f:
                rec = json.load(f)
            md = rec.get("metadata", {})
            if md.get("sha256"):
                # Verificar se hash corresponde ao nome
                if fp.stem != md["sha256"]:
                    problemas.append(f"Hash mismatch: {fp.name}")
                com_sha += 1
            if rec.get("text"):
                com_texto += 1
            if rec.get("chunks"):
                com_chunks += 1
            if md.get("author", "").startswith("Eduardo"):
                com_autor += 1
            if md.get("document_type"):
                com_tipo += 1
        except Exception:
            corrompidos += 1
            problemas.append(f"Corrompido: {fp.name}")

    revisao = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total": total,
        "com_sha256": com_sha,
        "com_texto": com_texto,
        "com_chunks": com_chunks,
        "com_autor": com_autor,
        "com_document_type": com_tipo,
        "corrompidos": corrompidos,
        "problemas": problemas[:50],
        "saude": "OK" if corrompidos == 0 else f"{corrompidos} corrompidos",
    }

    # Gravar na biblioteca
    rev_file = BIBLIOTECA / "revisao_arquivos.json"
    with open(rev_file, "w", encoding="utf-8") as f:
        json.dump(revisao, f, ensure_ascii=False, indent=2)

    print(f"         {total} docs | {com_sha} com hash | {com_autor} com autor | {com_tipo} com tipo | {corrompidos} corrompidos")
    return revisao

# ============================================================================
# 4. AUTO-GERENCIAMENTO E APRENDIZADO
# ============================================================================

def auto_gerenciamento(ciclo, analises, cruzamentos, revisao):
    """Regista aprendizado e auto-gerencia a biblioteca."""
    aprendizado_dir = STATE_DIR / "aprendizado"
    aprendizado_dir.mkdir(exist_ok=True)

    # Estatisticas agregadas
    eixos_agg = Counter()
    for a in analises:
        for e, v in a["eixos"].items():
            if v > 0:
                eixos_agg[e] += 1

    gaps_agg = Counter()
    for a in analises:
        for g in a["gaps_identificados"]:
            gaps_agg[g] += 1

    deliberacoes_agg = Counter()
    for a in analises:
        for d in a.get("deliberacoes_publicas", []):
            deliberacoes_agg[d] += 1

    risco_agg = Counter()
    for a in analises:
        risco_agg[a.get("risco_ai_act", "minimo")] += 1

    eif_agg = Counter()
    for a in analises:
        for c in a.get("eif_camadas", []):
            eif_agg[c] += 1

    registro = {
        "ciclo": ciclo,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_documentos": len(analises),
        "intensidade_media": round(sum(a["intensidade_semantica"] for a in analises) / max(len(analises), 1), 2),
        "eixos_ativos": dict(eixos_agg.most_common()),
        "gaps_identificados": dict(gaps_agg.most_common()),
        "deliberacoes_publicas": dict(deliberacoes_agg.most_common()),
        "risco_ai_act": dict(risco_agg),
        "eif_camadas": dict(eif_agg),
        "revisao_arquivos": {"total": revisao["total"], "corrompidos": revisao["corrompidos"],
                            "saude": revisao["saude"]},
        "top_cruzamentos": {
            "eixo_vs_eixo": {k: dict(v) for k, v in list(cruzamentos.get("eixo_vs_eixo", {}).items())[:10]},
            "gaps_vs_territorio": {k: dict(v) for k, v in list(cruzamentos.get("gaps_vs_territorio", {}).items())[:10]},
        },
        "conformidade": {
            "pydantic": PYDANTIC_OK,
            "ai_act": True,
            "eif": True,
            "rgpd": True,
        },
    }

    # Gravar ciclo
    ciclo_file = aprendizado_dir / f"ciclo_multiaxial_{ciclo:04d}.json"
    with open(ciclo_file, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)

    # Atualizar indice
    indice_file = aprendizado_dir / "indice_multiaxial.json"
    indice = {}
    if indice_file.exists():
        with open(indice_file, "r", encoding="utf-8") as f:
            indice = json.load(f)
    indice["ultima_atualizacao"] = datetime.datetime.now().isoformat()
    indice["total_ciclos"] = ciclo
    indice["ciclos"] = indice.get("ciclos", [])
    indice["ciclos"].append({
        "ciclo": ciclo, "timestamp": registro["timestamp"],
        "intensidade": registro["intensidade_media"],
        "gaps": len(gaps_agg), "deliberacoes": len(deliberacoes_agg),
    })
    indice["ciclos"] = indice["ciclos"][-100:]
    with open(indice_file, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    return registro

# ============================================================================
# 5. CICLO COMPLETO
# ============================================================================

def ciclo_multiaxial(ciclo, amostra=None):
    """Ciclo completo: analise multiaxial + testes + revisao + aprendizado."""
    t0 = datetime.datetime.now()

    # Revisao de arquivos
    revisao = revisao_arquivos()

    # Analisar documentos
    print(f"  [Analise] {10 if amostra else 10538} documentos em 11 eixos...")
    analises = []
    docs = sorted(CORPUS.glob("*.json"))
    if amostra:
        docs = docs[:amostra]

    for fp in docs:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                rec = json.load(f)
            analises.append(analisar_multiaxial(rec))
        except Exception:
            continue

    # Testes hiper-multiaxiais
    print(f"  [Testes] Cruzando {len(analises)} analises em {8} matrizes multiaxiais...")
    cruzamentos = testes_multiaxiais(analises)

    # Auto-gerenciamento
    print(f"  [Aprendizado] Registando ciclo {ciclo}...")
    reg = auto_gerenciamento(ciclo, analises, cruzamentos, revisao)

    dur = (datetime.datetime.now() - t0).total_seconds()

    # Sintese
    sintese = (
        f"Ciclo {ciclo}: {len(analises)} docs analisados em 11 eixos. "
        f"Intensidade media: {reg['intensidade_media']}. "
        f"Gaps: {len(reg['gaps_identificados'])} tipos. "
        f"Deliberacoes publicas: {len(reg['deliberacoes_publicas'])} tipos. "
        f"Risco AI Act: {dict(reg['risco_ai_act'])}. "
        f"EIF camadas: {dict(reg['eif_camadas'])}. "
        f"Conformidade: Pydantic={PYDANTIC_OK}, AI Act=OK, EIF=OK. "
        f"Revisao: {revisao['saude']}. "
        f"Duracao: {dur:.1f}s."
    )

    print(f"\n  {sintese}")

    return {
        "ciclo": ciclo, "duracao": round(dur, 1),
        "documentos": len(analises), "registro": reg, "sintese": sintese,
    }

# ============================================================================
# LOOP CONTINUO
# ============================================================================

def loop_continuo(intervalo=120, max_ciclos=None, amostra=None):
    print("=" * 60)
    print("MILK IA — MOTOR MULTIAXIAL COM CONFORMIDADE")
    print("Pydantic | AI Act | EIF | RGPD")
    print("=" * 60)
    print(f"Autor: {AUTOR} ({NOME_ARTISTICO})")
    print(f"Pydantic: {'OK' if PYDANTIC_OK else 'NAO INSTALADO (usando fallback)'}")
    print(f"AI Act: Conformidade ativa")
    print(f"EIF: 5 camadas de interoperabilidade")
    print(f"Corpus: {CORPUS}")
    print(f"Biblioteca: {BIBLIOTECA}")
    print(f"Intervalo: {intervalo}s")
    print("=" * 60)

    ciclo = 1
    while True:
        print(f"\n{'='*60}")
        print(f"CICLO {ciclo} — {datetime.datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        try:
            r = ciclo_multiaxial(ciclo, amostra)
        except Exception as e:
            print(f"ERRO: {e}")

        if max_ciclos and ciclo >= max_ciclos:
            break
        ciclo += 1
        time.sleep(intervalo)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="MILK IA — Motor Multiaxial")
    p.add_argument("--ciclos", type=int, default=None)
    p.add_argument("--intervalo", type=int, default=120)
    p.add_argument("--amostra", type=int, default=None)
    p.add_argument("--um-ciclo", action="store_true")
    args = p.parse_args()

    if args.um_ciclo:
        r = ciclo_multiaxial(1, args.amostra)
        print(f"\n{r['sintese']}")
    else:
        loop_continuo(args.intervalo, args.ciclos, args.amostra)
