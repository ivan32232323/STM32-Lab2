#include "cli.h"
#include <string.h>

static const char *skip_ws(const char *s) { while (*s == ' ' || *s == '\t') s++; return s; }

/* Порівняти слово w на початку s; повертає хвіст після слова або NULL */
static const char *word(const char *s, const char *w)
{
  s = skip_ws(s);
  size_t n = strlen(w);
  if (strncmp(s, w, n) != 0) return NULL;
  if (s[n] != '\0' && s[n] != ' ' && s[n] != '\t') return NULL;
  return s + n;
}

static int parse_uint(const char *s, int32_t *out)
{
  s = skip_ws(s);
  if (*s < '0' || *s > '9') return 0;
  int32_t v = 0;
  while (*s >= '0' && *s <= '9') {
    if (v > 100000) return 0;
    v = v * 10 + (*s++ - '0');
  }
  if (*skip_ws(s) != '\0') return 0;
  *out = v;
  return 1;
}

static int at_end(const char *t) { return t && *skip_ws(t) == '\0'; }

cli_result_t cli_parse(const char *line)
{
  cli_result_t r = { CMD_UNKNOWN, 0 };
  const char *t;
  if (at_end(line))                        { r.cmd = CMD_NONE; return r; }
  if (at_end(word(line, "help")))          { r.cmd = CMD_HELP; return r; }
  if (at_end(word(line, "st")))            { r.cmd = CMD_SELFTEST; return r; }
  if (at_end(word(line, "mode")))          { r.cmd = CMD_MODE; return r; }
  if ((t = word(line, "i2c")) != NULL) {
    if (at_end(word(t, "hw")))             { r.cmd = CMD_I2C_HW; return r; }
    if (at_end(word(t, "sw")))             { r.cmd = CMD_I2C_SW; return r; }
    return r;
  }
  if ((t = word(line, "tel")) != NULL) {
    if (at_end(word(t, "on")))             { r.cmd = CMD_TEL; r.arg = 1; return r; }
    if (at_end(word(t, "off")))            { r.cmd = CMD_TEL; r.arg = 0; return r; }
    return r;
  }
  if ((t = word(line, "cap")) != NULL) {
    const char *u;
    if (at_end(word(t, "i2c")))            { r.cmd = CMD_CAP_I2C; return r; }
    if (at_end(word(t, "nack")))           { r.cmd = CMD_CAP_NACK; return r; }
    if (at_end(word(t, "spi")))            { r.cmd = CMD_CAP_SPI; return r; }
    if (at_end(word(t, "adc")))            { r.cmd = CMD_CAP_ADC; return r; }
    if ((u = word(t, "pwm")) != NULL) {
      int32_t us;
      if (parse_uint(u, &us) && us >= 500 && us <= 2500) { r.cmd = CMD_CAP_PWM; r.arg = us; }
      return r;
    }
  }
  return r;
}

int cli_feed(cli_line_t *l, int ch)
{
  if (ch < 0) return 0;
  if (ch == '\r' || ch == '\n') {
    l->buf[l->len] = '\0';
    l->len = 0;
    return 1;
  }
  if (ch == 0x08 || ch == 0x7F) { if (l->len) l->len--; return 0; }
  if (l->len < sizeof l->buf - 1) l->buf[l->len++] = (char)ch;
  return 0;
}
