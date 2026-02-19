FROM python:3.11-slim

WORKDIR /app

# Install git, docker, Node.js, Go, Java, and Rust for multi-language support
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    curl \
    wget \
    default-jdk \
    maven \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz \
    && rm go1.21.0.linux-amd64.tar.gz \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && rm -rf /var/lib/apt/lists/*

# Set Go environment variables
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/root/go"
ENV PATH="${GOPATH}/bin:${PATH}"

# Set Rust environment variables
ENV PATH="/root/.cargo/bin:${PATH}"

# Set Java environment variables
ENV JAVA_HOME="/usr/lib/jvm/default-java"
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Python testing tools globally
RUN pip install --no-cache-dir flake8 mypy pytest pylint

# Create necessary directories
RUN mkdir -p /tmp/repos results

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
