FROM python:3.10-slim
ADD file_api.py /
RUN pip install fastapi uvicorn gunicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0", "file_api:app", "-p", "8000"]