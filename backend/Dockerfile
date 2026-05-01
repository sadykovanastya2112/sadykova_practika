FROM python:3.11-slim

WORKDIR /app

ENV FLASK_APP=run.py

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

RUN echo "#!/bin/sh\nflask db upgrade\npython run.py" > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
