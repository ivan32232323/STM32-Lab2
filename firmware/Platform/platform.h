/**
 * platform.h — «порт» платформи для прикладного шару.
 *
 * Це ЄДИНИЙ заголовок Platform/, який дозволено включати з App/.
 * Він не містить жодного типу HAL; реалізація — Platform/platform.c,
 * у хостових тестах — tests/doubles/fake_platform.c.
 */
#ifndef PLATFORM_H
#define PLATFORM_H

#include <stdint.h>
#include "bus.h"

typedef enum { SERVO_PAN = 0, SERVO_TILT = 1 } servo_id_t;
typedef enum { PROBE_ADC = 0, PROBE_LOOP = 1 } probe_id_t;   /* службові GPIO для LA */

uint32_t plat_millis(void);
void     plat_delay_ms(uint32_t ms);
uint32_t plat_sysclk_hz(void);

/* UART (VCP) */
void plat_puts(const char *s);
int  plat_getc(void);                 /* -1, якщо байта немає */

/* Аналоговий вхід (потенціометр). Під час перетворення PROBE_ADC = 1. */
int  plat_adc_read(uint16_t *value);

/* Серво: ширина імпульсу в мкс (TIM3: 1 тік = 1 мкс) */
void     plat_servo_set_us(servo_id_t ch, uint32_t us);
uint32_t plat_servo_get_us(servo_id_t ch);

void plat_led(int on);
void plat_led_toggle(void);
int  plat_button_pressed(void);       /* 1 = натиснута (активний 0 на піні) */
void plat_probe(probe_id_t p, int level);

/* Шини для драйверів Devices/ */
const i2c_bus_t *plat_i2c_hw(void);   /* HAL I2C1 PB8/PB9                    */
const i2c_bus_t *plat_i2c_sw(void);   /* bit-bang на тих самих пінах         */
const spi_dev_t *plat_flash_spi(void);/* SPI1 PB3/PB4/PB5 + CS# PB10         */

/* Діагностика останньої помилки HAL I2C (HAL_I2C_GetError) */
uint32_t plat_i2c_hw_last_error(void);

#endif
