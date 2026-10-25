FROM python:3.12-slim

# Prevent bytecode files and enable immediate Python log output.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependencies first so Docker can cache their installation.
COPY requirements.txt .

# Install dependencies and create a non-root application user.
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home appuser

# Copy application files and assign their ownership.
COPY --chown=appuser:appuser app/ .

# Run the application as the non-root user.
USER 10001

EXPOSE 8080

# Start Gunicorn with two worker processes.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
