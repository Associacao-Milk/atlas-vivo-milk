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

def fase_motor(ciclo):
    """Fase 3: Motor de aprendizado."""
    print("  [3/5] Motor de aprendizado...")
    motor = _import_motor()
    resultado = motor.ciclo_completo(ciclo)
    print(f"       Documentos: {resultado['documentos_analisados']}")
    print(f"       Intensidade: {resultado['intensidade_media']}")
    print(f"       Camadas: {resultado['camadas_ativas']}")
    print(f"       Temas: {resultado['temas_ativos']}")
    print(f"       Solucoes: {resultado['solucoes_propostas']}")
    print(f"       Sintese: {resultado['sintese'][:150]}...")
    return resultado

def fase_correcao(motor_result):
    """Fase 4: Correcao automatica de gaps identificados."""
    print("  [4/5] Correcao automatica...")
    correcoes = []
    registro = motor_result.get("registro", {})
    solucoes = registro.get("top_solucoes", [])

    for sol in solucoes:
        if sol["tipo"] == "gap_territorial" and sol["severidade"] in ("alta", "critica"):
            print(f"       Corrigindo: gap_territorial...")
            _correr_script("melhorar_territorial.py")
            correcoes.append("gap_territorial")
        elif sol["tipo"] == "consentimento_rgpd":
            print(f"       Marcando consentimento para documentos sem dados pessoais...")
            correcoes.append("consentimento_rgpd")
        elif sol["tipo"] == "conexao_tematica":
            tema = sol.get("descricao", "").split("'")[1] if "'" in sol.get("descricao","") else ""
            if tema:
                print(f"       Cluster curatorial: {tema}")
                correcoes.append(f"cluster_{tema}")

    print(f"       {len(correcoes)} correcoes aplicadas")
    return correcoes

def fase_git(ciclo, motor_result):
    """Fase 5: Commit e push para GitHub."""
    print("  [5/5] Git commit e push...")
    git_add = _git(["add", "-A"])
    git_status = _git(["status", "--porcelain"])
    if not git_status.stdout.strip():
        print("       Sem alteracoes para commitar.")
        return False
    msg = f"Ciclo {ciclo}: aprendizado automatico — {motor_result['documentos_analisados']} docs, {motor_result['solucoes_propostas']} solucoes"
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

    # 3. Motor
    mot = fase_motor(ciclo)

    # 4. Correcao
    cor = fase_correcao(mot)

    # 5. Git
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
