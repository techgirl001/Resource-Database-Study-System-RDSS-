"""
ResourceLibrary: the core of Phase 2. Facilitators upload a file once,
tag it to a module, and it's stored + indexed for interns to find later.
No content is generated here -- this only stores and organizes what's given to it.
"""

import json
import os
import shutil

from models.resource import Resource, ALLOWED_TYPES, UnsupportedFileTypeError


class DuplicateResourceError(Exception):
    pass


class ResourceLibrary:
    def __init__(
        self,
        index_path="data/resources_index.json",
        upload_root="uploads",
        module_list=None,
    ):
        self.index_path = index_path
        self.upload_root = upload_root
        self.module_list = module_list  # ModuleList instance, for tag validation
        self.resources = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.index_path):
            self.resources = {}
            return
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.resources = {r["resource_id"]: Resource.from_dict(r) for r in raw}
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Corrupted resource index: {e}")

    def save(self):
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.resources.values()], f, indent=2)

    def upload(
        self, source_filepath, resource_type, module_code, uploaded_by, description=""
    ):
        """
        Copies the file into uploads/<type>/ and registers it in the index.
        Raises UnsupportedFileTypeError, ModuleNotFoundError, or
        DuplicateResourceError as appropriate.
        """
        if not os.path.exists(source_filepath):
            raise FileNotFoundError(f"Source file not found: {source_filepath}")

        if resource_type not in ALLOWED_TYPES:
            raise ValueError(f"resource_type must be one of {ALLOWED_TYPES}")

        filename = os.path.basename(source_filepath)

        # Validate module tag against the syllabus list, if one was provided
        if self.module_list is not None:
            module = self.module_list.normalize(module_code)
            module_code = module.code

        # Prevent uploading the exact same filename+module twice
        for r in self.resources.values():
            if r.filename == filename and r.module_code == module_code.upper():
                raise DuplicateResourceError(
                    f"'{filename}' is already uploaded under module {module_code}."
                )

        resource_id = Resource.new_id()
        resource = Resource(
            resource_id, filename, resource_type, module_code, uploaded_by, description
        )

        dest_dir = os.path.join(self.upload_root, resource_type + "s" if not resource_type.endswith("s") else resource_type)
        # normalize: note -> notes, slide -> slides, classwork -> classwork
        dest_dir = os.path.join(self.upload_root, {
            "note": "notes", "slide": "slides", "classwork": "classwork"
        }[resource_type])
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, resource.filename)
        shutil.copy2(source_filepath, dest_path)

        self.resources[resource_id] = resource
        self.save()
        return resource

    def delete(self, resource_id):
        if resource_id not in self.resources:
            raise KeyError(f"No resource with ID {resource_id}")
        resource = self.resources.pop(resource_id)
        self.save()
        return resource

    def list_by_module(self, module_code):
        module_code = module_code.strip().upper()
        return [r for r in self.resources.values() if r.module_code == module_code]

    def list_by_type(self, resource_type):
        return [r for r in self.resources.values() if r.resource_type == resource_type]

    def get_file_path(self, resource_id):
        resource = self.resources.get(resource_id)
        if not resource:
            raise KeyError(f"No resource with ID {resource_id}")
        subfolder = {"note": "notes", "slide": "slides", "classwork": "classwork"}[
            resource.resource_type
        ]
        return os.path.join(self.upload_root, subfolder, resource.filename)

    def all(self):
        return list(self.resources.values())
