from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Adjust imports to match your own project structure
# e.g., `from openai_utils import register_client, client, force_api_type, force_api_cache, LLMRequest`
from openai_utils import (
    register_client, 
    client, 
    force_api_type,
    force_api_cache,
    LLMRequest,
    OpenAIClient,
    AzureClient,
    _api_type_to_client,  # If you want to list or debug your existing clients
    InvalidRequestError,
    NonTerminalError
)

app = FastAPI(title="TinyTroupe OpenAI Utils API")

# ------------------------------------------------------------------------------
# 1) Data Models
# ------------------------------------------------------------------------------
class ChatCompletionRequest(BaseModel):
    messages: List[Dict[str, str]] = Field(..., description="List of messages in ChatGPT style (role/content).")
    model: Optional[str] = Field(None, description="Override model if desired.")
    temperature: Optional[float] = Field(None, description="Override temperature.")
    max_tokens: Optional[int] = Field(None, description="Override max_tokens.")
    top_p: Optional[float] = Field(None, description="Override top_p.")
    frequency_penalty: Optional[float] = Field(None, description="Override frequency_penalty.")
    presence_penalty: Optional[float] = Field(None, description="Override presence_penalty.")
    stop: Optional[List[str]] = Field(None, description="Stop sequences.")
    n: int = Field(1, description="Number of responses to generate.")
    # You can add more parameters as you like, e.g. timeout, attempts, etc.

class EmbeddingRequest(BaseModel):
    text: str = Field(..., description="Input text to get an embedding for.")
    model: Optional[str] = Field(None, description="Override embedding model if desired.")

class LLMPromptRequest(BaseModel):
    system_prompt: Optional[str] = Field(None, description="Raw system prompt. Must not be used if system_template_name is used.")
    system_template_name: Optional[str] = Field(None, description="System template name. Must not be used if system_prompt is used.")
    user_prompt: Optional[str] = Field(None, description="Raw user prompt. Must not be used if user_template_name is used.")
    user_template_name: Optional[str] = Field(None, description="User template name. Must not be used if user_prompt is used.")
    rendering_configs: Dict[str, Any] = Field(default_factory=dict, description="Variables for mustache templates.")
    # Additional LLMRequest parameters (model, temperature, etc.) could be passed in a dict if needed.

class APICacheRequest(BaseModel):
    cache_api_calls: bool = Field(..., description="Whether to enable/disable caching.")
    cache_file_name: str = Field("openai_api_cache.pickle", description="Name of the file to store cached calls.")

# ------------------------------------------------------------------------------
# 2) Basic Endpoints for LLM and Embeddings
# ------------------------------------------------------------------------------

@app.post("/chat-completion")
def chat_completion(req: ChatCompletionRequest):
    """
    Make a chat completion call to the configured client() with given messages.
    """
    try:
        # Prepare parameters
        kwargs = {}
        if req.model is not None:
            kwargs["model"] = req.model
        if req.temperature is not None:
            kwargs["temperature"] = req.temperature
        if req.max_tokens is not None:
            kwargs["max_tokens"] = req.max_tokens
        if req.top_p is not None:
            kwargs["top_p"] = req.top_p
        if req.frequency_penalty is not None:
            kwargs["frequency_penalty"] = req.frequency_penalty
        if req.presence_penalty is not None:
            kwargs["presence_penalty"] = req.presence_penalty
        if req.stop is not None:
            kwargs["stop"] = req.stop
        kwargs["n"] = req.n

        response_data = client().send_message(current_messages=req.messages, **kwargs)
        if response_data is None:
            raise HTTPException(status_code=500, detail="LLM returned None or invalid response.")
        
        return {"response": response_data}

    except InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NonTerminalError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed")
def get_embedding(req: EmbeddingRequest):
    """
    Get an embedding for the given text using the configured client().
    """
    try:
        model_override = req.model
        embedding = client().get_embedding(req.text, model=model_override) if model_override else client().get_embedding(req.text)
        return {"embedding": embedding}
    except InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NonTerminalError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm-request")
def llm_request(req: LLMPromptRequest):
    """
    Create an LLMRequest object and call it. Demonstrates usage of the LLMRequest class.
    """
    try:
        # The LLMRequest requires that exactly one of (system_template_name, system_prompt) is set
        # and exactly one of (user_template_name, user_prompt) is set
        llm = LLMRequest(
            system_template_name=req.system_template_name,
            system_prompt=req.system_prompt,
            user_template_name=req.user_template_name,
            user_prompt=req.user_prompt
            # If you have additional model params, you'd pass them as `**model_params`.
        )
        result = llm.call(**req.rendering_configs)
        return {"result": result, "model_output": llm.model_output}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NonTerminalError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# 3) Switch/Inspect Clients (OpenAI vs. Azure), Caching, etc.
# ------------------------------------------------------------------------------

@app.post("/force-api-type/{api_type}")
def set_api_type(api_type: str):
    """
    Force the system to use either 'openai' or 'azure' (or any other registered clients).
    """
    if api_type not in _api_type_to_client:
        raise HTTPException(status_code=404, detail=f"API type '{api_type}' not registered.")
    try:
        force_api_type(api_type)
        return {"msg": f"API type forced to '{api_type}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/force-api-cache")
def set_api_cache(req: APICacheRequest):
    """
    Enable or disable API call caching, optionally specify a cache file name.
    Applies to all registered clients.
    """
    try:
        force_api_cache(cache_api_calls=req.cache_api_calls, cache_file_name=req.cache_file_name)
        return {
            "msg": f"API cache set to {req.cache_api_calls}. Using file '{req.cache_file_name}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clients")
def list_api_clients():
    """
    Debug endpoint to list all registered clients.
    """
    return {
        "registered_clients": list(_api_type_to_client.keys())
    }

# ------------------------------------------------------------------------------
# 4) Health Check
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "up"}
