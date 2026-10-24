import re


_ABBREVIATIONS = {
    r"\bprod\b": "production",
    r"\bsvc\b": "service",
    r"\berr\b": "error",
    r"\bcfg\b": "configuration",
}
_DECOMPOSITION_BOUNDARY = re.compile(
    r"\b(?:and also|also determine|also identify|also find|and what|and which|and how)\b",
    flags=re.IGNORECASE,
)


def rewrite_query(query: str) -> str:
    rewritten = re.sub(r"\s+", " ", query).strip()
    for pattern, replacement in _ABBREVIATIONS.items():
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
    return rewritten


def decompose_query(query: str) -> list[str]:
    rewritten = rewrite_query(query)
    parts = [part.strip(" ,;:") for part in _DECOMPOSITION_BOUNDARY.split(rewritten)]
    subqueries = [
        part for part in parts[1:]
        if len(part.split()) >= 3
    ]
    return [rewritten, *subqueries[:2]]
