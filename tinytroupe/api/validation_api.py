from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# Adjust imports to match your project’s structure
# e.g. from validator import TinyPersonValidator
# from tinytroupe.agent import TinyPerson
from validator import TinyPersonValidator
from tinytroupe.agent import TinyPerson

app = FastAPI(title="TinyTroupe Validation API")

# ------------------------------------------------------------------------------
# 1) In-Memory Agent Registry (example)
#    Replace or remove if your system manages agents differently.
# ------------------------------------------------------------------------------
AGENT_REGISTRY = {}  # e.g. "alice" -> TinyPerson(...)

# ------------------------------------------------------------------------------
# 2) Pydantic Models for Requests
# ------------------------------------------------------------------------------

class ValidationRequest(BaseModel):
    """Request body to validate a specific TinyPerson."""
    agent_name: str = Field(..., description="Name/ID of the agent to validate.")
    expectations: Optional[str] = Field(None, description="Rules or expectations for the validation process.")
    include_agent_spec: bool = Field(False, description="Whether to include the agent’s full specification in the prompt.")
    max_content_length: int = Field(1024, description="Max content length to display in the conversation.")

class ValidationResponse(BaseModel):
    """Response body containing the validation score and justification."""
    score: float
    justification: str

# ------------------------------------------------------------------------------
# 3) Endpoints
# ------------------------------------------------------------------------------

@app.post("/validate", response_model=ValidationResponse)
def validate_tiny_person(req: ValidationRequest):
    """
    Validates an agent (TinyPerson) by simulating an LLM-driven interview.
    Returns a 0.0–1.0 confidence score and a textual justification.
    """
    # 1) Lookup the agent from your agent registry
    agent = AGENT_REGISTRY.get(req.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{req.agent_name}' found.")

    # 2) Perform the validation
    score, justification = TinyPersonValidator.validate_person(
        person=agent,
        expectations=req.expectations,
        include_agent_spec=req.include_agent_spec,
        max_content_length=req.max_content_length
    )

    # 3) If the LLM conversation ended or validation failed, return an error
    if score is None:
        raise HTTPException(status_code=500, detail="Validation process failed or no score returned.")

    # 4) Otherwise, return the results
    return {"score": score, "justification": justification}

@app.get("/health")
def health_check():
    """
    Simple health-check endpoint.
    """
    return {"status": "up"}

