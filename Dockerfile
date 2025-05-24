FROM python:3.11-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    tini \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash app
USER app

# Set up working directory
WORKDIR /home/app

# Copy requirements first to leverage Docker cache
COPY --chown=app:app requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p /home/app/data/charts

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV PATH="/home/app/.local/bin:${PATH}"

# Add Xvfb start script
COPY --chown=app:app scripts/start.sh /home/app/start.sh
RUN chmod +x /home/app/start.sh

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use tini as entrypoint
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run the application with Xvfb
CMD ["/home/app/start.sh"]
