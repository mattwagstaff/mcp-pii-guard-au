# mcp-pii-guard-au

Australian and New Zealand PII detection and sanitisation for AI agents. An [MCP server](https://modelcontextprotocol.io) that finds and redacts Tax File Numbers (TFN), Medicare card numbers, ABNs, ACNs, BSB and bank account numbers, drivers licence numbers, passport numbers, Centrelink CRNs, Australian addresses, Australian phone numbers, NZ IRD numbers, NZ NHI numbers, NZ drivers licences, and 13 standard entity types — before text reaches an LLM or gets stored. Built on [Microsoft Presidio](https://microsoft.github.io/presidio/) with 14 custom AU/NZ recognisers that use real checksum validation and context-word boosting, not just regex.

[Model Context Protocol](https://modelcontextprotocol.io) (MCP) is an open standard that lets AI assistants — Claude, Cursor, Copilot, custom agents — call external tools over a standardised interface. This server exposes PII detection and sanitisation as MCP tools. Any MCP-compatible client can call them without custom integration code.

Built for teams in regulated Australian industries — financial services, government, healthcare — who need to prove PII was scrubbed before data left a trust boundary. Compliance-ready for the Australian Privacy Act (APPs), GDPR, HIPAA, SOX, and PCI-DSS.

---

**Fourteen AU/NZ entity types that don't exist elsewhere.** TFN, Medicare, ABN, ACN, BSB, bank account, drivers licence, passport, Centrelink CRN, Australian address, Australian phone number, NZ IRD, NZ NHI, and NZ drivers licence recognisers — with real checksum validation where algorithms exist, and context-word boosting throughout. No other Presidio wrapper or PII tool on GitHub handles these. If you're building AI tooling for AU/NZ enterprise, government, or health, this is the gap.

**Audit logging that a compliance officer can actually use.** Every scan writes structured JSON to an append-only log file. It records *what types of PII were found*, *how many*, *what tool was called*, and *what confidence threshold was used*. It never records the original text. It never records the detected values. This is the difference between an audit trail and a liability — and it's what GDPR Article 30, the Australian Privacy Act, and SOX controls actually require.

**Five tools, deliberately.** Most MCP servers ship a dozen tools and let the model figure it out. Every tool an agent has to evaluate costs context window tokens, increases routing errors, and makes the system harder to audit. This server exposes exactly five tools with clear contracts: detect, sanitise text, sanitise documents, de-tokenise, and list entities. Small surface. Predictable behaviour. Easy to reason about in an agent workflow.

---

## When to use this

- An AI agent is summarising customer support tickets and you need to strip names, emails, and tax file numbers before the text hits the LLM context window
- You're building a RAG pipeline over Australian government case files and need to redact PII before indexing into a vector store
- A compliance team needs evidence that PII was handled — not just a policy document, but machine-readable audit logs with scan IDs and entity counts
- You're processing Australian customer data (CRM exports, form submissions, call transcripts) and need TFN/Medicare/ABN detection that actually validates checksums instead of matching any 9-digit number
- Payroll or invoicing data contains BSB numbers, bank account numbers, and addresses that must be stripped before entering an AI system
- You need to satisfy Australian Privacy Principle 11 (APP 11) requirements for securing personal information before it enters an AI system
- Government or social services data contains Centrelink CRNs that must never reach an LLM context window

## How it works

```
┌─────────────┐     stdio      ┌──────────────────┐   Presidio    ┌─────────┐
│  MCP Client │◄──────────────►│mcp-pii-guard-au  │──────────────►│  spaCy  │
│  (Claude,   │  JSON-RPC      │                  │ NLP detection │en_core_ │
│   Cursor,   │                │  5 tools         │ + 14 custom   │web_lg   │
│   agent)    │                │  audit log       │AU/NZ recognsrs│         │
└─────────────┘                └────────┬─────────┘               └─────────┘
                                        │
                                        ▼
                                 logs/pii_guard_audit.jsonl
                                 (metadata only, never PII values)
```

The server runs as a **local subprocess** of the MCP client, communicating over **stdio** (standard input/output). No HTTP server, no network port, no authentication surface. The client starts the process, sends JSON-RPC messages over stdin, and reads responses from stdout. When the client disconnects, the process exits.

This is deliberate for regulated environments: the PII never leaves the machine over a network connection. The server runs in the same trust boundary as the client.

## Install

**Prerequisites:** Python 3.11+, ~500MB disk for the spaCy language model.

```bash
# From PyPI
uv pip install mcp-pii-guard-au
python -m spacy download en_core_web_lg
```

```bash
# From source
git clone https://github.com/mattwagstaff/mcp-pii-guard-au.git
cd mcp-pii-guard-au
uv pip install -e .
python -m spacy download en_core_web_lg
```

Verify the install:

```bash
python -c "import spacy; spacy.load('en_core_web_lg'); print('ready')"
```

## Running the server

### With Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "pii-guard-au": {
      "command": "mcp-pii-guard-au",
      "env": {
        "PII_GUARD_AUDIT_LOG": "/absolute/path/to/logs/pii_guard_audit.jsonl"
      }
    }
  }
}
```

Restart Claude Desktop. The PII guard tools will appear in Claude's tool list automatically.

### With Claude Code

```json
// .mcp.json in your project root
{
  "mcpServers": {
    "pii-guard-au": {
      "command": "mcp-pii-guard-au"
    }
  }
}
```

### With any MCP client

Any client that implements the [MCP specification](https://modelcontextprotocol.io) can use this server. The transport is stdio — the client starts the process and communicates over stdin/stdout. Refer to your client's documentation for how to register an MCP server.

### Development and testing

Use the MCP Inspector to test tools interactively without a full client:

```bash
mcp dev mcp_pii_guard_au/server.py
```

Or run directly to verify startup (will wait for stdin and exit when you close it):

```bash
mcp-pii-guard-au
```

## Tools

This server exposes exactly five tools. An MCP client (like Claude) discovers them automatically on connection.

### `detect_pii`

Scan text and return detected PII entities without modifying anything. Use this when you need to inspect what's there before deciding what to do.

```json
// Input
{"text": "Contact Jane Smith at jane@acme.com. TFN: 123 456 782. BSB: 062-000 Acct: 1234 5678", "min_confidence": 0.7}

// Output
{
  "entity_count": 5,
  "entities": [
    {"type": "PERSON", "text": "Jane Smith", "start": 8, "end": 18, "confidence": 0.92},
    {"type": "EMAIL_ADDRESS", "text": "jane@acme.com", "start": 22, "end": 35, "confidence": 0.95},
    {"type": "AU_TFN", "text": "123 456 782", "start": 42, "end": 53, "confidence": 0.85},
    {"type": "AU_BSB", "text": "062-000", "start": 60, "end": 67, "confidence": 0.80},
    {"type": "AU_BANK_ACCOUNT", "text": "1234 5678", "start": 74, "end": 83, "confidence": 0.75}
  ],
  "has_pii": true,
  "scan_id": "a1b2c3d4-..."
}
```

### `sanitize_text`

Detect and scrub PII in one call. The workhorse tool — call this when you need clean text safe for an LLM, a database, or a response.

```json
// Input
{"text": "Invoice for Jane Smith (jane@acme.com). TFN: 123 456 782. Pay to BSB 062-000 Acct 1234 5678", "mode": "redact"}

// Output
{
  "sanitized_text": "Invoice for [REDACTED:PERSON] ([REDACTED:EMAIL]). TFN: [REDACTED:AU_TFN]. Pay to BSB [REDACTED:AU_BSB] Acct [REDACTED:AU_BANK_ACCOUNT]",
  "entities_removed": 5,
  "entity_types_found": ["AU_BANK_ACCOUNT", "AU_BSB", "AU_TFN", "EMAIL_ADDRESS", "PERSON"],
  "mode": "redact",
  "scan_id": "e5f6g7h8-...",
  "audit_logged": true
}
```

Three modes:
- **`redact`** (default) — `[REDACTED:TYPE]` labels. No reversibility. Safest.
- **`replace`** — Realistic fake values via Presidio's faker operators. Preserves text shape for downstream processing.
- **`tokenize`** — Stable tokens like `{{EMAIL_ADDRESS_1}}`. Useful when you need to reference the same entity across a workflow without exposing the value. Use `detokenize_text` with the returned `scan_id` to reverse tokenisation within the same session.

All tools accept an optional `entity_thresholds` parameter — a dict of per-entity-type confidence overrides (e.g. `{"AU_ADDRESS": 0.9, "PERSON": 0.5}`). Entity types not listed fall back to `min_confidence`.

### `sanitize_document`

Recursively sanitise all string fields in a JSON document. For CRM records, customer objects, form submissions — anything structured.

```json
// Input
{
  "document": {
    "id": "cust-001",
    "name": "Jane Smith",
    "email": "jane@acme.com",
    "address": "123 Pitt Street, Sydney NSW 2000",
    "tfn": "123 456 782",
    "bank": {"bsb": "062-000", "account": "1234 5678"}
  },
  "skip_fields": ["id"],
  "mode": "redact"
}

// Output
{
  "sanitized_document": {
    "id": "cust-001",
    "name": "[REDACTED:PERSON]",
    "email": "[REDACTED:EMAIL]",
    "address": "[REDACTED:AU_ADDRESS]",
    "tfn": "[REDACTED:AU_TFN]",
    "bank": {"bsb": "[REDACTED:AU_BSB]", "account": "[REDACTED:AU_BANK_ACCOUNT]"}
  },
  "fields_processed": 6,
  "fields_sanitised": 6,
  "total_entities_removed": 6,
  "entity_summary": {"PERSON": 1, "EMAIL_ADDRESS": 1, "AU_ADDRESS": 1, "AU_TFN": 1, "AU_BSB": 1, "AU_BANK_ACCOUNT": 1},
  "scan_id": "i9j0k1l2-..."
}
```

### `detokenize_text`

Reverse tokenisation by replacing tokens with their original values. Pass the `scan_id` from a previous `sanitize_text` call with `mode="tokenize"`.

```json
// Input
{"text": "Invoice for {{PERSON_1}} ({{EMAIL_ADDRESS_1}})", "scan_id": "e5f6g7h8-..."}

// Output
{
  "original_text": "Invoice for Jane Smith (jane@acme.com)",
  "tokens_reversed": 2,
  "scan_id": "e5f6g7h8-..."
}
```

Token mappings are **session-scoped** — they exist only while the server process is running and are never written to disk. If the server restarts, all mappings are lost. This is deliberate: original PII values are never persisted to storage.

### `list_supported_entities`

Returns every entity type this server can detect, with descriptions, compliance framework mappings, and examples. No arguments. Call this first if you need to build an `entity_types` filter.

## Supported Entity Types

### Australian entities (11 custom recognisers)

These are the entity types that don't exist in other PII tools. Each uses official government-published validation algorithms where they exist, context-word boosting throughout, and structured pattern matching.

| Entity Type | Description | Frameworks | Validation |
|---|---|---|---|
| `AU_TFN` | Australian Tax File Number (8 or 9 digit) | APPs, TAA | Pattern + weighted mod-11 checksum + context |
| `AU_MEDICARE` | Australian Medicare card number (10 digit) | APPs, HIPAA | Pattern + weighted mod-10 checksum + context |
| `AU_ABN` | Australian Business Number (11 digit) | APPs, ATO | Pattern + mod-89 checksum + context |
| `AU_ACN` | Australian Company Number (9 digit) | APPs, ASIC | Pattern + modulus-10 checksum + context |
| `AU_DRIVERS_LICENCE` | Drivers licence number (varies by state) | APPs | Multi-pattern (NSW/QLD/WA formats) + context |
| `AU_PASSPORT` | Australian passport number (1–2 letters + 7 digits) | APPs, DFAT | Pattern + context |
| `AU_BSB` | Bank-State-Branch number (6 digit) | APPs, PCI-DSS | Pattern + bank prefix validation + context |
| `AU_BANK_ACCOUNT` | Bank account number (6–10 digits) | APPs, PCI-DSS | Pattern + financial context |
| `AU_ADDRESS` | Street or postal address | APPs, GDPR | Multi-pattern (street/PO Box/state+postcode) + context |
| `AU_PHONE_NUMBER` | Australian phone number (mobile/landline/international) | APPs, GDPR | Pattern + carrier-prefix validation + context |
| `CENTRELINK_CRN` | Centrelink Customer Reference Number (9 digits + check letter) | APPs, Social Security Act | Pattern + weighted checksum + letter validation + context |

### New Zealand entities (3 custom recognisers)

| Entity Type | Description | Frameworks | Validation |
|---|---|---|---|
| `NZ_IRD` | NZ IRD (Inland Revenue) number (8–9 digit) | NZ Privacy Act, NZ Tax Administration Act | Pattern + mod-11 checksum + context |
| `NZ_NHI` | NZ National Health Index number (3 letters + 4 digits) | NZ Privacy Act, NZ Health Act | Pattern + check digit validation + context |
| `NZ_DRIVERS_LICENCE` | NZ drivers licence number (2 letters + 6 digits) | NZ Privacy Act | Pattern + context |

### Standard entities (13 via Presidio)

| Entity Type | Description | Frameworks | Validation |
|---|---|---|---|
| `PERSON` | Person names | GDPR, APPs, HIPAA, SOX | NLP (spaCy NER) |
| `EMAIL_ADDRESS` | Email addresses | GDPR, APPs, HIPAA | Pattern |
| `PHONE_NUMBER` | Phone numbers (local + international, incl. AU) | GDPR, APPs, HIPAA | Pattern |
| `CREDIT_CARD` | Credit/debit card numbers | PCI-DSS, GDPR, APPs | Luhn checksum |
| `IBAN_CODE` | International Bank Account Numbers | GDPR, PCI-DSS, SOX | Pattern + checksum |
| `IP_ADDRESS` | IPv4 and IPv6 addresses | GDPR | Pattern |
| `URL` | URLs that may contain PII | GDPR | Pattern |
| `DATE_TIME` | Dates and times (e.g. date of birth) | GDPR, HIPAA, APPs | Pattern + NLP |
| `LOCATION` | Physical locations (generic NLP — see `AU_ADDRESS` for Australian-specific) | GDPR, APPs, HIPAA | NLP |
| `MEDICAL_LICENSE` | Medical licence numbers | HIPAA | Pattern |
| `US_SSN` | US Social Security Numbers | SOX, HIPAA | Pattern + checksum |
| `US_PASSPORT` | US passport numbers | GDPR, SOX | Pattern |
| `US_BANK_NUMBER` | US bank account numbers | SOX, PCI-DSS | Pattern |

## Audit Logging

Every tool call writes a structured JSON entry to `./logs/pii_guard_audit.jsonl` (override with `PII_GUARD_AUDIT_LOG` env var). Append-only JSONL format. Each tool has an `audit` parameter (default `true`) to control this per-call.

```json
{
  "timestamp": "2026-03-26T10:42:00Z",
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tool": "sanitize_text",
  "entity_types_detected": ["PERSON", "EMAIL_ADDRESS", "AU_TFN", "AU_BSB"],
  "entity_count": 4,
  "mode": "redact",
  "text_length": 240,
  "min_confidence": 0.7,
  "language": "en"
}
```

**What's logged:** scan ID, tool name, entity types found, entity count, mode, text length, confidence threshold, language.

**What's never logged:** the original text, the detected PII values, the sanitised output. The audit trail proves *that* PII was handled. It doesn't create a second copy of the PII.

For production use, forward the JSONL file to your SIEM or log aggregator (Splunk, Datadog, ELK). Each line is a self-contained JSON object — no parsing needed beyond newline splitting.

## Deployment

### Local (recommended for most use cases)

The server runs as a subprocess of your MCP client. No separate deployment step — configure the client to start the server process, and it runs on the same machine. This is the simplest and most secure option: PII never crosses a network boundary.

```
Your machine
├── Claude Desktop / Claude Code / your agent
│   └── spawns: mcp-pii-guard-au (stdio)
│       └── writes: logs/pii_guard_audit.jsonl
```

### Docker

For standardised environments or CI pipelines:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install . && python -m spacy download en_core_web_lg
# No EXPOSE — stdio transport, no network port
CMD ["mcp-pii-guard-au"]
```

The container communicates over stdio (attached stdin/stdout), not HTTP. Your MCP client must be able to start and attach to the container process. Claude Desktop supports this natively:

```json
{
  "mcpServers": {
    "pii-guard-au": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp-pii-guard-au"],
      "env": {
        "PII_GUARD_AUDIT_LOG": "/app/logs/pii_guard_audit.jsonl"
      }
    }
  }
}
```

### Why stdio, not HTTP

This server deliberately does not expose an HTTP endpoint. In a compliance context:

- **No network attack surface.** No port to scan, no TLS to misconfigure, no auth tokens to leak.
- **No PII in transit.** Data moves over a Unix pipe between two processes on the same machine, not over a network socket.
- **Simpler audit story.** "The PII never left the machine" is easier to prove than "the PII was encrypted in transit and the TLS cert was valid and the auth token wasn't compromised."

If you need remote access, put an MCP proxy in front of it — but understand that you're changing the trust boundary.

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `PII_GUARD_AUDIT_LOG` | `./logs/pii_guard_audit.jsonl` | Path to the append-only audit log file |

Tool-level defaults (configured in `mcp_pii_guard_au/config.py`):

| Setting | Default | Description |
|---|---|---|
| Confidence threshold | `0.7` | Minimum Presidio score to report an entity |
| Language | `en` | Language code for NLP analysis |
| Entity types | All 27 types | Which entity types to scan for by default |

All defaults can be overridden per-call via tool parameters.

## FAQ

### How does TFN detection work? Is it just regex?

No. The TFN recogniser uses a two-stage process: a regex pattern matches 8 or 9-digit sequences formatted like TFNs (`\d{3}\s?\d{3}\s?\d{2,3}`), then the match is validated using the ATO's weighted checksum algorithm (weights `[1, 4, 3, 7, 5, 8, 6, 9, 10]`, sum divisible by 11). Only numbers that pass the checksum are reported. Context words like "TFN", "tax file number", and "ATO" near the match boost the confidence score above the default threshold.

### How does Medicare number detection work?

The Medicare recogniser matches 10-digit numbers where the first digit is 2–6, then validates using a weighted checksum (weights `[1, 3, 7, 9, 1, 3, 7, 9]` across the first 8 digits, with the 9th digit as the check digit). Context words like "medicare", "medicare card", and "Services Australia" boost confidence.

### How does ABN validation work?

The ABN recogniser matches 11-digit numbers and validates using the official ABN algorithm: subtract 1 from the first digit, multiply each digit by its weight (`[10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]`), sum the products, and check divisibility by 89. Context words like "ABN", "business number", and "GST" boost confidence.

### How does ACN validation work?

The ACN recogniser matches 9-digit numbers and validates using the ASIC modulus-10 algorithm: multiply digits 1–8 by weights `[8, 7, 6, 5, 4, 3, 2, 1]`, sum the products, and verify the check digit equals `(10 - (sum % 10)) % 10`. Context words like "ACN", "ASIC", and "Pty Ltd" boost confidence.

### How does BSB detection work?

The BSB recogniser matches 6-digit codes (formatted as XXX-XXX or XXXXXX), then validates the first two digits against a table of known Australian financial institution prefixes (01 = ANZ, 03 = Westpac, 06 = CBA, 08 = NAB, etc.). Context words like "BSB", "bank details", and "direct deposit" boost confidence.

### How does Centrelink CRN detection work?

The CRN recogniser matches 9-digit + letter sequences and validates using a weighted checksum: multiply each digit by weights `[1, 2, 3, 4, 5, 6, 7, 8, 9]`, sum the products, and verify the trailing letter matches the remainder when divided by 26 (0=A, 1=B, ..., 25=Z). Context words like "CRN", "Centrelink", and "Services Australia" boost confidence.

### How does Australian address detection work?

The address recogniser uses three patterns: full street addresses (number + street name + street type + optional suburb/state/postcode), PO Box / GPO Box addresses, and state abbreviation + 4-digit postcode fragments. Street types cover standard Australian abbreviations (St, Rd, Ave, Dr, Cres, Pl, Ct, Ln, Tce, Hwy, Bvd, Cl, Pde, Cct, etc.). All Australian states and territories are recognised (NSW, VIC, QLD, SA, WA, TAS, NT, ACT).

### How does drivers licence detection work?

Licence formats vary by state (NSW: 2 letters + 6 digits, QLD: 8 digits, WA: 7 digits, etc.). Because these formats overlap heavily with other number types, the recogniser uses deliberately low base scores and relies on context words like "licence", "driver", "RMS", "VicRoads", or "Service NSW" for confidence boosting. Without nearby context, matches will not reach the default 0.7 threshold.

### Does this work with Claude Desktop?

Yes. Add the server to your Claude Desktop configuration file and restart. Claude will automatically discover the four PII tools and can call them during conversations. See the [Claude Desktop configuration](#with-claude-desktop) section above.

### Does this work with Claude Code?

Yes. Add the server to a `.mcp.json` file in your project root. Claude Code will discover the tools when it starts. See the [Claude Code configuration](#with-claude-code) section above.

### Does it detect Australian phone numbers?

Yes. The custom `AU_PHONE_NUMBER` recogniser detects mobile (04XX), landline (02/03/07/08), and international (+61) formats. Mobile numbers are validated against known carrier prefix ranges (Telstra 0400–0419/0470–0489, Optus 0430–0449/0490–0499, Vodafone 0420–0429/0450–0469). Presidio's built-in `PHONE_NUMBER` type also catches international formats as a fallback.

### Does the audit log contain the original PII?

No. This is a deliberate design decision. The audit log records metadata only: what entity types were found, how many, which tool was called, the text length, and the confidence threshold. It never records the original text, the detected values, or the sanitised output. The audit trail proves that PII was handled without creating a second copy of the PII itself.

### What compliance frameworks does this support?

Entity types are mapped to: the **Australian Privacy Act** (APPs), the **Taxation Administration Act** (TAA), **GDPR**, **HIPAA**, **SOX**, **PCI-DSS**, **ATO**, **ASIC**, **DFAT**, and **Social Security Act** compliance requirements. The `list_supported_entities` tool returns the full framework mapping for each entity type.

### Can I use this without MCP? As a Python library?

The core detection and sanitisation logic is in `mcp_pii_guard_au/core/detector.py` and `mcp_pii_guard_au/core/sanitizer.py`. You can import and call these directly without running the MCP server. The MCP layer in `mcp_pii_guard_au/server.py` is a thin wrapper.

### Does it detect New Zealand PII?

Yes. Three NZ entity types are supported: IRD numbers (with mod-11 checksum validation), NHI numbers (with check digit validation), and drivers licence numbers. Context words like "IRD", "NHI", "NZTA", and "Waka Kotahi" boost confidence.

### Can I set different confidence thresholds per entity type?

Yes. All detection and sanitisation tools accept an optional `entity_thresholds` parameter — a dict mapping entity types to confidence thresholds. For example, `{"AU_ADDRESS": 0.9, "PERSON": 0.5}` would require high confidence for addresses but accept lower confidence for person names. Entity types not listed fall back to the `min_confidence` parameter.

### How does de-tokenisation work?

When you call `sanitize_text` with `mode="tokenize"`, the server stores a mapping from each token (like `{{EMAIL_ADDRESS_1}}`) to its original value, keyed by the `scan_id`. You can then call `detokenize_text` with the tokenised text and the `scan_id` to reverse the tokens back to original values. Mappings are session-scoped — they exist only in memory while the server is running and are never written to disk.

### Why only five tools?

Every tool an LLM agent has access to must be described in the system prompt, consuming context window tokens. Each additional tool increases the chance of the model selecting the wrong one. Five tools with clear, non-overlapping purposes (detect, sanitise text, sanitise document, de-tokenise, list entities) gives agents enough capability to handle any PII workflow without the ambiguity of a large tool surface. This is a deliberate constraint, not a limitation.

## Roadmap

- **v3**: Partial masking mode (e.g. `TFN: ***-***-782` showing last few characters)
- **v3**: Configurable context-word lists per entity type
- **v3**: Additional NZ entity types (NZ passport, NZ bank account)

## Licence

MIT
