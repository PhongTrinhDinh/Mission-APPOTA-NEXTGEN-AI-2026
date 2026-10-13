from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    user_id: str = Field(..., description="Mã định danh nhân viên (VD: U01, U02, U99)")
    name: str = Field(..., description="Họ và tên nhân viên")
    company: str = Field(..., description="Công ty thành viên / Tập đoàn")
    dept: str = Field(..., description="Phòng ban (HR, Sales, Engineering, BOD,...)")
    role_level: int = Field(..., ge=1, le=5, description="Cấp bậc phân quyền (1: Nhân viên, 3: Trưởng phòng, 4: C-Level, 5: Chủ tịch)")

class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="Mã User ID đăng nhập")

class LoginResponse(BaseModel):
    status: str = Field(default="success")
    user: UserProfile

class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID của người đang đặt câu hỏi")
    query: str = Field(..., min_length=1, description="Nội dung câu hỏi cần tra cứu")

class SourceNodeInfo(BaseModel):
    title: str = Field(..., description="Tiêu đề tài liệu nguồn")
    file_id: Optional[str] = Field(default=None, description="Mã hiệu văn bản")
    required_level: Optional[int] = Field(default=None, description="Cấp bảo mật của tài liệu")
    required_dept: Optional[str] = Field(default=None, description="Phòng ban tài liệu")
    score: Optional[float] = Field(default=None, description="Điểm số tương quan sau rerank")
    text_excerpt: Optional[str] = Field(default=None, description="Đoạn văn trích dẫn từ tài liệu")

class ChatResponse(BaseModel):
    status: str = Field(default="success")
    query: str
    response: str = Field(..., description="Câu trả lời tổng hợp từ AI")
    user: UserProfile
    sources: List[str] = Field(default_factory=list, description="Danh sách tài liệu đã trích xuất")
    source_details: Optional[List[SourceNodeInfo]] = Field(default=None, description="Chi tiết các nguồn trích dẫn")

class IngestResponse(BaseModel):
    status: str = Field(default="success")
    message: str
    documents_count: Optional[int] = None

class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    app_name: str
    version: str
    is_ready: bool
    config: Dict[str, Any]
