FROM python:3.10-slim-buster

WORKDIR /backend-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

# change access permission to allow execution of the script
RUN chmod +x ./command.sh

ENV FLASK_ENV=development FRONTEND_URL='*' BACKEND_URL='*'

EXPOSE ${PORT}

# use command script as starting point
CMD ["./command.sh"]