from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# Adjust to your project's actual imports:
# e.g. from story import TinyStory
# from tinytroupe.agent import TinyPerson
# from tinytroupe.environment import TinyWorld
from tinytroupe.story import TinyStory
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld

app = FastAPI(title="TinyTroupe Story API")

# ------------------------------------------------------------------------------
# 1) In-Memory Registries and Helper Lookups
#    In real code, you'd have these in a shared data layer or module.
# ------------------------------------------------------------------------------
STORIES = {}          # story_id -> TinyStory object
AGENT_REGISTRY = {}   # agent_name -> TinyPerson
WORLD_REGISTRY = {}   # world_name -> TinyWorld

# ------------------------------------------------------------------------------
# 2) Pydantic Models
# ------------------------------------------------------------------------------

class CreateStoryRequest(BaseModel):
    """
    Request to create a TinyStory object, referencing either an environment or agent.
    """
    story_id: str = Field(..., description="A unique ID for this story.")
    environment_name: Optional[str] = Field(None, description="Name of a TinyWorld. If set, agent_name must not be used.")
    agent_name: Optional[str] = Field(None, description="Name of a TinyPerson. If set, environment_name must not be used.")
    purpose: str = Field("Be a realistic simulation.", description="High-level purpose or theme of the story.")
    context: str = Field("", description="Initial text context to seed the story.")
    first_n: int = Field(10, description="Number of earliest interactions to include in story.")
    last_n: int = Field(20, description="Number of most recent interactions to include in story.")
    include_omission_info: bool = Field(True, description="Whether to note info about omitted interactions.")

class StartStoryRequest(BaseModel):
    """
    Request to start a story with some constraints.
    """
    story_id: str = Field(..., description="ID of the existing story.")
    requirements: str = Field("Start some interesting story about the agents.", description="High-level instructions for the story.")
    number_of_words: int = Field(100, description="Approximate size of the story beginning.")
    include_plot_twist: bool = Field(False, description="If True, try to insert a plot twist.")

class ContinueStoryRequest(BaseModel):
    """
    Request to continue a story with new constraints.
    """
    story_id: str = Field(..., description="ID of the existing story.")
    requirements: str = Field("Continue the story in an interesting way.", description="High-level instructions for continuing the story.")
    number_of_words: int = Field(100, description="Approximate size of the continuation.")
    include_plot_twist: bool = Field(False, description="If True, try to insert a plot twist.")

# ------------------------------------------------------------------------------
# 3) Endpoints
# ------------------------------------------------------------------------------

@app.post("/stories", summary="Create a new TinyStory object")
def create_story(req: CreateStoryRequest):
    """
    Create a new TinyStory object for either a single agent or an entire environment.
    Exactly one of environment_name or agent_name must be provided.
    """
    # Validate that story_id is unique
    if req.story_id in STORIES:
        raise HTTPException(status_code=400, detail=f"Story '{req.story_id}' already exists.")

    if req.environment_name and req.agent_name:
        raise HTTPException(status_code=400, detail="Cannot provide both environment_name and agent_name.")
    if not req.environment_name and not req.agent_name:
        raise HTTPException(status_code=400, detail="Must provide either environment_name or agent_name.")

    # Retrieve the environment or agent object
    environment = None
    agent = None

    if req.environment_name:
        environment = WORLD_REGISTRY.get(req.environment_name)
        if not environment:
            raise HTTPException(
                status_code=404,
                detail=f"No environment named '{req.environment_name}' found."
            )
    if req.agent_name:
        agent = AGENT_REGISTRY.get(req.agent_name)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"No agent named '{req.agent_name}' found."
            )

    # Create the TinyStory instance
    try:
        story = TinyStory(
            environment=environment,
            agent=agent,
            purpose=req.purpose,
            context=req.context,
            first_n=req.first_n,
            last_n=req.last_n,
            include_omission_info=req.include_omission_info
        )
        STORIES[req.story_id] = story
        return {
            "msg": f"Story '{req.story_id}' created successfully.",
            "environment_name": req.environment_name,
            "agent_name": req.agent_name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/stories/start", summary="Start a new story for an existing TinyStory object")
def start_story(req: StartStoryRequest):
    """
    Calls the .start_story(...) method on an existing TinyStory object.
    Returns the text of the newly started story portion.
    """
    story = STORIES.get(req.story_id)
    if not story:
        raise HTTPException(status_code=404, detail=f"No story with ID '{req.story_id}' found.")
    
    beginning = story.start_story(
        requirements=req.requirements,
        number_of_words=req.number_of_words,
        include_plot_twist=req.include_plot_twist
    )
    return {
        "msg": f"Story '{req.story_id}' started.",
        "beginning": beginning
    }

@app.post("/stories/continue", summary="Continue an existing story")
def continue_story(req: ContinueStoryRequest):
    """
    Calls the .continue_story(...) method on an existing TinyStory object.
    Returns the text of the newly added continuation.
    """
    story = STORIES.get(req.story_id)
    if not story:
        raise HTTPException(status_code=404, detail=f"No story with ID '{req.story_id}' found.")
    
    continuation = story.continue_story(
        requirements=req.requirements,
        number_of_words=req.number_of_words,
        include_plot_twist=req.include_plot_twist
    )
    return {
        "msg": f"Story '{req.story_id}' continued.",
        "continuation": continuation
    }

@app.get("/stories/{story_id}")
def get_story_text(story_id: str):
    """
    Retrieve the entire text for a given story.
    """
    story = STORIES.get(story_id)
    if not story:
        raise HTTPException(status_code=404, detail=f"No story with ID '{story_id}' found.")
    
    return {
        "story_id": story_id,
        "current_story": story.current_story
    }

@app.delete("/stories/{story_id}")
def delete_story(story_id: str):
    """
    Delete a story from memory.
    """
    story = STORIES.pop(story_id, None)
    if not story:
        raise HTTPException(status_code=404, detail=f"No story with ID '{story_id}' found.")
    return {"msg": f"Story '{story_id}' deleted."}

# ------------------------------------------------------------------------------
# 4) Health Check
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "up"}
