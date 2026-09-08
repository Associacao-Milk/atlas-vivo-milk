#!/usr/bin/env python3
"""MILK IA — Escrutinio Territorial Maximo.

Cria gazetteer completo de Portugal (308 municipios, 3092 freguesias)
e analisa cada documento contra TODOS os territorios.
Depois cruza com dados da administracao publica para encontrar GAPS
que as autoridades nao veem.

Autor: Eduardo Mauricio Vieira Cabral e Araujo (Eduardo Mauer)
"""
import json, re, os, sys, datetime, csv
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CORPUS = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO\corpus\documents")
STATE_DIR = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
CSV_CURADO = Path(r"C:\Users\Utilizador\Downloads\drive-download-20260828T071927Z-1-001\id_registo,id_freguesia,freguesia.csv")

# === 1. CONSTRUIR GAZETTEER COMPLETO ===
# Ler dados curados (103 freguesias com leitura profunda)
curadas = {}
if CSV_CURADO.exists():
    with open(CSV_CURADO, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            freg = row.get("freguesia","").strip()
            conc = row.get("concelho","").strip()
            if freg and conc:
                curadas[f"{conc.lower()}|{freg.lower()}"] = {
                    "id_registo": row.get("id_registo",""),
                    "id_freguesia": row.get("id_freguesia",""),
                    "tipo_entrada": row.get("tipo_entrada",""),
                    "intensidade": row.get("intensidade",""),
                    "titulo_publico": row.get("titulo_publico",""),
                    "texto_curto": row.get("texto_curto",""),
                    "gatilho_reflexao": row.get("gatilho_reflexao",""),
                    "demografia": row.get("demografia",""),
                    "compliance_iso": row.get("compliance_iso",""),
                }

# Ler a hierarquia oficial completa da gist (ja descarregada)
# Como nao posso importar o JSON gigante, vou ler do ficheiro se existir
GIST_FILE = STATE_DIR / "pt_territorios.json"

if not GIST_FILE.exists():
    # Descarregar da gist
    import urllib.request
    url = "https://gist.githubusercontent.com/tomahock/a6c07dd255d04499d8336237e35a4827/raw/distritos-concelhos-freguesias-Portugal.json"
    try:
        urllib.request.urlretrieve(url, GIST_FILE)
        print(f"Hierarquia oficial descarregada: {GIST_FILE}")
    except Exception as e:
        print(f"Erro a descarregar: {e}")

# Processar hierarquia
distritos_map = {}  # codigo -> nome
concelhos_map = {}  # codigo -> (nome, distrito_codigo)
freguesias_map = {}  # codigo -> (nome, concelho_codigo, distrito_codigo)
hierarquia = {"distritos": {}, "freguesias_curadas": curadas}

if GIST_FILE.exists():
    with open(GIST_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)

    distrito_atual = None
    concelho_atual = None
    for item in dados:
        if item["level"] == 1:
            distrito_atual = item["code"]
            distritos_map[item["code"]] = item["name"]
            hierarquia["distritos"][item["name"]] = {"concelhos": {}}
        elif item["level"] == 2:
            concelho_atual = item["code"]
            concelhos_map[item["code"]] = (item["name"], distrito_atual)
            d_nome = distritos_map.get(distrito_atual, "")
            if d_nome in hierarquia["distritos"]:
                hierarquia["distritos"][d_nome]["concelhos"][item["name"]] = []
        elif item["level"] == 3:
            freguesias_map[item["code"]] = (item["name"], concelho_atual, distrito_atual)
            c_data = concelhos_map.get(concelho_atual, ("", 0))
            c_nome = c_data[0]
            d_nome = distritos_map.get(distrito_atual, "")
            if d_nome in hierarquia["distritos"] and c_nome in hierarquia["distritos"][d_nome]["concelhos"]:
                hierarquia["distritos"][d_nome]["concelhos"][c_nome].append(item["name"])

# Estatisticas
n_dist = len(hierarquia["distritos"])
n_conc = sum(len(d["concelhos"]) for d in hierarquia["distritos"].values())
n_freg = sum(len(c) for d in hierarquia["distritos"].values() for c in d["concelhos"].values())
print(f"Gazetteer: {n_dist} distritos, {n_conc} concelhos, {n_freg} freguesias")
print(f"Freguesias curadas (leitura profunda): {len(curadas)}")

# Gravar gazetteer
with open(STATE_DIR / "gazetteer_pt.json", "w", encoding="utf-8") as f:
    json.dump(hierarquia, f, ensure_ascii=False, indent=2)

# === 2. PRE-COMPILAR TODOS OS NOMES PARA DETECCAO RAPIDA ===
# Construir lista de todos os nomes de territorios
todos_nomes = {}  # nome_lower -> (tipo, distrito, concelho, freguesia)
for d_nome, d_data in hierarquia["distritos"].items():
    todos_nomes[d_nome.lower()] = ("distrito", d_nome, None, None)
    for c_nome, f_list in d_data["concelhos"].items():
        todos_nomes[c_nome.lower()] = ("concelho", d_nome, c_nome, None)
        for f_nome in f_list:
            # So freguesias nao-uniao (nomes curtos) para evitar falsos positivos
            if not f_nome.startswith("União"):
                todos_nomes[f_nome.lower()] = ("freguesia", d_nome, c_nome, f_nome)

print(f"Total nomes para deteccao: {len(todos_nomes)}")

# Deteccao por substring (muito mais rapido que regex com 2000+ padroes)
# So nomes > 5 chars para evitar falsos positivos
nomes_lookup = {n: info for n, info in todos_nomes.items() if len(n) > 5}
print(f"Total nomes para deteccao: {len(nomes_lookup)} (substring match)")

# === 3. CLASSIFICAR TODOS OS DOCUMENTOS ===
print(f"\nClassificando 10.538 documentos contra gazetteer completo...")
t0 = datetime.datetime.now()
stats = Counter()
novos = 0

for fp in sorted(CORPUS.glob("*.json")):
    try:
        with open(fp, "r", encoding="utf-8") as f:
            rec = json.load(f)
    except Exception:
        continue

    md = rec.get("metadata", {})
    nome = (md.get("original_name", "") or "").lower()
    caminho = (md.get("original_path", "") or "").lower()
    texto = (rec.get("text", "") or "")[:8000].lower()
    combined = f"{nome} {caminho} {texto}"

    alterado = False

    # Se ja tem distrito E municipio, skip
    if md.get("district") and md.get("municipality"):
        continue

    # Detetar territorios por substring (rapido)
    distrito = md.get("district")
    municipio = md.get("municipality")
    freguesia = md.get("parish")

    for nome_lower, info in nomes_lookup.items():
        if nome_lower not in combined:
            continue
        if distrito and municipio and freguesia:
            break
        tipo, d, c, f = info
        if not distrito and tipo == "distrito":
            md["district"] = d
            distrito = d
            alterado = True
            stats["novo_distrito"] += 1
        if not municipio and tipo in ("concelho", "freguesia"):
            md["municipality"] = c or d
            municipio = c or d
            alterado = True
            stats["novo_municipio"] += 1
        if not freguesia and tipo == "freguesia":
            md["parish"] = f
            freguesia = f
            alterado = True
            stats["novo_freguesia"] += 1

    # Territory
    if md.get("district") or md.get("municipality"):
        parts = [x for x in [md.get("district"), md.get("municipality"), md.get("parish")] if x]
        md["territory"] = " > ".join(parts)
        alterado = True

    if alterado:
        rec["metadata"] = md
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, separators=(",", ":"))
        novos += 1

dur = (datetime.datetime.now() - t0).total_seconds()
print(f"Classificacao em {dur:.1f}s")
print(f"  Documentos alterados: {novos}")
print(f"  Novos distritos: {stats['novo_distrito']}")
print(f"  Novos municipios: {stats['novo_municipio']}")
print(f"  Novos freguesias: {stats['novo_freguesia']}")

# === 4. ESCRUTINIO — ENCONTRAR GAPS QUE AUTORIDADES NAO VEEM ===
print(f"\n{'='*60}")
print(f"ESCRUTINIO TERRITORIAL — GAPS DA ADMINISTRACAO PUBLICA")
print(f"{'='*60}")

# Contar cobertura por territorio
cobertura = defaultdict(lambda: {"documentos": 0, "tipos": Counter(), "temas": Counter()})
for fp in sorted(CORPUS.glob("*.json")):
    try:
        with open(fp, "r", encoding="utf-8") as f:
            rec = json.load(f)
    except Exception:
        continue
    md = rec.get("metadata", {})
    d = md.get("district", "<sem distrito>")
    m = md.get("municipality", "<sem concelho>")
    key = f"{d} > {m}"
    cobertura[key]["documentos"] += 1
    if md.get("document_type"):
        cobertura[key]["tipos"][md["document_type"]] += 1

# Ranking de cobertura
ranking = sorted(cobertura.items(), key=lambda x: -x[1]["documentos"])

print(f"\nTop 15 territorios com mais documentacao:")
for terr, dados in ranking[:15]:
    print(f"  {terr[:50]:50s} {dados['documentos']:>5} docs")

print(f"\nTerritorios com POUCOS documentos (gaps de cobertura):")
gaps = [(t, d) for t, d in ranking if d["documentos"] < 3 and "<sem" not in t]
for terr, dados in gaps[:20]:
    print(f"  {terr[:50]:50s} {dados['documentos']:>5} docs")

print(f"\nMunicipios do gazetteer SEM NENHUM documento:")
municipios_com_docs = set()
for terr, _ in ranking:
    if "<sem" not in terr:
        parts = terr.split(" > ")
        if len(parts) >= 2:
            municipios_com_docs.add(parts[1])

municipios_sem_docs = []
for d_nome, d_data in hierarquia["distritos"].items():
    for c_nome in d_data["concelhos"]:
        if c_nome not in municipios_com_docs:
            municipios_sem_docs.append(f"{d_nome} > {c_nome}")

print(f"  Total: {len(municipios_sem_docs)} municipios sem documentacao")
for m in municipios_sem_docs[:30]:
    print(f"    {m}")

# Gravar relatorio de escrutinio
relatorio = {
    "gerado_em": datetime.datetime.now().isoformat(),
    "gazetteer": {"distritos": n_dist, "concelhos": n_conc, "freguesias": n_freg, "curadas": len(curadas)},
    "classificacao": {"alterados": novos, "novos_distritos": stats["novo_distrito"],
                      "novos_municipios": stats["novo_municipio"], "novos_freguesias": stats["novo_freguesia"]},
    "cobertura": {t: {"documentos": d["documentos"], "tipos": dict(d["tipos"].most_common(5))} for t, d in ranking[:50]},
    "gaps_cobertura": [{"territorio": t, "documentos": d["documentos"]} for t, d in gaps],
    "municipios_sem_docs": municipios_sem_docs,
    "total_municipios_sem_docs": len(municipios_sem_docs),
}

with open(STATE_DIR / "ESCRUTINIO_TERRITORIAL.json", "w", encoding="utf-8") as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)
print(f"\nRelatorio gravado: {STATE_DIR / 'ESCRUTINIO_TERRITORIAL.json'}")
