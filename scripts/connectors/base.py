from typing import Any, TypedDict

class Document(TypedDict):
    id : str
    text : str
    metadata : dict[str, Any]