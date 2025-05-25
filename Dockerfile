FROM akhmadavtor/my-python-image@sha256:53a2a6c997f67a71a43e264d9630d3cb3c18f8949ee19591cff6a9f5ea1f3de5

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
