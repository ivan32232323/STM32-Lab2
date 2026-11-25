# Тулчейн-образ ЛР2: docker build -t stm32-build:lab2 docker/
# Версії пакетів зафіксовано (=версія), щоб збірка через рік дала той самий
# результат; для повної незмінності базового образу тег можна замінити на
# digest: docker inspect --format='{{index .RepoDigests 0}}' ubuntu:22.04
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      make=4.3-4.1build1 \
      gcc-arm-none-eabi=15:10.3-2021.07-4 \
      binutils-arm-none-eabi=2.38-3ubuntu1+15build1 \
      libnewlib-arm-none-eabi=3.3.0-1.3 \
      gcc=4:11.2.0-1ubuntu1 \
      clang=1:14.0-55~exp2 lld=1:14.0-55~exp2 \
      python3 python3-pip git ca-certificates \
 && pip3 install --no-cache-dir gcovr==8.8 \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
