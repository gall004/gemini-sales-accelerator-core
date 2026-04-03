# Briefing Agent — Example Vertex AI Agent

A reference implementation of a Sales Intelligence Agent compatible with the **Gemini Sales Accelerator Core** API.

## What This Agent Does

When queried by the API, this agent:

1. Receives account/contact/campaign data via `query(input="...")`
2. Uses **Google Search grounding** to research the target company in real-time
3. Generates a structured JSON response with:
   - Strategic briefing (Markdown)
   - Contact-specific briefing (Markdown)
   - P2B Score (0–100)
   - Account Signal
   - "Why We Matter" — tailored to the campaign/product focus
   - Anticipated objection + pivot
   - Suggested buying committee contacts

## Prerequisites

- Python 3.12+
- GCP project with Vertex AI API enabled
- Authenticated via `gcloud auth application-default login`

## Deploy

```bash
pip install -r requirements.txt

python deploy.py \
  --project-id YOUR_GCP_PROJECT_ID \
  --location us-central1 \
  --model-name gemini-3-preview
```

After deployment, copy the `Agent ID` from the output and set it in your API configuration:

```bash
# Option 1: Environment variable
BRIEFING_AGENT_ENGINE_ID=5864266157464223744

# Option 2: platform_config table
INSERT INTO platform_config (key, value, category, description)
VALUES ('default_briefing_agent_id', '5864266157464223744', 'ai',
        'Default Briefing Agent Reasoning Engine ID');
```

## Output Schema Contract

The API expects the agent's `query()` method to return a dict with these keys:

| Key | Type | Description |
|---|---|---|
| `briefing` | `string` | Account-level strategic briefing (Markdown) |
| `contactBriefing` | `string\|null` | Contact-specific executive briefing |
| `p2bScore` | `integer` | Propensity to Buy (0–100) |
| `accountSignal` | `string` | 1–2 sentence strategic signal |
| `whyWeMatter` | `string` | Value prop tied to campaign context |
| `anticipatedObjection` | `string` | Most likely executive objection |
| `objectionPivot` | `string` | Strategic pivot to redirect |
| `suggestedContacts` | `array` | `[{"title": "...", "reason": "..."}]` |

## Customization

This is a **reference implementation**. Tenants should fork and customize:

- **System prompt** — adjust persona, constraints, company context
- **Model** — swap `gemini-3-preview` for `gemini-2.5-pro` etc.
- **Tools** — add RAG data stores, custom tools, or remove Google Search
- **Output schema** — extend with additional fields (the API ignores unknown keys)

## Local Testing

```python
from agent import BriefingAgent

agent = BriefingAgent(project_id="your-project-id")
agent.set_up()

response = agent.query(input="""
Generate a strategic sales briefing for entity_type: account

<CRM_DATA>
Account Name: Ticketmaster
Industry: Entertainment
Website: https://ticketmaster.com
</CRM_DATA>

Campaign/Product Focus: Google Actions Center Integrations for Event Ticketing
""")

print(response)
```
