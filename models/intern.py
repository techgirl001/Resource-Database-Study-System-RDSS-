"""
Intern: a trainee profile. Used by the resource portal to track who
uploaded or is registered for which module.
"""

import json
import os
import re


class Intern:
    ID_PATTERN = re.compile(r"^[A-Z]{2,5}-\d{3,6}$")  # e.g. NCAIR-0001
    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, intern_id, name, module_code, email=None):
        self.intern_id = self._validate_id(intern_id)
        self.name = name.strip()
        self.module_code = module_code.strip().upper()
        self.email = self._validate_email(email) if email else None

    @classmethod
    def _validate_id(cls, intern_id):
        intern_id = intern_id.strip().upper()
        if not cls.ID_PATTERN.match(intern_id):
            raise ValueError(
                f"Invalid intern ID format: '{intern_id}'. Expected e.g. NCAIR-0001"
            )
        return intern_id

    @classmethod
    def _validate_email(cls, email):
        email = email.strip()
        if not cls.EMAIL_PATTERN.match(email):
            raise ValueError(f"Invalid email format: '{email}'")
        return email

    def to_dict(self):
        return {
            "intern_id": self.intern_id,
            "name": self.name,
            "module_code": self.module_code,
            "email": self.email,
        }

    @staticmethod
    def from_dict(data):
        return Intern(
            data["intern_id"], data["name"], data["module_code"], data.get("email")
        )

    def __repr__(self):
        return f"Intern({self.intern_id}: {self.name})"


class InternNotFoundError(Exception):
    pass


class DuplicateInternError(Exception):
    pass


class InternStore:
    """Loads/saves the roster of interns to JSON."""

    def __init__(self, filepath="data/interns.json"):
        self.filepath = filepath
        self.interns = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            self.interns = {}
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.interns = {i["intern_id"]: Intern.from_dict(i) for i in raw}
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Corrupted interns file: {e}")

    def save(self):
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([i.to_dict() for i in self.interns.values()], f, indent=2)

    def add(self, intern: Intern):
        if intern.intern_id in self.interns:
            raise DuplicateInternError(
                f"Intern {intern.intern_id} is already registered."
            )
        self.interns[intern.intern_id] = intern
        self.save()

    def get(self, intern_id):
        intern_id = intern_id.strip().upper()
        if intern_id not in self.interns:
            raise InternNotFoundError(f"No intern found with ID '{intern_id}'.")
        return self.interns[intern_id]

    def all(self):
        return list(self.interns.values())
