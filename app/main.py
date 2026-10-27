"""Minimal corpus-grounded Madhwa16 API.

GitHub remains the source of truth. This first version uses lexical retrieval,
not a vector database. It only sends retrieved corpus passages to the model.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

REPO = os.getenv("MADHWA16_REPO", "balaji4aws/madhwa16-corpus")
BRANCH = os.getenv("MADHWA16_BRANCH", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
MAX_PASSAGES = int(os.getenv("MAX_PASSAGES", "5"))

app = FastAPI(
    title="Madhwa16 API",
    description="Corpus-grounded answers with source links and transcript timestamps.",
    version="0.1.0",
)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class Citation(BaseModel):
    title: str
    source_url: str
    timestamp: str
    excerpt: str
    status: str


class AskResponse(BaseModel):
    answer: str
    found_evidence: bool
    citations: list[Citation]


def fetch_text(path: str) -> str:
    url = f"{RAW_BASE}/{path}"
    with urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8")


@lru_cache(maxsize=1)
def load_corpus() -> dict[str, Any]:
    """Load the manifest and transcript records; clear cache to refresh."""
    manifest = json.loads(fetch_text("manifest.json"))
    records = []
    for talk in manifest.get("talks", []):
        metadata = json.loads(fetch_text(talk["metadata"]))
        transcript = fetch_text(talk["transcript"])
        records.append({
            "manifest": talk,
            "metadata": metadata,
            "transcript": transcript,
        })
    return {"manifest": manifest, "records": records}


def tokenize(text: str) -> set[str]:
    # Keep Unicode letters/digits so Kannada and Sanskrit tokens are retained.
    return {token.casefold() for token in re.findall(r"[^\W_]+", text, flags=re.UNICODE)
            if len(token) > 1}


def passages_for(record: dict[str, Any]) -> list[dict[str, str]]:
    """Create timestamped passages from transcript lines."""
    metadata = record["metadata"]
    manifest = record["manifest"]
    passages = []
    for line in record["transcript"].splitlines():
        match = re.match(r"^\[(\d{2}:\d{2})\]\s+(.+)$", line.strip())
        if not match:
            continue
        timestamp, text = match.groups()
        # Masked verses must never be supplied to the model as recoverable text.
        if "unverified Sanskrit verse" in text.casefold():
            continue
        if not tokenize(text):
            continue
        passages.append({
            "title": metadata.get("title") or manifest.get("title", "Untitled talk"),
            "source_url": metadata.get("source_url") or manifest.get("source_url", ""),
            "timestamp": timestamp,
            "text": text,
            "status": metadata.get("status", "unknown"),
            "slug": metadata.get("slug", manifest.get("slug", "")),
        })
    return passages


def retrieve(question: str, limit: int = MAX_PASSAGES) -> list[dict[str, str]]:
    """Small lexical baseline. Replace with hybrid/vector search only when needed."""
    query_terms = tokenize(question)
    if not query_terms:
        return []
    ranked = []
    for record in load_corpus()["records"]:
        for passage in passages_for(record):
            passage_terms = tokenize(passage["text"])
            overlap = query_terms & passage_terms
            if not overlap:
                continue
            # Conservative threshold: avoid asking the model to guess from unrelated text.
            score = len(overlap) / max(1, len(query_terms))
            if score >= 0.15:
                ranked.append((score, passage))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [passage for _, passage in ranked[:limit]]


def generate_answer(question: str, passages: list[dict[str, str]]) -> str:
    """Call OpenAI only when evidence has been retrieved."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="Install dependencies from requirements.txt") from exc

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")

    evidence = "\n\n".join(
        f"[{i}] Talk: {p['title']} | timestamp: {p['timestamp']} | "
        f"source: {p['source_url']}\nTranscript: {p['text']}"
        for i, p in enumerate(passages, start=1)
    )
    client = OpenAI()
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are Madhwa16, an assistant for Madhwa teachings. Answer using ONLY the "
            "provided corpus excerpts. Do not use outside knowledge or fill gaps. If the "
            "excerpts do not establish the answer, say: 'I cannot establish that from the "
            "current Madhwa16 corpus.' Never reconstruct masked or unverified Sanskrit. "
            "The transcript may be a machine draft, not a verbatim quotation. Clearly "
            "describe it as a draft when relevant. Cite evidence inline using [1], [2], etc. "
            "Do not invent citations."
        ),
        input=f"Question: {question}\n\nCorpus excerpts:\n{evidence}",
    )
    return response.output_text.strip()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "madhwa16-api"}


@app.get("/corpus")
def corpus_status() -> dict[str, Any]:
    try:
        corpus = load_corpus()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not load the GitHub corpus") from exc
    return {
        "corpus": corpus["manifest"].get("corpus"),
        "talk_count": len(corpus["records"]),
        "updated": corpus["manifest"].get("updated"),
        "source_of_truth": f"https://github.com/{REPO}",
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        passages = retrieve(request.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not retrieve the GitHub corpus") from exc

    if not passages:
        return AskResponse(
            answer="I cannot establish that from the current Madhwa16 corpus.",
            found_evidence=False,
            citations=[],
        )

    answer = generate_answer(request.question, passages)
    citations = [
        Citation(
            title=p["title"],
            source_url=p["source_url"],
            timestamp=p["timestamp"],
            excerpt=p["text"],
            status=p["status"],
        )
        for p in passages
    ]
    return AskResponse(answer=answer, found_evidence=True, citations=citations)
