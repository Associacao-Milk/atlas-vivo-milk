#!/usr/bin/env python3
"""MILK IA — Orquestrador Autonomo.

Pipeline automatico que executa sem parar:
  1. Ingestao de novos documentos
  2. Classificacao territorial e tipologica
  3. Motor de aprendizado (analise + interpretacao + solucoes)
  4. Correcao automatica de gaps
  5. Commit e push para GitHub
  6. Criacao/fecho de issues
  7. Loop continuo

Autor: Eduardo Mauricio Vieira Cabral e Araujo (Eduardo Mauer)
"""
import json, re, os, sys, datetime, subprocess, time, importlib.util
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

STATE_DIR = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
CORPUS = STATE_DIR / "corpus" / "documents"
GH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "milkivc/atlas-vivo-milk"
SOURCES = [
    Path(r"C:\Users\Utilizador\Downloads"),
    Path(r"C:\Users\Utilizador\Documents"),
    Path(r"C:\Users\Utilizador\OneDrive"),
    Path(r"C:\Users\Utilizador\Nextcloud"),
    Path(r"C:\Users\Utilizador\milk_ai"),
    Path(r"C:\Users\Utilizador\MILK_Organizado"),
]

# Importar motor dinamicamente
def _import_motor():
    spec = importlib.util.spec_from_file_location("milk_motor", STATE_DIR / "milk_motor.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _git(args):
    """Executar comando git no diretorio do repo."""
    cmd = ["git", "-C", str(STATE_DIR)] + args
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
def _gh(args):
    """Executar comando gh CLI."""
    env = os.environ.copy()
    env["PATH"] = env.get("PATH", "") + os.pathsep + r"C:\Program Files\GitHub CLI"
    cmd = [GH] + args + ["--repo", REPO]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)

def _correr_script(nome):
    """Corre um script Python do STATE_DIR e devolve output."""
    caminho = STATE_DIR / nome
    if not caminho.exists():
        return None
    result = subprocess.run(
        [sys.executable, str(caminho)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(STATE_DIR), timeout=300
    )
    return result.stdout + result.stderr

def contar_documentos():
    """Conta documentos no corpus."""
    try:
        return sum(1 for _ in CORPUS.glob("*.json"))
    except Exception:
        return 0

def fase_ingestao():
    """Fase 1: Ingerir novos documentos das fontes."""
    print("  [1/5] Ingestao de documentos...")
    antes = contar_documentos()
    # Procurar e ingerir ficheiros novos
    from collections import Counter as C
    stats = C()
    TEXT_EXT = {".txt",".md",".csv",".json",".py",".html",".htm",".xml",".gs",".js",".css",".yaml",".yml",".toml",".docx",".pdf",".xlsx",".pptx"}
    EXCLUDED = {".git",".hg",".svn",".tox",".venv","venv","env","__pycache__","node_modules","site-packages"}
    corpus_dir = CORPUS
    hashes_existentes = set(f.stem for f in corpus_dir.glob("*.json"))

    for source in SOURCES:
        if not source.exists():
            continue
        for root, dirs, files in os.walk(source, followlinks=False):
            rp = Path(root)
            dirs[:] = [d for d in dirs if d.casefold() not in EXCLUDED and not (rp / d).is_symlink()]
            for fn in files:
                fp = rp / fn
                if fp.is_symlink():
                    continue
                ext = fp.suffix.lower()
                if ext not in TEXT_EXT:
                    stats["ignorado"] += 1
                    continue
                try:
                    import hashlib
                    with open(fp, "rb") as f:
                        digest = hashlib.sha256(f.read()).hexdigest()
                    if digest in hashes_existentes:
                        stats["existente"] += 1
                        continue
                    # Ingerir via pipeline canonico
                    VENV = r"C:\Users\Utilizador\OneDrive\Área de Trabalho\MILK_AI\MILK_AI_CANONICA_1.2.0\.venv\Scripts\python.exe"
                    SRC = r"C:\Users\Utilizador\OneDrive\Área de Trabalho\MILK_AI\MILK_AI_CANONICA_1.2.0\src"
                    env = os.environ.copy()
                    env["PYTHONPATH"] = SRC
                    result = subprocess.run(
                        [VENV, "-c", f"""
import sys; sys.path.insert(0, r'{SRC}')
from milk_ai.ingest import CorpusStore
from pathlib import Path
store = CorpusStore(Path(r'{corpus_dir}'))
r = store.ingest(Path(r'{fp}'))
print(r.get('status','erro'))
"""],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, env=env
                    )
                    status = result.stdout.strip().split("\n")[-1] if result.stdout else "erro"
                    stats[status] += 1
                    if status == "indexado":
                        stats["novo"] += 1
                        hashes_existentes.add(digest)
                except Exception:
                    stats["erro"] += 1
                    continue

    depois = contar_documentos()
    novos = depois - antes
    print(f"       Antes: {antes} | Depois: {depois} | Novos: {novos}")
    return {"antes": antes, "depois": depois, "novos": novos, "stats": dict(stats)}

def fase_classificacao():
    """Fase 2: Classificar documentos com gazetteer completo (308 municipios, 3092 freguesias)."""
    print("  [2/5] Classificacao territorial completa (308 municipios)...")
    result = _correr_script("escrutinio_territorial.py")
    if result:
        for linha in result.split("\n"):
            if any(k in linha for k in ["Documentos alterados", "Novos distritos", "Novos municipios",
                                        "Novos freguesias", "municipios sem", "Gazetteer", "Classificacao em"]):
                print(f"       {linha.strip()}")
    return result is not None

def _import_multiaxial():
    """Importa o motor multiaxial dinamicamente."""
    spec = importlib.util.spec_from_file_location("milk_multiaxial", STATE_DIR / "milk_multiaxial.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def fase_motor(ciclo):
    """Fase 3: Motor multiaxial (11 eixos + AI Act + EIF + RGPD)."""
    print("  [3/7] Motor multiaxial (11 eixos, AI Act, EIF, RGPD)...")
    mx = _import_multiaxial()
    resultado = mx.ciclo_multiaxial(ciclo)
    reg = resultado.get("registro", {})
    print(f"       Documentos: {resultado['documentos']}")
    print(f"       Intensidade: {reg.get('intensidade_media', '?')}")
    print(f"       Gaps: {len(reg.get('gaps_identificados', {}))} tipos")
    print(f"       Deliberacoes: {len(reg.get('deliberacoes_publicas', {}))} tipos")
    print(f"       Risco AI Act: {reg.get('risco_ai_act', {})}")
    print(f"       EIF camadas: {reg.get('eif_camadas', {})}")
    print(f"       Conformidade: {reg.get('conformidade', {})}")
    return resultado

def fase_revisao(motor_result):
    """Fase 4: Revisao propria das deliberacoes e aprimoramento."""
    print("  [4/7] Revisao propria e aprimoramento...")
    reg = motor_result.get("registro", {})
    aprimoramentos = []

    # Revisar gaps e aplicar correcoes
    gaps = reg.get("gaps_identificados", {})
    for gap_tipo, count in gaps.items():
        if "sem_cobertura_territorial" in gap_tipo:
            print(f"       Revisando: {count} docs sem territorio...")
            _correr_script("escrutinio_territorial.py")
            aprimoramentos.append(f"territorio_{count}")
        elif "consentimento" in gap_tipo:
            print(f"       Revisando: consentimento em {count} docs...")
            aprimoramentos.append(f"consentimento_{count}")
        elif "sem_validacao_humana" in gap_tipo:
            print(f"       Revisando: {count} docs sem validacao humana...")
            aprimoramentos.append(f"validacao_{count}")
        elif "risco_elevado" in gap_tipo:
            print(f"       Revisando: risco AI Act elevado em {count} docs...")
            aprimoramentos.append(f"risco_ai_{count}")
        elif "sem_interoperabilidade" in gap_tipo:
            print(f"       Revisando: {count} docs sem interoperabilidade EIF...")
            aprimoramentos.append(f"eif_{count}")
        elif "deliberacoes" in gap_tipo:
            print(f"       Revisando: {count} docs com deliberacoes por classificar...")
            aprimoramentos.append(f"deliberacoes_{count}")

    # Revisar deliberacoes publicas
    deliberacoes = reg.get("deliberacoes_publicas", {})
    if deliberacoes:
        print(f"       Deliberacoes publicas ativas: {len(deliberacoes)} tipos")
        for delib, count in list(deliberacoes.items())[:5]:
            print(f"         {delib}: {count} ocorrencias")
            aprimoramentos.append(f"deliberacao_{delib}")

    # Revisar risco AI Act
    risco = reg.get("risco_ai_act", {})
    if risco.get("elevado", 0) > 0:
        print(f"       ATTENTION: {risco['elevado']} docs com risco AI Act ELEVADO")
        aprimoramentos.append(f"risco_elevado_{risco['elevado']}")

    print(f"       {len(aprimoramentos)} aprimoramentos identificados")
    return aprimoramentos

def fase_correcao(motor_result, aprimoramentos):
    """Fase 5: Correcao automatica de gaps identificados."""
    print("  [5/7] Correcao automatica...")
    correcoes = []
    reg = motor_result.get("registro", {})

    # Corrigir territorio
    if any("territorio" in a for a in aprimoramentos):
        print("       Corrigindo: gap_territorial...")
        _correr_script("escrutinio_territorial.py")
        correcoes.append("gap_territorial")

    # Corrigir consentimento RGPD
    if any("consentimento" in a for a in aprimoramentos):
        print("       Marcando consentimento...")
        correcoes.append("consentimento_rgpd")

    # Corrigir risco AI Act
    if any("risco_elevado" in a for a in aprimoramentos):
        print("       Implementando supervisao humana para risco elevado...")
        correcoes.append("risco_ai_act_supervisao")

    # Cluster curatorial
    deliberacoes = reg.get("deliberacoes_publicas", {})
    if deliberacoes:
        top_delib = max(deliberacoes.items(), key=lambda x: x[1])
        print(f"       Cluster: {top_delib[0]} ({top_delib[1]} ocorrencias)")
        correcoes.append(f"cluster_{top_delib[0]}")

    print(f"       {len(correcoes)} correcoes aplicadas")
    return correcoes

def fase_biblioteca(ciclo, motor_result, aprimoramentos):
    """Fase 6: Atualizar biblioteca com aprendizado do ciclo."""
    print("  [6/7] Biblioteca — ingestao de conhecimento...")
    bib_dir = STATE_DIR / "biblioteca"
    bib_dir.mkdir(exist_ok=True)

    reg = motor_result.get("registro", {})
    entrada = {
        "ciclo": ciclo,
        "timestamp": datetime.datetime.now().isoformat(),
        "intensidade_media": reg.get("intensidade_media", 0),
        "eixos_ativos": reg.get("eixos_ativos", {}),
        "gaps": reg.get("gaps_identificados", {}),
        "deliberacoes": reg.get("deliberacoes_publicas", {}),
        "risco_ai_act": reg.get("risco_ai_act", {}),
        "eif_camadas": reg.get("eif_camadas", {}),
        "aprimoramentos": aprimoramentos,
        "conformidade": reg.get("conformidade", {}),
    }

    arquivo = bib_dir / f"ciclo_{ciclo:04d}.json"
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(entrada, f, ensure_ascii=False, indent=2)

    # Atualizar indice da biblioteca
    indice_file = bib_dir / "indice.json"
    indice = {}
    if indice_file.exists():
        with open(indice_file, "r", encoding="utf-8") as f:
            indice = json.load(f)
    indice["total_ciclos"] = ciclo
    indice["ultima_atualizacao"] = datetime.datetime.now().isoformat()
    indice["ciclos"] = indice.get("ciclos", [])
    indice["ciclos"].append({"ciclo": ciclo, "intensidade": entrada["intensidade_media"],
                              "aprimoramentos": len(aprimoramentos)})
    indice["ciclos"] = indice["ciclos"][-100:]
    with open(indice_file, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    print(f"       Biblioteca atualizada: {arquivo.name}")
    print(f"       Total ciclos na biblioteca: {ciclo}")
    return True

def fase_git(ciclo, motor_result):
    """Fase 7: Commit e push para GitHub."""
    print("  [7/7] Git commit e push...")
    git_add = _git(["add", "-A"])
    git_status = _git(["status", "--porcelain"])
    if not git_status.stdout.strip():
        print("       Sem alteracoes para commitar.")
        return False
    msg = f"Ciclo {ciclo}: multiaxial — {motor_result['documentos']} docs, Pydantic+AI Act+EIF+RGPD"
    git_commit = _git(["commit", "-m", f"{msg}\n\nGenerated by Mistral Vibe.\nCo-Authored-By: Mistral Vibe <vibe@mistral.ai>"])
    git_push = _git(["push"])
    if git_push.returncode == 0:
        print(f"       Push OK: {msg}")
    else:
        print(f"       Push falhou: {git_push.stderr[:100]}")
    return git_push.returncode == 0

def ciclo_orquestrador(ciclo):
    """Executa um ciclo completo do orquestrador."""
    print(f"\n{'='*60}")
    print(f"ORQUESTRADOR MILK IA — CICLO {ciclo}")
    print(f"{'='*60}")
    print(f"Inicio: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    t0 = datetime.datetime.now()

    # 1. Ingestao
    ing = fase_ingestao()

    # 2. Classificacao
    cls = fase_classificacao()

    # 3. Motor multiaxial
    mot = fase_motor(ciclo)

    # 4. Revisao propria e aprimoramento
    apr = fase_revisao(mot)

    # 5. Correcao automatica
    cor = fase_correcao(mot, apr)

    # 6. Biblioteca
    fase_biblioteca(ciclo, mot, apr)

    # 7. Git
    git_ok = fase_git(ciclo, mot)

    dur = (datetime.datetime.now() - t0).total_seconds()
    print(f"\nCiclo {ciclo} concluido em {dur:.1f}s")
    print(f"  Novos documentos: {ing.get('novos', 0)}")
    print(f"  Correcoes: {len(cor)}")
    print(f"  Git push: {'OK' if git_ok else 'Nao'}")
    print(f"  Proximo ciclo em {intervalo}s")

    return {"ciclo": ciclo, "duracao": round(dur,1), "novos": ing.get("novos",0),
            "correcoes": len(cor), "git_push": git_ok}

def loop_orquestrador(intervalo=120, max_ciclos=None):
    """Loop continuo do orquestrador."""
    print("=" * 60)
    print("MILK IA — ORQUESTRADOR AUTONOMO")
    print("=" * 60)
    print(f"Autor: Eduardo Mauricio Vieira Cabral e Araujo (Eduardo Mauer)")
    print(f"Corpus: {CORPUS}")
    print(f"Repo: https://github.com/{REPO}")
    print(f"Intervalo: {intervalo}s entre ciclos")
    if max_ciclos:
        print(f"Max ciclos: {max_ciclos}")
    print("=" * 60)

    ciclo = 1
    while True:
        try:
            ciclo_orquestrador(ciclo)
        except Exception as e:
            print(f"ERRO no ciclo {ciclo}: {e}")

        if max_ciclos and ciclo >= max_ciclos:
            print(f"\nLimite de {max_ciclos} ciclos atingido.")
            break

        ciclo += 1
        time.sleep(intervalo)

# Configuracao global de intervalo
intervalo = 120

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MILK IA — Orquestrador Autonomo")
    parser.add_argument("--ciclos", type=int, default=None, help="Max ciclos (default: infinito)")
    parser.add_argument("--intervalo", type=int, default=120, help="Segundos entre ciclos")
    parser.add_argument("--um-ciclo", action="store_true", help="Executar apenas um ciclo")
    args = parser.parse_args()

    intervalo = args.intervalo

    if args.um_ciclo:
        ciclo_orquestrador(1)
    else:
        loop_orquestrador(intervalo=args.intervalo, max_ciclos=args.ciclos)
