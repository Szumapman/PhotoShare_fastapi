FROM python:3.11-alpine
LABEL authors="Paweł Szumański"

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

WORKDIR /PhotoShare_fastapi

COPY . /PhotoShare_fastapi

RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]