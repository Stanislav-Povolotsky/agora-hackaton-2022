FROM python:3.9.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ENV PORT=8100
COPY src/requirements.txt /code/
RUN pip install -r requirements.txt
RUN mkdir ./logs ./data ./var
COPY ./src /code/app/
#CMD python server/server.py >>data/logs/stdout.log 2>&1
CMD python app/server.py 
