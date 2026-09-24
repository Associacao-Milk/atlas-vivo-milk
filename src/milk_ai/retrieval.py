from __future__ import annotations

import hashlib
import math
import os
import pickle
import re
import time
import unicodedata
from collections import Counter
from typing import Callable

from .models import RetrievalHit


EmbeddingFunction = Callable[[list[str]], list[list[float]]]
TOKEN = re.compile(r"[a-z0-9]+", flags=re.IGNORECASE)


def _features(text: str) -> list[str]:
    normalised = "".join(
        char for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    )
    tokens = TOKEN.findall(normalised)
    return tokens + [f"{left} {right}" for left, right in zip(tokens, tokens[1:])]


def _normalise_sparse(vector: dict[str, float]) -> dict[str, float]:
    norm = math.sqrt(sum(value * value for value in vector.values()))
    return {key: value / norm for key, value in vector.items()} if norm else {}


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _normalise_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    low, high = min(scores), max(scores)
    if math.isclose(low, high):
        return [1.0 if high > 0 else 0.0 for _ in scores]
    return [(score - low) / (high - low) for score in scores]


def _signature(chunks: list[dict]) -> str:
    digest = hashlib.sha1()
    digest.update(str(len(chunks)).encode("utf-8"))
    for item in chunks:
        digest.update(item.get("id", "").encode("utf-8", "ignore"))
        digest.update(str(len(item.get("text", ""))).encode("utf-8"))
    return digest.hexdigest()


class HybridRetriever:
    """Pesquisa TF-IDF esparsa e embeddings, com cache em disco."""

    def __init__(
        self,
        chunks: list[dict],
        embed: EmbeddingFunction | None = None,
        max_features: int = 50_000,
        cache_dir: str | None = None,
    ):
        self.chunks = chunks
        self.embed = embed
        self.idf: dict[str, float] = {}
        self.lexical_vectors: list[dict[str, float]] = []
        self.semantic_matrix: list[list[float]] | None = None
        if not chunks:
            return

        signature = _signature(chunks)
        cache_path = None
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, f"retriever_{signature}.pkl")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "rb") as handle:
                        cached = pickle.load(handle)
                    self.idf = cached["idf"]
                    self.lexical_vectors = cached["lexical_vectors"]
                    self.semantic_matrix = cached.get("semantic_matrix")
                    print(f"[retriever] cache carregada: {len(self.chunks)} chunks")
                    return
                except Exception as error:
                    print(f"[retriever] cache invalida ({error}); a reconstruir")

        started = time.time()
        term_counts = [Counter(_features(item["text"])) for item in chunks]
        document_frequency: Counter[str] = Counter()
        for counts in term_counts:
            document_frequency.update(counts.keys())
        selected = {
            term for term, _frequency in document_frequency.most_common(max_features)
        }
        total = len(chunks)
        self.idf = {
            term: math.log((1 + total) / (1 + document_frequency[term])) + 1.0
            for term in selected
        }
        total_chunks = len(chunks)
        for index, counts in enumerate(term_counts):
            self.lexical_vectors.append(self._vectorise_counts(counts))
            if (index + 1) % 5000 == 0:
                elapsed = time.time() - started
                print(f"[retriever] indice lexical: {index + 1}/{total_chunks} chunks ({elapsed:.0f}s)")
        if embed:
            print(f"[retriever] a calcular embeddings para {total_chunks} chunks...")
            vectors = embed([item["text"] for item in chunks])
            if len(vectors) != len(chunks):
                raise ValueError("o servico de embeddings devolveu uma contagem invalida")
            self.semantic_matrix = [[float(value) for value in vector] for vector in vectors]
        if cache_path:
            try:
                with open(cache_path, "wb") as handle:
                    pickle.dump(
                        {
                            "idf": self.idf,
                            "lexical_vectors": self.lexical_vectors,
                            "semantic_matrix": self.semantic_matrix,
                        },
                        handle,
                        protocol=pickle.HIGHEST_PROTOCOL,
                    )
                print(f"[retriever] cache guardada ({time.time() - started:.0f}s)")
            except Exception as error:
                print(f"[retriever] nao foi possivel guardar a cache: {error}")

    def _vectorise_counts(self, counts: Counter[str]) -> dict[str, float]:
        weighted = {
            term: (1.0 + math.log(count)) * self.idf[term]
            for term, count in counts.items()
            if term in self.idf and count > 0
        }
        return _normalise_sparse(weighted)

    def _lexical_scores(self, query: str) -> list[float]:
        query_vector = self._vectorise_counts(Counter(_features(query)))
        return [
            sum(weight * document.get(term, 0.0) for term, weight in query_vector.items())
            for document in self.lexical_vectors
        ]

    def search(self, query: str, limit: int = 5, visibility: set[str] | None = None) -> list[RetrievalHit]:
        if not self.chunks or not query.strip() or not self.idf or limit <= 0:
            return []
        lexical = self._lexical_scores(query)
        semantic: list[float] | None = None
        if self.embed and self.semantic_matrix is not None:
            query_vectors = self.embed([query])
            if len(query_vectors) != 1:
                raise ValueError("o servico de embeddings nao devolveu a pergunta")
            semantic = [_cosine(query_vectors[0], vector) for vector in self.semantic_matrix]
        lexical_n = _normalise_scores(lexical)
        semantic_n = _normalise_scores(semantic) if semantic is not None else None
        combined = lexical_n if semantic_n is None else [
            0.45 * lexical_score + 0.55 * semantic_score
            for lexical_score, semantic_score in zip(lexical_n, semantic_n)
        ]
        allowed = [
            not visibility or item.get("metadata", {}).get("visibility") in visibility
            for item in self.chunks
        ]
        order = sorted(
            range(len(self.chunks)),
            key=lambda position: combined[position] * (1.0 if allowed[position] else 0.0),
            reverse=True,
        )
        return [
            RetrievalHit(
                chunk_id=self.chunks[position].get('chunk_id', ''),
                source_id=self.chunks[position].get('source_id', ''),
                score=combined[position],
                lexical_score=lexical_n[position],
                semantic_score=semantic_n[position] if semantic_n is not None else None,
                text=self.chunks[position].get('text', ''),
                metadata=self.chunks[position].get('metadata', {}),
            )
            for position in order[:limit]
            if combined[position] > 0.0
        ]

