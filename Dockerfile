# Use the official lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face Spaces requires running as a non-root user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy the rest of the application code
COPY --chown=user . /app

# Hugging Face Spaces routes external traffic to port 7860
EXPOSE 7860

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
