FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /app/

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /app/

#RUN python manage.py migrate
#RUn python manage.py collectstatic --no-input

CMD ["daphne","-b", "0.0.0.0", "-p", "8000", "WebChat.asgi:application"]


