/**
 * w25q64.chip.c — модель SPI NOR flash Winbond W25Q64JV для Wokwi (Custom Chips API).
 *
 * У бібліотеці Wokwi немає SPI-flash; ця модель відтворює підмножину
 * інструкцій, що використовує драйвер firmware/Devices/w25q.c:
 *   9Fh JEDEC ID -> EF 40 17     05h Read SR1 (BUSY, WEL)
 *   06h/04h Write Enable/Disable 03h Read Data (3-байтова адреса)
 *   02h Page Program (≤256 Б, загортання в межах сторінки, біти лише 1->0)
 *   20h Sector Erase 4 КБ        90h Manufacturer/Device ID -> EF 16
 * Таймінги BUSY: tPP = 0.4 мс, tSE = 45 мс (типові значення, «AC Electrical Characteristics»).
 * Обмеження моделі: зберігається лише 256 КБ (адреса маскується), без
 * QSPI, без регістрів захисту/SFDP. Режими SPI 0 і 3 (вибір хостом).
 *
 * Збірка: make -C chips (clang --target=wasm32, без libc).
 */
#include "wokwi-api.h"

#define MEM_SIZE   (256u * 1024u)
#define PAGE_SIZE  256u
#define SECT_SIZE  4096u
#define T_PP_US    400u
#define T_SE_US    45000u

enum { ST_CMD, ST_ADDR, ST_DATA, ST_IGNORE };

/* Масив 256 КБ не робимо статичним: з --import-memory lld записав би його
 * як 256 КБ нулів у секцію DATA. Пам'ять береться memory.grow під час init. */
static uint8_t *mem;

typedef struct {
  pin_t cs, miso;
  spi_dev_t spi;
  timer_t busy_timer;
  uint8_t buf[1];
  uint8_t cmd, state, addr_n;
  uint32_t addr;
  uint32_t idx;            /* лічильник байтів у фазі даних */
  uint8_t sr1;             /* bit0 BUSY, bit1 WEL */
  uint8_t page[PAGE_SIZE]; /* буфер Page Program */
  uint8_t page_mask[PAGE_SIZE];
  uint8_t selected;
} chip_t;

static chip_t chip;

static void fill(uint8_t *p, uint32_t n, uint8_t v) { for (uint32_t i = 0; i < n; i++) p[i] = v; }

static void busy_done(void *ud)
{
  chip_t *c = ud;
  c->sr1 &= (uint8_t)~0x03u;            /* BUSY=0, WEL=0 після завершення */
}

static uint8_t data_out(chip_t *c)
{
  switch (c->cmd) {
  case 0x9F: { static const uint8_t id[3] = { 0xEF, 0x40, 0x17 };
               return c->idx < 3 ? id[c->idx] : 0xFF; }
  case 0x05: return c->sr1;
  case 0x03: return mem[(c->addr + c->idx) & (MEM_SIZE - 1u)];
  case 0x90: return (c->idx & 1u) ? 0x16 : 0xEF;
  default:   return 0xFF;
  }
}

static void on_byte(void *ud, uint8_t *buffer, uint32_t count)
{
  chip_t *c = ud;
  if (!c->selected || count == 0) return;
  uint8_t in = buffer[0];

  switch (c->state) {
  case ST_CMD:
    c->cmd = in; c->idx = 0; c->addr = 0; c->addr_n = 0;
    if ((c->sr1 & 0x01u) && in != 0x05) { c->state = ST_IGNORE; break; }  /* BUSY */
    switch (in) {
    case 0x06: c->sr1 |= 0x02u; c->state = ST_IGNORE; break;
    case 0x04: c->sr1 &= (uint8_t)~0x02u; c->state = ST_IGNORE; break;
    case 0x9F: case 0x05: c->state = ST_DATA; break;
    case 0x03: case 0x02: case 0x20: case 0x90: c->state = ST_ADDR; break;
    default:   c->state = ST_IGNORE; break;
    }
    if (c->cmd == 0x02) { fill(c->page_mask, PAGE_SIZE, 0); }
    break;
  case ST_ADDR:
    c->addr = (c->addr << 8) | in;
    if (++c->addr_n == 3) c->state = ST_DATA;
    break;
  case ST_DATA:
    if (c->cmd == 0x02) {
      uint32_t off = (c->addr + c->idx) % PAGE_SIZE;       /* загортання в сторінці */
      c->page[off] = in; c->page_mask[off] = 1;
    }
    c->idx++;
    break;
  default: break;
  }
  buffer[0] = (c->state == ST_DATA) ? data_out(c) : 0xFF;
  spi_start(c->spi, c->buf, 1);
}

static void on_cs(void *ud, pin_t pin, uint32_t value)
{
  (void)pin;
  chip_t *c = ud;
  if (value == LOW) {                                  /* вибір */
    c->selected = 1; c->state = ST_CMD;
    c->buf[0] = 0xFF;
    spi_start(c->spi, c->buf, 1);
    return;
  }
  /* CS# high: кінець інструкції; запис/стирання стартують саме тут (розд. «Page Program», «Sector Erase») */
  c->selected = 0;
  spi_stop(c->spi);
  pin_mode(c->miso, INPUT);                            /* DO -> High-Z */
  if (!(c->sr1 & 0x02u) || c->state != ST_DATA) return;   /* без WEL нічого не робимо */
  if (c->cmd == 0x02 && c->idx > 0) {
    uint32_t base = (c->addr & ~(PAGE_SIZE - 1u)) & (MEM_SIZE - 1u);
    for (uint32_t i = 0; i < PAGE_SIZE; i++)
      if (c->page_mask[i]) mem[base + i] &= c->page[i];   /* NOR: лише 1 -> 0 */
    c->sr1 |= 0x01u;
    timer_start(c->busy_timer, T_PP_US, false);
  } else if (c->cmd == 0x20) {
    uint32_t base = (c->addr & ~(SECT_SIZE - 1u)) & (MEM_SIZE - 1u);
    fill(&mem[base], SECT_SIZE, 0xFF);
    c->sr1 |= 0x01u;
    timer_start(c->busy_timer, T_SE_US, false);
  }
}

void chip_init(void)
{
  unsigned long base = __builtin_wasm_memory_size(0);
  if (__builtin_wasm_memory_grow(0, MEM_SIZE / 65536u) == (unsigned long)-1) return;
  mem = (uint8_t *)(base * 65536u);
  fill(mem, MEM_SIZE, 0xFF);
  chip.cs   = pin_init("CS", INPUT_PULLUP);
  chip.miso = pin_init("DO", INPUT);
  const spi_config_t spi = {
    .sck = pin_init("CLK", INPUT), .mosi = pin_init("DI", INPUT), .miso = chip.miso,
    .mode = 0, .done = on_byte, .user_data = &chip,
  };
  chip.spi = spi_init(&spi);
  const timer_config_t tc = { .callback = busy_done, .user_data = &chip };
  chip.busy_timer = timer_init(&tc);
  const pin_watch_config_t w = { .edge = BOTH, .pin_change = on_cs, .user_data = &chip };
  pin_watch(chip.cs, &w);
}
