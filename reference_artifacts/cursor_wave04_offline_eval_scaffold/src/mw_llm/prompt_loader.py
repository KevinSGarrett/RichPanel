"""Utility helpers to hydrate prompt text from Markdown artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(slots=True)
class PromptSections:
     system: str
     sections: Dict[str, str]

     def get(self, key: str, default: str = "") -> str:
         return self.sections.get(key.lower(), default)


def load_prompt_sections(path: Path) -> PromptSections:
     if not path.exists():
         raise FileNotFoundError(f"Prompt file not found: {path}")

     with path.open("r", encoding="utf-8") as handle:
         lines = handle.readlines()

     current_header = None
     sections: Dict[str, list[str]] = {}
     buffer: list[str] = []
     for raw_line in lines:
         line = raw_line.rstrip("\n")
         if line.startswith("## "):
             if current_header is not None:
                 sections[current_header] = buffer
             current_header = line[3:].strip().lower()
             buffer = []
         else:
             buffer.append(line)
     if current_header is not None:
         sections[current_header] = buffer

     system_key = "system message (recommended)"
     system_lines = sections.get(system_key)
     if not system_lines:
         raise ValueError(f"Prompt {path} missing '{system_key}' section")

     normalized_sections = {
         header: "\n".join(content).strip()
         for header, content in sections.items()
         if header != system_key
     }

     return PromptSections(system="\n".join(system_lines).strip(), sections=normalized_sections)
