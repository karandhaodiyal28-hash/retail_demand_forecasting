# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the Python backend & serve frontend
FROM python:3.12-slim
WORKDIR /app

# Install system utilities needed for building packages if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend python code
COPY backend/ ./backend
# Copy startup scripts
COPY run.py .

# Copy built frontend assets from Stage 1 into the correct location
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port and start FastAPI server
EXPOSE 10000
ENV PORT=10000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
