/**
 * mpu6050.h — драйвер IMU MPU-6050 (InvenSense), лише через i2c_bus_t.
 * Регістри: RM-MPU-6000A-00 rev 4.2; таймінги/адреси: PS-MPU-6000A-00 rev 3.4.
 */
#ifndef MPU6050_H
#define MPU6050_H

#include "bus.h"

#define MPU6050_ADDR_AD0_LOW   0x68u   /* PS с.15, табл. «I2C ADDRESS»   */
#define MPU6050_ADDR_AD0_HIGH  0x69u
#define MPU6050_WHO_AM_I_VALUE 0x68u   /* RM с.45, розд. 4.32            */

/* Регістри (RM-MPU-6000A-00) */
#define MPU6050_REG_SMPLRT_DIV   0x19u /* 4.2  */
#define MPU6050_REG_CONFIG       0x1Au /* 4.3  DLPF_CFG                   */
#define MPU6050_REG_GYRO_CONFIG  0x1Bu /* 4.4  FS_SEL                     */
#define MPU6050_REG_ACCEL_CONFIG 0x1Cu /* 4.5  AFS_SEL                    */
#define MPU6050_REG_ACCEL_XOUT_H 0x3Bu /* 4.17 початок блоку 14 байтів    */
#define MPU6050_REG_PWR_MGMT_1   0x6Bu /* 4.28                            */
#define MPU6050_REG_WHO_AM_I     0x75u /* 4.32                            */

#define MPU6050_BURST_LEN        14u   /* ACCEL(6) + TEMP(2) + GYRO(6)   */

/* Чутливість при AFS_SEL=0 (±2 g) і FS_SEL=0 (±250 °/с), RM с.29, 31 */
#define MPU6050_ACCEL_LSB_PER_G   16384
#define MPU6050_GYRO_LSB_PER_DPS  131

typedef struct {
  const i2c_bus_t *bus;
  uint8_t addr;           /* 7-бітна */
} mpu6050_t;

typedef struct {
  int16_t ax, ay, az;     /* сирі LSB */
  int16_t temp;
  int16_t gx, gy, gz;
} mpu6050_raw_t;

typedef struct {
  int32_t ax_mg, ay_mg, az_mg;       /* міліg                          */
  int32_t temp_cdeg;                 /* соті °C                        */
  int32_t gx_mdps, gy_mdps, gz_mdps; /* мілі-°/с                       */
} mpu6050_data_t;

/* Прочитати WHO_AM_I. Повертає BUS_OK / помилку шини. */
int mpu6050_read_id(const mpu6050_t *dev, uint8_t *id);

/* Ідентифікація + вихід зі сну + ±2 g, ±250 °/с, DLPF 44 Гц, 1 кГц/(1+9)=100 Гц.
 * BUS_BADID, якщо WHO_AM_I != 0x68. */
int mpu6050_init(const mpu6050_t *dev);

/* Одне багатобайтове читання 0x3B..0x48 */
int mpu6050_read_raw(const mpu6050_t *dev, mpu6050_raw_t *raw);

/* Розбір 14 байтів у порядку регістрів (big-endian), без шини — для тестів */
void mpu6050_parse(const uint8_t buf[MPU6050_BURST_LEN], mpu6050_raw_t *raw);

/* Перетворення у фізичні одиниці (цілочисельно, без FPU) */
void mpu6050_convert(const mpu6050_raw_t *raw, mpu6050_data_t *out);

/* Температура: T[°C] = raw/340 + 36.53 (RM с.30, розд. 4.18) -> соті °C */
int32_t mpu6050_temp_cdeg(int16_t raw);

#endif
