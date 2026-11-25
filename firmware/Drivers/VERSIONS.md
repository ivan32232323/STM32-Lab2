# Версії сторонніх бібліотек (vendoring)

Код у `Drivers/`, `tests/vendor/` і `chips/wokwi-api.h` не редагується. Щоб
оновити бібліотеку, замініть каталог цілком і змініть рядок у таблиці.

| Бібліотека | Версія | Джерело | Як перевірити |
|---|---|---|---|
| STM32C0xx HAL Driver | **v1.4.1** (`__STM32C0xx_HAL_VERSION` = 0x01040100) | github.com/STMicroelectronics/stm32c0xx-hal-driver, тег `v1.4.1`, коміт `038bed9f00e0c07328627470328fe8abc184d071`; той самий, що в STM32Cube FW_C0 V1.4.1 (`firmware.ioc`) | `grep VERSION_ Src/stm32c0xx_hal.c` |
| CMSIS Device STM32C0 | **v1.4.1** (`__STM32C0_CMSIS_VERSION`) | STM32Cube FW_C0 V1.4.1 | `grep CMSIS_VERSION_ Include/stm32c0xx.h` |
| CMSIS Core(M) | **5.x** (`__CM_CMSIS_VERSION_MAIN` = 5, SUB = 3) | STM32Cube FW_C0 V1.4.1 | `Include/cmsis_version.h` |
| Unity (тести) | **v2.6.0** | github.com/ThrowTheSwitch/Unity, архів тегу v2.6.0, sha256 `aa4c9fb1ae5fc5242f914c65f3557e817e40cb37f04a31e5ff76d1ab89dbf674` | `tests/vendor/unity/unity.h` |
| Wokwi Chips API | `wokwi-api.h` версії 1 (`__wokwi_api_version_1`) | github.com/wokwi/inverter-chip (MIT) | `chips/wokwi-api.h` |

У ЛР2 з HAL додано лише `stm32c0xx_hal_spi.c` і `stm32c0xx_hal_spi_ex.c` з того самого тегу v1.4.1.
Модулі, які компілюються, перелічені явно (`HAL_USED` у `firmware/Makefile`), а не через `wildcard`.

Тулчейн зафіксовано в `docker/Dockerfile`: arm-none-eabi-gcc 10.3-2021.07, binutils 2.38, newlib 3.3.0, gcovr 8.8.
