FROM python:3.9-alpine

WORKDIR /app
COPY . .
RUN pip install -U -r required_modules.txt

CMD ["python", "bot.py"]