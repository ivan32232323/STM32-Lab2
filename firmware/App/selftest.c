#include "selftest.h"
#include "platform.h"
#include "attitude.h"
#include "servo_map.h"
#include <stdio.h>
#include <string.h>

static const char *const LVL[] = { "PASS", "FAIL", "WARN", "INFO" };

int st_format(char *buf, unsigned len, const char *dev, const char *check,
              st_level_t lvl, const char *value, const char *crit)
{
  return snprintf(buf, len, "ST;%s;%s;%s;%s;%s\r\n", dev, check, LVL[lvl],
                  value ? value : "", crit ? crit : "");
}

void st_emit(st_counts_t *c, const char *dev, const char *check,
             st_level_t lvl, const char *value, const char *crit)
{
  char line[96];
  st_format(line, sizeof line, dev, check, lvl, value, crit);
  plat_puts(line);
  if (lvl == ST_PASS) c->pass++;
  else if (lvl == ST_FAIL) c->fail++;
  else if (lvl == ST_WARN) c->warn++;
}

int st_accel_norm_ok(int32_t ax, int32_t ay, int32_t az, uint32_t *norm)
{
  uint32_t n = isqrt32((uint32_t)(ax * ax + ay * ay + az * az));
  if (norm) *norm = n;
  return n >= 950u && n <= 1050u;
}
int st_temp_ok(int32_t cdeg) { return cdeg >= 1500 && cdeg <= 3500; }
int st_gyro_still_ok(int32_t gx, int32_t gy, int32_t gz)
{
  const int32_t lim = 5000;   /* 5 °/с у мілі-°/с */
  return gx > -lim && gx < lim && gy > -lim && gy < lim && gz > -lim && gz < lim;
}

static const char *bus_err(int st)
{
  switch (st) {
  case BUS_OK: return "ok"; case BUS_NACK: return "nack"; case BUS_TIMEOUT: return "timeout";
  case BUS_BADID: return "bad_id"; case BUS_ARG: return "arg"; default: return "error";
  }
}

static void st_imu(selftest_ctx_t *x)
{
  st_counts_t *c = &x->counts;
  char v[40];
  uint8_t id = 0;
  x->imu.addr = MPU6050_ADDR_AD0_LOW;

  /* 1) апаратний I2C1 */
  x->imu.bus = plat_i2c_hw();
  int st = mpu6050_read_id(&x->imu, &id);
  if (st != BUS_OK || id != MPU6050_WHO_AM_I_VALUE) {
    snprintf(v, sizeof v, "%s err=0x%02lX id=0x%02X", bus_err(st),
             (unsigned long)plat_i2c_hw_last_error(), id);
    st_emit(c, "I2C1", "hw_read", ST_WARN, v, "HAL_I2C_Mem_Read ok");
    x->imu.bus = plat_i2c_sw();                 /* 2) bit-bang на тих самих пінах */
    st_emit(c, "I2C1", "bus", ST_INFO, "soft-i2c", "fallback");
  } else {
    st_emit(c, "I2C1", "bus", ST_INFO, "hal-i2c1", "");
  }

  st = mpu6050_read_id(&x->imu, &id);
  snprintf(v, sizeof v, "0x%02X", id);
  st_emit(c, "MPU6050", "who_am_i", (st == BUS_OK && id == 0x68) ? ST_PASS : ST_FAIL, v, "0x68");
  if (st != BUS_OK || id != 0x68) return;

  st = mpu6050_init(&x->imu);
  st_emit(c, "MPU6050", "init", st == BUS_OK ? ST_PASS : ST_FAIL, bus_err(st), "ok");
  if (st != BUS_OK) return;
  plat_delay_ms(20);                            /* > 1/100 Гц: новий зразок у регістрах */

  mpu6050_raw_t raw; mpu6050_data_t d;
  st = mpu6050_read_raw(&x->imu, &raw);
  st_emit(c, "MPU6050", "burst14", st == BUS_OK ? ST_PASS : ST_FAIL, bus_err(st), "ok");
  if (st != BUS_OK) return;
  mpu6050_convert(&raw, &d);

  uint32_t n;
  snprintf(v, sizeof v, "%ld,%ld,%ld", (long)d.ax_mg, (long)d.ay_mg, (long)d.az_mg);
  st_emit(c, "MPU6050", "accel_mg", ST_INFO, v, "");
  int ok = st_accel_norm_ok(d.ax_mg, d.ay_mg, d.az_mg, &n);
  snprintf(v, sizeof v, "%lu", (unsigned long)n);
  st_emit(c, "MPU6050", "accel_norm_mg", ok ? ST_PASS : ST_FAIL, v, "1000+-5%");
  snprintf(v, sizeof v, "%ld.%02ld", (long)(d.temp_cdeg / 100), (long)((d.temp_cdeg < 0 ? -d.temp_cdeg : d.temp_cdeg) % 100));
  st_emit(c, "MPU6050", "temp_c", st_temp_ok(d.temp_cdeg) ? ST_PASS : ST_FAIL, v, "15..35");
  snprintf(v, sizeof v, "%ld,%ld,%ld", (long)d.gx_mdps, (long)d.gy_mdps, (long)d.gz_mdps);
  st_emit(c, "MPU6050", "gyro_mdps", st_gyro_still_ok(d.gx_mdps, d.gy_mdps, d.gz_mdps) ? ST_PASS : ST_FAIL,
          v, "|w|<5dps");
  x->imu_ok = 1;
}

#define FLASH_TEST_ADDR 0x001000u      /* сектор 1; сектор 0 лишаємо під заголовок траєкторії (ЛР3) */
#define FLASH_TEST_LEN  16u

static void st_flash(selftest_ctx_t *x)
{
  st_counts_t *c = &x->counts;
  char v[40];
  uint32_t id = 0;
  x->flash.spi = plat_flash_spi();
  int st = w25q_read_jedec(&x->flash, &id);
  snprintf(v, sizeof v, "0x%06lX", (unsigned long)id);
  st_emit(c, "W25Q64", "jedec_id", (st == BUS_OK && id == W25Q64_JEDEC_ID) ? ST_PASS : ST_FAIL, v, "0xEF4017");
  if (w25q_init(&x->flash) != BUS_OK) return;

  uint8_t wr[FLASH_TEST_LEN], rd[FLASH_TEST_LEN];
  for (unsigned i = 0; i < FLASH_TEST_LEN; i++) wr[i] = (uint8_t)(0x5Au ^ (i * 0x11u));

  st = w25q_sector_erase(&x->flash, FLASH_TEST_ADDR);
  st_emit(c, "W25Q64", "sector_erase", st == BUS_OK ? ST_PASS : ST_FAIL, bus_err(st), "ok");
  memset(rd, 0, sizeof rd);
  st = w25q_read(&x->flash, FLASH_TEST_ADDR, rd, sizeof rd);
  int blank = st == BUS_OK;
  for (unsigned i = 0; i < FLASH_TEST_LEN; i++) blank &= rd[i] == 0xFFu;
  st_emit(c, "W25Q64", "blank_check", blank ? ST_PASS : ST_FAIL, blank ? "all_FF" : "dirty", "all_FF");

  st = w25q_page_program(&x->flash, FLASH_TEST_ADDR, wr, sizeof wr);
  st_emit(c, "W25Q64", "page_program", st == BUS_OK ? ST_PASS : ST_FAIL, bus_err(st), "ok");
  st = w25q_read(&x->flash, FLASH_TEST_ADDR, rd, sizeof rd);
  unsigned diff = 0;
  for (unsigned i = 0; i < FLASH_TEST_LEN; i++) diff += rd[i] != wr[i];
  snprintf(v, sizeof v, "%u/%u_diff", diff, FLASH_TEST_LEN);
  st_emit(c, "W25Q64", "readback", (st == BUS_OK && diff == 0) ? ST_PASS : ST_FAIL, v, "0_diff");
  x->flash_ok = (diff == 0);
}

static void st_adc_pwm_gpio(selftest_ctx_t *x)
{
  st_counts_t *c = &x->counts;
  char v[40];
  uint16_t a = 0, b = 0;
  int st = plat_adc_read(&a);
  if (st == BUS_OK) st = plat_adc_read(&b);
  int d = (int)a - (int)b;
  if (d < 0) d = -d;
  snprintf(v, sizeof v, "%u,%u", a, b);
  st_emit(c, "POT", "adc_two_reads", (st == BUS_OK && d <= 8) ? ST_PASS : ST_FAIL, v, "|d|<=8LSB");

  /* PWM: дві різні ширини по 3 періоди — видно на LA (docs/captures) */
  static const int32_t us_set[] = { SERVO_MIN_US, SERVO_MAX_US };
  for (unsigned i = 0; i < 2; i++) {
    plat_servo_set_us(SERVO_PAN, (uint32_t)us_set[i]);
    plat_delay_ms(60);
    uint32_t got = plat_servo_get_us(SERVO_PAN);
    snprintf(v, sizeof v, "%lu", (unsigned long)got);
    st_emit(c, "SERVO_PAN", i ? "ccr_2000" : "ccr_1000", got == (uint32_t)us_set[i] ? ST_PASS : ST_FAIL, v,
            i ? "2000us" : "1000us");
  }
  plat_servo_set_us(SERVO_PAN, SERVO_MID_US);
  plat_servo_set_us(SERVO_TILT, SERVO_MID_US);

  int pressed = plat_button_pressed();
  st_emit(c, "BTN", "idle_level", pressed ? ST_WARN : ST_PASS, pressed ? "pressed" : "released", "released");
}

int selftest_run(selftest_ctx_t *x)
{
  char v[40];
  memset(&x->counts, 0, sizeof x->counts);
  x->imu_ok = x->flash_ok = 0;
  snprintf(v, sizeof v, "sysclk=%lu", (unsigned long)plat_sysclk_hz());
  st_emit(&x->counts, "BEGIN", "lab2", ST_INFO, v, "fmt=v1");
  st_imu(x);
  st_flash(x);
  st_adc_pwm_gpio(x);
  st_counts_t *c = &x->counts;
  snprintf(v, sizeof v, "pass=%d fail=%d warn=%d", c->pass, c->fail, c->warn);
  char line[96];
  st_format(line, sizeof line, "SUMMARY", "all", c->fail ? ST_FAIL : ST_PASS, v, "");
  plat_puts(line);
  return c->fail;
}
