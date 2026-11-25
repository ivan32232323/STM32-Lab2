##########################################################################
# Кореневий Makefile (ЛР2) — усі цілі виконуються в Docker-образі тулчейну,
# тому результат не залежить від машини (локально, CI, через рік).
#
#   make image     зібрати образ (один раз; версії пакетів зафіксовані)
#   make build     прошивка firmware/build/firmware.{elf,hex,bin}, -Wall -Wextra -Werror
#   make test      хостові тести (gcc + Unity), плата не потрібна
#   make coverage  тести + звіт покриття Devices/ і App/ (поріг 90 % рядків)
#   make check     правило залежностей шарів + узгодженість pinout
#   make chip      модель W25Q64 для Wokwi (clang -> wasm)
#   make ci        build + check + coverage (те, що запускає GitHub Actions)
#   make flash / monitor — підказки для Wokwi і реальної плати
#
#   NATIVE=1 make <ціль>  — те саме без Docker (якщо тулчейн уже встановлено)
##########################################################################
IMAGE ?= stm32-build:lab2
ELF    = firmware/build/firmware.elf
PORT  ?= /dev/ttyACM0

ifeq ($(NATIVE),1)
  RUN =
else
  ifeq ($(OS),Windows_NT)
    DOCKER_USER :=
  else
    DOCKER_USER := --user $(shell id -u):$(shell id -g)
  endif
  RUN = docker run --rm -v "$(CURDIR)":/workspace -w /workspace $(DOCKER_USER) $(IMAGE)
endif

image:
	docker build -t $(IMAGE) docker/

build:
	$(RUN) make -C firmware all

test:
	$(RUN) make -C tests run

# Тести завжди перезбираються: .gcno/.gcda містять абсолютні шляхи збірки,
# і чужі бінарники (з іншої машини/контейнера) дають покриття 0 %.
coverage:
	$(RUN) make -C tests clean
	$(RUN) make -C tests coverage

check:
	$(RUN) python3 tools/check_deps.py firmware
	$(RUN) python3 tools/check_pinout.py

chip:
	$(RUN) make -C chips

ci: build check coverage

clean:
	$(RUN) make -C firmware clean
	$(RUN) make -C tests clean

flash: build
	@echo "ELF готовий: $(ELF)"
	@echo "Wokwi: F1 -> 'Wokwi: Restart Simulator' (wokwi.toml вказує на firmware/build/firmware.hex)."
	@echo "Форма A: st-flash --reset write firmware/build/firmware.bin 0x08000000"

monitor:
	@echo "Wokwi: вивід USART2 — у панелі Serial Monitor/терміналі симулятора."
	@echo "Форма A: picocom -b 115200 --imap lfcrlf $(PORT)"
	@echo "Розбір self-test: python3 tools/parse_selftest.py <лог>"

.PHONY: image build test coverage check chip ci clean flash monitor
