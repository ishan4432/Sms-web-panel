FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    redis \
    requests \
    smpplib

CMD ["python", "smpp_server/server.py"]

