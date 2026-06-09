from __future__ import annotations

from pydantic import BaseModel, Field


class FetchConfig(BaseModel):
    connect_timeout_seconds: float = 3.0
    read_timeout_seconds: float = 6.0
    max_bytes: int = 1_000_000
    max_redirects: int = 3
    concurrency: int = 5
    user_agent: str = "llm-context-search/0.1"
    block_private_ips: bool = True


class ContextSearchConfig(BaseModel):
    max_results: int = Field(default=10, ge=1, le=50)
    max_sources: int = Field(default=5, ge=1, le=20)
    max_passages: int = Field(default=12, ge=1, le=100)
    budget_tokens: int = Field(default=4000, ge=500, le=100_000)

    searxng_timeout_seconds: float = Field(default=5.0, gt=0)
    fetch_connect_timeout_seconds: float = Field(default=3.0, gt=0)
    fetch_timeout_seconds: float = Field(default=6.0, gt=0)
    max_fetch_bytes: int = Field(default=1_000_000, gt=0)
    max_redirects: int = Field(default=3, ge=0, le=10)
    fetch_concurrency: int = Field(default=5, ge=1, le=20)

    user_agent: str = "llm-context-search/0.1"
    block_private_ips: bool = True
    allow_http: bool = True
    allow_https: bool = True

    chunk_target_chars: int = Field(default=1200, ge=300, le=5000)
    chunk_max_chars: int = Field(default=2000, ge=500, le=8000)
    chunk_overlap_chars: int = Field(default=150, ge=0, le=1000)

    search_cache_ttl_seconds: float = Field(default=300.0, ge=0)
    fetch_cache_ttl_seconds: float = Field(default=300.0, ge=0)

    def to_fetch_config(self) -> FetchConfig:
        return FetchConfig(
            connect_timeout_seconds=self.fetch_connect_timeout_seconds,
            read_timeout_seconds=self.fetch_timeout_seconds,
            max_bytes=self.max_fetch_bytes,
            max_redirects=self.max_redirects,
            concurrency=self.fetch_concurrency,
            user_agent=self.user_agent,
            block_private_ips=self.block_private_ips,
        )
