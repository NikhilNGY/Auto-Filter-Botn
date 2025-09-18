# Use official Python 3.11 image
FROM python:3.11-slim

# Set working directory
WORKDIR /Auto-Filter-Bot

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot files
COPY . .

# Expose port for web server if needed
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]