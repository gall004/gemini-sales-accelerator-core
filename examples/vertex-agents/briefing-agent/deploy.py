"""Deploy the Briefing Agent to Vertex AI Agent Engine.

Usage:
    python deploy.py --project-id YOUR_PROJECT_ID
    python deploy.py --project-id YOUR_PROJECT_ID --staging-bucket gs://my-bucket

Prerequisites:
    1. gcloud auth application-default login
    2. pip install -r requirements.txt
    3. Enable Vertex AI API in your GCP project
    4. A GCS bucket for staging (auto-defaults to gs://{project_id}-gsa-staging)
"""

import argparse

import vertexai
from vertexai.preview import reasoning_engines

from agent import BriefingAgent


def deploy(
    project_id: str,
    location: str = "us-central1",
    model_name: str = "gemini-3-flash-preview",
    display_name: str = "Briefing Agent",
    staging_bucket: str | None = None,
) -> str:
    """Deploy the BriefingAgent to Vertex AI Reasoning Engine.

    Args:
        project_id: GCP project ID.
        location: GCP region for deployment.
        model_name: Gemini model name.
        display_name: Display name in the GCP console.
        staging_bucket: GCS bucket for staging artifacts (gs://...).
            Defaults to gs://{project_id}-gsa-staging.

    Returns:
        The Reasoning Engine resource name (contains the agent_id).
    """
    if not staging_bucket:
        staging_bucket = f"gs://{project_id}-gsa-staging"

    print(f"   Staging bucket: {staging_bucket}")
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=staging_bucket,
    )

    agent = BriefingAgent(
        project_id=project_id,
        location=location,
        model_name=model_name,
    )

    remote_agent = reasoning_engines.ReasoningEngine.create(
        agent,
        requirements=[
            "google-cloud-aiplatform[reasoningengine,langchain]>=1.86.0",
            "google-genai>=1.51.0",
        ],
        display_name=display_name,
        description=(
            "Strategic sales intelligence agent with Google Search "
            "grounding. Generates structured briefings for CRM enrichment."
        ),
    )

    print(f"\n✅ Agent deployed successfully!")
    print(f"   Resource Name: {remote_agent.resource_name}")

    # Extract numeric ID from resource name
    agent_id = remote_agent.resource_name.split("/")[-1]
    print(f"   Agent ID: {agent_id}")
    print(f"\n   Set this in your API config:")
    print(f"   BRIEFING_AGENT_ENGINE_ID={agent_id}")

    return remote_agent.resource_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deploy the Briefing Agent to Vertex AI Agent Engine."
    )
    parser.add_argument(
        "--project-id", required=True, help="GCP project ID"
    )
    parser.add_argument(
        "--location", default="us-central1", help="GCP region"
    )
    parser.add_argument(
        "--model-name", default="gemini-3-flash-preview",
        help="Gemini model name",
    )
    parser.add_argument(
        "--display-name", default="Briefing Agent",
        help="Display name in GCP console",
    )
    parser.add_argument(
        "--staging-bucket", default=None,
        help="GCS bucket for staging (gs://...). Defaults to gs://{project-id}-gsa-staging",
    )
    args = parser.parse_args()

    deploy(
        project_id=args.project_id,
        location=args.location,
        model_name=args.model_name,
        display_name=args.display_name,
        staging_bucket=args.staging_bucket,
    )
