/**
 * w25q.c — драйвер W25Q64. Кожна інструкція = один інтервал CS# low.
 */
#include "w25q.h"

/* Одна транзакція: CS# low, cmd(+адреса), [tx data], [rx data], CS# high */
static int xfer(const w25q_t *f, const uint8_t *hdr, size_t hn,
                const uint8_t *tx, uint8_t *rx, size_t n)
{
  const spi_dev_t *s = f->spi;
  s->select(s->ctx, 1);
  int st = s->transfer(s->ctx, hdr, NULL, hn);
  if (st == BUS_OK && n) st = s->transfer(s->ctx, tx, rx, n);
  s->select(s->ctx, 0);
  return st;
}

static void addr24(uint8_t *h, uint8_t cmd, uint32_t a)
{
  h[0] = cmd; h[1] = (uint8_t)(a >> 16); h[2] = (uint8_t)(a >> 8); h[3] = (uint8_t)a;
}

int w25q_read_jedec(const w25q_t *f, uint32_t *id)
{
  if (!f || !f->spi || !id) return BUS_ARG;
  const uint8_t cmd = W25Q_CMD_JEDEC_ID;
  uint8_t r[3] = { 0 };
  int st = xfer(f, &cmd, 1, NULL, r, 3);
  if (st == BUS_OK) *id = ((uint32_t)r[0] << 16) | ((uint32_t)r[1] << 8) | r[2];
  return st;
}

int w25q_init(w25q_t *f)
{
  uint32_t id = 0;
  int st = w25q_read_jedec(f, &id);
  if (st != BUS_OK) return st;
  /* 0x000000 / 0xFFFFFF — MISO висить (немає чипа або обрив) */
  if ((id >> 16) != W25Q_MANUF_WINBOND) return BUS_BADID;
  uint8_t cap = (uint8_t)id;
  if (cap < 0x10 || cap > 0x19) return BUS_BADID;
  f->capacity = 1ul << cap;
  return BUS_OK;
}

int w25q_read_sr1(const w25q_t *f, uint8_t *sr)
{
  const uint8_t cmd = W25Q_CMD_READ_SR1;
  return xfer(f, &cmd, 1, NULL, sr, 1);
}

int w25q_wait_ready(const w25q_t *f, uint32_t timeout_us)
{
  uint32_t waited = 0;
  for (;;) {
    uint8_t sr = 0xFF;
    int st = w25q_read_sr1(f, &sr);
    if (st != BUS_OK) return st;
    if (!(sr & W25Q_SR1_BUSY)) return BUS_OK;
    if (waited >= timeout_us) return BUS_TIMEOUT;
    f->spi->delay_us(f->spi->ctx, W25Q_POLL_US);
    waited += W25Q_POLL_US;
  }
}

int w25q_write_enable(const w25q_t *f)
{
  const uint8_t cmd = W25Q_CMD_WRITE_ENABLE;
  int st = xfer(f, &cmd, 1, NULL, NULL, 0);
  if (st != BUS_OK) return st;
  /* Перевірити, що WEL справді встановився (захист від WP#/обриву MOSI) */
  uint8_t sr = 0;
  st = w25q_read_sr1(f, &sr);
  if (st != BUS_OK) return st;
  return (sr & W25Q_SR1_WEL) ? BUS_OK : BUS_ERROR;
}

int w25q_read(const w25q_t *f, uint32_t addr, uint8_t *buf, size_t n)
{
  if (!f || !f->spi || !buf) return BUS_ARG;
  uint8_t h[4];
  addr24(h, W25Q_CMD_READ_DATA, addr);
  return xfer(f, h, 4, NULL, buf, n);
}

int w25q_page_program(const w25q_t *f, uint32_t addr, const uint8_t *data, size_t n)
{
  if (!f || !f->spi || !data || n == 0 || n > W25Q_PAGE_SIZE) return BUS_ARG;
  if ((addr % W25Q_PAGE_SIZE) + n > W25Q_PAGE_SIZE) return BUS_ARG;
  int st = w25q_write_enable(f);
  if (st != BUS_OK) return st;
  uint8_t h[4];
  addr24(h, W25Q_CMD_PAGE_PROGRAM, addr);
  st = xfer(f, h, 4, data, NULL, n);
  if (st != BUS_OK) return st;
  return w25q_wait_ready(f, W25Q_TPP_MAX_US);
}

int w25q_sector_erase(const w25q_t *f, uint32_t addr)
{
  if (!f || !f->spi) return BUS_ARG;
  int st = w25q_write_enable(f);
  if (st != BUS_OK) return st;
  uint8_t h[4];
  addr24(h, W25Q_CMD_SECTOR_ERASE, addr & ~(W25Q_SECTOR_SIZE - 1u));
  st = xfer(f, h, 4, NULL, NULL, 0);
  if (st != BUS_OK) return st;
  return w25q_wait_ready(f, W25Q_TSE_MAX_US);
}
