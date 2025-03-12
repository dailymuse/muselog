FROM python:3.8

# Set working directory
WORKDIR /muselog

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Copy the test requirements file
COPY test-requirements.txt .

# Install Python dependencies
RUN /bin/bash -c ". $HOME/.cargo/env && pip install -r test-requirements.txt"

# Copy the rest of the project files
COPY . .

# Run tests
CMD ["bash", "-c", "python -m unittest"]

