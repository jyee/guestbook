FROM python:2.7-alpine
RUN apk add --no-cache build-base linux-headers

WORKDIR /usr/src/app

COPY app/requirements.txt app/app.py ./
COPY app/templates/main.html ./templates/main.html

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./app.py" ]
