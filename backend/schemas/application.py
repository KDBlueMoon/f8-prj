import uuid

from pydantic import BaseModel


class ApplyJobRequest(BaseModel):
    cv_id: uuid.UUID
    cover_letter: str | None = None
