from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class DomainUser(BaseModel):
    id: int
    username: str
    fullName: Optional[str] = None
    title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
