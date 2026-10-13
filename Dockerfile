FROM python:3.12-slim

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=7860

# Cài đặt các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Tạo user theo tiêu chuẩn bảo mật của Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /app

# Copy và cài đặt thư viện python
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container (thuộc quyền sở hữu của user)
COPY --chown=user . .

# Port mặc định mà Hugging Face Spaces lắng nghe là 7860
EXPOSE 7860

# Khởi chạy FastAPI Backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
