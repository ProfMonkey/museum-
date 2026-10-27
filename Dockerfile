# Wonder Atlas / 万物博物馆 — full FastAPI application image.
# Build and deployment do not invoke GitHub Actions.
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WONDER_DATA_DIR=/data \
    WONDER_COOKIE_SECURE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# server.py imports feature modules through V37; copy every first-party Python module.
COPY *.py ./
COPY assets-bundle.zip ./
COPY static/ ./static/

# Restore packaged art at build time; /data is reserved for persistent user data.
RUN python -c "import restore_assets"

VOLUME ["/data"]
EXPOSE 8000
# Railway supplies PORT; local Docker runs on 8000 by default.
CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
