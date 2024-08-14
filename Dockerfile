FROM --platform=linux/amd64 python:3.9-slim
RUN pip install kubernetes
COPY role-patcher.py /app/
WORKDIR /app
CMD ["python", "role-patcher.py"]
