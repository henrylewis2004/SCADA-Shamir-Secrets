FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/common/ .
COPY src/prep/nodes.py .
COPY src/prep/dealer.py .
COPY src/eval/evaluation.py .
COPY src/mtu/mtu.py .

CMD ["python", "mtu.py"]
