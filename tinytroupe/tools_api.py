from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json

# Adjust these imports to match your actual code organization.
# For example, from tinytroupe.tools import TinyTool, TinyCalendar, TinyWordProcessor
# from tinytroupe.agent import TinyPerson
# from tinytroupe.enrichment import TinyEnricher
# from tinytroupe.extraction import ArtifactExporter

from tools import TinyTool, TinyCalendar, TinyWordProcessor
from tinytroupe.agent import TinyPerson
from tinytroupe.enrichment import TinyEnricher
from tinytroupe.extraction import ArtifactExporter

app = FastAPI(title="TinyTroupe Tools API")

# ------------------------------------------------------------------------------
# 1) In-Memory Registry
# ------------------------------------------------------------------------------
TOOLS_REGISTRY = {}         # tool_id -> TinyTool instance
AGENTS_REGISTRY = {}        # agent_name -> TinyPerson
ENRICHERS_REGISTRY = {}     # enricher_id -> TinyEnricher
EXPORTERS_REGISTRY = {}     # exporter_id -> ArtifactExporter

# ------------------------------------------------------------------------------
# 2) Pydantic Models
# ------------------------------------------------------------------------------

class ToolCreateRequest(BaseModel):
    """
    Data needed to create a generic tool (or a specialized subclass).
    """
    tool_id: str = Field(..., description="Unique ID for this tool object.")
    tool_type: str = Field("generic", description="One of: 'generic', 'calendar', 'wordprocessor' (or others).")
    name: str = Field(..., description="Name of the tool.")
    description: str = Field("", description="Short description of the tool.")
    owner_name: Optional[str] = Field(None, description="Name of the agent who owns this tool.")
    real_world_side_effects: bool = Field(False, description="If true, tool can affect external state.")
    enricher_id: Optional[str] = Field(None, description="ID of a TinyEnricher to associate.")
    exporter_id: Optional[str] = Field(None, description="ID of an ArtifactExporter to associate.")

class ToolActionRequest(BaseModel):
    """
    Request to simulate an agent performing an action on a tool.
    """
    tool_id: str = Field(..., description="ID of the tool to act on.")
    agent_name: str = Field(..., description="Name of the agent performing the action.")
    action: Dict[str, Any] = Field(..., description="Action dictionary. E.g. {'type':'WRITE_DOCUMENT','content':'{\"title\":\"Foo\",...}' }")

# ------------------------------------------------------------------------------
# 3) Tool Management Endpoints
# ------------------------------------------------------------------------------

@app.post("/tools", summary="Create a new tool (TinyTool, TinyCalendar, or TinyWordProcessor)")
def create_tool(req: ToolCreateRequest):
    """
    Create and store a new tool object. 
    """
    if req.tool_id in TOOLS_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Tool '{req.tool_id}' already exists.")

    # (Optional) retrieve the associated owner, enricher, exporter, if any
    owner = None
    if req.owner_name:
        owner = AGENTS_REGISTRY.get(req.owner_name)
        if not owner:
            raise HTTPException(
                status_code=404,
                detail=f"No agent named '{req.owner_name}' found. Please register this agent first."
            )

    enricher = None
    if req.enricher_id:
        enricher = ENRICHERS_REGISTRY.get(req.enricher_id)
        if not enricher:
            raise HTTPException(
                status_code=404,
                detail=f"No enricher with ID '{req.enricher_id}' found."
            )

    exporter = None
    if req.exporter_id:
        exporter = EXPORTERS_REGISTRY.get(req.exporter_id)
        if not exporter:
            raise HTTPException(
                status_code=404,
                detail=f"No exporter with ID '{req.exporter_id}' found."
            )

    # Decide which tool subclass to instantiate
    if req.tool_type.lower() == "generic":
        tool = TinyTool(
            name=req.name,
            description=req.description,
            owner=owner,
            real_world_side_effects=req.real_world_side_effects,
            enricher=enricher,
            exporter=exporter
        )
    elif req.tool_type.lower() == "calendar":
        tool = TinyCalendar(owner=owner)
        # Overwrite the default name/description if provided:
        tool.name = req.name
        tool.description = req.description
    elif req.tool_type.lower() == "wordprocessor":
        tool = TinyWordProcessor(owner=owner, exporter=exporter, enricher=enricher)
        tool.name = req.name
        tool.description = req.description
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool_type: {req.tool_type}")

    # store in registry
    TOOLS_REGISTRY[req.tool_id] = tool

    return {"msg": f"Tool '{req.tool_id}' of type '{req.tool_type}' created successfully."}

@app.get("/tools")
def list_tools():
    """
    List all tool IDs in the registry.
    """
    return {"tool_ids": list(TOOLS_REGISTRY.keys())}

@app.get("/tools/{tool_id}")
def get_tool_info(tool_id: str):
    """
    Retrieve basic info about a tool (like its name, description, owner).
    """
    tool = TOOLS_REGISTRY.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"No tool with ID '{tool_id}' found.")

    owner_name = tool.owner.name if (tool.owner and hasattr(tool.owner, "name")) else None
    return {
        "tool_id": tool_id,
        "name": tool.name,
        "description": tool.description,
        "owner": owner_name,
        "real_world_side_effects": tool.real_world_side_effects,
        "class_type": type(tool).__name__
    }

@app.delete("/tools/{tool_id}")
def delete_tool(tool_id: str):
    """
    Delete a tool from memory.
    """
    tool = TOOLS_REGISTRY.pop(tool_id, None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"No tool with ID '{tool_id}' found.")
    return {"msg": f"Tool '{tool_id}' deleted."}

# ------------------------------------------------------------------------------
# 4) Tool Action Endpoint
# ------------------------------------------------------------------------------

@app.post("/tools/action", summary="Simulate an agent performing an action on a tool")
def tool_action(req: ToolActionRequest):
    """
    Let an agent (req.agent_name) perform an action on the specified tool.
    Action is a dict, for example:
      {
        "type": "WRITE_DOCUMENT",
        "content": "{\"title\": \"Foo\", \"content\": \"some text...\"}"
      }
    The tool's .process_action(...) method is invoked. If successful, returns True.
    """
    tool = TOOLS_REGISTRY.get(req.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"No tool with ID '{req.tool_id}' found.")
    
    agent = AGENTS_REGISTRY.get(req.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{req.agent_name}' found.")

    action = req.action
    # Example: action = {"type": "WRITE_DOCUMENT", "content": "JSON-encoded string..."}

    try:
        success = tool.process_action(agent, action)
        if success is None:
            # Some tools might return None for 'success' if the action didn't match
            return {"msg": f"Action type '{action.get('type')}' not handled by tool '{req.tool_id}'."}
        elif success is True:
            return {"msg": f"Action '{action.get('type')}' executed successfully on tool '{req.tool_id}'."}
        else:
            return {"msg": f"Action '{action.get('type')}' executed but returned {success}."}
    except ValueError as ve:
        # Possibly an ownership error or invalid field
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# 5) Optional: You might add endpoints to manage agents, enrichers, or exporters
#    if you want to dynamically create them from this same API.
# ------------------------------------------------------------------------------

# Example of a quick agent creation for testing (very minimal):
class AgentCreateRequest(BaseModel):
    agent_name: str
    # You could add more fields like occupation, age, etc.

@app.post("/agents")
def create_agent(req: AgentCreateRequest):
    if req.agent_name in AGENTS_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Agent '{req.agent_name}' already exists.")
    agent = TinyPerson(name=req.agent_name)
    AGENTS_REGISTRY[req.agent_name] = agent
    return {"msg": f"Agent '{req.agent_name}' created."}

#  ... similarly for enricher, exporter, etc.

# ------------------------------------------------------------------------------
# 6) Health Check
# ------------------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "up"}
