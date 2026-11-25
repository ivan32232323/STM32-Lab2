/**
 * mpu6050.c — драйвер MPU-6050. Залежить лише від bus.h.
 */
#include "mpu6050.h"

static int reg_write(const mpu6050_t *d, uint8_t reg, uint8_t val)
{
  const uint8_t b[2] = { reg, val };
  return d->bus->write(d->bus->ctx, d->addr, b, 2);
}

static int reg_read(const mpu6050_t *d, uint8_t reg, uint8_t *buf, size_t n)
{
  return d->bus->write_read(d->bus->ctx, d->addr, &reg, 1, buf, n);
}

int mpu6050_read_id(const mpu6050_t *dev, uint8_t *id)
{
  if (!dev || !dev->bus || !id) return BUS_ARG;
  return reg_read(dev, MPU6050_REG_WHO_AM_I, id, 1);
}

int mpu6050_init(const mpu6050_t *dev)
{
  uint8_t id = 0;
  int st = mpu6050_read_id(dev, &id);
  if (st != BUS_OK) return st;
  /* WHO_AM_I містить біти [6:1] адреси, AD0 не відображається: 0x68 для обох */
  if (id != MPU6050_WHO_AM_I_VALUE) return BUS_BADID;

  /* Послідовність ініціалізації (RM 4.28, 4.3–4.5, 4.2):
   * 1) PWR_MGMT_1 = 0x01: вийти зі сну, тактування від PLL гіроскопа X
   * 2) CONFIG = 0x03: DLPF 44 Гц (accel) / 42 Гц (gyro), Fs_int = 1 кГц
   * 3) SMPLRT_DIV = 9: 1 кГц / (1 + 9) = 100 Гц ≥ 2 × 50 Гц контуру
   * 4) GYRO_CONFIG = 0 (±250 °/с), ACCEL_CONFIG = 0 (±2 g) */
  static const uint8_t seq[][2] = {
    { MPU6050_REG_PWR_MGMT_1,   0x01 },
    { MPU6050_REG_CONFIG,       0x03 },
    { MPU6050_REG_SMPLRT_DIV,   0x09 },
    { MPU6050_REG_GYRO_CONFIG,  0x00 },
    { MPU6050_REG_ACCEL_CONFIG, 0x00 },
  };
  for (size_t i = 0; i < sizeof seq / sizeof seq[0]; i++) {
    st = reg_write(dev, seq[i][0], seq[i][1]);
    if (st != BUS_OK) return st;
  }
  return BUS_OK;
}

void mpu6050_parse(const uint8_t b[MPU6050_BURST_LEN], mpu6050_raw_t *r)
{
#define BE16(i) ((int16_t)(uint16_t)(((uint16_t)b[(i)] << 8) | b[(i) + 1]))
  r->ax = BE16(0);  r->ay = BE16(2);  r->az = BE16(4);
  r->temp = BE16(6);
  r->gx = BE16(8);  r->gy = BE16(10); r->gz = BE16(12);
#undef BE16
}

int mpu6050_read_raw(const mpu6050_t *dev, mpu6050_raw_t *raw)
{
  uint8_t b[MPU6050_BURST_LEN];
  if (!dev || !dev->bus || !raw) return BUS_ARG;
  int st = reg_read(dev, MPU6050_REG_ACCEL_XOUT_H, b, sizeof b);
  if (st == BUS_OK) mpu6050_parse(b, raw);
  return st;
}

int32_t mpu6050_temp_cdeg(int16_t raw)
{
  /* raw/340 + 36.53 °C  ->  (raw*100)/340 + 3653 сотих °C.
   * Ділення з округленням до найближчого: просте '/' у C відкидає дріб
   * у бік нуля і давало 24.01 замість 24.00 °C (знайдено тестом,
   * tests/test_mpu6050.c: test_temperature_formula_datasheet). */
  int32_t num = (int32_t)raw * 100;
  num += (num >= 0) ? 170 : -170;
  return num / 340 + 3653;
}

void mpu6050_convert(const mpu6050_raw_t *r, mpu6050_data_t *o)
{
  o->ax_mg = (int32_t)r->ax * 1000 / MPU6050_ACCEL_LSB_PER_G;
  o->ay_mg = (int32_t)r->ay * 1000 / MPU6050_ACCEL_LSB_PER_G;
  o->az_mg = (int32_t)r->az * 1000 / MPU6050_ACCEL_LSB_PER_G;
  o->temp_cdeg = mpu6050_temp_cdeg(r->temp);
  o->gx_mdps = (int32_t)r->gx * 1000 / MPU6050_GYRO_LSB_PER_DPS;
  o->gy_mdps = (int32_t)r->gy * 1000 / MPU6050_GYRO_LSB_PER_DPS;
  o->gz_mdps = (int32_t)r->gz * 1000 / MPU6050_GYRO_LSB_PER_DPS;
}
