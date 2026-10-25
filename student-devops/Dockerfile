FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser  # Creates a safe, non-admin user named appuser (ID 10001) so the app doesn't run with dangerous administrator (root) permissions.
COPY --chown=appuser:appuser app/ . # Copies your application source code (app/ folder) into the container and assigns its ownership to appuser.
USER 10001
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
# gunicorn: A populer server to run python web application
# --workers", "2": gunicorn start 2 work processes to handle traffic

