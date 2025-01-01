from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tinytroupe.examples

app = FastAPI(title="TinyTroupe Examples API")

class PersonaConfig(BaseModel):
    persona_type: str = "architect"
    name: str = "Oscar"

@app.post("/create-persona")
def create_persona(config: PersonaConfig):
    """
    Create a persona from TinyTroupe using a single endpoint.
    You pick which persona_type (architect, linguist, physician, data_scientist, etc.)
    and set a name.
    """

    try:
        # Decide which function to call based on persona_type
        if config.persona_type.lower() == "architect":
            persona = tinytroupe.examples.create_oscar_the_architect()
        elif config.persona_type.lower() == "linguist":
            persona = tinytroupe.examples.create_lila_the_linguist()
        elif config.persona_type.lower() == "physician":
            persona = tinytroupe.examples.create_marcos_the_physician()
        elif config.persona_type.lower() == "data_scientist":
            persona = tinytroupe.examples.create_lisa_the_data_scientist()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown persona_type: {config.persona_type}"
            )
        
        # Override the default name with whatever the user provided
        persona.name = config.name
        
        # Return the persona data
        return {
            "persona": persona.to_dict() 
                if hasattr(persona, "to_dict") 
                else str(persona)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "up"}
