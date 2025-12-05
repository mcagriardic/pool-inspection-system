FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install uv

RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
