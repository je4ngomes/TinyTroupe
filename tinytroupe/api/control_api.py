from fastapi import FastAPI, HTTPException
from typing import Optional

# Import the control.py functions we want to expose
from control import begin, end, checkpoint, reset, current_simulation
from control import cache_hits, cache_misses

app = FastAPI(title="TinyTroupe Control API")

@app.post("/begin")
def begin_endpoint(
    sim_id: str = "default",
    cache_path: Optional[str] = None,
    auto_checkpoint: bool = False
):
    """
    Start (begin) a simulation with optional cache path and auto-checkpointing.
    """
    try:
        begin(cache_path=cache_path, id=sim_id, auto_checkpoint=auto_checkpoint)
        return {
            "msg": "Simulation started",
            "simulation_id": sim_id,
            "cache_path": cache_path,
            "auto_checkpoint": auto_checkpoint
        }
    except ValueError as e:
        # e.g. "Simulation is already started under id ..."
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/end")
def end_endpoint(sim_id: str = "default"):
    """
    End (stop) a simulation for a given ID.
    """
    try:
        end(sim_id)
        return {"msg": "Simulation ended", "simulation_id": sim_id}
    except ValueError as e:
        # e.g. "Simulation is already stopped."
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checkpoint")
def checkpoint_endpoint(sim_id: str = "default"):
    """
    Manually checkpoint (save) the simulation state.
    """
    try:
        checkpoint(sim_id)
        return {"msg": "Checkpoint saved", "simulation_id": sim_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
def reset_endpoint():
    """
    Reset the entire simulation control state (only one simulation at a time).
    """
    try:
        reset()
        return {"msg": "System reset. No simulation is active now."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache-stats")
def cache_stats(sim_id: str = "default"):
    """
    Show how many cache hits/misses have occurred for a simulation ID.
    """
    try:
        return {
            "simulation_id": sim_id,
            "hits": cache_hits(sim_id),
            "misses": cache_misses(sim_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/current-simulation")
def get_current_simulation():
    """
    Return info about the currently active simulation, if any.
    """
    sim = current_simulation()
    if sim is None:
        return {"current_simulation": None}
    return {
        "current_simulation": sim.id,
        "status": sim.status,
        "cache_path": sim.cache_path,
        "auto_checkpoint": sim.auto_checkpoint
    }

@app.get("/health")
def health_check():
    """
    Simple health-check endpoint.
    """
    return {"status": "up"}
