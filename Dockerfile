FROM python:3.9.18

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

WORKDIR app
COPY requirements.txt ./
RUN pip install --user --trusted-host pypi.python.org -r requirements.txt
COPY . /app/

EXPOSE 8000

CMD ["python3", "plate-deformation/main.py"]
