FROM python:3.12.9

# Python configuration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off

# Install Poetry globally
RUN python -m pip install --upgrade pip && \
    pip install poetry

# Copy dependency descriptors
COPY poetry.lock pyproject.toml /usr/src/poetry/

# Set working directory for dependency install
WORKDIR /usr/src/poetry

# Install only main dependencies (no dev) and skip installing project as a package
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main

# Set working directory for the app itself
WORKDIR /usr/src/upload-server

# Copy source code into the container
COPY src .

# Відкриваємо порт для FastAPI
EXPOSE 8000-8009

# Запуск через Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
