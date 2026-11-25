/**
 * fake_i2c.h — FAKE шини I2C: робоча спрощена модель slave з регістровим
 * файлом (автоінкремент адреси, як у MPU-6050). Не перевіряє порядок
 * викликів — лише стан. Дозволяє інжектувати помилки (NACK, timeout).
 */
#ifndef FAKE_I2C_H
#define FAKE_I2C_H

#include "bus.h"

typedef struct {
  uint8_t addr7;            /* адреса «присутнього» slave              */
  uint8_t regs[256];
  int     fail_after;       /* >0: N успішних транзакцій, потім force  */
  int     force;            /* код помилки (BUS_NACK/BUS_TIMEOUT) або 0 */
  int     n_xfer;           /* лічильник транзакцій                    */
  uint8_t last_reg_written; /* остання адреса регістру з write()       */
  int     n_writes;
} fake_i2c_t;

void fake_i2c_init(fake_i2c_t *f, uint8_t addr7);
i2c_bus_t fake_i2c_bus(fake_i2c_t *f);

#endif
