# ==========================================
# 1. Base Image Optimization
# ==========================================
FROM python:3.11-slim

# Thiết lập các biến môi trường tối ưu cho Python trong môi trường Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1

# Thiết lập thư mục làm việc cố định
WORKDIR /app

# ==========================================
# 2. Dependency Installation
# ==========================================
# Polars cung cấp sẵn các pre-built wheels cho Linux x86_64/aarch64 
# nên không cần cài thêm build-essential, giúp tiết kiệm hàng trăm MB dung lượng image.
RUN pip install --no-cache-dir --upgrade pip

# Sao chép file requirements trước để tối ưu cơ chế lưu đệm (layer caching) của Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# 3. Source Application Copy
# ==========================================
# Sao chép mã nguồn của ứng dụng vào container
COPY src/ ./src/

# Mặc định tạo cổng chờ lệnh (Entrypoint) để chạy như một công cụ CLI độc lập
ENTRYPOINT ["python", "-m", "src.cli"]