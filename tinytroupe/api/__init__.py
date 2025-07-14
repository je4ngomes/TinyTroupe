"""
TinyTroupe API Module

This module contains FastAPI endpoints for all TinyTroupe functionality,
including agents, environments, stories, experiments, and more.

Main APIs:
- agent_api: Manage TinyPerson agents
- environment_api: Manage TinyWorld environments  
- story_api: Generate and manage stories
- extraction_api: Extract data from simulations
- experimentation_api: Run experiments
- combined_api: Unified API combining all endpoints

Usage:
    from tinytroupe.api.combined_api import app
    # Run with: uvicorn tinytroupe.api.combined_api:app --reload
"""

__version__ = "0.4.0"
