# Resource Database Study System (RDSS)

A central place for facilitators to store notes, slides, and classwork —
and for interns to search, revisit, and download them — instead of
materials being regenerated or resent every time someone asks.

## What's built

| Phase | Status | What it delivers |
|---|---|---|
| 1. Data models | ✅ | `Intern`, `Module`, `Resource`, `ClassworkRecord` + JSON storage |
| 2. Upload + Search | ✅ | Facilitators upload/tag files; interns search/download |
| 3. Classwork Log | ✅ | Permanent record of classwork/exercises per module and date |
| 4. AI tag suggestion | ✅ (optional) | `tag_suggester.py` — Gemini suggests a module tag; facilitator confirms |

## Setup

```bash
pip install -r requirements.txt
```

Tkinter ships with Python on Windows and macOS. On Linux, if it isn't
already installed: `sudo apt install python3-tk` (Debian/Ubuntu).

For the optional AI tag-suggestion feature, create a `.env` file:

```
GEMINI_API_KEY=your_free_gemini_api_key
```

(Get a free key at https://ai.google.dev/ — the app works fine without one,
it just skips the tag-suggestion step.)

## Run

```bash
python app.py
```

This opens the desktop window with four tabs: Upload, Browse & Search,
Classwork Log, and Interns.

## Project structure

```
ncair_portal/
├── data/              # JSON "database" (interns, modules, resources, classwork)
├── uploads/           # actual uploaded files, sorted by type
├── models/            # Module, Intern, Resource, ClassworkRecord
├── services/          # ResourceLibrary, SearchIndex, tag_suggester
└── app.py             # Streamlit UI tying it all together
```

## Design decisions worth knowing

- **No database server** — JSON files are the storage layer. Fine at this
  scale (a training cohort), keeps cost at $0, and every file is
  human-readable/git-diffable.
- **AI is a convenience, not a requirement** — the tag-suggester only runs
  if a `GEMINI_API_KEY` is set, and the facilitator always confirms the
  suggested tag before it's saved. Nothing breaks if the key is missing.
- **Module tags are validated against a syllabus list**, not free text —
  so search and filtering stay reliable as the resource library grows.

## Testing it yourself

The core logic (`models/` and `services/`) has no UI dependency, so you can
exercise it directly in a Python shell: create a `ModuleList`, add a
module, register an `Intern`, upload a `Resource`, and log a
`ClassworkRecord` — each one raises a clear exception on bad input
(duplicate IDs, unsupported file types, unknown modules, empty descriptions).
