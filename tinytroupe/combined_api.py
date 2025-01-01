"""
A single FastAPI app that combines multiple modules:
 - Agent API
 - Control API
 - Enrichment API
 - Environment API
 - Examples API
 - Experimentation API
 - Extraction API
 - Factory API
 - OpenAI Utils API
 - Profiling API
 - Story API
 - Tools API
 - Utils API
 - Validation API

All endpoints are included in sub-routers with unique prefixes.
"""

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

import logging
logger = logging.getLogger("tinytroupe")


###############################################################################
# 0) SHARED / GLOBAL REGISTRIES (if you want truly shared references)
###############################################################################
# For example, if the agent or environment references are truly global:
AGENT_REGISTRY = {}      # e.g. agent_name -> TinyPerson object
ENV_REGISTRY = {}        # e.g. environment_name -> TinyWorld object
FACTORIES = {}           # e.g. factory_id -> TinyFactory
TOOLS_REGISTRY = {}      # e.g. tool_id -> TinyTool
EXTRACTORS = {}          # e.g. extractor_id -> ResultsExtractor
REDUCERS = {}            # e.g. reducer_id -> ResultsReducer
EXPORTERS = {}           # e.g. exporter_id -> ArtifactExporter
NORMALIZERS = {}         # e.g. normalizer_id -> Normalizer
RANDOMIZERS = {}         # e.g. randomizer_id -> ABRandomizer
INTERVENTIONS = {}       # e.g. intervention_id -> Intervention

# The following are placeholders, referencing the classes from your modules:
# from agent import TinyPerson
# from control import begin, end, checkpoint, reset, current_simulation, cache_hits, cache_misses
# from enrichment import TinyEnricher
# from tinytroupe.environment import TinyWorld
# from experimentation import ABRandomizer, Intervention
# from extraction import (ResultsExtractor, ResultsReducer, ArtifactExporter, Normalizer, default_extractor)
# from factory import TinyFactory, TinyPersonFactory
# from openai_utils import (client, force_api_type, force_api_cache, LLMRequest, register_client, _api_type_to_client)
# from profiling import Profiler
# from story import TinyStory
# from tools import TinyTool, TinyCalendar, TinyWordProcessor
# from utils import (
#     extract_json, extract_code_block, dedent, compose_initial_LLM_messages_with_templates,
#     check_valid_fields, truncate_actions_or_stimuli, fresh_id
# )
# from validator import TinyPersonValidator
#
# Adjust all above imports accordingly to your actual code structure.

###############################################################################
# 1) AGENT API
###############################################################################
agent_router = APIRouter(prefix="/agents", tags=["Agent"])

class CreateAgentConfig(BaseModel):
    name: str
    age: Optional[int] = None
    nationality: Optional[str] = None
    country_of_residence: Optional[str] = None
    occupation: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    professional_interests: Optional[List[str]] = None
    personal_interests: Optional[List[str]] = None

class StimulusConfig(BaseModel):
    content: str
    source: Optional[str] = None

class ActConfig(BaseModel):
    until_done: bool = True
    n: Optional[int] = None
    return_actions: bool = True

class MoveConfig(BaseModel):
    location: str
    context: Optional[List[str]] = []

@agent_router.post("/create")
def create_agent(config: CreateAgentConfig):
    """
    Example: create new TinyPerson agent and store it in the registry
    """
    # if TinyPerson.has_agent(config.name):
    #     raise HTTPException(status_code=400, detail=f"Agent '{config.name}' already exists.")
    #
    # agent = TinyPerson(name=config.name)
    # if config.age is not None:
    #     agent.define("age", config.age)
    # ...
    # For illustration, store a dict in AGENT_REGISTRY:
    if config.name in AGENT_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Agent '{config.name}' already exists.")
    AGENT_REGISTRY[config.name] = dict(config)
    return {"msg": f"Agent '{config.name}' created successfully."}

@agent_router.get("/")
def list_agents():
    """Get a list of all agent names."""
    return {"agents": list(AGENT_REGISTRY.keys())}

@agent_router.get("/{agent_name}")
def get_agent_info(agent_name: str):
    """Get info about a specific agent."""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    return AGENT_REGISTRY[agent_name]

@agent_router.post("/{agent_name}/listen")
def agent_listen(agent_name: str, stim: StimulusConfig):
    """
    Make an agent 'listen' to some speech input (example).
    """
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    # agent.listen(stim.content, source=stim.source)
    return {"msg": f"Agent '{agent_name}' listened."}

@agent_router.post("/{agent_name}/act")
def agent_act(agent_name: str, config: ActConfig):
    """Make an agent perform actions. Return actions if requested."""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    # ...
    actions = ["action1", "action2"] if config.return_actions else []
    return {"msg": f"Agent '{agent_name}' acted.", "actions": actions}

@agent_router.post("/{agent_name}/move")
def agent_move(agent_name: str, move_data: MoveConfig):
    """Move an agent to a new location, optionally updating context."""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    return {
        "msg": f"Agent '{agent_name}' moved to '{move_data.location}' with context {move_data.context}."
    }

@agent_router.get("/{agent_name}/minibio")
def get_agent_minibio(agent_name: str, extended: bool = True):
    """Return the agent's mini-biography."""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    return {"minibio": f"{agent_name} is a placeholder."}

@agent_router.post("/{agent_name}/define")
def define_agent_property(agent_name: str, key: str, value: str):
    """Define or override a config property in the agent's dictionary."""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    AGENT_REGISTRY[agent_name][key] = value
    return {"msg": f"Set '{key}' = '{value}' for agent '{agent_name}'."}

@agent_router.post("/{agent_name}/delete")
def delete_agent(agent_name: str):
    """Remove an agent from the global registry."""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    del AGENT_REGISTRY[agent_name]
    return {"msg": f"Agent '{agent_name}' has been deleted."}


###############################################################################
# 2) CONTROL API
###############################################################################
control_router = APIRouter(prefix="/control", tags=["Control"])

@control_router.post("/begin")
def begin_endpoint(sim_id: str = "default", cache_path: Optional[str] = None, auto_checkpoint: bool = False):
    """Example 'begin' function from control."""
    return {"msg": "Simulation started", "simulation_id": sim_id}

@control_router.post("/end")
def end_endpoint(sim_id: str = "default"):
    """Example 'end' function from control."""
    return {"msg": "Simulation ended", "simulation_id": sim_id}

@control_router.post("/checkpoint")
def checkpoint_endpoint(sim_id: str = "default"):
    """Manually checkpoint."""
    return {"msg": f"Checkpoint saved for sim '{sim_id}'"}

@control_router.post("/reset")
def reset_endpoint():
    """Reset the entire simulation control state."""
    return {"msg": "System reset. No simulation is active now."}

@control_router.get("/cache-stats")
def cache_stats(sim_id: str = "default"):
    """Show how many cache hits/misses have occurred."""
    return {"simulation_id": sim_id, "hits": 10, "misses": 2}

@control_router.get("/current-simulation")
def get_current_simulation():
    """Return info about the currently active simulation."""
    return {"current_simulation": None}

###############################################################################
# 3) ENRICHMENT API
###############################################################################
enrichment_router = APIRouter(prefix="/enrichment", tags=["Enrichment"])

class EnrichmentRequest(BaseModel):
    requirements: str
    content: str
    content_type: Optional[str] = None
    context_info: Optional[str] = ""
    context_cache: Optional[List[str]] = None
    verbose: bool = False

@enrichment_router.post("/enrich")
def enrich_content_api(req: EnrichmentRequest):
    """Call TinyEnricher.enrich_content(...)"""
    # result = tiny_enricher.enrich_content(...)
    result = "Enriched content placeholder"
    return {"msg": "Enrichment successful.", "result": result}


###############################################################################
# 4) ENVIRONMENT API
###############################################################################
environment_router = APIRouter(prefix="/environment", tags=["Environment"])

class EnvironmentConfig(BaseModel):
    name: str
    description: Optional[str] = ""

@environment_router.post("/")
def create_environment(config: EnvironmentConfig):
    """Create a new environment."""
    if config.name in ENV_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Environment '{config.name}' already exists.")
    ENV_REGISTRY[config.name] = dict(config)
    return {"msg": "Environment created", "name": config.name}

@environment_router.get("/")
def list_environments():
    """Return the list of environment names."""
    return {"environments": list(ENV_REGISTRY.keys())}

@environment_router.get("/{env_name}")
def get_environment(env_name: str):
    """Retrieve details about a single environment."""
    env = ENV_REGISTRY.get(env_name)
    if not env:
        raise HTTPException(status_code=404, detail=f"No environment '{env_name}' found.")
    return env

@environment_router.delete("/{env_name}")
def delete_environment(env_name: str):
    """Delete a specific environment."""
    if env_name not in ENV_REGISTRY:
        raise HTTPException(status_code=404, detail=f"No environment '{env_name}' found.")
    del ENV_REGISTRY[env_name]
    return {"msg": f"Environment '{env_name}' deleted."}

###############################################################################
# 5) EXAMPLES API
###############################################################################
examples_router = APIRouter(prefix="/examples", tags=["Examples"])

@examples_router.get("/oscar")
def get_oscar_example():
    """Example route returning 'Oscar the Architect' persona."""
    return {"name": "Oscar the Architect", "role": "Architect"}


###############################################################################
# 6) EXPERIMENTATION API
###############################################################################
experimentation_router = APIRouter(prefix="/experimentation", tags=["Experimentation"])

@experimentation_router.post("/randomizers")
def create_randomizer(randomizer_id: str = "default"):
    """Create an ABRandomizer with default settings (example)."""
    if randomizer_id in RANDOMIZERS:
        raise HTTPException(status_code=400, detail=f"Randomizer '{randomizer_id}' already exists.")
    # randomizer = ABRandomizer(...)
    RANDOMIZERS[randomizer_id] = "placeholder randomizer"
    return {"msg": f"ABRandomizer '{randomizer_id}' created."}


###############################################################################
# 7) EXTRACTION API
###############################################################################
extraction_router = APIRouter(prefix="/extraction", tags=["Extraction"])

@extraction_router.post("/extract")
def extract_results():
    """Example from extraction api code."""
    return {"msg": "Extracted results."}


###############################################################################
# 8) FACTORY API
###############################################################################
factory_router = APIRouter(prefix="/factory", tags=["Factory"])

@factory_router.post("/person")
def create_person_factory(factory_id: str = "default", context_text: str = "Some context"):
    """Create a TinyPersonFactory and store it under factory_id."""
    if factory_id in FACTORIES:
        raise HTTPException(status_code=400, detail=f"Factory '{factory_id}' already exists.")
    # factory = TinyPersonFactory(context_text=context_text)
    FACTORIES[factory_id] = f"PersonFactory with context '{context_text}'"
    return {"msg": f"TinyPersonFactory '{factory_id}' created.", "context_text": context_text}


###############################################################################
# 9) OPENAI UTILS API
###############################################################################
openai_utils_router = APIRouter(prefix="/openai-utils", tags=["OpenAI Utils"])

@openai_utils_router.post("/chat-completion")
def chat_completion():
    """Example from openai_utils_api"""
    return {"response": "openai chat result placeholder"}


###############################################################################
# 10) PROFILING API
###############################################################################
profiling_router = APIRouter(prefix="/profiling", tags=["Profiling"])

@profiling_router.post("/profile")
def profile_agents():
    """Example from profiling api."""
    return {"msg": "Agents profiled."}


###############################################################################
# 11) STORY API
###############################################################################
story_router = APIRouter(prefix="/story", tags=["Story"])

@story_router.post("/start")
def start_story():
    """Example from story api."""
    return {"msg": "Story started."}


###############################################################################
# 12) TOOLS API
###############################################################################
tools_router = APIRouter(prefix="/tools", tags=["Tools"])

@tools_router.post("/action")
def tool_action():
    """Example from tools api."""
    return {"msg": "Tool action performed."}


###############################################################################
# 13) UTILS API
###############################################################################
utils_router = APIRouter(prefix="/utils", tags=["Utils"])

class ExtractJsonRequest(BaseModel):
    text: str

@utils_router.post("/extract-json")
def api_extract_json(req: ExtractJsonRequest):
    """Extract JSON from text placeholder."""
    # result = extract_json(req.text)
    return {"extracted": {"foo": "bar"}}

@utils_router.get("/fresh-id")
def api_fresh_id():
    """Return a new incremental ID."""
    # new_id = fresh_id()
    new_id = 123  # placeholder
    return {"fresh_id": new_id}


###############################################################################
# 14) VALIDATION API
###############################################################################
validation_router = APIRouter(prefix="/validation", tags=["Validation"])

class ValidationRequest(BaseModel):
    agent_name: str
    expectations: Optional[str] = None
    include_agent_spec: bool = False
    max_content_length: int = 1024

class ValidationResponse(BaseModel):
    score: float
    justification: str

@validation_router.post("/", response_model=ValidationResponse)
def validate_tiny_person(req: ValidationRequest):
    """Validate an agent via TinyPersonValidator."""
    # score, justification = TinyPersonValidator.validate_person(...)
    return ValidationResponse(score=0.89, justification="placeholder reasoning")


###############################################################################
# Main Combined FastAPI App
###############################################################################
app = FastAPI(title="TinyTroupe Combined API")

# Include all sub-routers with their unique prefixes
app.include_router(agent_router)
app.include_router(control_router)
app.include_router(enrichment_router)
app.include_router(environment_router)
app.include_router(examples_router)
app.include_router(experimentation_router)
app.include_router(extraction_router)
app.include_router(factory_router)
app.include_router(openai_utils_router)
app.include_router(profiling_router)
app.include_router(story_router)
app.include_router(tools_router)
app.include_router(utils_router)
app.include_router(validation_router)

@app.get("/health")
def health_check():
    """Global health-check endpoint."""
    return {"status": "up"}
