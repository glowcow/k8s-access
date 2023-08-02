FROM python:3.10-slim-bookworm AS stage-1
WORKDIR /builder
COPY requirements.txt .
RUN pip3 wheel --no-cache-dir --no-deps --wheel-dir /builder/wheels -r requirements.txt

FROM python:3.10-slim-bookworm AS stage-2
WORKDIR /app
ARG TZ=Asia/Jerusalem
ENV PYTHONUNBUFFERED=1
ENV KUBECONFIG=/app/kube_conf.yaml
COPY --from=stage-1 /builder/wheels /wheels
COPY . /app/
RUN ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata \
    && pip3 install --no-cache /wheels/*

CMD ["/usr/bin/tail", "-f", "/dev/null"]
