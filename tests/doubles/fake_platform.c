/**
 * fake_platform.c — реалізація platform.h для хоста (STUB-и + захоплення UART).
 * Дає змогу виконати App/selftest.c без плати.
 */
#include "fake_platform.h"
#include <string.h>

fake_platform_t fp;

void fake_platform_reset(void)
{
  memset(&fp, 0, sizeof fp);
  fp.adc_value = 2048;
}

uint32_t plat_millis(void) { return fp.now_ms; }
void plat_delay_ms(uint32_t ms) { fp.now_ms += ms; }
uint32_t plat_sysclk_hz(void) { return 48000000u; }

void plat_puts(const char *s)
{
  size_t n = strlen(s), room = sizeof fp.out - 1 - fp.out_len;
  if (n > room) n = room;
  memcpy(fp.out + fp.out_len, s, n);
  fp.out_len += n;
  fp.out[fp.out_len] = '\0';
}
int plat_getc(void) { return -1; }

int plat_adc_read(uint16_t *v) { fp.adc_reads++; *v = fp.adc_value; return fp.adc_fail ? BUS_TIMEOUT : BUS_OK; }
void plat_servo_set_us(servo_id_t ch, uint32_t us) { fp.servo[ch] = fp.servo_stuck ? fp.servo[ch] : us; }
uint32_t plat_servo_get_us(servo_id_t ch) { return fp.servo[ch]; }
void plat_led(int on) { fp.led = on; }
void plat_led_toggle(void) { fp.led = !fp.led; }
int  plat_button_pressed(void) { return fp.button; }
void plat_probe(probe_id_t p, int level) { fp.probe[p] = level; }

const i2c_bus_t *plat_i2c_hw(void) { return fp.i2c_hw; }
const i2c_bus_t *plat_i2c_sw(void) { return fp.i2c_sw; }
const spi_dev_t *plat_flash_spi(void) { return fp.spi; }
uint32_t plat_i2c_hw_last_error(void) { return fp.i2c_hw_err; }
