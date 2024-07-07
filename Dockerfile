
FROM python:3.9.2-slim-buster
RUN mkdir /app && chmod 777 /app
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
RUN apt -qq install -y git python3 python3-pip ffmpeg
COPY . . 
RUN pip3 install --no-cache-dir -r requirements.txt
CMD echo "starting Bot ~@TeamDrom" & flask run -h 0.0.0.0 -p 10000 & python3 -m main
