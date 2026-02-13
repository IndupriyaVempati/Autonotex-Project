from abc import ABC, abstractmethod
import json
import time
import re


# Models ordered by preference; smaller ones are tried when the primary is rate-limited.
PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODELS = [
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
]


class _SyntheticMessage:
    """Minimal stand-in for a ChatCompletionMessage when we repair JSON ourselves."""
    def __init__(self, content: str):
        self.content = content
        self.role = "assistant"


class _SyntheticChoice:
    def __init__(self, content: str):
        self.message = _SyntheticMessage(content)
        self.index = 0
        self.finish_reason = "stop"


class _SyntheticCompletion:
    """Returned when we recover usable JSON from a failed_generation error."""
    def __init__(self, content: str):
        self.choices = [_SyntheticChoice(content)]
        self.id = "repaired"
        self.model = "repaired"


def rate_limit_retry(groq_client, create_kwargs, max_retries=3, agent_name="Agent"):
    """Call groq_client.chat.completions.create with automatic retry + model fallback.

    On 429 (RateLimitError) the helper:
      1. Extracts the suggested wait time from the error message.
      2. Waits with exponential back-off (clamped to 120 s).
      3. After exhausting retries on the primary model, tries FALLBACK_MODELS.

    On 400 json_validate_failed the helper:
      - Extracts the ``failed_generation`` text, attempts to repair it,
        and returns a synthetic completion so callers don't crash.
      - If repair fails, retries without ``response_format`` so the model
        returns free-form text the caller can parse.

    Returns the ChatCompletion on success, or raises the last exception.
    """
    models_to_try = [create_kwargs.get("model", PRIMARY_MODEL)] + FALLBACK_MODELS

    last_exc = None
    for model in models_to_try:
        kwargs = {**create_kwargs, "model": model}
        for attempt in range(1, max_retries + 1):
            try:
                result = groq_client.chat.completions.create(**kwargs)
                if model != models_to_try[0]:
                    print(f"{agent_name}: Succeeded with fallback model '{model}' on attempt {attempt}")
                return result
            except Exception as e:
                last_exc = e
                err_str = str(e)

                # ── Handle json_validate_failed (400) ──
                if "json_validate_failed" in err_str or "failed_generation" in err_str:
                    repaired = _try_repair_failed_json(err_str, agent_name)
                    if repaired is not None:
                        return repaired
                    # Retry once without response_format constraint
                    if "response_format" in kwargs:
                        print(f"{agent_name}: Retrying without response_format on '{model}'")
                        kwargs_no_fmt = {k: v for k, v in kwargs.items() if k != "response_format"}
                        try:
                            result = groq_client.chat.completions.create(**kwargs_no_fmt)
                            return result
                        except Exception:
                            pass  # fall through to next model
                    break  # move to next model

                # ── Handle rate-limit (429) ──
                is_rate_limit = "429" in err_str or "rate_limit" in err_str.lower()
                if not is_rate_limit:
                    raise  # non-rate-limit errors should propagate immediately

                wait = _parse_wait_seconds(err_str, default=min(10 * attempt, 120))
                # On free tier daily limit, skip waiting and try fallback model instead
                if "tokens per day" in err_str.lower() or "TPD" in err_str:
                    print(f"{agent_name}: Daily token limit hit on '{model}', switching to fallback model")
                    break  # move to next model immediately
                print(f"{agent_name}: Rate limited on '{model}' (attempt {attempt}/{max_retries}), "
                      f"waiting {wait:.0f}s …")
                time.sleep(wait)
        # If all retries for this model exhausted, try next model
        print(f"{agent_name}: All retries exhausted for model '{model}', trying next fallback …")

    # Everything failed
    print(f"{agent_name}: All models and retries exhausted")
    raise last_exc


# ── JSON repair helpers ──────────────────────────────────────────────

def _try_repair_failed_json(error_str: str, agent_name: str):
    """Extract ``failed_generation`` from a Groq 400 error and try to fix it.

    Returns a _SyntheticCompletion on success, or None.
    """
    # Pull the raw failed text from the error dict
    raw = _extract_failed_generation(error_str)
    if not raw:
        return None

    repaired = _repair_json(raw)
    if repaired is not None:
        print(f"{agent_name}: Repaired invalid JSON from failed_generation ({len(repaired)} chars)")
        return _SyntheticCompletion(repaired)
    return None


def _extract_failed_generation(error_str: str) -> str | None:
    """Best-effort extraction of the failed_generation value."""
    # Pattern 1: 'failed_generation': '...'
    m = re.search(r"'failed_generation':\s*'(.*)'", error_str, re.DOTALL)
    if m:
        return m.group(1)
    # Pattern 2: "failed_generation": "..."
    m = re.search(r'"failed_generation":\s*"(.*)"', error_str, re.DOTALL)
    if m:
        return m.group(1)
    return None


def _repair_json(text: str) -> str | None:
    """Attempt to fix common JSON errors produced by smaller LLMs.

    Handles:
      - Python-style set literals  {\"a\", \"b\"}  → [\"a\", \"b\"]
      - Trailing commas before } or ]
      - Single quotes → double quotes
    Returns the repaired JSON string or None if still unparseable.
    """
    # Un-escape if the string was repr'd inside another string
    try:
        t = text.replace("\\n", "\n").replace('\\"', '"')
    except Exception:
        t = text

    # Replace Python set-like {\"str\", \"str\", ...} with arrays
    # Match { followed by quoted strings separated by commas, ending with }
    # but NOT when preceded by : (which would be a JSON object)
    def _set_to_array(m):
        return "[" + m.group(1) + "]"

    # This regex targets { "string", "string", ... } that don't look like objects (no colons inside)
    t = re.sub(
        r'\{\s*((?:"[^"]*"(?:\s*,\s*"[^"]*")*)\s*)\}',
        lambda m: _set_to_array(m) if ":" not in m.group(1) else m.group(0),
        t
    )

    # Remove trailing commas: ,  } or ,  ]
    t = re.sub(r",\s*([}\]])", r"\1", t)

    # Try parsing
    try:
        obj = json.loads(t)
        return json.dumps(obj)
    except json.JSONDecodeError:
        pass

    # Last resort: replace single quotes with double quotes (risky but common)
    t2 = t.replace("'", '"')
    try:
        obj = json.loads(t2)
        return json.dumps(obj)
    except json.JSONDecodeError:
        return None


def _parse_wait_seconds(error_message: str, default: float = 30) -> float:
    """Extract 'Please try again in Xm Ys' from Groq error messages."""
    match = re.search(r"try again in\s+(?:(\d+)m)?(\d+(?:\.\d+)?)s", error_message)
    if match:
        minutes = int(match.group(1) or 0)
        seconds = float(match.group(2))
        total = minutes * 60 + seconds
        # Clamp: don't wait more than 120 s
        return min(total, 120)
    return default


class BaseAgent(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def process(self, data):
        """
        Process the input data and return the result.
        """
        pass
