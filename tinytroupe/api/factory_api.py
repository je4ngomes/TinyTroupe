from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

# Adjust imports to match your project structure:
#   e.g. `from tinytroupe.factory import TinyFactory, TinyPersonFactory`
#   or `from factory import TinyFactory, TinyPersonFactory`
from factory import TinyFactory, TinyPersonFactory
from tinytroupe.agent import TinyPerson

app = FastAPI(title="TinyTroupe Factory API")

# ------------------------------------------------------------------------------
# 1) In-memory Registry
#    We’ll store all factories keyed by an ID (string).
#    This is in addition to TinyFactory.all_factories, which tracks by factory.name.
# ------------------------------------------------------------------------------
FACTORIES = {}

# ------------------------------------------------------------------------------
# 2) Pydantic Models
# ------------------------------------------------------------------------------

class PersonFactoryCreateRequest(BaseModel):
    """
    Request body for creating a TinyPersonFactory.
    """
    context_text: str = Field(..., description="Context text for generating TinyPerson instances.")
    simulation_id: Optional[str] = Field(None, description="Simulation ID if relevant.")

class GeneratePersonRequest(BaseModel):
    """
    Request body for generating a single TinyPerson from an existing TinyPersonFactory.
    """
    agent_particularities: Optional[str] = Field(None, description="Particularities for the agent to generate.")
    temperature: float = Field(1.5, description="LLM temperature for generation.")
    attempts: int = Field(10, description="Max number of generation attempts.")

class GeneratePeopleRequest(GeneratePersonRequest):
    """
    Request body for generating multiple persons from the factory.
    """
    number_of_people: int = Field(1, description="How many persons to generate.")
    verbose: bool = Field(False, description="If True, prints logging info to console.")

# ------------------------------------------------------------------------------
# 3) Create & Manage Factories
# ------------------------------------------------------------------------------

@app.post("/factories/person", summary="Create a new TinyPersonFactory")
def create_person_factory(req: PersonFactoryCreateRequest, factory_id: str = "default"):
    """
    Create a TinyPersonFactory, store it under `factory_id`.
    """
    if factory_id in FACTORIES:
        raise HTTPException(
            status_code=400, 
            detail=f"Factory with ID '{factory_id}' already exists."
        )
    # Instantiate the factory
    factory = TinyPersonFactory(
        context_text=req.context_text,
        simulation_id=req.simulation_id
    )

    # Store in our local registry
    FACTORIES[factory_id] = factory
    return {
        "msg": f"TinyPersonFactory '{factory_id}' created.",
        "factory_name": factory.name
    }

@app.get("/factories")
def list_factories():
    """
    List all factory IDs currently tracked in the local registry.
    """
    return {"factory_ids": list(FACTORIES.keys())}

@app.get("/factories/{factory_id}")
def get_factory(factory_id: str):
    """
    Return basic info about a specific factory.
    """
    factory = FACTORIES.get(factory_id)
    if not factory:
        raise HTTPException(status_code=404, detail=f"No factory with ID '{factory_id}' found.")
    
    return {
        "factory_id": factory_id,
        "factory_name": factory.name,
        "simulation_id": factory.simulation_id,
        "type": type(factory).__name__, 
        "context_text": getattr(factory, "context_text", None)  # only exists on TinyPersonFactory
    }

@app.delete("/factories/{factory_id}")
def delete_factory(factory_id: str):
    """
    Remove a factory from the local registry (and optionally from TinyFactory.all_factories).
    """
    factory = FACTORIES.pop(factory_id, None)
    if not factory:
        raise HTTPException(status_code=404, detail=f"No factory with ID '{factory_id}' found.")
    
    # Also remove from TinyFactory.all_factories if it’s in there
    if factory.name in TinyFactory.all_factories:
        del TinyFactory.all_factories[factory.name]

    return {"msg": f"Factory '{factory_id}' deleted."}

# ------------------------------------------------------------------------------
# 4) Generate Persons from a TinyPersonFactory
# ------------------------------------------------------------------------------

@app.post("/factories/{factory_id}/generate-person")
def generate_single_person(factory_id: str, req: GeneratePersonRequest):
    """
    Use a TinyPersonFactory to generate a single TinyPerson.
    """
    factory = FACTORIES.get(factory_id)
    if not factory or not isinstance(factory, TinyPersonFactory):
        raise HTTPException(
            status_code=404, 
            detail=f"No valid TinyPersonFactory with ID '{factory_id}' found."
        )
    
    person = factory.generate_person(
        agent_particularities=req.agent_particularities,
        temperature=req.temperature,
        attepmpts=req.attempts
    )
    if not person:
        raise HTTPException(status_code=500, detail="Failed to generate a person after several attempts.")

    return {
        "msg": f"Generated person '{person.name}' successfully.",
        "person_name": person.name,
        "mini_bio": person.minibio()
    }

@app.post("/factories/{factory_id}/generate-people")
def generate_multiple_people(factory_id: str, req: GeneratePeopleRequest):
    """
    Use a TinyPersonFactory to generate multiple TinyPersons.
    """
    factory = FACTORIES.get(factory_id)
    if not factory or not isinstance(factory, TinyPersonFactory):
        raise HTTPException(
            status_code=404,
            detail=f"No valid TinyPersonFactory with ID '{factory_id}' found."
        )

    people = factory.generate_people(
        number_of_people=req.number_of_people,
        agent_particularities=req.agent_particularities,
        temperature=req.temperature,
        attepmpts=req.attempts,
        verbose=req.verbose
    )
    # Return minimal info about generated persons
    people_info = [{"name": p.name, "mini_bio": p.minibio()} for p in people]

    return {
        "msg": f"Generated {len(people)} persons successfully.",
        "people": people_info
    }

# ------------------------------------------------------------------------------
# 5) Health Check
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "up"}
