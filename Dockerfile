FROM python:3.11
WORKDIR /app/
COPY ./ /app/
RUN pip install --no-cache-dir --upgrade -r requirements.txt
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "80"]