FROM python:3-alpine

ENV APP_HOME /app
WORKDIR $APP_HOME

RUN apk add bc gcc linux-headers musl-dev


# RUN pip install --no-binary gevent gevent
RUN pip install setuptools
RUN pip install Flask requests gevent
COPY . $APP_HOME

CMD ["python", "calc-pi.py"]
