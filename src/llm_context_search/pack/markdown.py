from __future__ import annotations

from collections import defaultdict

from llm_context_search.models import Passage


def _render_markdown(passages: list[Passage]) -> str:
    """
    Render selected passages grouped by source into Markdown:

    # Source N: <title>
    URL: <url>
    Score: <quality>

    ## Passage N
    <text>

    ---
    """
    by_source: dict[str, list[Passage]] = defaultdict(list)
    source_order: list[str] = []

    for passage in passages:
        if passage.source_url not in by_source:
            source_order.append(passage.source_url)
        by_source[passage.source_url].append(passage)

    sections: list[str] = []
    for source_idx, url in enumerate(source_order, start=1):
        source_passages = by_source[url]
        first = source_passages[0]

        header = (
            f"# Source {source_idx}: {first.source_title}\n"
            f"URL: {url}\n"
            f"Score: {first.source_quality_score:.2f}"
        )
        passage_blocks = []
        for p_idx, passage in enumerate(source_passages, start=1):
            passage_blocks.append(f"## Passage {p_idx}\n{passage.text}")

        sections.append(header + "\n\n" + "\n\n".join(passage_blocks))

    return "\n\n---\n\n".join(sections)


class MarkdownPacker:
    """
    Selects top passages that fit within budget_tokens and max_passages,
    then renders them as Markdown context.
    """

    def pack(self, passages: list[Passage], budget_tokens: int, max_passages: int) -> tuple[str, list[Passage]]:
        sorted_passages = sorted(passages, key=lambda p: p.final_score, reverse=True)

        selected: list[Passage] = []
        total_tokens = 0

        for passage in sorted_passages:
            if len(selected) >= max_passages:
                break
            fits = total_tokens + passage.token_estimate <= budget_tokens
            # Always include the top passage even if it exceeds the budget —
            # an empty context is never useful.
            is_first = len(selected) == 0
            if fits or is_first:
                selected.append(passage)
                total_tokens += passage.token_estimate

        context_text = _render_markdown(selected) if selected else ""
        return context_text, selected
