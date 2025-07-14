from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

# 1) Import the relevant functions from your utils.py
#    Adjust this import path to match your project's structure
from utils import (
    extract_json,
    extract_code_block,
    dedent,
    compose_initial_LLM_messages_with_templates,
    check_valid_fields,
    truncate_actions_or_stimuli,
    fresh_id
)

app = FastAPI(title="TinyTroupe Utils API")

# ------------------------------------------------------------------------------
# 2) Pydantic Models
# ------------------------------------------------------------------------------

class ExtractJsonRequest(BaseModel):
    text: str = Field(..., description="String that may contain JSON data.")

class ExtractJsonResponse(BaseModel):
    extracted: Dict[str, Any] = Field(..., description="Resulting JSON object (empty if none found).")


class ExtractCodeBlockRequest(BaseModel):
    text: str = Field(..., description="String that may contain a code block in triple backticks.")

class ExtractCodeBlockResponse(BaseModel):
    code_block: str = Field(..., description="Extracted code block text (including backticks).")


class DedentRequest(BaseModel):
    text: str = Field(..., description="Multiline text to dedent.")

class DedentResponse(BaseModel):
    dedented: str = Field(..., description="Result after removing common indentation.")


class ComposeLLMMessagesRequest(BaseModel):
    system_template_name: str = Field(..., description="Filename in 'prompts/' for system template.")
    user_template_name: Optional[str] = Field(
        None, description="Filename in 'prompts/' for user template (optional)."
    )
    rendering_configs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variables used in Mustache template rendering."
    )

class ComposeLLMMessagesResponse(BaseModel):
    messages: List[Dict[str, str]] = Field(..., description="A list of role/content messages.")


class CheckValidFieldsRequest(BaseModel):
    obj: Dict[str, Any] = Field(..., description="Dictionary to validate.")
    valid_fields: List[str] = Field(..., description="List of allowed keys.")


class TruncateItem(BaseModel):
    """Represents a single message item with 'role' and 'content' keys."""
    role: str
    content: Dict[str, Any]

class TruncateRequest(BaseModel):
    list_of_actions_or_stimuli: List[TruncateItem] = Field(..., description="List of messages/actions to be truncated.")
    max_content_length: int = Field(..., description="Maximum length for the content field.")

class TruncateResponse(BaseModel):
    truncated: List[TruncateItem] = Field(..., description="The truncated list of items.")


# ------------------------------------------------------------------------------
# 3) Endpoints
# ------------------------------------------------------------------------------

@app.post("/extract-json", response_model=ExtractJsonResponse)
def api_extract_json(req: ExtractJsonRequest):
    """
    Extract JSON from the given text by ignoring any text before the first '{' or '[', 
    and trimming anything after the corresponding closing brace/bracket.
    """
    try:
        data = extract_json(req.text)
        return {"extracted": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/extract-code-block", response_model=ExtractCodeBlockResponse)
def api_extract_code_block(req: ExtractCodeBlockRequest):
    """
    Extract a code block (``` ... ```) from the given text, removing anything before 
    the first triple backtick and after the last triple backtick.
    """
    try:
        block = extract_code_block(req.text)
        return {"code_block": block}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/dedent", response_model=DedentResponse)
def api_dedent(req: DedentRequest):
    """
    Dedent the given text (removing common indentation) and strip outer blank lines.
    """
    try:
        dedented_text = dedent(req.text)
        return {"dedented": dedented_text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/compose-llm-messages", response_model=ComposeLLMMessagesResponse)
def api_compose_llm_messages(req: ComposeLLMMessagesRequest):
    """
    Compose the initial messages (system + optional user) by rendering Mustache templates 
    located in `prompts/<template_name>` with the given rendering configs.
    """
    try:
        messages = compose_initial_LLM_messages_with_templates(
            system_template_name=req.system_template_name,
            user_template_name=req.user_template_name,
            rendering_configs=req.rendering_configs
        )
        return {"messages": messages}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Template file not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/check-valid-fields")
def api_check_valid_fields(req: CheckValidFieldsRequest):
    """
    Check that the dictionary (req.obj) contains only the allowed keys (req.valid_fields).
    If any disallowed key is found, raises a 400 error.
    """
    try:
        check_valid_fields(req.obj, req.valid_fields)
        return {"msg": "Fields are valid."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.post("/truncate-actions-stimuli", response_model=TruncateResponse)
def api_truncate_actions_stimuli(req: TruncateRequest):
    """
    Truncate the 'content' field of actions/stimuli in the given list to 'max_content_length'.
    """
    try:
        truncated_list = truncate_actions_or_stimuli(req.list_of_actions_or_stimuli, req.max_content_length)
        truncated_typed = [TruncateItem(role=item["role"], content=item["content"]) for item in truncated_list]
        return {"truncated": truncated_typed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/fresh-id")
def api_fresh_id():
    """
    Returns a new incremental ID (using the 'fresh_id()' utility).
    """
    new_id = fresh_id()
    return {"fresh_id": new_id}


# ------------------------------------------------------------------------------
# 4) Health Check
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """
    Simple endpoint to verify the API is running.
    """
    return {"status": "up"}
