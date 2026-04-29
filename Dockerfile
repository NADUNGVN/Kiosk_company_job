# Sử dụng Python 3.10 với phiên bản slim
FROM python:3.10-slim

# Đặt thư mục làm việc
WORKDIR /app

# Sao chép tệp requirements.txt và cài đặt dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
# Ensure Celery is installed
RUN pip install celery redis

# Sao chép toàn bộ mã nguồn vào container
COPY . /app/

# Expose cổng 8000 để phục vụ ứng dụng Django
EXPOSE 8000

# Thiết lập các biến môi trường
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Lệnh để chạy ứng dụng Django với Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
