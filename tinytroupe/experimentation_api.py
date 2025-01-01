from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

# Import the classes from your experimentation code
# e.g. "from experiment import ABRandomizer, Intervention"
# Adjust this if your classes are in another file or package:
from experimentation import ABRandomizer, Intervention

app = FastAPI(title="TinyTroupe Experimentation API")

# ------------------------------------------------------------------------------
# 1) In-memory Registry for ABRandomizer Objects
#    We’ll store ABRandomizer instances keyed by an ID (string or int).
# ------------------------------------------------------------------------------
RANDOMIZERS: Dict[str, ABRandomizer] = {}

# Optionally, a global registry for Intervention objects, if desired:
INTERVENTIONS: Dict[str, Intervention] = {}

# ------------------------------------------------------------------------------
# 2) Pydantic Models for Request Bodies
# ------------------------------------------------------------------------------

class RandomizerCreateRequest(BaseModel):
    """
    Model for creating a new ABRandomizer with optional overrides.
    """
    real_name_1: str = Field("control", description="Real name of option 1")
    real_name_2: str = Field("treatment", description="Real name of option 2")
    blind_name_a: str = Field("A", description="Blind name for option 1")
    blind_name_b: str = Field("B", description="Blind name for option 2")
    passtrough_name: List[str] = Field(default_factory=list, description="List of names to skip randomization")
    random_seed: int = Field(42, description="Random seed for repeatable randomization")

class RandomizeRequest(BaseModel):
    """
    Model for calling the .randomize() method.
    """
    item_index: int = Field(..., description="Index of the item to randomize.")
    option_a: str = Field(..., description="First choice (string).")
    option_b: str = Field(..., description="Second choice (string).")

class DerandomizeRequest(BaseModel):
    """
    Model for calling the .derandomize() method.
    """
    item_index: int = Field(..., description="Index of the item to de-randomize.")
    option_a: str = Field(..., description="First choice (string).")
    option_b: str = Field(..., description="Second choice (string).")

class DerandomizeNameRequest(BaseModel):
    """
    Model for calling the .derandomize_name() method.
    """
    item_index: int = Field(..., description="Index of the item to de-randomize.")
    chosen_blind_name: str = Field(..., description="The blind name the user picked (e.g., 'A' or 'B').")

class InterventionCreateRequest(BaseModel):
    """
    Minimal model to create an Intervention object.
    For now, we’ll just store references to agent or environment by name/ID.
    """
    intervention_id: str = Field(..., description="Unique ID for this Intervention.")
    agent_name: Optional[str] = Field(None, description="Name of an agent to intervene on.")
    environment_name: Optional[str] = Field(None, description="Name of an environment to intervene on.")
    # We could add 'agents: List[str]' or 'environments: List[str]' for multiple

# ------------------------------------------------------------------------------
# 3) ABRandomizer Endpoints
# ------------------------------------------------------------------------------

@app.post("/randomizers", summary="Create a new ABRandomizer")
def create_randomizer(req: RandomizerCreateRequest, randomizer_id: str = "default"):
    """
    Create an ABRandomizer with the given configuration and store it under `randomizer_id`.
    """
    if randomizer_id in RANDOMIZERS:
        raise HTTPException(
            status_code=400,
            detail=f"Randomizer with ID '{randomizer_id}' already exists."
        )
    randomizer = ABRandomizer(
        real_name_1=req.real_name_1,
        real_name_2=req.real_name_2,
        blind_name_a=req.blind_name_a,
        blind_name_b=req.blind_name_b,
        passtrough_name=req.passtrough_name,
        random_seed=req.random_seed
    )
    RANDOMIZERS[randomizer_id] = randomizer
    return {"msg": f"ABRandomizer '{randomizer_id}' created."}

@app.post("/randomizers/{randomizer_id}/randomize")
def randomize_item(randomizer_id: str, data: RandomizeRequest):
    """
    Call randomize(item_index, option_a, option_b) on the specified ABRandomizer.
    Returns whichever choice ends up as the 'A' or 'B' after randomization.
    """
    r = RANDOMIZERS.get(randomizer_id)
    if not r:
        raise HTTPException(
            status_code=404,
            detail=f"No randomizer found with ID '{randomizer_id}'."
        )
    a_result, b_result = r.randomize(data.item_index, data.option_a, data.option_b)
    return {
        "msg": f"Randomized item {data.item_index} using randomizer '{randomizer_id}'",
        "result": [a_result, b_result]
    }

@app.post("/randomizers/{randomizer_id}/derandomize")
def derandomize_item(randomizer_id: str, data: DerandomizeRequest):
    """
    Call derandomize(item_index, option_a, option_b) on the specified ABRandomizer.
    Returns the original order before randomization.
    """
    r = RANDOMIZERS.get(randomizer_id)
    if not r:
        raise HTTPException(
            status_code=404,
            detail=f"No randomizer found with ID '{randomizer_id}'."
        )
    a_result, b_result = r.derandomize(data.item_index, data.option_a, data.option_b)
    return {
        "msg": f"Derandomized item {data.item_index} using randomizer '{randomizer_id}'",
        "result": [a_result, b_result]
    }

@app.post("/randomizers/{randomizer_id}/derandomize_name")
def derandomize_name(randomizer_id: str, data: DerandomizeNameRequest):
    """
    Call derandomize_name(item_index, chosen_blind_name) on the specified ABRandomizer.
    Returns the 'real' name for whichever blind name the user chose.
    """
    r = RANDOMIZERS.get(randomizer_id)
    if not r:
        raise HTTPException(
            status_code=404,
            detail=f"No randomizer found with ID '{randomizer_id}'."
        )
    real_name = r.derandomize_name(data.item_index, data.chosen_blind_name)
    return {
        "msg": f"Derandomized blind name '{data.chosen_blind_name}' for item {data.item_index}.",
        "real_name": real_name
    }

@app.get("/randomizers")
def list_randomizers():
    """
    List all ABRandomizer IDs in memory.
    """
    return {"randomizer_ids": list(RANDOMIZERS.keys())}

@app.delete("/randomizers/{randomizer_id}")
def delete_randomizer(randomizer_id: str):
    """
    Remove an ABRandomizer from memory.
    """
    if randomizer_id not in RANDOMIZERS:
        raise HTTPException(
            status_code=404,
            detail=f"No randomizer found with ID '{randomizer_id}'."
        )
    del RANDOMIZERS[randomizer_id]
    return {"msg": f"ABRandomizer '{randomizer_id}' deleted."}


# ------------------------------------------------------------------------------
# 4) Intervention Endpoints
#   Since Intervention is still under development, here's a minimal pattern.
# ------------------------------------------------------------------------------

@app.post("/interventions", summary="Create a new Intervention object")
def create_intervention(req: InterventionCreateRequest):
    """
    Create an Intervention with references to an agent or environment by name.
    For now, we won't deeply check agent/environment existence—just store the references.
    """
    if req.intervention_id in INTERVENTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Intervention with ID '{req.intervention_id}' already exists."
        )
    # Build the Intervention object
    # (We assume you're fetching TinyPerson / TinyWorld from elsewhere if needed)
    intervention = Intervention(
        agent=None,  # you'd look up the actual agent object if you have a registry
        environment=None
    )
    # Potentially store the agent_name, environment_name for later usage
    # or fetch the actual objects now if you have a global agent registry
    # e.g. intervention.agents = [some_global_agent_dict[req.agent_name]]

    INTERVENTIONS[req.intervention_id] = intervention
    return {"msg": f"Intervention '{req.intervention_id}' created."}

@app.get("/interventions")
def list_interventions():
    """
    List all Intervention IDs in memory.
    """
    return {"intervention_ids": list(INTERVENTIONS.keys())}

@app.get("/interventions/{intervention_id}")
def get_intervention(intervention_id: str):
    """
    Retrieve minimal info about a single Intervention.
    """
    itv = INTERVENTIONS.get(intervention_id)
    if not itv:
        raise HTTPException(
            status_code=404,
            detail=f"No intervention found with ID '{intervention_id}'."
        )
    # Return any relevant fields; note that Intervention code is incomplete
    return {
        "intervention_id": intervention_id,
        # "agents": [a.name for a in itv.agents] if itv.agents else None,
        # "environments": [e.name for e in itv.environments] if itv.environments else None
    }

@app.post("/interventions/{intervention_id}/apply")
def apply_intervention(intervention_id: str):
    """
    Apply the effect of an Intervention.
    NOTE: 'Intervention' is incomplete in the snippet, so this is just a demo.
    """
    itv = INTERVENTIONS.get(intervention_id)
    if not itv:
        raise HTTPException(
            status_code=404,
            detail=f"No intervention found with ID '{intervention_id}'."
        )
    try:
        # You’d typically call `itv.check_precondition()` and `itv.apply()`.
        # We'll assume .apply() is implemented
        itv.apply()  
        return {"msg": f"Intervention '{intervention_id}' applied successfully."}
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Intervention apply() not implemented yet."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/interventions/{intervention_id}")
def delete_intervention(intervention_id: str):
    """
    Remove an Intervention from memory.
    """
    if intervention_id not in INTERVENTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"No intervention found with ID '{intervention_id}'."
        )
    del INTERVENTIONS[intervention_id]
    return {"msg": f"Intervention '{intervention_id}' deleted."}


# ------------------------------------------------------------------------------
# 5) Health Check or Root
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "up"}
