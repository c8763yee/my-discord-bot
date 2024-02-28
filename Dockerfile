FROM python:3.10-slim

RUN useradd user
COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt
ADD . /app
WORKDIR /app
RUN chown -R user:user /app

USER user:user

CMD ["python", "app.py"]
