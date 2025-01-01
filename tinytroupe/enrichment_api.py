from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

# Import TinyEnricher and dependencies
# Adjust the import path to match your actual folder structure
from enrichment import TinyEnricher

app = FastAPI(title="TinyTroupe Enrichment API")

# ------------------------------------------------------------------------------
# 1. A Pydantic model for the request body
# ------------------------------------------------------------------------------
class EnrichmentRequest(BaseModel):
    requirements: str = Field(..., description="Requirements for the enrichment process.")
    content: str = Field(..., description="The raw text or data to be enriched.")
    content_type: Optional[str] = Field(None, description="Type or format of the content. (optional)")
    context_info: Optional[str] = Field("", description="Additional context. (optional)")
    context_cache: Optional[List[str]] = Field(None, description="A list of past results or context strings. (optional)")
    verbose: bool = Field(False, description="If True, prints debugging info.")

# ------------------------------------------------------------------------------
# 2. Instantiate a single TinyEnricher (or multiple if needed)
# ------------------------------------------------------------------------------
tiny_enricher = TinyEnricher(use_past_results_in_context=True)

# ------------------------------------------------------------------------------
# 3. Define the enrichment endpoint
# ------------------------------------------------------------------------------
@app.post("/enrich")
def enrich_content_api(req: EnrichmentRequest):
    """
    Enrich content by calling TinyEnricher.enrich_content().
    Submit requirements, content, type, context, etc.
    """
    try:
        result = tiny_enricher.enrich_content(
            requirements=req.requirements,
            content=req.content,
            content_type=req.content_type,
            context_info=req.context_info,
            context_cache=req.context_cache,
            verbose=req.verbose
        )
        if not result:
            return {"msg": "No result from enrichment.", "result": None}
        else:
            return {"msg": "Enrichment successful.", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# 4. Health Check
# ------------------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "up"}
