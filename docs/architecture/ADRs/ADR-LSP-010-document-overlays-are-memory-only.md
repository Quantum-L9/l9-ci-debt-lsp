# ADR-LSP-010: Editor document overlays are memory-only
- Status: Accepted
- Phase: LSP-P2
## Decision
Unsaved editor content remains in memory and is deleted when the document or
workspace closes.
Normal incremental analysis does not persist source text, write SQLite state
per keystroke, or emit source content into logs or telemetry.
