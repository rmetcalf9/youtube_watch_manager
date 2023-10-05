ARG PYTHON_IMAGE

FROM ${PYTHON_IMAGE}

MAINTAINER Robert Metcalf

COPY ./requirements.txt requirements.txt

RUN pip3 install -r requirements.txt
