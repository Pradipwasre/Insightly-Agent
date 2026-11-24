FROM python:3.12-slim
WORKDIR /code

# Logs show up live; no .pyc files; no pip "new version" notice
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Libraries first, so code changes don't reinstall them (layer caching).
# Retries + a longer timeout survive slow or flaky networks.
COPY requirements.txt .
RUN pip install --no-cache-dir --retries 10 --timeout 60 -r requirements.txt

COPY app ./app
COPY ui ./ui
COPY tests ./tests
COPY evals ./evals
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
