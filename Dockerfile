FROM python:3.6

WORKDIR /app

# Download Python dependencies
COPY ["requirements.txt", "./"]
RUN pip install -r requirements.txt

# Bring source code into image
COPY src/ .

# Use gunicorn to server flask app, not flask's dev/test server
EXPOSE 5090
CMD ["gunicorn", "--bind", "0.0.0.0:5090", "api:app"]