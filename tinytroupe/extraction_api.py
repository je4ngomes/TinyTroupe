from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

# Import the relevant classes from your extraction module
# Adjust the import paths as needed to match your actual code structure.
from extraction import (
    ResultsExtractor, 
    ResultsReducer, 
    ArtifactExporter, 
    Normalizer,
    TinyPerson,        # Typically from tinytroupe.agent
    TinyWorld,         # Typically from tinytroupe.environment
    default_extractor  # example convenience instance
)

app = FastAPI(title="TinyTroupe Extraction API")

# ------------------------------------------------------------------------------
# 1) In-memory registries
# ------------------------------------------------------------------------------
EXTRACTORS: Dict[str, ResultsExtractor] = {}
REDUCERS: Dict[str, ResultsReducer] = {}
EXPORTERS: Dict[str, ArtifactExporter] = {}
NORMALIZERS: Dict[str, Normalizer] = {}

# Also, you'd need a place to fetch actual agents / worlds if you want to do real extractions:
AGENT_REGISTRY: Dict[str, TinyPerson] = {}
WORLD_REGISTRY: Dict[str, TinyWorld] = {}

# ------------------------------------------------------------------------------
# 2) Pydantic Models
# ------------------------------------------------------------------------------

class ExtractorCreateRequest(BaseModel):
    extraction_objective: str = Field(
        "The main points present in the agents' interactions history.",
        description="Default extraction objective to be used"
    )
    situation: str = Field(
        "", 
        description="Default situation to consider"
    )
    fields: Optional[List[str]] = Field(
        None, 
        description="List of default fields to extract"
    )
    fields_hints: Optional[Dict[str, str]] = Field(
        None, 
        description="Default hints for the fields"
    )
    verbose: bool = Field(
        False, 
        description="Whether to print debug messages by default"
    )

class AgentExtractionRequest(BaseModel):
    extractor_id: str = Field(..., description="ID of the ResultsExtractor to use.")
    agent_name: str = Field(..., description="Name of the agent from which to extract data.")
    extraction_objective: Optional[str] = None
    situation: Optional[str] = None
    fields: Optional[List[str]] = None
    fields_hints: Optional[Dict[str, str]] = None
    verbose: Optional[bool] = None

class WorldExtractionRequest(BaseModel):
    extractor_id: str = Field(..., description="ID of the ResultsExtractor to use.")
    world_name: str = Field(..., description="Name of the TinyWorld from which to extract data.")
    extraction_objective: Optional[str] = None
    situation: Optional[str] = None
    fields: Optional[List[str]] = None
    fields_hints: Optional[Dict[str, str]] = None
    verbose: Optional[bool] = None

class ReducerCreateRequest(BaseModel):
    pass  # In this simple example, we don’t require initial data

class ReductionRuleRequest(BaseModel):
    reducer_id: str = Field(..., description="Which ResultsReducer to modify.")
    trigger: str = Field(..., description="Stimulus/action type to match (e.g., 'VISUAL', 'SAY', etc.).")

class ReduceAgentRequest(BaseModel):
    reducer_id: str = Field(..., description="ID of the ResultsReducer.")
    agent_name: str = Field(..., description="Agent name to reduce.")

class ExporterCreateRequest(BaseModel):
    base_output_folder: str = Field(
        "./exports", 
        description="The base folder where artifacts will be exported."
    )

class ExportArtifactRequest(BaseModel):
    exporter_id: str = Field(..., description="ID of the ArtifactExporter.")
    artifact_name: str
    artifact_data: Union[str, Dict[str, Any]]
    content_type: str
    content_format: Optional[str] = None
    target_format: str = Field("txt", description="txt, md, docx, json, etc.")
    verbose: bool = False

class NormalizerCreateRequest(BaseModel):
    elements: List[str] = Field(..., description="Elements to cluster or categorize.")
    n: int = Field(..., description="How many normalized categories we want.")
    verbose: bool = Field(False, description="If true, debug logs are printed.")

class NormalizeRequest(BaseModel):
    normalizer_id: str = Field(..., description="ID of the Normalizer.")
    items: Union[str, List[str]] = Field(..., description="Text(s) to normalize.")


# ------------------------------------------------------------------------------
# 3) ResultsExtractor Endpoints
# ------------------------------------------------------------------------------

@app.post("/extractors", summary="Create a new ResultsExtractor")
def create_extractor(req: ExtractorCreateRequest, extractor_id: str = "default"):
    """
    Create a new ResultsExtractor and store it by `extractor_id`.
    """
    if extractor_id in EXTRACTORS:
        raise HTTPException(status_code=400, detail=f"Extractor '{extractor_id}' already exists.")

    extractor = ResultsExtractor(
        extraction_prompt_template_path=None,  # or path to your mustache template
        extraction_objective=req.extraction_objective,
        situation=req.situation,
        fields=req.fields,
        fields_hints=req.fields_hints,
        verbose=req.verbose
    )
    EXTRACTORS[extractor_id] = extractor
    return {"msg": f"Extractor '{extractor_id}' created."}


@app.get("/extractors")
def list_extractors():
    return {"extractor_ids": list(EXTRACTORS.keys())}


@app.post("/extractors/extract-agent")
def extract_from_agent(data: AgentExtractionRequest):
    """
    Use a ResultsExtractor to extract results from a single TinyPerson agent.
    """
    extractor = EXTRACTORS.get(data.extractor_id)
    if not extractor:
        raise HTTPException(status_code=404, detail=f"No extractor '{data.extractor_id}' found.")
    agent = AGENT_REGISTRY.get(data.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{data.agent_name}' found.")

    result = extractor.extract_results_from_agent(
        tinyperson=agent,
        extraction_objective=data.extraction_objective,
        situation=data.situation,
        fields=data.fields,
        fields_hints=data.fields_hints,
        verbose=data.verbose
    )
    return {
        "msg": f"Extraction from agent '{data.agent_name}' completed.",
        "result": result
    }


@app.post("/extractors/extract-agents")
def extract_from_agents(data: AgentExtractionRequest):
    """
    Use a ResultsExtractor to extract results from multiple agents (same config).
    """
    extractor = EXTRACTORS.get(data.extractor_id)
    if not extractor:
        raise HTTPException(status_code=404, detail=f"No extractor '{data.extractor_id}' found.")

    # For this example, you might pass a list of agents.  
    # We'll just show how you might do a single agent name or a stub for multiple.
    # In a real scenario, you’d pass a list of agent names.
    agent_names = [data.agent_name]  # Example: single
    agents = []
    for name in agent_names:
        if name not in AGENT_REGISTRY:
            raise HTTPException(status_code=404, detail=f"No agent '{name}' found.")
        agents.append(AGENT_REGISTRY[name])

    results = extractor.extract_results_from_agents(
        agents=agents,
        extraction_objective=data.extraction_objective,
        situation=data.situation,
        fields=data.fields,
        fields_hints=data.fields_hints,
        verbose=data.verbose
    )
    return {
        "msg": "Extraction from multiple agents completed.",
        "results": results
    }


@app.post("/extractors/extract-world")
def extract_from_world(data: WorldExtractionRequest):
    """
    Use a ResultsExtractor to extract results from a TinyWorld instance.
    """
    extractor = EXTRACTORS.get(data.extractor_id)
    if not extractor:
        raise HTTPException(status_code=404, detail=f"No extractor '{data.extractor_id}' found.")
    world = WORLD_REGISTRY.get(data.world_name)
    if not world:
        raise HTTPException(status_code=404, detail=f"No world named '{data.world_name}' found.")

    result = extractor.extract_results_from_world(
        tinyworld=world,
        extraction_objective=data.extraction_objective,
        situation=data.situation,
        fields=data.fields,
        fields_hints=data.fields_hints,
        verbose=data.verbose
    )
    return {
        "msg": f"Extraction from world '{data.world_name}' completed.",
        "result": result
    }


@app.post("/extractors/{extractor_id}/save-json")
def extractor_save_json(extractor_id: str, filename: str = "extraction_results.json", verbose: bool = False):
    """
    Instruct the specified extractor to save its last cached agent/world extractions to a JSON file.
    """
    extractor = EXTRACTORS.get(extractor_id)
    if not extractor:
        raise HTTPException(status_code=404, detail=f"No extractor '{extractor_id}' found.")

    extractor.save_as_json(filename, verbose=verbose)
    return {"msg": f"Extractor '{extractor_id}' saved extraction to '{filename}'."}


# ------------------------------------------------------------------------------
# 4) ResultsReducer Endpoints
# ------------------------------------------------------------------------------

@app.post("/reducers", summary="Create a new ResultsReducer")
def create_reducer(req: ReducerCreateRequest, reducer_id: str = "default"):
    """
    Create a new ResultsReducer and store it by `reducer_id`.
    """
    if reducer_id in REDUCERS:
        raise HTTPException(status_code=400, detail=f"Reducer '{reducer_id}' already exists.")
    reducer = ResultsReducer()
    REDUCERS[reducer_id] = reducer
    return {"msg": f"Reducer '{reducer_id}' created."}


@app.get("/reducers")
def list_reducers():
    return {"reducer_ids": list(REDUCERS.keys())}


class ReductionRuleFunctionRequest(BaseModel):
    reducer_id: str
    trigger: str
    # We'll simulate a tiny Python code snippet or a descriptive text.
    # In practice, you might store a function reference or dynamically load it.
    # For now, let's keep it a simple placeholder string.
    function_description: str

@app.post("/reducers/add-rule")
def add_reduction_rule(req: ReductionRuleFunctionRequest):
    """
    Add a custom rule to the ResultsReducer.
    In a real scenario, you'd store an actual Python function or callable.
    Here we just store a placeholder lambda or something similar.
    """
    reducer = REDUCERS.get(req.reducer_id)
    if not reducer:
        raise HTTPException(status_code=404, detail=f"No reducer '{req.reducer_id}' found.")

    if req.trigger in reducer.rules:
        raise HTTPException(status_code=400, detail=f"Rule for trigger '{req.trigger}' already exists.")

    # Example: we create a dummy function. 
    # In a real scenario, you might parse or compile the user’s function_description.
    def dummy_rule(**kwargs):
        # do something with kwargs
        return {
            "kind": kwargs.get("kind"),
            "event": kwargs.get("event"),
            "content": kwargs.get("content"),
            "source": kwargs.get("source_agent").name if kwargs.get("source_agent") else None,
            "target": kwargs.get("target_agent").name if kwargs.get("target_agent") else None
        }

    reducer.add_reduction_rule(req.trigger, dummy_rule)
    return {"msg": f"Rule for trigger '{req.trigger}' added to reducer '{req.reducer_id}'."}


@app.post("/reducers/reduce-agent")
def reduce_agent_stimuli(req: ReduceAgentRequest):
    """
    Use a ResultsReducer to parse an agent's memory and produce a simplified structure.
    """
    reducer = REDUCERS.get(req.reducer_id)
    if not reducer:
        raise HTTPException(status_code=404, detail=f"No reducer '{req.reducer_id}' found.")

    agent = AGENT_REGISTRY.get(req.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent '{req.agent_name}' found.")

    reduced_data = reducer.reduce_agent(agent)
    return {
        "msg": f"Reducer '{req.reducer_id}' produced reduced data for agent '{req.agent_name}'.",
        "data": reduced_data
    }

# ------------------------------------------------------------------------------
# 5) ArtifactExporter Endpoints
# ------------------------------------------------------------------------------

@app.post("/exporters", summary="Create a new ArtifactExporter")
def create_exporter(req: ExporterCreateRequest, exporter_id: str = "default"):
    """
    Create an ArtifactExporter with the specified base output folder.
    """
    if exporter_id in EXPORTERS:
        raise HTTPException(status_code=400, detail=f"Exporter '{exporter_id}' already exists.")
    exporter = ArtifactExporter(req.base_output_folder)
    EXPORTERS[exporter_id] = exporter
    return {"msg": f"Exporter '{exporter_id}' created at folder '{req.base_output_folder}'."}


@app.get("/exporters")
def list_exporters():
    return {"exporter_ids": list(EXPORTERS.keys())}


@app.post("/exporters/export")
def export_artifact(req: ExportArtifactRequest):
    """
    Export artifact_data to a file with the chosen format (txt, md, docx, json, etc.).
    """
    exporter = EXPORTERS.get(req.exporter_id)
    if not exporter:
        raise HTTPException(status_code=404, detail=f"No exporter '{req.exporter_id}' found.")

    try:
        exporter.export(
            artifact_name=req.artifact_name,
            artifact_data=req.artifact_data,
            content_type=req.content_type,
            content_format=req.content_format,
            target_format=req.target_format,
            verbose=req.verbose
        )
        return {"msg": f"Artifact '{req.artifact_name}' exported as {req.target_format}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------------------
# 6) Normalizer Endpoints
# ------------------------------------------------------------------------------

@app.post("/normalizers", summary="Create a new Normalizer")
def create_normalizer(req: NormalizerCreateRequest, normalizer_id: str = "default"):
    """
    Create a Normalizer object that groups the given elements into n categories.
    """
    if normalizer_id in NORMALIZERS:
        raise HTTPException(status_code=400, detail=f"Normalizer '{normalizer_id}' already exists.")
    normalizer = Normalizer(req.elements, req.n, verbose=req.verbose)
    NORMALIZERS[normalizer_id] = normalizer
    return {"msg": f"Normalizer '{normalizer_id}' created."}


@app.get("/normalizers")
def list_normalizers():
    return {"normalizer_ids": list(NORMALIZERS.keys())}


@app.post("/normalizers/normalize")
def normalize_items(data: NormalizeRequest):
    """
    Use a Normalizer to map the provided items (strings) to their normalized forms.
    """
    normalizer = NORMALIZERS.get(data.normalizer_id)
    if not normalizer:
        raise HTTPException(status_code=404, detail=f"No normalizer '{data.normalizer_id}' found.")
    result = normalizer.normalize(data.items)
    return {
        "msg": f"Normalized with '{data.normalizer_id}'.",
        "normalized_result": result
    }


# ------------------------------------------------------------------------------
# 7) Health Check
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "up"}
