# Phase 2: Service Name Translations

## Why this is deferred

Service names on TEVIS (Düsseldorf appointment system) are German legal/administrative terms. Mistranslating them risks users booking the wrong service. Phase 1 (UI translation) delivers immediate value with zero risk.

Build Phase 2 only if users report that service names are confusing (e.g., asking "what does X mean?"). The German names plus department context are often sufficient.

## Design

### DB change

Add a `translations` TEXT column to the `services` table (JSON string, keyed by language code):

```sql
ALTER TABLE services ADD COLUMN translations TEXT DEFAULT NULL;
```

```python
# In models.py — Service class
translations = Column(Text, nullable=True)  # JSON: {"en": "...", "ru": "...", ...}
```

Add to `apply_migrations()` in `database.py` (already idempotent by design):

```python
conn.execute(sqlalchemy.text(
    "ALTER TABLE services ADD COLUMN translations TEXT DEFAULT NULL"
))
```

### Translation source

Use **DeepL API** (free tier: 500k chars/month). DeepL handles German → Russian/Ukrainian significantly better than Google Translate for formal/bureaucratic German.

- API key: store in `.env` as `DEEPL_API_KEY`
- If key is absent, fall back to German name silently — no error shown to user.

DeepL language codes differ from ours: `en`→`EN`, `ru`→`RU`, `uk`→`UK`, `tr`→`TR`.

### On-demand translation with caching

Add to `BotHandlers` in `handlers.py`:

```python
import json
import aiohttp

async def _get_service_display_name(self, service, lang: str) -> str:
    """Return translated name if available, otherwise German original."""
    if lang == "de":
        return service.service_name

    if service.translations:
        cached = json.loads(service.translations)
        if lang in cached:
            return f"{cached[lang]}\n({service.service_name})"

    translated = await self._translate_via_deepl(service.service_name, lang)
    if translated:
        existing = json.loads(service.translations or "{}")
        existing[lang] = translated
        with self.db.get_session() as session:
            session.query(Service).filter_by(id=service.id).update(
                {"translations": json.dumps(existing)}
            )
        return f"{translated}\n({service.service_name})"

    return service.service_name

async def _translate_via_deepl(self, text: str, lang: str) -> Optional[str]:
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        return None
    deepl_lang = {"en": "EN", "ru": "RU", "uk": "UK", "tr": "TR"}.get(lang)
    if not deepl_lang:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api-free.deepl.com/v2/translate",
                data={"auth_key": api_key, "text": text,
                      "target_lang": deepl_lang, "source_lang": "DE"},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                data = await resp.json()
                return data["translations"][0]["text"]
    except Exception:
        return None
```

Then in `_show_services()`, replace `service.service_name` with `await self._get_service_display_name(service, lang)`.

### Display format

```
Internationaler Führerschein
(International driving licence)
```

For inline keyboard buttons (64-byte limit), use: `International driving licence (Intern…)` — translated name first, German original truncated if needed.

### Concerns

| Concern | Mitigation |
|---------|-----------|
| Mistranslation of legal terms | German original always shown in brackets — user can verify |
| Turkish translation quality | DeepL TR is weaker than RU/UK; monitor for complaints |
| DeepL quota | ~118 services × 4 langs = ~472 translations total; well within free tier |
| Service name changes | Clear `translations` JSON when `schema_loader.py` updates a `service_name` |
| aiohttp not in requirements | Add `aiohttp` to `requirements.txt` / `pyproject.toml` |

### Estimated scope

- ~50 lines of new code in `handlers.py`
- 1 migration line in `database.py`
- 1 model column
- 1 new dependency (`aiohttp`, or use `httpx` which may already be present)
- Optional: batch pre-translate on startup if translations cache is empty

**Total: ~60 lines of new code.**
