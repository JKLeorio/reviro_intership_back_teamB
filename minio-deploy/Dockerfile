FROM minio/minio

WORKDIR /data

EXPOSE 9000
EXPOSE 9001

ENTRYPOINT ["minio", "server", "--address", ":9000", "--console-address", ":9001", "/data", "--quiet"]
