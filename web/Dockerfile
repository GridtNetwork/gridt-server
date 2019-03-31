FROM python:3.7 AS builder
ENV PYTHONUNBUFFERED 1

# pipenv install --system --deploy --ignore-pipfile
WORKDIR /build/
RUN pip install -U pip && pip install pipenv
COPY Pipfile.lock Pipfile /build/
RUN bash -c 'PIPENV_VENV_IN_PROJECT=1 pipenv install'

FROM python:3.7-slim
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /usr/src/gridt-server
COPY --from=builder /build/ /usr/src/gridt-server
WORKDIR /usr/src/gridt-server
COPY . /usr/src/gridt-server

RUN . .venv/bin/activate
# RUN .venv/bin/flask initdb
RUN flask initdb
EXPOSE 8000
CMD [".venv/bin/gunicorn", "-w", "2", "-b", ":8000", "wsgi:app"]
