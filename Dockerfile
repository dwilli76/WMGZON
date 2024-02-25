FROM python:3.12.2
WORKDIR /WMGZON
ADD . /WMGZON

COPY ./requirements.txt /app
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python","app.py"]