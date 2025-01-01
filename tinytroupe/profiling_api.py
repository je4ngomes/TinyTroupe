from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import base64
import io

# Adjust import path to wherever your Profiler class is defined
from profiling import Profiler

app = FastAPI(title="TinyTroupe Profiling API")

# ------------------------------------------------------------------------------
# 1) In-Memory Registry of Profilers (if you want multiple)
# ------------------------------------------------------------------------------
PROFILERS = {}

# ------------------------------------------------------------------------------
# 2) Pydantic Models
# ------------------------------------------------------------------------------

class ProfilerCreateRequest(BaseModel):
    """
    Create a Profiler specifying which attributes to track.
    """
    attributes: List[str] = Field(default=["age", "occupation", "nationality"], description="List of agent attributes to profile.")

class AgentData(BaseModel):
    """
    Minimal representation of an agent's attributes.
    You can extend this if your agent has more fields.
    """
    age: Optional[int] = None
    occupation: Optional[str] = None
    nationality: Optional[str] = None
    # Add any other keys you'd like to track

class ProfilingRequest(BaseModel):
    """
    Request body for profiling a list of agents with a given Profiler.
    """
    profiler_id: str = Field(..., description="ID of the Profiler to use.")
    agents: List[AgentData] = Field(..., description="List of agent attributes to profile.")

class PlotRequest(BaseModel):
    """
    Request body to optionally retrieve plots (as base64) for the distributions.
    """
    profiler_id: str = Field(..., description="ID of the Profiler whose plots we want.")
    # For advanced usage, you might add a 'specific_attributes' or other options if you only want some plots.


# ------------------------------------------------------------------------------
# 3) Endpoints
# ------------------------------------------------------------------------------

@app.post("/profilers", summary="Create a new Profiler")
def create_profiler(req: ProfilerCreateRequest, profiler_id: str = "default"):
    """
    Create a Profiler object that will analyze the given attributes.
    """
    if profiler_id in PROFILERS:
        raise HTTPException(status_code=400, detail=f"Profiler '{profiler_id}' already exists.")
    profiler = Profiler(attributes=req.attributes)
    PROFILERS[profiler_id] = profiler
    return {"msg": f"Profiler '{profiler_id}' created with attributes {req.attributes}."}

@app.get("/profilers")
def list_profilers():
    """
    List all Profiler IDs in memory.
    """
    return {"profiler_ids": list(PROFILERS.keys())}

@app.delete("/profilers/{profiler_id}")
def delete_profiler(profiler_id: str):
    """
    Remove a Profiler from memory.
    """
    profiler = PROFILERS.pop(profiler_id, None)
    if not profiler:
        raise HTTPException(status_code=404, detail=f"No profiler with ID '{profiler_id}' found.")
    return {"msg": f"Profiler '{profiler_id}' deleted."}

@app.post("/profilers/profile", summary="Profile a list of agents using an existing Profiler")
def profile_agents(req: ProfilingRequest):
    """
    Pass a list of agents' attributes to the Profiler.
    Returns a JSON of the computed distributions.
    """
    profiler = PROFILERS.get(req.profiler_id)
    if not profiler:
        raise HTTPException(status_code=404, detail=f"No profiler with ID '{req.profiler_id}' found.")

    # Convert list[AgentData] to list[dict]
    agents_dicts = [agent.dict() for agent in req.agents]
    distributions = profiler.profile(agents=agents_dicts)
    # `distributions` is a dict of { attribute: (DataFrame) }

    # Convert each DataFrame to a JSON-friendly dict, e.g. { "value1": count1, "value2": count2 }
    out = {}
    for attribute, df in distributions.items():
        # df is a pd.Series from .value_counts(), so convert it to dictionary
        # e.g.: {index_value: count, index_value2: count2, ...}
        out[attribute] = df.to_dict()

    return {
        "msg": f"Profile computed for profiler '{req.profiler_id}'.",
        "distributions": out
    }

@app.post("/profilers/render", summary="Render the attribute distributions as plots (optionally returning base64 images)")
def render_plots(req: PlotRequest, return_plots_base64: bool = False):
    """
    Renders the distributions previously computed by the Profiler.
    Optionally returns the plots as base64-encoded PNG images if you want them inline via API.
    """
    profiler = PROFILERS.get(req.profiler_id)
    if not profiler:
        raise HTTPException(status_code=404, detail=f"No profiler with ID '{req.profiler_id}' found.")

    # The Profiler has a .render() that calls ._plot_attributes_distributions(),
    # which draws matplotlib plots to the screen by default (plt.show()).
    # For an API, we often want to either:
    # (1) Save the plots to files, or
    # (2) Convert them to base64 strings and return them in JSON.
    # We'll show how to do (2).

    if not return_plots_base64:
        # Just call .render() so it shows locally (if running on a server with GUI).
        # Many servers won't have a display, so you may not see anything.
        profiler.render()
        return {"msg": "Plots rendered (locally, if available). No images returned."}
    
    # If returning images, we can intercept the plotting calls to get the figure data:
    import matplotlib
    matplotlib.use("Agg")  # Use a non-GUI backend
    import matplotlib.pyplot as plt

    # We'll replicate the logic from .render() => ._plot_attributes_distributions()
    # but capture each figure as base64:
    images = {}

    for attribute, df in profiler.attributes_distributions.items():
        if df.empty:
            # If we never profiled or there's no data, skip
            images[attribute] = None
            continue

        fig, ax = plt.subplots()
        df.plot(kind='bar', ax=ax, title=f"{attribute.capitalize()} distribution")

        # Convert to PNG in memory
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        base64_img = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)

        images[attribute] = f"data:image/png;base64,{base64_img}"

    return {
        "msg": "Plots generated as base64 images.",
        "images": images
    }


@app.get("/health")
def health_check():
    """
    Simple endpoint to verify the API is running.
    """
    return {"status": "up"}
