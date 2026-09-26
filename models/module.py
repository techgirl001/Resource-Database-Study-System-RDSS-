"""
Module: represents one topic/module from the course syllabus.
Used to validate that resources and classwork are tagged consistently,
instead of facilitators typing free-text topic names that don't match.
"""

import json
import os
import re


class Module:
    def __init__(self, code, name):
        self.code = code.strip().upper()
        self.name = name.strip()

    def to_dict(self):
        return {"code": self.code, "name": self.name}

    @staticmethod
    def from_dict(data):
        return Module(data["code"], data["name"])

    def __repr__(self):
        return f"Module({self.code}: {self.name})"


class ModuleNotFoundError(Exception):
    """Raised when a module code/name doesn't match the syllabus list."""
    pass


class ModuleList:
    """
    Loads and manages the master syllabus module list from a JSON file.
    Every resource/classwork tag gets validated against this list.
    """

    CODE_PATTERN = re.compile(r"^[A-Z0-9\-]{2,10}$")

    def __init__(self, filepath="data/modules.json"):
        self.filepath = filepath
        self.modules = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            self.modules = {}
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.modules = {
                m["code"]: Module.from_dict(m) for m in raw
            }
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Corrupted modules file: {e}")

    def save(self):
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.modules.values()], f, indent=2)

    def add(self, code, name):
        code = code.strip().upper()
        if not self.CODE_PATTERN.match(code):
            raise ValueError(f"Invalid module code format: '{code}'")
        self.modules[code] = Module(code, name)
        self.save()

    def normalize(self, code_or_name):
        """
        Validate/normalize a module code or name against the syllabus list.
        Raises ModuleNotFoundError if there's no reasonable match.
        """
        if not code_or_name or not code_or_name.strip():
            raise ValueError("Module code/name cannot be empty.")

        cleaned = code_or_name.strip().upper()

        # Exact code match
        if cleaned in self.modules:
            return self.modules[cleaned]

        # Fuzzy match on name (case-insensitive substring)
        for module in self.modules.values():
            if cleaned.lower() in module.name.lower():
                return module

        raise ModuleNotFoundError(
            f"'{code_or_name}' does not match any module in the syllabus."
        )

    def all(self):
        return list(self.modules.values())
