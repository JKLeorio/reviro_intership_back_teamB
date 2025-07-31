FROM minio/minio

WORKDIR /data

EXPOSE 80
EXPOSE 81

ENTRYPOINT ["minio", "server", "--address", ":80", "--console-address", ":81", "/data", "--quiet"]
