FROM 52north/tum-era-critical-infrastructure-analysis-single:latest

COPY javaps_wrapper_multi.sh ./javaps_wrapper.sh
RUN chmod +x javaps_wrapper.sh

ENV INPUT_HAZARD lahar
ENV INPUT_COUNTRY ecuador
ENV INPUT_HEIGHT=./testinputs/Lahar_N_VEI3mio_maxheight_25m.xml
ENV INPUT_VELOCITY=./testinputs/Lahar_N_VEI3mio_maxvelocity_25m.xml
ENV OUTPUT_DAMAGE_CONSUMER_AREAS /tmp/output/output.json

