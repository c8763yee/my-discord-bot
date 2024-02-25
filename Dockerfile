FROM python:3.10-slim

# Copy the vcgencmd binary to the container(raspberry pi)
ADD . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]