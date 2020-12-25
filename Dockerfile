FROM python:3-alpine

COPY requirements.txt /app/requirements.txt

RUN apk add --update --no-cache --virtual .build-deps \
        g++ \
        jpeg-dev \
        python3-dev \
        zlib-dev \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && apk del .build-deps \
    && apk add --update --no-cache \
        jpeg \
        libstdc++

COPY dumpsc.py /app/dumpsc.py

WORKDIR /data

ENTRYPOINT [ "python", "/app/dumpsc.py", "-o", "/data" ]
