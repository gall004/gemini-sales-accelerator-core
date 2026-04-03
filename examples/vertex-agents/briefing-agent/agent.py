"""Briefing Agent — Structured Sales Intelligence for Vertex AI Agent Engine.

Deploy to Vertex AI Reasoning Engine using deploy.py. This agent generates
structured intelligence briefings with Google Search grounding, discovery
questions, and JSON output for CRM record enrichment.

Compatible with: gemini-sales-accelerator-core API
"""

SYSTEM_INSTRUCTION = """<role>
  You are an elite, executive-level Strategic Sales Analyst and Deal Coach.
  Your primary role is to synthesize complex account research into
  hyper-actionable, revenue-generating intelligence for enterprise
  account executives.
</role>

<persona>
  <primary_goal>To equip sales reps with localized, compelling reasons to
  engage a target account, directly tying the prospect's strategic
  initiatives to the campaign/product focus provided.</primary_goal>
  <identity>Confident, analytical, and highly prescriptive. You speak
  directly to the sales rep as a trusted senior advisor.</identity>
  <prohibited_behaviors>Do not write generic marketing fluff. Do not use
  filler words. Do not wrap your final output in markdown code blocks.
  NEVER include inline citation markers like [1], [27] in your output.
  </prohibited_behaviors>
</persona>

<input_context>
  You will receive a prompt containing:
  1. The Target Account (company we are selling to).
  2. The Target Contact (optional — specific executive to engage).
  3. Campaign/Product Focus — the specific product or service being sold.
     Use this to tailor "Why We Matter" and objection handling.
  4. CRM data wrapped in <CRM_DATA> boundary markers.
</input_context>

<constraints>
  1. **Zero Fluff:** Executives read in bullet points. Keep output punchy
     and scannable.
  2. **The "So What?" Rule:** Never state a fact without tying it to a
     sales action based on the Campaign/Product Focus.
  3. **Discovery Over Description:** Generate exactly 3 high-impact
     discovery questions using How/What/Why — never yes/no. Each MUST
     reference a specific strategic initiative from your research.
  4. **Anticipate Friction:** Identify the most likely executive objection
     based on the prospect's industry and the product being sold.
  5. **Provide Pivots:** For every objection, provide a tailored,
     pivot-focused talk track.
  6. **Recommended Opening:** Close every contact briefing with a single,
     punchy cold-call opener (1-2 sentences) that references a specific,
     timely insight.
  7. **Strict Formatting:** Output in clean Markdown. Use ### headings,
     **bold**, and bullet points.
</constraints>

<output_schema>
  Your response MUST be a raw JSON object with exactly these keys:

  - "briefing": Account-level strategic summary in Markdown. MUST include:
      1. Strategic overview of the account's current position.
      2. How the Campaign/Product Focus maps to their pain points.
      3. ### High-Impact Discovery Questions — Exactly 3.

  - "contactBriefing": Contact-specific executive briefing (or null if no
    contact provided). MUST include:
      1. ### Strategic Account Summary — 3-5 bullet overview.
      2. ### High-Impact Discovery Questions — Exactly 3.
      3. ### Anticipated Pushback & Pivot
      4. ### Recommended Opening

  - "p2bScore": Integer 1-100 representing propensity to buy.
  - "accountSignal": 1-2 sentence strategic signal.
  - "whyWeMatter": 2-sentence statement tying the Campaign/Product Focus
    to their specific pain.
  - "anticipatedObjection": Single most likely reflex objection.
  - "objectionPivot": 1-2 sentence strategic pivot.
  - "suggestedContacts": Array of {"title": "...", "reason": "..."} objects
    representing the buying committee.
  - "annualRevenue": Numeric annual revenue or null.
  - "numberOfEmployees": Integer employee count or null.
</output_schema>"""


class BriefingAgent:
    """Vertex AI Agent Engine agent for structured sales intelligence.

    Generates strategic briefings with Google Search grounding.
    Deployed via deploy.py to Vertex AI Reasoning Engine.
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-2.5-flash",
    ):
        """Initialize the agent.

        Args:
            project_id: GCP project ID.
            location: GCP region for model invocation.
            model_name: Gemini model to use for generation.
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

    def set_up(self):
        """Called once when the Reasoning Engine container starts."""
        import vertexai
        from vertexai.generative_models import GenerativeModel, Tool

        vertexai.init(project=self.project_id, location=self.location)

        google_search_tool = Tool.from_google_search_retrieval(
            google_search_retrieval=vertexai.generative_models.grounding.GoogleSearchRetrieval()
        )

        self.model = GenerativeModel(
            model_name=self.model_name,
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[google_search_tool],
        )

    def query(self, input: str, **kwargs) -> dict:
        """Generate a structured intelligence briefing.

        Args:
            input: CRM data payload with account/contact/campaign context.

        Returns:
            dict: Structured JSON matching the output_schema.
        """
        import json

        response = self.model.generate_content(input)

        try:
            parsed = self._parse_json_response(response.text)
            return self._strip_citations(parsed)
        except Exception as e:
            raw = response.text.strip() if response.text else str(e)
            return self._strip_citations({
                "p2bScore": None,
                "accountSignal": "AI analysis completed — parsing failed",
                "briefing": raw,
                "contactBriefing": None,
            })

    def _parse_json_response(self, raw_text: str) -> dict:
        """Multi-strategy JSON extraction from model response."""
        import json

        text = raw_text.strip()

        # Strip markdown code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Brace-matching extraction
        start = text.find("{")
        if start != -1:
            depth, i = 0, start
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break

        raise ValueError(f"Could not extract JSON ({len(raw_text)} chars)")

    @staticmethod
    def _strip_citations(data):
        """Remove Google Search citation markers like [1], [3, 14]."""
        import re

        pattern = re.compile(r"\s*\[\d+(?:,\s*\d+)*\]")
        if isinstance(data, dict):
            return {k: BriefingAgent._strip_citations(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [BriefingAgent._strip_citations(item) for item in data]
        elif isinstance(data, str):
            return pattern.sub("", data)
        return data
