FROM minio/minio

WORKDIR /data

EXPOSE 80
EXPOSE 81

ENTRYPOINT ["minio", "server", "--console-address", ":80", "/data", "--address", ":81", "--quiet"]
