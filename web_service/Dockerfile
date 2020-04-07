FROM python:latest
COPY . .
RUN pip install requests[socks]
RUN pip install Flask
CMD python ./web_service.py
