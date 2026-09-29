FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/shareholder/shareholder_http.py .

CMD ["python", "shareholder_http.py"]
