FROM minio/minio

WORKDIR /data

EXPOSE 80

ENTRYPOINT ["minio", "server", "--console-address", ":80", "/data", "--address", ":80", "--quiet"]
