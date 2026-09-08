#!/usr/bin/env python3
"""Reportar documento em falta — cria issue no GitHub automaticamente.
O utilizador so precisa de escrever o nome do ficheiro e o caminho.
"""
import sys, subprocess, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO = "milkivc/atlas-vivo-milk"
GH = r"C:\Program Files\GitHub CLI\gh.exe"

def criar_issue(titulo, labels, body):
    cmd = [GH, "issue", "create", "--repo", REPO, "--title", titulo, "--label", labels, "--body", body]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip() or result.stderr.strip()

def main():
    print("=" * 50)
    print("REPORTAR DOCUMENTO EM FALTA")
    print("=" * 50)
    nome = input("Nome do ficheiro (ou ENTER para saltar): ").strip()
    caminho = input("Caminho original (ou ENTER): ").strip()
    fonte = input("Fonte (OneDrive/Nextcloud/Downloads/Outra): ").strip()
    contexto = input("Porque e importante? (ou ENTER): ").strip()

    body = f"""## Documento em falta

**Nome do ficheiro:** {nome or '(nao especificado)'}
**Caminho original:** {caminho or '(nao especificado)'}
**Fonte:** {fonte or '(nao especificada)'}

## Contexto
{contexto or '(sem contexto adicional)'}

---
Issue criada automaticamente por reportar_falta.py
"""
    titulo = f"[DOC-FALTA] {nome or caminho or 'Documento sem nome'}"[:80]
    url = criar_issue(titulo, "documento,ingestao", body)
    print(f"\nIssue criado: {url}")

if __name__ == "__main__":
    main()
