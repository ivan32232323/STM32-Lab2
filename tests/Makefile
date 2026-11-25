##########################################################################
# tests/Makefile — хостові тести (звичайний gcc, без плати і без Docker-ARM)
#   make -C tests          зібрати й запустити всі тести
#   make -C tests coverage звіт покриття (gcovr) для Devices/ і App/
##########################################################################
CC      ?= gcc
FW       = ../firmware
BUILD    = build
UNITY    = vendor/unity
COV_MIN ?= 90

CFLAGS  = -std=c11 -O0 -g -Wall -Wextra -Werror -Wno-unused-function \
          -I$(FW)/Devices -I$(FW)/App -I$(FW)/Platform -Idoubles -I. -I$(UNITY) \
          -DUNITY_INCLUDE_DOUBLE -DUNITY_SUPPORT_64 --coverage
LDLIBS  = -lm --coverage

# Тест -> модулі, які він перевіряє (лише Devices/ і App/, жодного HAL)
DEV  = $(FW)/Devices
APP  = $(FW)/App
SRC_test_mpu6050   = $(DEV)/mpu6050.c doubles/fake_i2c.c
SRC_test_w25q      = $(DEV)/w25q.c doubles/mock_spi.c
SRC_test_app_logic = $(APP)/servo_map.c $(APP)/attitude.c $(APP)/cli.c
SRC_test_selftest  = $(APP)/selftest.c $(APP)/attitude.c $(APP)/servo_map.c \
                     $(DEV)/mpu6050.c $(DEV)/w25q.c \
                     doubles/fake_i2c.c doubles/mock_spi.c doubles/fake_platform.c

TESTS = test_mpu6050 test_w25q test_app_logic test_selftest

all: run

# Залежність від модулів під тестом (SRC_<тест>) — інакше зміна драйвера не перезбирає тест
.SECONDEXPANSION:
$(BUILD)/%: %.c $(UNITY)/unity.c $$(SRC_$$*) $$(wildcard doubles/*.h) la_vectors.h Makefile
	@mkdir -p $(BUILD)
	@$(CC) $(CFLAGS) $< $(UNITY)/unity.c $(SRC_$*) $(LDLIBS) -o $@

run: $(addprefix $(BUILD)/,$(TESTS))
	@rm -f $(BUILD)/*.gcda          # лічильники лише цього прогону
	@fail=0; for t in $(TESTS); do echo "== $$t"; ./$(BUILD)/$$t || fail=1; done; exit $$fail

coverage: run
	@gcovr --root .. \
	  --filter '../firmware/Devices/' --filter '../firmware/App/' \
	  --exclude '../firmware/App/app.c' \
	  --txt --txt-summary --fail-under-line $(COV_MIN) \
	  --html-details $(BUILD)/coverage.html \
	  $(BUILD)

clean:
	rm -rf $(BUILD)

.PHONY: all run coverage clean
