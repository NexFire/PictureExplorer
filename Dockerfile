# Stage 1: Builder stage to install PyQt5 and other dependencies without cache
FROM python:3.12 AS builder

# Update the package list
RUN apt-get update

# Install Qt development libraries required by PyQt5
RUN apt-get install -y qtbase5-dev

# Install PyQt5 without caching to reduce memory overhead
RUN pip install --no-cache-dir PyQt5

# Stage 2: Final stage for Nuitka and cross-compilation setup
FROM python:3.12

# Update the package list again for this stage
RUN apt-get update

# Install native GCC, G++, and MinGW-w64 for cross-compilation
RUN apt-get install -y \
    gcc \
    g++ \
    mingw-w64 \
    patchelf

# Install Nuitka itself
RUN pip install nuitka

# Set environment variables to avoid version parsing issues
ENV CC="gcc" \
    CXX="g++" \
    NUITKA_CC="gcc" \
    NUITKA_CXX="g++" \
    NUITKA_CC_VERSION="12.0.0" \
    NUITKA_CROSS_COMPILE=1

# Copy PyQt5 from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Set up a working directory for your application code
WORKDIR /src

# Copy your Python script and any other project files into the container
COPY . /src
