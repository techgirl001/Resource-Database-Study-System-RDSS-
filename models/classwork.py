"""
ClassworkRecord: a log entry for classwork/exercises given in a session,
so there's a permanent, searchable record of what was covered and when.
"""

import json
import os
import uuid
from datetime import datetime


class ClassworkRecord:
    def __init__(
        self, record_id, module_code, date, description, resource_id=None
    ):
        self.record_id = record_id
        self.module_code = module_code.strip().upper()
        self.date = date
        self.description = description.strip()
        if not self.description:
            raise ValueError("Classwork description cannot be empty.")
        self.resource_id = resource_id  # optional link to an uploaded Resource

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "module_code": self.module_code,
            "date": self.date,
            "description": self.description,
            "resource_id": self.resource_id,
        }

    @staticmethod
    def from_dict(data):
        return ClassworkRecord(
            data["record_id"],
            data["module_code"],
            data["date"],
            data["description"],
            data.get("resource_id"),
        )

    @staticmethod
    def new_id():
        return uuid.uuid4().hex[:10]

    def __repr__(self):
        return f"ClassworkRecord({self.date} [{self.module_code}]: {self.description[:30]})"


class ClassworkStore:
    """Loads/saves all classwork records to JSON."""

    def __init__(self, filepath="data/classwork_log.json"):
        self.filepath = filepath
        self.records = []
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            self.records = []
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.records = [ClassworkRecord.from_dict(r) for r in raw]
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Corrupted classwork log: {e}")

    def save(self):
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.records], f, indent=2)

    def add(self, record: ClassworkRecord):
        self.records.append(record)
        self.save()

    def by_module(self, module_code):
        module_code = module_code.strip().upper()
        return [r for r in self.records if r.module_code == module_code]

    def by_date_range(self, start_date, end_date):
        return [r for r in self.records if start_date <= r.date <= end_date]

    def all(self):
        return list(self.records)
