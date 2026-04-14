"""Helpers for persisting campaign logs and performance history."""

from __future__ import annotations

import json
from pathlib import Path


class CampaignLogger:
    """Small JSON append helper used by the mocked CRM pipeline."""

    def append_record(self, file_path: Path, record: dict) -> list:
        """Append one record to a JSON array file and return the updated list."""
        current = self._load_records(file_path)
        current.append(record)
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(current, file, indent=2)
        return current

    def _load_records(self, file_path: Path) -> list:
        """Load records from a JSON array file, returning an empty list when missing or invalid."""
        try:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
