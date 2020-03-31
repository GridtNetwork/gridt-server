FROM python:3.8 AS builder
ENV PYTHONUNBUFFERED 1

WORKDIR /packages/
RUN pip install -U pip && pip install pipenv
COPY Pipfile.lock Pipfile /packages/
RUN bash -c 'PIPENV_VENV_IN_PROJECT=1 pipenv install'

FROM python:3.8
ARG FLASK_CONFIGURATION
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /usr/src/gridt-server
COPY --from=builder /packages/ /packages
ENV PATH="/packages/.venv/bin:${PATH}" FLASK_CONFIGURATION=${FLASK_CONFIGURATION}
WORKDIR /usr/src/gridt-server
COPY . /usr/src/gridt-server

EXPOSE 8000
CMD ["gunicorn", "-w", "2", "-b", ":8000", "wsgi:app"]
