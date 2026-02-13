"""Free web search via DuckDuckGo + optional Groq summarisation."""

from __future__ import annotations
import os
import json
from typing import List, Optional

from ddgs import DDGS


class WebSearchService:
    """Searches the web for a query and optionally summarises the snippets
    into study-note-friendly markdown using the Groq LLM."""

    def __init__(self, groq_client=None):
        self.groq_client = groq_client

    # ── public API ───────────────────────────────────────────

    def search(self, query: str, max_results: int = 6) -> List[dict]:
        """Return a list of {title, url, snippet} dicts from DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                }
                for r in results
            ]
        except Exception as e:
            print(f"WebSearchService: Search error – {e}")
            return []

    def search_and_summarise(
        self,
        concept: str,
        context_hint: str = "",
        max_results: int = 6,
    ) -> dict:
        """Search the web for *concept*, then use the LLM to turn the
        snippets into concise, study-friendly markdown notes.

        Returns ``{"concept", "search_results", "summary"}``.
        """
        results = self.search(f"{concept} {context_hint}".strip(), max_results)

        if not results:
            return {
                "concept": concept,
                "search_results": [],
                "summary": f"No web results found for **{concept}**.",
            }

        summary = self._summarise(concept, results) if self.groq_client else self._plain_summary(concept, results)

        return {
            "concept": concept,
            "search_results": results,
            "summary": summary,
        }

    # ── internal helpers ─────────────────────────────────────

    def _summarise(self, concept: str, results: list) -> str:
        """Use Groq to produce markdown study notes from search snippets."""
        from agents.base_agent import rate_limit_retry

        snippets_text = "\n\n".join(
            f"**{r['title']}**\n{r['snippet']}\nSource: {r['url']}"
            for r in results
        )

        try:
            completion = rate_limit_retry(
                self.groq_client,
                dict(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a study-notes assistant. "
                                "Given web search snippets about a concept, produce concise, "
                                "well-structured Markdown notes the student can paste into "
                                "their existing notes. "
                                "Include key definitions, important points, and cite sources "
                                "as inline links. Keep it under 600 words."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Concept: **{concept}**\n\n"
                                f"Web search results:\n\n{snippets_text}\n\n"
                                "Produce study notes in Markdown."
                            ),
                        },
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.4,
                    max_tokens=1500,
                ),
                agent_name="WebSearch",
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"WebSearchService: Summarise error – {e}")
            return self._plain_summary(concept, results)

    def search_images(
        self,
        query: str,
        max_results: int = 12,
    ) -> List[dict]:
        """Search for images related to *query* using DuckDuckGo image search.

        Returns a list of ``{title, image_url, thumbnail, source, width, height}``.
        """
        try:
            with DDGS() as ddgs:
                raw = list(
                    ddgs.images(
                        f"{query} diagram",
                        max_results=max_results,
                    )
                )
            return [
                {
                    "title": r.get("title", ""),
                    "image_url": r.get("image", ""),
                    "thumbnail": r.get("thumbnail", ""),
                    "source": r.get("url", r.get("source", "")),
                    "width": r.get("width", 0),
                    "height": r.get("height", 0),
                }
                for r in raw
                if r.get("image")
            ]
        except Exception as e:
            print(f"WebSearchService: Image search error – {e}")
            return []

    @staticmethod
    def _plain_summary(concept: str, results: list) -> str:
        """Fallback when no LLM is available."""
        lines = [f"## Web Results for *{concept}*\n"]
        for r in results:
            lines.append(f"### [{r['title']}]({r['url']})\n{r['snippet']}\n")
        return "\n".join(lines)
