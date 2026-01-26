FROM python:3.13.1-slim

WORKDIR /app

COPY  requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#copy script start
COPY  start.sh /start.sh
RUN chmod +x /start.sh

CMD [ "/start.sh" ]
