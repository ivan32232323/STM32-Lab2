#include "fake_i2c.h"
#include <string.h>

void fake_i2c_init(fake_i2c_t *f, uint8_t addr7)
{
  memset(f, 0, sizeof *f);
  f->addr7 = addr7;
}

static int gate(fake_i2c_t *f, uint8_t a)
{
  f->n_xfer++;
  if (f->force && (f->fail_after == 0 || f->n_xfer > f->fail_after)) return f->force;
  return a == f->addr7 ? BUS_OK : BUS_NACK;   /* немає slave -> NACK на адресі */
}

static int w(void *ctx, uint8_t a, const uint8_t *d, size_t n)
{
  fake_i2c_t *f = ctx;
  int st = gate(f, a);
  if (st != BUS_OK) return st;
  if (n == 0) return BUS_OK;
  uint8_t reg = d[0];
  f->last_reg_written = reg;
  for (size_t i = 1; i < n; i++) f->regs[(uint8_t)(reg + i - 1)] = d[i];
  f->n_writes++;
  return BUS_OK;
}

static int wr(void *ctx, uint8_t a, const uint8_t *wd, size_t wn, uint8_t *r, size_t rn)
{
  fake_i2c_t *f = ctx;
  int st = gate(f, a);
  if (st != BUS_OK) return st;
  uint8_t reg = wn ? wd[0] : 0;
  for (size_t i = 0; i < rn; i++) r[i] = f->regs[(uint8_t)(reg + i)];
  return BUS_OK;
}

i2c_bus_t fake_i2c_bus(fake_i2c_t *f)
{
  i2c_bus_t b = { w, wr, f };
  return b;
}
