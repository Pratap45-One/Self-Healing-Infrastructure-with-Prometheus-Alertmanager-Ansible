FROM python:3.9-slim

WORKDIR /app

# copy handler
COPY handler.py /app/handler.py

# dependencies
RUN pip install --no-cache-dir flask docker

EXPOSE 5001

CMD ["python", "handler.py"]
