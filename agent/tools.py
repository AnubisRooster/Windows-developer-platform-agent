"""Agent tools - summarization and helpers."""


def summarize(content: str, max_length: int = 200) -> str:
    """Summarize text content."""
    if not content or not content.strip():
        return ""
    text = content.strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rsplit(maxsplit=1)[0] + "..."
