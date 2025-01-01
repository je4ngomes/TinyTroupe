from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# 1) Import the main classes/functions from agent.py
#    In this snippet, we assume agent.py is in the same directory.
#    If it's in a sub-package, adjust the import accordingly.
from agent import TinyPerson

app = FastAPI(title="TinyTroupe Agent API")

# -----------------------------------------------------------------------------
# 2) Pydantic models for request bodies
# -----------------------------------------------------------------------------
class CreateAgentConfig(BaseModel):
    """Data required to create a new TinyPerson."""
    name: str
    age: Optional[int] = None
    nationality: Optional[str] = None
    country_of_residence: Optional[str] = None
    occupation: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    professional_interests: Optional[List[str]] = None
    personal_interests: Optional[List[str]] = None

class StimulusConfig(BaseModel):
    """Data for stimuli like 'listen', 'see', 'socialize', etc."""
    content: str
    source: Optional[str] = None

class ActConfig(BaseModel):
    """Options to control the act() method."""
    until_done: bool = True
    n: Optional[int] = None
    return_actions: bool = True

class MoveConfig(BaseModel):
    """Data for move_to() method."""
    location: str
    context: Optional[List[str]] = []

# -----------------------------------------------------------------------------
# 3) Endpoints
# -----------------------------------------------------------------------------

@app.post("/agents/create")
def create_agent(config: CreateAgentConfig):
    """
    Create a new TinyPerson agent and store it in the global registry.
    """
    if TinyPerson.has_agent(config.name):
        raise HTTPException(
            status_code=400, 
            detail=f"Agent with name '{config.name}' already exists."
        )
    
    # Create the agent with minimal required info (only name is strictly required)
    agent = TinyPerson(name=config.name)

    # Optionally define some key fields
    if config.age is not None:
        agent.define("age", config.age)
    if config.nationality is not None:
        agent.define("nationality", config.nationality)
    if config.country_of_residence is not None:
        agent.define("country_of_residence", config.country_of_residence)
    if config.occupation is not None:
        agent.define("occupation", config.occupation)
    if config.personality_traits:
        agent.define("personality_traits", config.personality_traits)
    if config.professional_interests:
        agent.define("professional_interests", config.professional_interests)
    if config.personal_interests:
        agent.define("personal_interests", config.personal_interests)

    return {"msg": f"Agent '{config.name}' created successfully."}


@app.get("/agents")
def list_agents():
    """
    Get a list of all agent names in the global registry.
    """
    return {"agents": TinyPerson.all_agents_names()}


@app.get("/agents/{agent_name}")
def get_agent_info(agent_name: str):
    """
    Get high-level info about a specific agent.
    """
    agent = TinyPerson.get_agent_by_name(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    
    # Could return a partial or full config. Here’s a minimal example:
    return {
        "name": agent.name,
        "current_location": agent._configuration.get("current_location"),
        "current_context": agent._configuration.get("current_context"),
        "age": agent._configuration.get("age"),
        "occupation": agent._configuration.get("occupation"),
        "personality_traits": agent._configuration.get("personality_traits"),
        "professional_interests": agent._configuration.get("professional_interests"),
        "personal_interests": agent._configuration.get("personal_interests"),
    }


@app.post("/agents/{agent_name}/listen")
def agent_listen(agent_name: str, stim: StimulusConfig):
    """
    Make an agent 'listen' to some speech input.
    """
    agent = TinyPerson.get_agent_by_name(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")

    agent.listen(stim.content, source=stim.source)
    return {"msg": f"Agent '{agent_name}' listened to input."}


@app.post("/agents/{agent_name}/act")
def agent_act(agent_name: str, config: ActConfig):
    """
    Make an agent perform actions (act) until done or for n steps.
    Return the actions if requested.
    """
    agent = TinyPerson.get_agent_by_name(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")

    actions = agent.act(
        until_done=config.until_done,
        n=config.n,
        return_actions=config.return_actions
    )

    if config.return_actions:
        return {"msg": f"Agent '{agent_name}' acted.", "actions": actions}
    else:
        return {"msg": f"Agent '{agent_name}' acted."}


@app.post("/agents/{agent_name}/move")
def agent_move(agent_name: str, move_data: MoveConfig):
    """
    Move an agent to a new location, optionally updating context.
    """
    agent = TinyPerson.get_agent_by_name(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")

    agent.move_to(move_data.location, context=move_data.context)
    return {
        "msg": f"Agent '{agent_name}' moved to '{move_data.location}' with context {move_data.context}."
    }


@app.get("/agents/{agent_name}/minibio")
def get_agent_minibio(agent_name: str, extended: bool = True):
    """
    Return the agent's mini-biography.
    """
    agent = TinyPerson.get_agent_by_name(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")

    bio = agent.minibio(extended=extended)
    return {"minibio": bio}


@app.post("/agents/{agent_name}/define")
def define_agent_property(agent_name: str, key: str, value: str):
    """
    Define or override a config property in the agent's _configuration dict.
    Example: POST /agents/bob/define?key=occupation&value=Chef
    """
    agent = TinyPerson.get_agent_by_name(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    
    agent.define(key, value)
    return {
        "msg": f"Set '{key}' = '{value}' for agent '{agent_name}'."
    }


@app.post("/agents/{agent_name}/delete")
def delete_agent(agent_name: str):
    """
    Remove an agent entirely from the global registry (if you want a 'delete' operation).
    """
    agent = TinyPerson.get_agent_by_name(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent named '{agent_name}' found.")
    
    # We can simply remove it from the global dictionary:
    del TinyPerson.all_agents[agent_name]
    return {"msg": f"Agent '{agent_name}' has been deleted."}


@app.get("/health")
def health_check():
    return {"status": "up"}
