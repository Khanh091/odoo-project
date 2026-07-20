# CV AI

CV AI extracts normalized candidate information from text-based PDF and DOCX
attachments. It calls a configurable Ollama server and does not create or store
candidate business records.

## Configuration

Open Settings and configure the **CV AI** section:

- Ollama URL (default `http://localhost:11434`)
- Model (default `qwen3:8b`)
- Request timeout (default `120` seconds)
- Maximum text length (default `50000` characters)

## Public contract

```python
result = self.env["cv.ai.service"].parse_attachment(attachment)
```

`attachment` must be one existing `ir.attachment` record containing a valid PDF
or DOCX file. The returned dictionary contains normalized candidate fields,
`raw_text`, `provider`, and `model`.

## Current limitations

- Only text-based PDF and DOCX files are supported.
- OCR is not supported.
- CV AI does not manage batches, approval, or candidate persistence.
