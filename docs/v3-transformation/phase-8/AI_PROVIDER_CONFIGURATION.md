# AutoHeal Phase 8: AI Provider Configuration & Dual-Mode Guide

## 1. Zero-Fabrication Contract

AutoHeal enforces a strict **Zero-Fabrication Contract** across all AI services:
1. **No Fake LLM Connectivity**: The platform never pretends an LLM is connected when API keys are absent.
2. **Transparent Operational Status**: The UI and API explicitly display the active provider name, model identifier, and connection mode.
3. **Deterministic Grounded Fallback**: When external LLMs are unavailable, AutoHeal activates its deterministic analytical engine. This engine computes 100% telemetry-grounded forensic analyses without sacrificing investigative accuracy.

---

## 2. Supported AI Providers & Environment Variables

The `AIProviderManager` inspects environment variables in order of priority:

```
[1. Google Gemini] ---> [2. Anthropic Claude] ---> [3. OpenAI] ---> [4. Ollama Local] ---> [5. Grounded Fallback]
```

### 2.1 Google Gemini (Recommended Default)
- **Environment Variables**:
  - `GEMINI_API_KEY`: API key from Google AI Studio.
  - `GEMINI_MODEL`: (Optional, default: `gemini-1.5-flash` or `gemini-1.5-pro`).
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`

### 2.2 Anthropic Claude
- **Environment Variables**:
  - `ANTHROPIC_API_KEY`: Anthropic API secret key.
  - `ANTHROPIC_MODEL`: (Optional, default: `claude-3-5-sonnet-20241022`).
- **Endpoint**: `https://api.anthropic.com/v1/messages`

### 2.3 OpenAI
- **Environment Variables**:
  - `OPENAI_API_KEY`: OpenAI API key.
  - `OPENAI_MODEL`: (Optional, default: `gpt-4o-mini` or `gpt-4o`).
- **Endpoint**: `https://api.openai.com/v1/chat/completions`

### 2.4 Ollama (Local Self-Hosted)
- **Environment Variables**:
  - `OLLAMA_BASE_URL`: (Default: `http://localhost:11434`).
  - `OLLAMA_MODEL`: (Default: `llama3.2:latest` or `mistral:latest`).
- **Endpoint**: `{OLLAMA_BASE_URL}/api/generate`

### 2.5 Grounded Local Mode (Zero-Config / Offline)
- **Activation**: Automatically engaged when none of the above API keys are set.
- **Provider String**: `DETERMINISTIC_GROUNDED`
- **Display Name**: `Deterministic Grounded Analyst Engine (Local SQLite Grounded)`
- **Online Flag**: `true` (operational and available locally).

---

## 3. Configuration Setup & Examples

### Setting Environment Variables in Windows PowerShell
```powershell
# For Gemini
$env:GEMINI_API_KEY="AIzaSyYourActualKeyHere..."
$env:GEMINI_MODEL="gemini-1.5-flash"

# For OpenAI
$env:OPENAI_API_KEY="sk-proj-YourActualKeyHere..."
$env:OPENAI_MODEL="gpt-4o-mini"

# Restart AutoHeal server
python server.py
```

### Setting Environment Variables in Linux / macOS Bash
```bash
export GEMINI_API_KEY="AIzaSyYourActualKeyHere..."
export GEMINI_MODEL="gemini-1.5-flash"
python server.py
```

---

## 4. Provider Status Verification via REST API

Verify provider status at any time using:

```bash
curl http://localhost:8000/api/copilot/provider-status
```

**Example Response (Offline / Grounded Mode)**:
```json
{
  "provider": "DETERMINISTIC_GROUNDED",
  "provider_display_name": "Deterministic Grounded Analyst Engine (Local SQLite Grounded)",
  "model": "rule-correlation-v3.0",
  "online": true,
  "mode": "deterministic_grounded",
  "external_llm_configured": false,
  "telemetry_sources_active": 7
}
```

**Example Response (Gemini Configured)**:
```json
{
  "provider": "GEMINI",
  "provider_display_name": "Google Gemini (gemini-1.5-flash)",
  "model": "gemini-1.5-flash",
  "online": true,
  "mode": "external_llm_augmented",
  "external_llm_configured": true,
  "telemetry_sources_active": 7
}
```

---

## 5. Security & Isolation Considerations

- External LLM requests transmit **only redacted forensic summaries** (IP addresses, sanitized URLs, and normalized detection rules).
- User passwords, authorization tokens, JWTs, API keys, database connection strings, and customer PII are **strictly stripped prior to dispatch** via `redact_secrets()`.
