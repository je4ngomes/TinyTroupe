import json
import sys
import unicodedata
import re
import html

from pydantic import ValidationError, BaseModel
from tinytroupe.utils import logger

################################################################################
# Validation
################################################################################
def check_valid_fields(obj: dict, valid_fields: list) -> None:
    """
    Checks whether the fields in the specified dict are valid, according to the list of valid fields. If not, raises a ValueError.
    """
    for key in obj:
        if key not in valid_fields:
            raise ValueError(f"Invalid key {key} in dictionary. Valid keys are: {valid_fields}")

def sanitize_raw_string(value: str) -> str:
    """
    Sanitizes the specified string by:
      - removing ANSI escape sequences.
      - decoding HTML entities (standard and non-standard formats).
      - decoding JSON-escaped unicode sequences (e.g., \\u00e7 -> ç).
      - removing any invalid characters.
      - ensuring it is not longer than the maximum Python string length.

    This is for an abundance of caution with security, to avoid any potential issues with the string.
    """

    # Remove ANSI escape sequences (some models output these for terminal formatting)
    # This pattern matches escape sequences like \x1b[...m
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07')
    value = ansi_escape.sub('', value)

    # Decode non-standard HTML entity format &#0XX (where 0 is used instead of x for hex)
    # Some models like Gemini output &#0E9; instead of &#xE9; for é
    def decode_nonstandard_hex_entity(match):
        hex_code = match.group(1)
        try:
            return chr(int(hex_code, 16))
        except (ValueError, OverflowError):
            return match.group(0)  # Return original if can't decode

    value = re.sub(r'&#0([0-9A-Fa-f]+);?', decode_nonstandard_hex_entity, value)

    # Decode standard HTML entities (&#233; for decimal, &#xE9; for hex, &eacute; for named)
    value = html.unescape(value)

    # Decode JSON-escaped unicode sequences (e.g., \u00e7\u00e3o -> ção)
    # This handles models that output escaped unicode instead of proper UTF-8
    try:
        # Use unicode_escape to decode \uXXXX sequences
        if '\\u' in value:
            value = value.encode('utf-8').decode('unicode_escape')
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass  # If decoding fails, keep the original value

    # remove any invalid characters by making sure it is a valid UTF-8 string
    value = value.encode("utf-8", "ignore").decode("utf-8")

    value = unicodedata.normalize("NFC", value)

    # ensure it is not longer than the maximum Python string length
    return value[:sys.maxsize]

def sanitize_dict(value: dict) -> dict:
    """
    Sanitizes the specified dictionary by:
      - removing any invalid characters.
      - ensuring that the dictionary is not too deeply nested.
    """

    # sanitize the string representation of the dictionary
    for k, v in value.items():
        if isinstance(v, str):
            value[k] = sanitize_raw_string(v)

    # ensure that the dictionary is not too deeply nested
    return value

def to_pydantic_or_sanitized_dict(value: dict, model: BaseModel=None) -> dict:
    """
    Converts the specified model response dictionary to a Pydantic model instance, or sanitizes it if the model is not valid.
    It is assumed that the dict contains the `content` key.
    """

    if model is not None and (isinstance(model, type) and issubclass(model, BaseModel)):
        # If a model is provided, try to validate the value against the model
        try:
            res = model.model_validate(sanitize_dict(json.loads(value['content'])))
            return res
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return sanitize_dict(value)
    else:
        return sanitize_dict(value)  # If no model, just sanitize the dict
