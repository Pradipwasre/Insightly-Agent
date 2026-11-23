"""Find numbers in text and check if two numbers match. Shared by the metrics."""
import re

NUM = re.compile(r"(-?\d[\d,]*\.?\d*)\s*(%|k\b|m\b|million|bn|b\b|billion)?", re.I)
SCALE = {"k": 1e3, "m": 1e6, "million": 1e6, "b": 1e9, "bn": 1e9, "billion": 1e9}


def strip_code(text):
    """Drop the SQL the agent shows at the end; we only judge the sentence."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.sub(r"`[^`]*`", " ", text)


def numbers(text, skip_small=True):
    """[(value, tolerance)] for every number written in the text."""
    out = []
    for raw, unit in NUM.findall(strip_code(text or "")):
        raw = raw.rstrip(".,")
        if not raw or raw == "-":
            continue
        value = float(raw.replace(",", ""))
        scale = SCALE.get((unit or "").lower(), 1)
        decimals = len(raw.split(".")[1]) if "." in raw else 0
        if skip_small and scale == 1 and not unit and decimals == 0 and abs(value) <= 12:
            continue  # "top 3", "1-3 sentences": not claims
        out.append((value * scale, 0.5 * 10 ** -decimals * scale))
    return out


def close(a, tol, b):
    """True if b rounds to a (or is within 1%)."""
    return abs(a - b) <= tol + 1e-9 or (b != 0 and abs(a - b) / abs(b) <= 0.01)


def source_values(text):
    return [v for v, _ in numbers(text, skip_small=False)]
