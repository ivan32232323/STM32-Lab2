/**
 * bus.h — апаратно-незалежний інтерфейс шин I2C і SPI.
 *
 * Драйвери з Devices/ працюють лише через ці структури і не знають,
 * що під ними: HAL_I2C, програмний bit-bang чи тестовий fake на хості.
 * Реалізації: Platform/plat_i2c.c, Platform/plat_spi.c (ціль),
 *             tests/doubles/fake_i2c.c, tests/doubles/mock_spi.c (хост).
 * Ідея та сама, що в ST platform-independent drivers (stmdev_ctx_t).
 */
#ifndef BUS_H
#define BUS_H

#include <stddef.h>
#include <stdint.h>

/* Коди повернення, спільні для всіх шин і драйверів */
typedef enum {
  BUS_OK      = 0,
  BUS_NACK    = -1,   /* slave не підтвердив адресу/байт              */
  BUS_TIMEOUT = -2,   /* шина/пристрій не відповів вчасно              */
  BUS_ERROR   = -3,   /* інша апаратна помилка (arbitration lost тощо) */
  BUS_BADID   = -4,   /* пристрій відповів, але ID не той (драйвер)    */
  BUS_ARG     = -5    /* некоректні аргументи                          */
} bus_status_t;

/* ---- I2C ------------------------------------------------------------- */
typedef struct {
  /* Запис n байтів на 7-бітну адресу: S addr+W data... P */
  int (*write)(void *ctx, uint8_t addr7, const uint8_t *data, size_t n);
  /* Комбінована транзакція: S addr+W w... Sr addr+R r... P */
  int (*write_read)(void *ctx, uint8_t addr7, const uint8_t *w, size_t wn,
                    uint8_t *r, size_t rn);
  void *ctx;
} i2c_bus_t;

/* ---- SPI (один slave, CS# керується через select) --------------------- */
typedef struct {
  void (*select)(void *ctx, int active);          /* 1 = CS# low       */
  /* Повнодуплексний обмін n байтів; tx або rx можуть бути NULL
   * (тоді передається 0xFF / прийняте відкидається). */
  int  (*transfer)(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n);
  void (*delay_us)(void *ctx, uint32_t us);       /* для опитування BUSY */
  void *ctx;
} spi_dev_t;

#endif /* BUS_H */
