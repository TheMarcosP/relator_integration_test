import os

# -------- parse helper ---------
def parse_settings(path: str) -> dict:
    """Return dict with API_KEY, ENDPOINT, DEPLOYMENT from a text file.

    Expected lines:
        API_KEY     = "sk-…"
        ENDPOINT    = "https://…"
    Blank lines or lines starting with # are ignored.
    """
    kv = {}
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing settings file: {path!r}")

    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"Malformed line: {raw!r}")
            key, value = map(str.strip, line.split("=", 1))
            kv[key] = value

    return kv