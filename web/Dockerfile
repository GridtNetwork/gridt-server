FROM python:3

RUN mkdir -p /usr/src/gridt-server
WORKDIR /usr/src/gridt-server
COPY . /usr/src/gridt-server

RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile

EXPOSE 8000
CMD ["gunicorn", "-w", "2", "-b", ":8000", "wsgi:app"]
