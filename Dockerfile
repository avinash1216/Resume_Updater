FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project configuration files first to cache dependencies layer
COPY pyproject.toml README.md ./

# Install python dependencies using standard pip
# Note: we disable build cache since this is a one-time build
RUN pip install --no-cache-dir .

# Copy application source code and template files
COPY app/ ./app/
COPY templates/ ./templates/

# Expose port
EXPOSE 8000

# Command to run uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
