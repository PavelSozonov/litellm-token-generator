FROM python:3.10-slim

# install everything needed to build python-ldap
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       libc6-dev \
       libldap2-dev \
       libsasl2-dev \
       python3-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
