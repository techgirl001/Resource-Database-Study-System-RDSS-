"""
SearchIndex: lets interns actually find materials, instead of just having
them dumped in a folder. Searches filename, description, and module.
"""

import re


class SearchIndex:
    def __init__(self, resource_library):
        self.library = resource_library

    @staticmethod
    def _clean_query(query):
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")
        # strip anything that isn't alphanumeric/space/hyphen
        return re.sub(r"[^\w\s\-]", "", query.strip().lower())

    def search(self, query):
        query = self._clean_query(query)
        terms = query.split()
        results = []
        for resource in self.library.all():
            haystack = " ".join(
                [
                    resource.filename.lower(),
                    resource.description.lower(),
                    resource.module_code.lower(),
                    resource.resource_type.lower(),
                ]
            )
            if all(term in haystack for term in terms):
                results.append(resource)
        return results

    def filter(self, module_code=None, resource_type=None):
        results = self.library.all()
        if module_code:
            module_code = module_code.strip().upper()
            results = [r for r in results if r.module_code == module_code]
        if resource_type:
            results = [r for r in results if r.resource_type == resource_type]
        return results
