import uuid

from pydantic import BaseModel


class EducationIn(BaseModel):
    school: str | None = None
    major: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class CVCreationRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    summary: str | None = None
    education: list[EducationIn] = []
    experience: list[dict] = []
    skills: list[str] = []


class CVCreateResponse(BaseModel):
    cv_id: uuid.UUID
    # Spec chỉ mô tả "Tạo CV online", không có yêu cầu render PDF thật —
    # không tự bịa thêm tính năng, trả null cho tới khi có yêu cầu cụ thể.
    pdf_url: str | None = None
