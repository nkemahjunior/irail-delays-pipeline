FROM python:3.12-slim
WORKDIR /app
COPY ingestion/requirements.txt ingestion/requirements.txt
RUN pip install --no-cache-dir -r ingestion/requirements.txt
COPY ingestion/ ingestion/
CMD ["python", "ingestion/poll_irail.py"]