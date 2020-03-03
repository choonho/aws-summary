FROM python:3

ENV PYTHONUNBUFFERED 1
ENV CLOUDONE_PORT 50051
ENV SERVER_TYPE grpc
ENV PKG_DIR /tmp/pkg
ENV SRC_DIR /tmp/src

COPY pkg/*.txt ${PKG_DIR}/
RUN apt-get update && apt-get install -y \
    $(cat ${PKG_DIR}/apt_packages.txt) && \
    pip install --upgrade pip && \
    pip install --upgrade -r ${PKG_DIR}/pip_requirements.txt

COPY src ${SRC_DIR}

WORKDIR ${SRC_DIR}
RUN python3 setup.py install && \
    rm -rf /tmp/*

EXPOSE ${CLOUDONE_PORT}

WORKDIR /opt

ENTRYPOINT ["server"]
CMD ["grpc", "inventory"]
