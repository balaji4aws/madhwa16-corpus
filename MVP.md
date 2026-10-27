# Madhwa16 minimal API — MVP

This is the first runnable backend prototype. It is deliberately **not** a hosted vector database or a full ChatGPT integration.

## Design

- **Source of truth:** the public `balaji4aws/madhwa16-corpus` GitHub repository.
- **Corpus discovery:** `manifest.json`.
- **Metadata:** `talks/<slug>.json`.
- **Evidence:** timestamped lines in `transcripts/<slug>.md`.
- **Retrieval:** small lexical baseline; no vector DB required for the first talk.
- **Generation:** OpenAI Responses API, called only when at least one relevant passage is retrieved.
- **Trust:** no retrieved evidence means an explicit abstention. Masked Sanskrit lines are excluded from retrieval. Responses include source URLs, timestamps, excerpts and draft status.

## Run locally

1. Install Python 3.11 or newer.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure the API key in your shell (do not commit it):

   ```bash
   export OPENAI_API_KEY="your-key"
   export OPENAI_MODEL="gpt-4.1-mini"
   ```

4. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Open `http://127.0.0.1:8000/docs` to try the API.

## Endpoints

- `GET /health` — service health.
- `GET /corpus` — current corpus count and source-of-truth link.
- `POST /ask` — question, evidence-grounded answer, and citations.

Example request:

```json
{
  "question": "What does this transcript say about Radha?"
}
```

The answer may be incomplete because this is a first-pass lexical retriever and the only transcript is a machine draft. It must not be presented as authoritative Madhwa scholarship.

## Known limitations before public launch

- Retrieval is lexical, not semantic; cross-language and paraphrase retrieval will be weak.
- The corpus is fetched from GitHub at runtime and cached in-process. Restart the service to refresh the cache; a scheduled incremental index is not yet implemented.
- The API returns candidate evidence citations alongside the generated answer. This prototype does not yet validate each inline citation token produced by the model.
- No authentication, rate limiting, deployment, monitoring or production evaluation suite yet.
- Do not expose an OpenAI API key in a browser or client app.
- The transcript's Kannada text is a machine draft. Masked Sanskrit remains unavailable until human validation.

## Next milestone

Add tests and citation validation, then deploy behind a protected API. Only add embeddings/vector storage when real query tests show lexical retrieval is insufficient.
