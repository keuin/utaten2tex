FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY *.py .

CMD ["python3", "web.py"]