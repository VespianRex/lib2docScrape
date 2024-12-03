from pydantic import BaseModel, Field

class URLInfo(BaseModel):
    """URL information model."""
    scheme: str = Field(default="")
    netloc: str = Field(default="")
    path: str = Field(default="")
    normalized: str = Field(default="")
    is_valid: bool = Field(default=False)
    original: str = Field(default="")

    def __init__(self, **data):
        if "original" not in data:
            data["original"] = data.get("normalized", "")
        super().__init__(**data) 