##########################################################################
# firmware/Makefile — STM32C031C6 (Nucleo-C031C6 / Wokwi), ЛР2
#
# Шари (docs/architecture.md):
#   Core/      CubeMX: init периферії, IRQ, main -> app_main()
#   Drivers/   CMSIS + HAL від ST (не редагуються, версії — Drivers/VERSIONS.md)
#   Platform/  board.h (піни/хендли) + реалізація platform.h і шин над HAL
#   Devices/   драйвери MPU-6050, W25Q64 — лише через Devices/bus.h
#   App/       прикладна логіка — лише platform.h + Devices/
#
# Власний код: -Wall -Wextra -Werror. Вендорський: ті ж -Wall -Wextra, але
# з точково вимкненими попередженнями (VENDOR_WNO) і -isystem для заголовків.
##########################################################################
TARGET    = firmware
BUILD_DIR = build
OPT      ?= -Os -flto

OWN_SOURCES = \
  $(wildcard Core/Src/*.c) \
  $(wildcard Platform/*.c) \
  $(wildcard Devices/*.c) \
  $(wildcard App/*.c)

HAL_USED = adc adc_ex cortex dma dma_ex flash flash_ex gpio i2c i2c_ex pwr pwr_ex \
           rcc rcc_ex spi spi_ex tim tim_ex uart uart_ex
VENDOR_SOURCES = Drivers/STM32C0xx_HAL_Driver/Src/stm32c0xx_hal.c \
  $(foreach m,$(HAL_USED),Drivers/STM32C0xx_HAL_Driver/Src/stm32c0xx_hal_$(m).c)

ASM_SOURCES = startup_stm32c031xx.s

PREFIX = arm-none-eabi-
CC = $(PREFIX)gcc
CP = $(PREFIX)objcopy
SZ = $(PREFIX)size

MCU = -mcpu=cortex-m0plus -mthumb
C_DEFS = -DUSE_HAL_DRIVER -DSTM32C031xx

OWN_INC = -ICore/Inc -IPlatform -IDevices -IApp
SYS_INC = -isystem Drivers/STM32C0xx_HAL_Driver/Inc \
          -isystem Drivers/STM32C0xx_HAL_Driver/Inc/Legacy \
          -isystem Drivers/CMSIS/Device/ST/STM32C0xx/Include \
          -isystem Drivers/CMSIS/Include

COMMON = $(MCU) $(C_DEFS) $(OWN_INC) $(SYS_INC) $(OPT) -g -std=gnu11 \
         -fdata-sections -ffunction-sections -ffile-prefix-map=$(CURDIR)=.
WARN_OWN    = -Wall -Wextra -Werror -Wshadow -Wdouble-promotion
VENDOR_WNO  = -Wno-unused-parameter
CFLAGS_OWN    = $(COMMON) $(WARN_OWN)
CFLAGS_VENDOR = $(COMMON) -Wall -Wextra $(VENDOR_WNO)

LDSCRIPT = STM32C031C6Tx_FLASH.ld
LDFLAGS  = $(MCU) -specs=nano.specs -T$(LDSCRIPT) -lc -lm -lnosys \
           -Wl,-Map=$(BUILD_DIR)/$(TARGET).map,--cref -Wl,--gc-sections \
           -Wl,--print-memory-usage $(LD_RWX)
# binutils ≥ 2.39 попереджає про RWX-сегмент startup; ключ є лише там
LD_RWX := $(shell $(PREFIX)ld --help 2>/dev/null | grep -q no-warn-rwx && echo -Wl,--no-warn-rwx-segments)

OWN_OBJ    = $(addprefix $(BUILD_DIR)/obj/,$(OWN_SOURCES:.c=.o))
VENDOR_OBJ = $(addprefix $(BUILD_DIR)/obj/,$(VENDOR_SOURCES:.c=.o))
ASM_OBJ    = $(addprefix $(BUILD_DIR)/obj/,$(ASM_SOURCES:.s=.o))
OBJECTS    = $(OWN_OBJ) $(VENDOR_OBJ) $(ASM_OBJ)

# Системні виклики newlib (_sbrk, _write…) викликаються з libc.a, яку LTO не бачить:
# компілюємо їх без LTO, інакше лінкер «губить» _sbrk.
NO_LTO_OBJ = $(BUILD_DIR)/obj/Core/Src/syscalls.o $(BUILD_DIR)/obj/Core/Src/sysmem.o
$(NO_LTO_OBJ): CFLAGS_OWN += -fno-lto

all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin

$(OWN_OBJ): $(BUILD_DIR)/obj/%.o: %.c Makefile
	@mkdir -p $(dir $@)
	@echo "CC  $<"
	@$(CC) -c $(CFLAGS_OWN) -MMD -MP $< -o $@

$(VENDOR_OBJ): $(BUILD_DIR)/obj/%.o: %.c Makefile
	@mkdir -p $(dir $@)
	@echo "CC  $< (vendor)"
	@$(CC) -c $(CFLAGS_VENDOR) -MMD -MP $< -o $@

$(ASM_OBJ): $(BUILD_DIR)/obj/%.o: %.s Makefile
	@mkdir -p $(dir $@)
	@echo "AS  $<"
	@$(CC) -x assembler-with-cpp -c $(MCU) -g $< -o $@

$(BUILD_DIR)/$(TARGET).elf: $(OBJECTS) $(LDSCRIPT)
	@echo "LD  $@"
	@$(CC) $(OBJECTS) $(LDFLAGS) -o $@
	@$(SZ) $@

$(BUILD_DIR)/%.hex: $(BUILD_DIR)/%.elf
	@$(CP) -O ihex $< $@

$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf
	@$(CP) -O binary -S $< $@

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all clean
-include $(shell find $(BUILD_DIR) -name '*.d' 2>/dev/null)
