FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/common/ .
COPY src/prep/nodes.py .
COPY src/prep/dealer.py .
COPY src/field_device/field_device.py .

CMD ["python", "field_device.py"]
