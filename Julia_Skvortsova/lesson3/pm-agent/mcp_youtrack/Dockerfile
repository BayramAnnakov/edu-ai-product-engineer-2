FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml /app/
COPY youtrack_server.py /app/
COPY youtrack_server_http.py /app/
COPY cache_service.py /app/

# Create virtual environment and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -e .

# Set environment variables for production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for HTTP transport
EXPOSE 8002

# Use HTTP transport for Docker deployment
CMD [".venv/bin/python", "youtrack_server_http.py"]