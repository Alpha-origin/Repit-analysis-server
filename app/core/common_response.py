from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class CommonResponse(BaseModel, Generic[T]):
    status: str = "ok"
    message: Optional[str] = None
    data: Optional[T] = None