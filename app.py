"""
Resource Database Study System (RDSS)
Desktop version — Tkinter interface.
Run with: python app.py
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from models.module import ModuleList, ModuleNotFoundError
from models.intern import Intern, InternStore, DuplicateInternError
from models.classwork import ClassworkRecord, ClassworkStore
from models.resource import UnsupportedFileTypeError
from services.resource_library import ResourceLibrary, DuplicateResourceError
from services.search_index import SearchIndex


# ---------------------------------------------------------------------------
# System initialization (same models/services used throughout the project)
# ---------------------------------------------------------------------------

def init_system():
    modules = ModuleList("data/modules.json")
    if not modules.all():
        for code, name in [
            ("PY-BASICS", "Python Basics"),
            ("PY-OOP", "Object-Oriented Programming"),
            ("PY-EXC", "Exception Handling"),
            ("PY-FILES", "File Handling"),
            ("PY-REGEX", "Regular Expressions"),
        ]:
            modules.add(code, name)

    interns = InternStore("data/interns.json")
    classwork = ClassworkStore("data/classwork_log.json")
    library = ResourceLibrary("data/resources_index.json", "uploads", module_list=modules)
    search = SearchIndex(library)
    return modules, interns, classwork, library, search


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class RDSSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Resource Database Study System (RDSS)")
        self.geometry("820x600")

        self.modules, self.interns, self.classwork, self.library, self.search = init_system()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.upload_tab = UploadTab(notebook, self)
        self.browse_tab = BrowseTab(notebook, self)
        self.classwork_tab = ClassworkTab(notebook, self)
        self.interns_tab = InternsTab(notebook, self)

        notebook.add(self.upload_tab, text="Upload (Facilitator)")
        notebook.add(self.browse_tab, text="Browse & Search")
        notebook.add(self.classwork_tab, text="Classwork Log")
        notebook.add(self.interns_tab, text="Interns")

        # refresh each tab's lists when it's selected, so changes made
        # in one tab show up when you switch to another
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._notebook = notebook

    def _on_tab_changed(self, event):
        selected = event.widget.select()
        widget = event.widget.nametowidget(selected)
        if hasattr(widget, "refresh"):
            widget.refresh()


# ---------------------------------------------------------------------------
# Tab: Upload
# ---------------------------------------------------------------------------

class UploadTab(ttk.Frame):
    def __init__(self, parent, app: RDSSApp):
        super().__init__(parent)
        self.app = app
        self.selected_path = tk.StringVar()

        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="Upload a note, slide, or classwork file", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", **pad
        )

        ttk.Button(self, text="Choose file...", command=self._choose_file).grid(row=1, column=0, sticky="w", **pad)
        ttk.Label(self, textvariable=self.selected_path).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(self, text="Type:").grid(row=2, column=0, sticky="w", **pad)
        self.type_var = tk.StringVar(value="note")
        ttk.Combobox(
            self, textvariable=self.type_var, values=["note", "slide", "classwork"], state="readonly"
        ).grid(row=2, column=1, sticky="w", **pad)

        ttk.Label(self, text="Module (code or name):").grid(row=3, column=0, sticky="w", **pad)
        self.module_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.module_var, width=40).grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(self, text="Your name (facilitator):").grid(row=4, column=0, sticky="w", **pad)
        self.uploader_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.uploader_var, width=40).grid(row=4, column=1, sticky="w", **pad)

        ttk.Label(self, text="Description (optional):").grid(row=5, column=0, sticky="nw", **pad)
        self.desc_text = tk.Text(self, width=40, height=4)
        self.desc_text.grid(row=5, column=1, sticky="w", **pad)

        ttk.Button(self, text="Upload", command=self._upload).grid(row=6, column=1, sticky="w", **pad)

        ttk.Label(self, text="Syllabus modules on file:", font=("", 10, "bold")).grid(
            row=7, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 4)
        )
        self.modules_list = tk.Listbox(self, width=60, height=6)
        self.modules_list.grid(row=8, column=0, columnspan=2, sticky="w", padx=10)
        self._refresh_modules()

    def _refresh_modules(self):
        self.modules_list.delete(0, tk.END)
        for m in self.app.modules.all():
            self.modules_list.insert(tk.END, f"{m.code} — {m.name}")

    def _choose_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.selected_path.set(path)

    def _upload(self):
        path = self.selected_path.get()
        module_input = self.module_var.get().strip()
        uploaded_by = self.uploader_var.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()

        if not path or not module_input or not uploaded_by:
            messagebox.showerror("Missing info", "File, module, and your name are all required.")
            return

        try:
            resource = self.app.library.upload(
                path, self.type_var.get(), module_input, uploaded_by, description
            )
            messagebox.showinfo("Uploaded", f"Uploaded '{resource.filename}' under {resource.module_code}.")
            self.selected_path.set("")
            self.module_var.set("")
            self.uploader_var.set("")
            self.desc_text.delete("1.0", tk.END)
        except UnsupportedFileTypeError as e:
            messagebox.showerror("Unsupported file type", str(e))
        except ModuleNotFoundError as e:
            messagebox.showerror("Unknown module", f"{e}\nCheck the modules list or add it first.")
        except DuplicateResourceError as e:
            messagebox.showwarning("Duplicate", str(e))
        except FileNotFoundError as e:
            messagebox.showerror("File not found", str(e))

    def refresh(self):
        self._refresh_modules()


# ---------------------------------------------------------------------------
# Tab: Browse & Search
# ---------------------------------------------------------------------------

class BrowseTab(ttk.Frame):
    def __init__(self, parent, app: RDSSApp):
        super().__init__(parent)
        self.app = app

        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="Find notes, slides, and classwork", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", **pad
        )

        self.query_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.query_var, width=40).grid(row=1, column=0, sticky="w", **pad)
        ttk.Button(self, text="Search", command=self._search).grid(row=1, column=1, sticky="w", **pad)
        ttk.Button(self, text="Show all", command=self.refresh).grid(row=1, column=2, sticky="w", **pad)

        columns = ("filename", "module", "type", "description")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col, width in zip(columns, (220, 90, 90, 300)):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=width)
        self.tree.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=6)

        ttk.Button(self, text="Show file location", command=self._reveal_file).grid(
            row=3, column=0, sticky="w", padx=10, pady=6
        )

        self.results = []
        self.refresh()

    def _search(self):
        query = self.query_var.get().strip()
        if not query:
            self.refresh()
            return
        try:
            self.results = self.app.search.search(query)
        except ValueError as e:
            messagebox.showerror("Search error", str(e))
            self.results = []
        self._render()

    def refresh(self):
        self.results = self.app.library.all()
        self._render()

    def _render(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.results:
            self.tree.insert(
                "", tk.END, iid=r.resource_id,
                values=(r.filename, r.module_code, r.resource_type, r.description),
            )

    def _reveal_file(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a resource first.")
            return
        resource_id = selected[0]
        try:
            path = self.app.library.get_file_path(resource_id)
            folder = os.path.dirname(os.path.abspath(path))
            messagebox.showinfo("File location", f"File stored at:\n{path}\n\nFolder:\n{folder}")
        except KeyError as e:
            messagebox.showerror("Error", str(e))


# ---------------------------------------------------------------------------
# Tab: Classwork Log
# ---------------------------------------------------------------------------

class ClassworkTab(ttk.Frame):
    def __init__(self, parent, app: RDSSApp):
        super().__init__(parent)
        self.app = app

        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="Log classwork/exercises given in a session", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", **pad
        )

        ttk.Label(self, text="Module (code):").grid(row=1, column=0, sticky="w", **pad)
        self.module_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.module_var, width=30).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(self, text="What was given / covered:").grid(row=2, column=0, sticky="nw", **pad)
        self.desc_text = tk.Text(self, width=50, height=4)
        self.desc_text.grid(row=2, column=1, sticky="w", **pad)

        ttk.Button(self, text="Log classwork", command=self._log).grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(self, text="Recent classwork:", font=("", 10, "bold")).grid(
            row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 4)
        )
        columns = ("date", "module", "description")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col, width in zip(columns, (100, 90, 420)):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=width)
        self.tree.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10)

        self.refresh()

    def _log(self):
        module_input = self.module_var.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        try:
            module = self.app.modules.normalize(module_input)
            record = ClassworkRecord(
                ClassworkRecord.new_id(), module.code, datetime.now().date().isoformat(), description
            )
            self.app.classwork.add(record)
            messagebox.showinfo("Logged", "Classwork logged.")
            self.module_var.set("")
            self.desc_text.delete("1.0", tk.END)
            self.refresh()
        except (ModuleNotFoundError, ValueError) as e:
            messagebox.showerror("Error", str(e))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        records = sorted(self.app.classwork.all(), key=lambda r: r.date, reverse=True)[:30]
        for r in records:
            self.tree.insert("", tk.END, values=(r.date, r.module_code, r.description))


# ---------------------------------------------------------------------------
# Tab: Interns
# ---------------------------------------------------------------------------

class InternsTab(ttk.Frame):
    def __init__(self, parent, app: RDSSApp):
        super().__init__(parent)
        self.app = app

        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="Register a new intern", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", **pad
        )

        ttk.Label(self, text="Intern ID (e.g. NCAIR-0001):").grid(row=1, column=0, sticky="w", **pad)
        self.id_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.id_var, width=30).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(self, text="Name:").grid(row=2, column=0, sticky="w", **pad)
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, width=30).grid(row=2, column=1, sticky="w", **pad)

        ttk.Label(self, text="Module code:").grid(row=3, column=0, sticky="w", **pad)
        self.module_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.module_var, width=30).grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(self, text="Email (optional):").grid(row=4, column=0, sticky="w", **pad)
        self.email_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.email_var, width=30).grid(row=4, column=1, sticky="w", **pad)

        ttk.Button(self, text="Register intern", command=self._register).grid(row=5, column=1, sticky="w", **pad)

        ttk.Label(self, text="Registered interns:", font=("", 10, "bold")).grid(
            row=6, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 4)
        )
        columns = ("id", "name", "module")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col, width in zip(columns, (100, 180, 100)):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=width)
        self.tree.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=10)

        self.refresh()

    def _register(self):
        try:
            intern = Intern(
                self.id_var.get(), self.name_var.get(), self.module_var.get(),
                self.email_var.get() or None,
            )
            self.app.interns.add(intern)
            messagebox.showinfo("Registered", f"Registered {intern.name} ({intern.intern_id})")
            self.id_var.set("")
            self.name_var.set("")
            self.module_var.set("")
            self.email_var.set("")
            self.refresh()
        except (ValueError, DuplicateInternError) as e:
            messagebox.showerror("Error", str(e))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i in self.app.interns.all():
            self.tree.insert("", tk.END, values=(i.intern_id, i.name, i.module_code))


if __name__ == "__main__":
    app = RDSSApp()
    app.mainloop()
