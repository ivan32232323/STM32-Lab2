# Збірка моделі W25Q64 для Wokwi: make -C chips
# Потрібен clang з ціллю wasm32 і wasm-ld (lld). libc не використовується.
CLANG ?= clang
w25q64.chip.wasm: w25q64.chip.c wokwi-api.h
	$(CLANG) --target=wasm32-unknown-wasi -O2 -nostdlib -ffreestanding \
	  -Wall -Wextra -Wno-unused-parameter -Wno-unused-function \
	  -Wl,--import-memory -Wl,--export-table -Wl,--no-entry \
	  -o $@ $<
.PHONY: clean
clean:
	rm -f w25q64.chip.wasm
