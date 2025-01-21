FROM public.ecr.aws/lambda/python:3.10

RUN yum install -y zip && \
    mkdir -p /lambda/python/lib/python3.10/site-packages && \
    pip3 install --default-timeout=100 --target /lambda/python/lib/python3.10/site-packages \
    opencv-python-headless==4.10.0.84 \
    numpy==1.24.3 --no-deps && \
    cd /lambda && \
    zip -r layer.zip python

WORKDIR /lambda

CMD ["bash"]