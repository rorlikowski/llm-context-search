from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str
    url: str
    normalized_url: str | None = None
    snippet: str | None = None
    provider: str
    rank: int | None = None
    raw_score: float | None = None


class ExtractedContent(BaseModel):
    title: str | None = None
    text: str | None = None
    author: str | None = None
    date: str | None = None
    language: str | None = None
    description: str | None = None


class SourceDocument(BaseModel):
    title: str
    url: str
    normalized_url: str
    snippet: str | None = None
    provider: str

    fetch_status: Literal["ok", "failed", "skipped"]
    extraction_status: Literal["ok", "failed", "empty", "skipped"]

    extracted_text: str | None = None
    extracted_chars: int = 0
    token_estimate: int = 0

    content_hash: str | None = None
    quality_score: float = Field(default=0.0, ge=0, le=1)

    error: str | None = None


class Passage(BaseModel):
    id: str
    source_url: str
    source_title: str
    text: str
    position: int

    char_count: int
    token_estimate: int

    lexical_score: float = Field(default=0.0, ge=0, le=1)
    source_quality_score: float = Field(default=0.0, ge=0, le=1)
    final_score: float = Field(default=0.0, ge=0, le=1)


class RetrievalStats(BaseModel):
    search_results_count: int = 0
    unique_urls_count: int = 0
    skipped_duplicate_urls_count: int = 0

    fetched_count: int = 0
    failed_fetch_count: int = 0

    extracted_count: int = 0
    failed_extraction_count: int = 0
    empty_extraction_count: int = 0

    passages_count: int = 0
    selected_passages_count: int = 0

    token_estimate: int = 0
    elapsed_ms: int = 0


class SourceCollection(BaseModel):
    query: str
    sources: list[SourceDocument]
    stats: RetrievalStats


class ContextBundle(BaseModel):
    query: str
    sources: list[SourceDocument]
    passages: list[Passage]
    selected_passages: list[Passage]
    context_text: str
    token_estimate: int
    stats: RetrievalStats
