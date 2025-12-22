"""Loader utilities for the SC_Data AI ready package."""

from __future__ import annotations

from dataclasses import dataclass
import json
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import zipfile

from ..redaction import (
     RedactionResult,
     contains_email,
     contains_order_number,
     contains_phone,
     contains_tracking_number,
     redact_text,
)
from ..types import ClassificationFeatures, ClassificationInput

SC_ROOT = "SC_Data_ai_ready"


@dataclass(slots=True)
class ConversationExample:
     conversation_id: str
     channel: str
     raw_text: str
     redacted_text: str
     features: ClassificationFeatures

     def to_classification_input(self) -> ClassificationInput:
         return ClassificationInput(text=self.redacted_text, features=self.features)


def _open_sc_file(base_path: Path, relative: str):
     if base_path.is_file() and base_path.suffix == ".zip":
         archive = zipfile.ZipFile(base_path)
         try:
             return archive.open(f"{SC_ROOT}/{relative}"), archive
         except KeyError as exc:
             archive.close()
             raise FileNotFoundError(f"{relative} not found inside {base_path}") from exc
     inner_path = base_path / SC_ROOT / relative
     if not inner_path.exists():
         raise FileNotFoundError(inner_path)
     return inner_path.open("rb"), None


def _iterate_messages(base_path: Path) -> Iterable[Dict]:
     handle, archive = _open_sc_file(base_path, "messages.jsonl")
     try:
         for raw in handle:
             if not raw.strip():
                 continue
             yield json.loads(raw)
     finally:
         handle.close()
         if archive:
             archive.close()


def _load_channel_map(base_path: Path) -> Dict[int, str]:
     handle, archive = _open_sc_file(base_path, "conversations_meta.csv")
     channel_map: Dict[int, str] = {}
     try:
         text_iter = (line.decode("utf-8", errors="ignore") for line in handle)
         reader = csv.DictReader(text_iter)
         for row in reader:
             try:
                 cid = int(row["conversation_id"])
             except (ValueError, KeyError):
                 continue
             channel_map[cid] = (row.get("ConversationType") or "email").lower()
     finally:
         handle.close()
         if archive:
             archive.close()
     return channel_map


def load_examples(base_path: Path, limit: Optional[int] = None) -> List[ConversationExample]:
     channel_map = _load_channel_map(base_path)
     first_messages: Dict[int, Dict] = {}
     for record in _iterate_messages(base_path):
         if record.get("role") != "customer":
             continue
         cid = int(record["conversation_id"])
         idx = int(record.get("message_index", 0))
         existing = first_messages.get(cid)
         if existing is None or idx < existing["message_index"]:
             first_messages[cid] = {"message_index": idx, "text": record.get("text", "")}
         if limit and len(first_messages) >= limit:
             break

     examples: List[ConversationExample] = []
     for cid, payload in first_messages.items():
         text = payload["text"]
         redaction = redact_text(text)
         features = _build_features(
             channel=channel_map.get(cid, "email"),
             redaction=redaction,
             raw_text=text,
         )
         examples.append(
             ConversationExample(
                 conversation_id=str(cid),
                 channel=features.channel,
                 raw_text=text,
                 redacted_text=redaction.redacted_text,
                 features=features,
             )
         )
     return examples


def _build_features(channel: str, redaction: RedactionResult, raw_text: str) -> ClassificationFeatures:
     has_order_number = contains_order_number(raw_text)
     has_tracking = contains_tracking_number(raw_text)
     has_email = bool(redaction.matches.get("email"))
     has_phone = bool(redaction.matches.get("phone"))
     deterministic_order_link = has_order_number or has_tracking
     return ClassificationFeatures(
         channel=channel,
         deterministic_order_link=deterministic_order_link,
         has_order_number=has_order_number,
         has_email=has_email,
         has_phone=has_phone,
         has_tracking_number=has_tracking,
     )
