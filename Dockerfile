# Use the official Python image from Docker Hub
FROM python:3.10-slim

# Set environment variables to avoid .pyc files and ensure outputs are shown in the container logs
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Install PostgreSQL dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        build-essential \
    && rm -rf /var/lib/apt/lists/*


# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port the app will run on
EXPOSE 8000

RUN python manage.py migrate
RUN python manage.py collectstatic --noinput
# Run the Django development server (for development use)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
