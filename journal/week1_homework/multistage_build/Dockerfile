FROM debian:10-slim AS basecontainer
RUN apt-get update && apt-get upgrade --yes && apt-get install sudo apt-utils python3 --yes


FROM basecontainer AS buildtool
RUN sudo apt-get update && sudo apt-get install git build-essential cmake --yes
RUN sudo apt-get install gcc-arm-none-eabi \
                        libnewlib-arm-none-eabi \
                        libstdc++-arm-none-eabi-newlib --yes


FROM buildtool AS sdkgetter
RUN adduser pico_user
USER pico_user
WORKDIR /home/pico_user
RUN git clone https://github.com/raspberrypi/pico-sdk.git --branch master && cd pico-sdk && git submodule update --init


FROM sdkgetter
ENV PICO_SDK_PATH="/home/pico_user/pico-sdk"
EXPOSE 5000