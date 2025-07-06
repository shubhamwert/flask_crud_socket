FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install  -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 5000

# Run app
CMD ["flask", "--app","app","run"]
