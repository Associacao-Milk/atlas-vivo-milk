from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


class ConnectorError(RuntimeError):
    pass


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[str, str]
    body: Any


class SafeHttpClient:
    def __init__(self, allowed_hosts: set[str], timeout: int = 30, retries: int = 3):
        self.allowed_hosts = {h.lower() for h in allowed_hosts}
        self.timeout = timeout
        self.retries = retries

    def request(self, method: str, url: str, *, params: dict[str, Any] | None = None,
                json_body: Any = None, headers: dict[str, str] | None = None) -> Response:
        parsed = urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in self.allowed_hosts:
            raise ConnectorError(f"destino não autorizado: {parsed.scheme}://{parsed.hostname}")
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        body = None if json_body is None else json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        req_headers = {"Accept": "application/json", "User-Agent": "atlas-vivo-milk/1.0"}
        req_headers.update(headers or {})
        if body is not None:
            req_headers["Content-Type"] = "application/json"
        req = Request(url, data=body, headers=req_headers, method=method.upper())
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                with urlopen(req, timeout=self.timeout) as res:
                    raw = res.read()
                    try:
                        parsed_body = json.loads(raw.decode("utf-8")) if raw else None
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        parsed_body = raw.decode("utf-8", errors="replace")
                    return Response(res.status, dict(res.headers), parsed_body)
            except HTTPError as exc:
                raw = exc.read().decode("utf-8", errors="replace")
                if exc.code not in (429, 500, 502, 503, 504) or attempt + 1 == self.retries:
                    raise ConnectorError(f"HTTP {exc.code}: {raw[:500]}") from exc
                last = exc
            except URLError as exc:
                last = exc
                if attempt + 1 == self.retries:
                    break
            time.sleep(2 ** attempt)
        raise ConnectorError(f"falha de ligação após {self.retries} tentativas: {last}")

