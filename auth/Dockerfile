FROM python:3.7

COPY . .
RUN pip install -r requirements.txt
EXPOSE 5001


ENTRYPOINT ["python3", "auth_instance.py"]
