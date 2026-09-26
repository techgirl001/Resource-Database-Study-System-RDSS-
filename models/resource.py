"""
Resource: a stored note, slide, or classwork file, tagged to a module.
This is metadata only -- the actual file lives under uploads/<type>/.
"""

import json
import os
import re
import uuid
from datetime import datetime

ALLOWED_TYPES = {"note", "slide", "classwork"}
ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"}


class UnsupportedFileTypeError(Exception):
    pass


class Resource:
    def __init__(
        self,
        resource_id,
        filename,
        resource_type,
        module_code,
        uploaded_by,
        description="",
        date_uploaded=None,
    ):
        self.resource_id = resource_id
        self.filename = self._validate_filename(filename)
        self.resource_type = self._validate_type(resource_type)
        self.module_code = module_code.strip().upper()
        self.uploaded_by = uploaded_by.strip()
        self.description = description.strip()
        self.date_uploaded = date_uploaded or datetime.now().isoformat()

    @staticmethod
    def _validate_filename(filename):
        filename = filename.strip()
        # strip anything that isn't a safe filename character
        filename = re.sub(r"[^\w\-. ]", "_", filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"'{ext}' is not a supported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
            )
        return filename

    @staticmethod
    def _validate_type(resource_type):
        resource_type = resource_type.strip().lower()
        if resource_type not in ALLOWED_TYPES:
            raise ValueError(
                f"resource_type must be one of {ALLOWED_TYPES}, got '{resource_type}'"
            )
        return resource_type

    def to_dict(self):
        return {
            "resource_id": self.resource_id,
            "filename": self.filename,
            "resource_type": self.resource_type,
            "module_code": self.module_code,
            "uploaded_by": self.uploaded_by,
            "description": self.description,
            "date_uploaded": self.date_uploaded,
        }

    @staticmethod
    def from_dict(data):
        return Resource(
            data["resource_id"],
            data["filename"],
            data["resource_type"],
            data["module_code"],
            data["uploaded_by"],
            data.get("description", ""),
            data.get("date_uploaded"),
        )

    @staticmethod
    def new_id():
        return uuid.uuid4().hex[:10]

    def __repr__(self):
        return f"Resource({self.resource_type}:{self.filename} -> {self.module_code})"
