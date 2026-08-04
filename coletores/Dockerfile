FROM python:3.12-slim

WORKDIR /app

COPY coletores/requirements.txt coletores/requirements.txt
RUN pip install --no-cache-dir -r coletores/requirements.txt

COPY coletores/ /app/coletores/

WORKDIR /app

CMD ["python", "-m", "coletores.main"]