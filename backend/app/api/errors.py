from google.genai import errors as genai_errors

QUOTA_MESSAGE = "AI quota reached. Try again in a minute."


def is_quota_error(exc: BaseException | None) -> bool:
    """Walk an exception's cause and context chain to detect Gemini API 429 quota exhaustion."""
    if exc is None:
        return False

    seen: set[int] = set()
    to_visit: list[BaseException] = [exc]

    while to_visit:
        curr = to_visit.pop(0)
        if id(curr) in seen:
            continue
        seen.add(id(curr))

        if isinstance(curr, genai_errors.APIError) and getattr(curr, "code", None) == 429:
            return True

        if curr.__cause__ is not None and id(curr.__cause__) not in seen:
            to_visit.append(curr.__cause__)
        if curr.__context__ is not None and id(curr.__context__) not in seen:
            to_visit.append(curr.__context__)

    return False
