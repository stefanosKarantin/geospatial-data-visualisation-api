FROM python:3.6

COPY . /home/app/
WORKDIR /home/app

# Download Python dependencies
RUN pip install -r requirements.txt

ENV ENVIRONMENT production
# Use gunicorn to server flask app, not flask's dev/test server
EXPOSE 5000

RUN chmod +x ./main.py
RUN chmod +x ./runserver.sh

ENTRYPOINT ["./runserver.sh"]
