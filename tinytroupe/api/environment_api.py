from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

# Import the TinyWorld class and related logic from tinytroupe
# Adjust the import path if needed
from tinytroupe.environment import TinyWorld

app = FastAPI(title="TinyTroupe Environment API")

# ------------------------------------------------------------------------------
# In-memory "registry" for environments, keyed by name.
# You could store them differently if you prefer a database, etc.
# ------------------------------------------------------------------------------
ENV_REGISTRY = {}

# ------------------------------------------------------------------------------
# 1. Pydantic model(s) for Environment creation
# ------------------------------------------------------------------------------
class EnvironmentConfig(BaseModel):
    name: str = Field(..., description="The unique name of the environment.")
    description: Optional[str] = Field("", description="A short description of the environment.")
    # Add other environment-related fields if needed

# ------------------------------------------------------------------------------
# 2. CREATE Environment endpoint
# ------------------------------------------------------------------------------
@app.post("/environments")
def create_environment(config: EnvironmentConfig):
    """
    Create a new TinyWorld environment with a unique name.
    """
    if config.name in ENV_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Environment '{config.name}' already exists."
        )
    # Instantiate a TinyWorld (or your environment class)
    env = TinyWorld(name=config.name)

    # Optionally set some descriptive field if you have it on TinyWorld
    # e.g., env.description = config.description

    # Store in the registry
    ENV_REGISTRY[config.name] = env

    return {
        "msg": "Environment created",
        "name": config.name
    }

# ------------------------------------------------------------------------------
# 3. LIST Environments
# ------------------------------------------------------------------------------
@app.get("/environments")
def list_environments():
    """
    Return the list of all environment names currently in memory.
    """
    return {"environments": list(ENV_REGISTRY.keys())}

# ------------------------------------------------------------------------------
# 4. GET a Single Environment by Name
# ------------------------------------------------------------------------------
@app.get("/environments/{env_name}")
def get_environment(env_name: str):
    """
    Retrieve details about a single TinyWorld environment.
    """
    env = ENV_REGISTRY.get(env_name)
    if not env:
        raise HTTPException(
            status_code=404,
            detail=f"No environment named '{env_name}' found."
        )
    # Return any relevant info. Adjust as needed for your TinyWorld class.
    return {
        "name": env.name,
        # "description": env.description,  # if you added one
        "agents_present": [agent.name for agent in env.agents],  # Example if TinyWorld has `env.agents`
        # add other environment fields or state you want to expose
    }

# ------------------------------------------------------------------------------
# 5. DELETE Environment
# ------------------------------------------------------------------------------
@app.delete("/environments/{env_name}")
def delete_environment(env_name: str):
    """
    Delete a TinyWorld environment from the registry.
    """
    env = ENV_REGISTRY.pop(env_name, None)
    if not env:
        raise HTTPException(
            status_code=404,
            detail=f"No environment named '{env_name}' found."
        )
    return {"msg": f"Environment '{env_name}' deleted"}

# ------------------------------------------------------------------------------
# 6. Health Check
# ------------------------------------------------------------------------------
@app.get("/health")
def health_check():
    """
    A simple check to confirm the API is running.
    """
    return {"status": "up"}
