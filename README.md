# mcp-pii-guard

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that detects and sanitizes personally identifiable information (PII) from text before it reaches an LLM or gets stored. Built on [Microsoft Presidio](https://microsoft.github.io/presidio/) for NLP-based entity recognition.

MCP is an open protocol that lets AI assistants (Claude, Cursor, Copilot, custom agents) call external tools over a standardised interface. This server exposes PII detection and sanitization as MCP tools — any MCP-compatible client can call them without custom integration code.

Designed for teams in regulated industries — financial services, government, healthcare — who need to prove PII was scrubbed before data left a boundary.

---

**Three things that matter about this project:**

**Australian entity types that don't exist elsewhere.** TFN, Medicare, and ABN recognizers with real checksum validation — not just regex. Every Presidio wrapper and PII tool on GitHub handles US SSNs and credit cards. None of them handle Australian Tax File Numbers, Medicare card numbers, or ABNs. If you're building AI tooling for AU/NZ enterprise, government, or health, this is the gap.

**Audit logging that a compliance officer can actually use.** Every scan writes structured JSON to an append-only log file. The log records *what types of PII were found*, *how many*, *what tool was called*, and *what confidence threshold was used*. It never records the original text. It never records the detected values. This is the difference between an audit trail and a liability — and it's what GDPR Article 30, the Australian Privacy Act, and SOX controls actually require.

**Four tools, deliberately.** Most MCP servers ship a dozen tools and let the model figure it out. Every tool an agent has to evaluate costs context window tokens, increases routing errors, and makes the system harder to audit. This server exposes exactly four tools with clear contracts: detect, sanitize text, sanitize documents, list entities. Small surface. Predictable behaviour. Easy to reason about in an agent workflow.

---

## When to use this

- An AI agent is summarising customer support tickets and you need to strip names, emails, and tax file numbers before the text hits the LLM context window
- You're building a RAG pipeline over government case files and need to redact PII before indexing into a vector store
- A compliance team needs evidence that PII was handled — not just a policy document, but machine-readable audit logs with scan IDs and entity counts
- You're processing Australian customer data (CRM exports, form submissions, call transcripts) and need TFN/Medicare/ABN detection that actually validates checksums instead of matching any 9-digit number

## How it works

```
┌─────────────┐     stdio      ┌──────────────┐     Presidio     ┌─────────┐
│  MCP Client │◄──────────────►│ mcp-pii-guard│───────────────►  │  spaCy  │
│  (Claude,   │  JSON-RPC      │              │  NLP detection   │en_core_ │
│   Cursor,   │                │  4 tools     │  + custom AU     │web_lg   │
│   agent)    │                │  audit log   │  recognizers     │         │
└─────────────┘                └──────┬───────┘                  └─────────┘
                                      │
                                      ▼
                               logs/pii_guard_audit.jsonl
                               (metadata only, never PII)
```

The server runs as a **local subprocess** of the MCP client, communicating over **stdio** (standard input/output). There is no HTTP server, no network port, no authentication surface. The client starts the process, sends JSON-RPC messages over stdin, and reads responses from stdout. When the client disconnects, the process exits.

This is deliberate for regulated environments: the PII never leaves the machine over a network connection. The server runs in the same trust boundary as the client.

## Install

**Prerequisites:** Python 3.11+, ~500MB disk for the spaCy language model.

```bash
# From PyPI (when published)
uv pip install mcp-pii-guard
python -m spacy download en_core_web_lg
```

```bash
# From source
git clone https://github.com/mattwagstaff/mcp-pii-guard.git
cd mcp-pii-guard
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
    "pii-guard": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-pii-guard/server.py"],
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
    "pii-guard": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-pii-guard/server.py"]
    }
  }
}
```

### With any MCP client

Any client that implements the [MCP specification](https://modelcontextprotocol.io) can use this server. The transport is stdio — the client starts the process and communicates over stdin/stdout. Refer to your client's documentation for how to register an MCP server.

### Development and testing

Use the MCP Inspector to test tools interactively without a full client:

```bash
mcp dev server.py
```

Or run directly to verify startup (will wait for stdin and exit when you close it):

```bash
python server.py
```

## Tools

This server exposes exactly four tools. An MCP client (like Claude) discovers them automatically on connection.

### `detect_pii`

Scan text and return detected PII entities without modifying anything. Use this when you need to inspect what's there before deciding what to do.

```json
// Input
{"text": "Contact Jane Smith at jane@acme.com or 0412 345 678", "min_confidence": 0.7}

// Output
{
  "entity_count": 3,
  "entities": [
    {"type": "PERSON", "text": "Jane Smith", "start": 8, "end": 18, "confidence": 0.92},
    {"type": "EMAIL_ADDRESS", "text": "jane@acme.com", "start": 22, "end": 35, "confidence": 0.95},
    {"type": "PHONE_NUMBER", "text": "0412 345 678", "start": 39, "end": 51, "confidence": 0.80}
  ],
  "has_pii": true,
  "scan_id": "a1b2c3d4-..."
}
```

### `sanitize_text`

Detect and scrub PII in one call. The workhorse tool — call this when you need clean text safe for an LLM, a database, or a response.

```json
// Input
{"text": "Invoice for Jane Smith (jane@acme.com). TFN: 123 456 782", "mode": "redact"}

// Output
{
  "sanitized_text": "Invoice for [REDACTED:PERSON] ([REDACTED:EMAIL]). TFN: [REDACTED:AU_TFN]",
  "entities_removed": 3,
  "entity_types_found": ["AU_TFN", "EMAIL_ADDRESS", "PERSON"],
  "mode": "redact",
  "scan_id": "e5f6g7h8-...",
  "audit_logged": true
}
```

Three modes:
- **`redact`** (default) — `[REDACTED:TYPE]` labels. No reversibility. Safest.
- **`replace`** — Realistic fake values via Presidio's faker operators. Preserves text shape for downstream processing.
- **`tokenize`** — Stable tokens like `{{EMAIL_ADDRESS_1}}`. Useful when you need to reference the same entity across a workflow without exposing the value.

### `sanitize_document`

Recursively sanitize all string fields in a JSON document. For CRM records, customer objects, form submissions — anything structured.

```json
// Input
{
  "document": {
    "id": "cust-001",
    "name": "Jane Smith",
    "email": "jane@acme.com",
    "notes": "Called re TFN 123 456 782"
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
    "notes": "Called re TFN [REDACTED:AU_TFN]"
  },
  "fields_processed": 3,
  "fields_sanitized": 3,
  "total_entities_removed": 4,
  "entity_summary": {"PERSON": 1, "EMAIL_ADDRESS": 1, "AU_TFN": 1},
  "scan_id": "i9j0k1l2-..."
}
```

### `list_supported_entities`

Returns every entity type this server can detect, with descriptions, compliance framework mappings, and examples. No arguments. Call this first if you need to build an `entity_types` filter.

## Supported Entity Types

| Entity Type | Description | Frameworks | Validation |
|---|---|---|---|
| `PERSON` | Person names | GDPR, APPs, HIPAA, SOX | NLP (spaCy NER) |
| `EMAIL_ADDRESS` | Email addresses | GDPR, APPs, HIPAA | Pattern |
| `PHONE_NUMBER` | Phone numbers (local + intl) | GDPR, APPs, HIPAA | Pattern |
| `CREDIT_CARD` | Credit/debit card numbers | PCI-DSS, GDPR, APPs | Luhn checksum |
| `IBAN_CODE` | International Bank Account Numbers | GDPR, PCI-DSS, SOX | Pattern + checksum |
| `IP_ADDRESS` | IPv4 and IPv6 | GDPR | Pattern |
| `URL` | URLs that may contain PII | GDPR | Pattern |
| `DATE_TIME` | Dates/times (e.g. DOB) | GDPR, HIPAA, APPs | Pattern + NLP |
| `LOCATION` | Physical addresses | GDPR, APPs, HIPAA | NLP |
| `MEDICAL_LICENSE` | Medical license numbers | HIPAA | Pattern |
| `US_SSN` | US Social Security Numbers | SOX, HIPAA | Pattern + checksum |
| `US_PASSPORT` | US passport numbers | GDPR, SOX | Pattern |
| `US_BANK_NUMBER` | US bank account numbers | SOX, PCI-DSS | Pattern |
| **`AU_TFN`** | **Australian Tax File Number** | **APPs, TAA** | **Pattern + weighted mod-11 checksum + context words** |
| **`AU_MEDICARE`** | **Australian Medicare number** | **APPs, HIPAA** | **Pattern + weighted mod-10 checksum + context words** |
| **`AU_ABN`** | **Australian Business Number** | **APPs, ATO** | **Pattern + mod-89 checksum + context words** |

## Audit Logging

Every tool call writes a structured JSON entry to `./logs/pii_guard_audit.jsonl` (override with `PII_GUARD_AUDIT_LOG` env var). Append-only JSONL format. Each tool has an `audit` parameter (default `true`) to control this per-call.

```json
{
  "timestamp": "2026-03-26T10:42:00Z",
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tool": "sanitize_text",
  "entity_types_detected": ["PERSON", "EMAIL_ADDRESS"],
  "entity_count": 2,
  "mode": "redact",
  "text_length": 240,
  "min_confidence": 0.7,
  "language": "en"
}
```

**What's logged:** scan ID, tool name, entity types found, entity count, mode, text length, confidence threshold, language.

**What's never logged:** the original text, the detected PII values, the sanitized output. The audit trail proves *that* PII was handled. It doesn't create a second copy of the PII.

For production use, forward the JSONL file to your SIEM or log aggregator (Splunk, Datadog, ELK). Each line is a self-contained JSON object — no parsing needed beyond newline splitting.

## Deployment

### Local (recommended for most use cases)

The server runs as a subprocess of your MCP client. No separate deployment step — configure the client to start the server process, and it runs on the same machine. This is the simplest and most secure option: PII never crosses a network boundary.

```
Your machine
├── Claude Desktop / Claude Code / your agent
│   └── spawns: python server.py (stdio)
│       └── writes: logs/pii_guard_audit.jsonl
```

### Docker

For standardised environments or CI pipelines:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e . && python -m spacy download en_core_web_lg
# No EXPOSE — stdio transport, no network port
CMD ["python", "server.py"]
```

The container communicates over stdio (attached stdin/stdout), not HTTP. Your MCP client must be able to start and attach to the container process. Claude Desktop supports this natively:

```json
{
  "mcpServers": {
    "pii-guard": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp-pii-guard"],
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

Tool-level defaults (configured in `config.py`):

| Setting | Default | Description |
|---|---|---|
| Confidence threshold | `0.7` | Minimum Presidio score to report an entity |
| Language | `en` | Language code for NLP analysis |
| Entity types | All 16 types | Which entity types to scan for by default |

All defaults can be overridden per-call via tool parameters.

## Roadmap

- **v2**: De-tokenization endpoint for `tokenize` mode (reverse tokens back to original values within a session)
- **v2**: Additional AU/NZ entity types (driver licence, passport, IRD number)
- **v2**: Configurable confidence thresholds per entity type

## License

MIT
