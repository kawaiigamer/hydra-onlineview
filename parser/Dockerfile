FROM python:latest
COPY . .
RUN pip install requests[socks]
RUN pip install psycopg2
RUN pip install Flask
RUN pip install bs4
RUN pip install lxml
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
CMD python ./parser.py -bu ${USERNAME} -bp ${PASSWORD} -r ${REGION} -c "${CATEGORYES}"
