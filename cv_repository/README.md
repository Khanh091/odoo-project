# CV Repository

CV Repository is an administrator-only internal CV and candidate store. It is
independent of HR, contacts, and school business models, and depends only on
`base`, `mail`, and `cv_ai`.

## Workflow

1. An administrator uploads one or more PDF/DOCX files.
2. One batch and one document per attachment are created.
3. Documents are queued and the upload request returns immediately.
4. A scheduled job processes one queued CV at a time, then CV AI extracts text,
   calls Ollama, and returns normalized candidate data.
5. Candidates enter **Waiting for Review** and can be edited.
6. Administrators approve one candidate, selected candidates, or every waiting
   candidate in a batch. Rejection requires a reason.

Batch states are Draft, Processing, Waiting for Review, Completed, Partial, and
Failed. Candidate states are Waiting for Review, Approved, Rejected, and
Archived.

The queue cron runs every minute with a limit of one document. Upload, retry,
and batch processing buttons only enqueue documents; they never wait for
Ollama in the web request.

Only members of **CV Repository Administrator** can access repository models,
wizards, actions, and menus. CV files remain in `ir.attachment`; archiving a
candidate does not delete the source file.
