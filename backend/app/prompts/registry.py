"""
Versioned prompt files: backend/prompts/<name>/<version>.yaml

Templates use {{ placeholder }} tokens (not str.format), so prompt text can
contain literal braces. A missing or unknown placeholder raises instead of
silently shipping a broken prompt.
"""
import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
_TOKEN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    description: str
    fields: dict
    sha256: str

    def render(self, template: str, **values: str) -> str:
        text = self.fields[template]

        def sub(m: re.Match) -> str:
            key = m.group(1)
            if key not in values:
                raise KeyError(f"prompt {self.name}/{self.version} '{template}' needs '{key}'")
            return values[key]

        return _TOKEN.sub(sub, text)


@lru_cache
def load_prompt(name: str, version: str) -> Prompt:
    path = PROMPTS_DIR / name / f"{version}.yaml"
    raw = path.read_bytes()
    data = yaml.safe_load(raw)
    if data.get("name") != name or data.get("version") != version:
        raise ValueError(f"{path} declares {data.get('name')}/{data.get('version')}, expected {name}/{version}")
    fields = {k: v for k, v in data.items() if k not in ("name", "version", "description")}
    return Prompt(name, version, data.get("description", ""), fields, hashlib.sha256(raw).hexdigest())


def available_versions(name: str) -> list[str]:
    return sorted(p.stem for p in (PROMPTS_DIR / name).glob("*.yaml"))
