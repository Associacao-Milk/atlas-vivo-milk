"""Mock server do Atlas Vivo MILK — serve o frontend estático e responde
às APIs com dados de exemplo, para visualização local no navegador.
Sem backend, sem PostgreSQL. Só para ver o aspeto antes do deploy.

Uso:  python preview_atlas.py  ->  abrir http://127.0.0.1:8070
Parar: Ctrl+C
"""
from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "frontend"

# ---- Dados mock (freguesias piloto + histórias de exemplo) ----
FREGUESIAS = [
    {"codigo_dgal": "030219", "nome": "Barcelos", "municipio": "Barcelos", "distrito": "Braga", "regiao": "Continente", "ccdr": "CCDR-N", "geom_centro": {"lat": 41.5287, "lng": -8.6145}},
    {"codigo_dgal": "070505", "nome": "Évora (Sé e São Pedro)", "municipio": "Évora", "distrito": "Évora", "regiao": "Continente", "ccdr": "CCDR-A", "geom_centro": {"lat": 38.5667, "lng": -7.9000}},
    {"codigo_dgal": "130806", "nome": "Matosinhos", "municipio": "Matosinhos", "distrito": "Porto", "regiao": "Continente", "ccdr": "CCDR-N", "geom_centro": {"lat": 41.1797, "lng": -8.6896}},
    {"codigo_dgal": "030237", "nome": "Arcozelo", "municipio": "Barcelos", "distrito": "Braga", "regiao": "Continente", "ccdr": "CCDR-N", "geom_centro": {"lat": 41.5763, "lng": -8.7150}},
    {"codigo_dgal": "070514", "nome": "Nossa Senhora da Tourega", "municipio": "Évora", "distrito": "Évora", "regiao": "Continente", "ccdr": "CCDR-A", "geom_centro": {"lat": 38.5342, "lng": -7.9300}},
    {"codigo_dgal": "130812", "nome": "Leça da Palmeira", "municipio": "Matosinhos", "distrito": "Porto", "regiao": "Continente", "ccdr": "CCDR-N", "geom_centro": {"lat": 41.1980, "lng": -8.6900}},
]

HISTORIAS = [
    {"id": "h1", "titulo": "A Moura Encantada da Fonte da Sabugueiro", "resumo": "Diz-se que na noite de São João uma moura de branco surge junto à fonte, a pentear os longos cabelos com um pente de ouro.", "tipo": "lenda", "freguesia_nome": "Arcozelo", "lat": 41.5763, "lng": -8.7150, "anonimato": "completo", "nome_submissor": None, "corpo": "A lenda remonta ao tempo dos mouros...", "cert_hash": "a1b2c3d4e5f6", "published_at": "2026-08-12T10:00:00Z"},
    {"id": "h2", "titulo": "O forno comunitário de Nossa Senhora da Tourega", "resumo": "O forno comunitário ainda se acende uma vez por ano, na festa da padroeira, com lenha trazida por cada casa.", "tipo": "oficio", "freguesia_nome": "Nossa Senhora da Tourega", "lat": 38.5342, "lng": -7.9300, "anonimato": "primeiro-nome", "nome_submissor": "Maria", "corpo": "Tradição mantida há gerações...", "cert_hash": "f7e8d9c0b1a2", "published_at": "2026-08-20T15:30:00Z"},
    {"id": "h3", "titulo": "A romaria de São Pedro em Matosinhos", "resumo": "Procissão que percorre as ruas até ao mar, com os pescadores a levar os santos aos ombros.", "tipo": "memoria", "freguesia_nome": "Leça da Palmeira", "lat": 41.1980, "lng": -8.6900, "anonimato": "nome-completo", "nome_submissor": "José Silva", "corpo": "Lembro-me de pequeno...", "cert_hash": "9z8y7x6w5v4u", "published_at": "2026-09-01T09:15:00Z"},
    {"id": "h4", "titulo": "O careto que assombrava o adro", "resumo": "Nas noites de Inverno um careto de máscara estremeçava os que passavam pelo adro da igreja.", "tipo": "curiosidade", "freguesia_nome": "Barcelos", "lat": 41.5287, "lng": -8.6145, "anonimato": "completo", "nome_submissor": None, "corpo": "Mistura de medo e fascínio...", "cert_hash": "q1w2e3r4t5y6", "published_at": "2026-09-05T18:00:00Z"},
    {"id": "h5", "titulo": "A transformação da antiga fábrica de conservas", "resumo": "O que foi fábrica de conservas é hoje centro cultural, mas conserva o cheiro a mar nos muros.", "tipo": "transformacao", "freguesia_nome": "Matosinhos", "lat": 41.1797, "lng": -8.6896, "anonimato": "pseudonimo", "nome_submissor": "filha-do-mar", "corpo": "A adaptação respeitou a memória...", "cert_hash": "m7n8o9p0q1r2", "published_at": "2026-09-04T12:00:00Z"},
]

USERS = [
    {"nome": "Maria", "pontos": 320, "nivel": 3, "badges": ["historiador"], "historias_submetidas": 7, "historias_validadas": 2, "ccdr": "CCDR-N"},
    {"nome": "José Silva", "pontos": 1050, "nivel": 5, "badges": ["historiador", "guardiao"], "historias_submetidas": 12, "historias_validadas": 1, "ccdr": "CCDR-N"},
    {"nome": "filha-do-mar", "pontos": 180, "nivel": 2, "badges": [], "historias_submetidas": 4, "historias_validadas": 0, "ccdr": "CCDR-N"},
]


class MockHandler(BaseHTTPRequestHandler):
    server_version = "AtlasMock/1.0"

    def log_message(self, *a): pass

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_error(404, "não encontrado")
            return
        mime, _ = mimetypes.guess_type(str(path))
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        params = {}
        if "?" in self.path:
            for pair in self.path.split("?", 1)[1].split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k] = v

        # ---- APIs mock ----
        if route == "/api/health":
            return self._json({"status": "ok", "db": "mock"})
        if route == "/api/map/stats":
            return self._json({"total": len(HISTORIAS), "publicadas": len(HISTORIAS), "por_tipo": [{"tipo": h["tipo"], "n": 1} for h in HISTORIAS]})
        if route == "/api/map/historias":
            feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [h["lng"], h["lat"]]}, "properties": {k: h.get(k) for k in ("id", "titulo", "resumo", "tipo", "freguesia_nome", "anonimato", "nome_submissor")}} for h in HISTORIAS if h.get("lat")]
            return self._json({"type": "FeatureCollection", "features": feats})
        if route == "/api/map/freguesias":
            feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [f["geom_centro"]["lng"], f["geom_centro"]["lat"]]}, "properties": {"codigo": f["codigo_dgal"], "nome": f["nome"], "municipio": f["municipio"], "distrito": f["distrito"]}} for f in FREGUESIAS]
            return self._json({"type": "FeatureCollection", "features": feats})
        if route == "/api/freguesias":
            q = params.get("q", "").lower()
            res = [f for f in FREGUESIAS if q in f["nome"].lower() or q in f["municipio"].lower()] if q else FREGUESIAS
            return self._json({"freguesias": res[:20]})
        if route == "/api/freguesias/municipios":
            return self._json({"municipios": [{"municipio": f["municipio"], "distrito": f["distrito"]} for f in FREGUESIAS]})
        if route == "/api/historias":
            return self._json({"historias": HISTORIAS})
        if route.startswith("/api/historias/"):
            hid = route.split("/")[-1]
            h = next((x for x in HISTORIAS if x["id"] == hid), None)
            return self._json(h) if h else self._json({"erro": "não encontrada"}, 404)
        if route == "/api/gamificacao/leaderboard":
            ccdr = params.get("ccdr")
            board = [u for u in USERS if not ccdr or u["ccdr"] == ccdr]
            return self._json({"leaderboard": board})
        if route == "/api/gamificacao/perfil":
            email = params.get("email", "").lower()
            if not email:
                return self._json({"erro": "email obrigatório"}, 400)
            return self._json(USERS[0])
        if route == "/api/connectors":
            return self._json({"total": 21, "sources": [{"id": "dgal", "name": "DGAL", "url": "https://www.portalautarquico.dgal.gov.pt", "category": "autarquias", "auth": "none", "response_format": "json", "rate_limit": None}]})

        # ---- Ficheiros estáticos do frontend ----
        if route == "/":
            return self._static(ROOT / "index.html")
        if route == "/manifest.json":
            return self._static(ROOT / "manifest.json")
        if route.startswith("/css/"):
            return self._static(ROOT / "css" / route.split("/")[-1])
        if route.startswith("/js/"):
            return self._static(ROOT / "js" / route.split("/")[-1])
        self._json({"erro": "endpoint desconhecido"}, 404)

    def do_POST(self):
        route = self.path.split("?", 1)[0]
        if route == "/submit-historia":
            return self._json({"status": "submetida", "id": "mock-0001", "cert_token": "eyJhbGciOiJIUzI1NiJ9.mock", "cert_hash": "mock-sha256-0000000000000000", "mensagem": "[MOCK] História recebida. Em produção iria para curadoria."}, 201)
        if route == "/api/gamificacao/registar":
            return self._json({"status": "ok"})
        self._json({"erro": "endpoint desconhecido"}, 404)


def main():
    port = 8070
    srv = ThreadingHTTPServer(("127.0.0.1", port), MockHandler)
    print(f"Atlas Vivo MILK — PREVIEW MOCK (sem backend)")
    print(f"Abrir no navegador:  http://127.0.0.1:{port}")
    print(f"Parar: Ctrl+C")
    print(f"Frontend servido de: {ROOT}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nA parar...")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
