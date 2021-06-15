FROM python:3.6.9-buster

RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /usr/share/git/system_reliability

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENV INPUT_HAZARD earthquake
ENV INPUT_COUNTRY ecuador
ENV INPUT_INTENSITY_0 ./testinputs/shakemap.xml
ENV OUTPUT_DAMAGE_CONSUMER_AREAS /tmp/output/output.json

RUN chmod +x javaps_wrapper.sh

CMD ["bash", "-c", "./javaps_wrapper.sh"]