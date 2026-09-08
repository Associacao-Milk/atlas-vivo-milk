#!/usr/bin/env python3
"""Melhoria da classificacao territorial — usa original_path + texto + nome.
Tambem detecta territorios por padroes no caminho do ficheiro."""
import json, re, os, sys, datetime
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CORPUS = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO\corpus\documents")

DISTRITOS = {"Aveiro","Beja","Braga","Braganca","Castelo Branco","Coimbra","Evora",
    "Faro","Guarda","Leiria","Lisboa","Portalegre","Porto","Santarem","Setubal",
    "Viana do Castelo","Vila Real","Viseu","Ponta Delgada","Angra do Heroismo","Horta","Funchal"}

MUNICIPIOS = {"Lisboa","Sintra","Cascais","Loures","Amadora","Oeiras","Vila Franca de Xira",
    "Mafra","Porto","Vila Nova de Gaia","Matosinhos","Gondomar","Maia","Valongo","Paredes",
    "Santo Tirso","Trofa","Felgueiras","Lousada","Pacos de Ferreira","Penafiel","Braga",
    "Guimaraes","Barcelos","Vila Nova de Famalicao","Esposende","Vieira do Minho","Fafe",
    "Amares","Aveiro","Ovar","Espinho","Santa Maria da Feira","Oliveira de Azemeis",
    "Ilhavo","Anadia","Estarreja","Albergaria-a-Velha","Sao Joao da Madeira","Coimbra",
    "Figueira da Foz","Cantanhede","Pombal","Lousa","Mealhada","Setubal","Almada","Seixal",
    "Barreiro","Montijo","Sesimbra","Palmela","Sines","Santiago do Cacem","Alcacer do Sal",
    "Faro","Loule","Albufeira","Portimao","Lagos","Tavira","Olhao","Silves","Lagoa",
    "Leiria","Caldas da Rainha","Alcobaca","Nazare","Peniche","Marinha Grande","Batalha",
    "Santarem","Tomar","Abrantes","Torres Novas","Almeirim","Coruche","Cartaxo",
    "Viseu","Lamego","Mangualde","Seia","Gouveia","Tondela","Guarda","Covilha","Sabugal",
    "Beja","Serpa","Moura","Odemira","Evora","Estremoz","Elvas","Montemor-o-Novo",
    "Portalegre","Ponte de Sor","Castelo Branco","Fundao","Braganca","Mirandela",
    "Macedo de Cavaleiros","Viana do Castelo","Valenca","Ponte de Lima","Caminha",
    "Arcos de Valdevez","Vila Real","Chaves","Peso da Regua","Funchal","Santa Cruz",
    "Ponta Delgada","Ribeira Grande","Horta","Angra do Heroismo","Grandola","Sertã",
    "Proenca-a-Nova","Oleiros","Vila de Rei","Vila Velha de Rodao","Miranda do Douro",
    "Vinhais","Mogadouro","Carrazeda de Ansiaes","Freixo de Espada a Cinta",
    "Melgaco","Moncao","Ribeira de Pena","Sabrosa","Alijo","Murca","Mesao Frio",
    "Santa Marta de Penaguiao","Vila do Bispo","Aljezur","Monchique","Castro Marim",
    "Vila Real de Santo Antonio","Sao Bras de Alportel","Vila Vicosa","Redondo",
    "Reguengos de Monsaraz","Arraiolos","Alandroal","Portel","Mora","Campo Maior",
    "Marvao","Arronches","Alter do Chao","Avis","Crato","Gaviao","Nisa","Castelo de Vide",
    "Penamacor","Idanha-a-Nova","Celorico da Beira","Fornos de Algodres","Manteigas",
    "Pinhel","Trancoso","Figueira de Castelo Rodrigo","Almeida","Castro Verde",
    "Almodovar","Vidigueira","Cuba","Ferreira do Alentejo","Mertola","Montemor-o-Velho",
    "Penacova","Soure","Arganil","Miranda do Corvo","Condeixa-a-Nova","Oliveira do Bairro",
    "Murtosa","Vagos","Arouca","Vale de Cambra","Sever do Vouga","Alcochete","Moita",
    "Ourém","Ferreira do Zezere","Entroncamento","Almeirim","Vila Nova de Cerveira"}

# Freguesias — lista expandida
FREGUESIAS = {"Alfama","Bairro Alto","Belem","Lumiar","Carnide","Olivais","Marvila",
    "Alvalade","Areeiro","Arroios","Campolide","Estrela","Ajuda","Benfica",
    "Santa Maria dos Olivais","Cedofeita","Bonfim","Paranhos","Campanha",
    "Lordelo do Ouro","Massarelos","Ramalde","Aldoar","Foz do Douro","Nevogilde",
    "Sao Vicente","Sao Joao do Souto","Maximinos","Real","Gualtar","Nogueira",
    "Sao Pedro","Sao Sebastiao","Nossa Senhora da Assuncao","Santa Maria",
    "Sao Joao","Sao Paulo","Sao Jorge","Trindade","Sao Mamede","Sao Lazaro",
    "Sao Jose","Encarnacao","Mercês","Pena","Anjos","Santiago","Castelo",
    "Sao Miguel","Santo Estevao","Sao Nicolau","Madalena","Santa Justa",
    "Sé","Lapa","Santos-o-Velho","Prazeres","Santa Catarina","Penha de Franca",
    "Graça","Anjos","Sao Jorge de Arroios"}

DIST_RE = re.compile(r'\b(' + '|'.join(re.escape(d) for d in sorted(DISTRITOS, key=len, reverse=True)) + r')\b', re.IGNORECASE)
MUN_RE = re.compile(r'\b(' + '|'.join(re.escape(m) for m in sorted(MUNICIPIOS, key=len, reverse=True)) + r')\b', re.IGNORECASE)
FREG_RE = re.compile(r'\b(' + '|'.join(re.escape(f) for f in sorted(FREGUESIAS, key=len, reverse=True)) + r')\b', re.IGNORECASE)

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
    nome = md.get("original_name", "") or ""
    caminho = md.get("original_path", "") or ""
    texto = rec.get("text", "") or ""

    # Combinar todas as fontes de deteccao
    combined = f"{nome} {caminho} {texto[:8000]}".lower()

    alterado = False

    # Distrito
    if not md.get("district"):
        m = DIST_RE.search(combined)
        if m:
            md["district"] = m.group(1).title()
            alterado = True
            stats["novo_distrito"] += 1

    # Municipio
    if not md.get("municipality"):
        m = MUN_RE.search(combined)
        if m:
            md["municipality"] = m.group(1).title()
            alterado = True
            stats["novo_municipio"] += 1

    # Freguesia
    if not md.get("parish"):
        m = FREG_RE.search(combined)
        if m:
            md["parish"] = m.group(1).title()
            alterado = True
            stats["novo_freguesia"] += 1

    # Territory
    if md.get("district") or md.get("municipality"):
        if not md.get("territory"):
            parts = [x for x in [md.get("district"), md.get("municipality"), md.get("parish")] if x]
            md["territory"] = " > ".join(parts)
            alterado = True

    if alterado:
        rec["metadata"] = md
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, separators=(",", ":"))
        novos += 1

dur = (datetime.datetime.now() - t0).total_seconds()
print(f"Melhoria territorial concluida — {dur:.1f}s")
print(f"  Novos distritos:    {stats['novo_distrito']}")
print(f"  Novos municipios:   {stats['novo_municipio']}")
print(f"  Novos freguesias:   {stats['novo_freguesia']}")
print(f"  Documentos alterados: {novos}")
