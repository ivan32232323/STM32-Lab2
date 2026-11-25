#include "mock_spi.h"
#include <stdio.h>
#include <string.h>

void mock_spi_init(mock_spi_t *m)
{
  memset(m, 0, sizeof *m);
  m->miso_idle = 0xFF;
}

void mock_spi_push_miso(mock_spi_t *m, const uint8_t *b, int n)
{
  for (int i = 0; i < n && m->n_miso < MOCK_MISO_MAX; i++) m->miso[m->n_miso++] = b[i];
}

static void logev(mock_spi_t *m, int e) { if (m->n_log < MOCK_LOG_MAX) m->log[m->n_log++] = e; }

static void sel(void *ctx, int active)
{
  mock_spi_t *m = ctx;
  m->selected = active;
  logev(m, active ? EV_SEL : EV_DESEL);
}

static int xfer(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n)
{
  mock_spi_t *m = ctx;
  if (m->fail_transfer) return m->fail_transfer;
  if (!m->selected) return BUS_ERROR;               /* обмін без CS# — помилка драйвера */
  for (size_t i = 0; i < n; i++) {
    logev(m, tx ? tx[i] : 0xFF);
    uint8_t r = m->miso_pos < m->n_miso ? m->miso[m->miso_pos++] : m->miso_idle;
    if (rx) rx[i] = r;
  }
  return BUS_OK;
}

static void dly(void *ctx, uint32_t us)
{
  mock_spi_t *m = ctx;
  m->delay_total_us += us;
  logev(m, EV_DELAY);
}

spi_dev_t mock_spi_dev(mock_spi_t *m)
{
  spi_dev_t d = { sel, xfer, dly, m };
  return d;
}

const char *mock_spi_log_str(const mock_spi_t *m)
{
  static char s[MOCK_LOG_MAX * 3 + 1];
  size_t p = 0;
  s[0] = '\0';
  for (int i = 0; i < m->n_log && p + 4 < sizeof s; i++) {
    int e = m->log[i];
    if (e == EV_SEL) p += (size_t)snprintf(s + p, sizeof s - p, "%sS", p ? " " : "");
    else if (e == EV_DESEL) p += (size_t)snprintf(s + p, sizeof s - p, " D");
    else if (e == EV_DELAY) p += (size_t)snprintf(s + p, sizeof s - p, " w");
    else p += (size_t)snprintf(s + p, sizeof s - p, " %02X", e);
  }
  return s;
}
