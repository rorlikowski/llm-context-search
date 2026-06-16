"""
llm-context-search
~~~~~~~~~~~~~~~~~~
Fast LLM-free search-to-context engine for AI agents.
"""

from llm_context_search.config import ContextSearchConfig, FetchConfig
from llm_context_search.engine import ContextSearchEngine
from llm_context_search.models import ContextBundle, Passage, SearchResult, SourceCollection, SourceDocument

__all__ = [
    "ContextSearchEngine",
    "ContextSearchConfig",
    "FetchConfig",
    "ContextBundle",
    "SourceCollection",
    "SourceDocument",
    "Passage",
    "SearchResult",
]

try:
    from llm_context_search._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"
