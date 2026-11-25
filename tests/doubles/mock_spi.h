/**
 * mock_spi.h — MOCK шини SPI: записує ПОСЛІДОВНІСТЬ подій (CS#↓, байти MOSI,
 * CS#↑) і віддає заздалегідь задані байти MISO. Тест порівнює журнал з
 * очікуваним — так перевіряється, що перед 02h/20h іде 06h (WREN) в окремому
 * інтервалі CS#, що адреса передається старшим байтом уперед тощо.
 */
#ifndef MOCK_SPI_H
#define MOCK_SPI_H

#include "bus.h"

#define MOCK_LOG_MAX 512
#define MOCK_MISO_MAX 512

enum { EV_SEL = 0x100, EV_DESEL = 0x101, EV_DELAY = 0x102 };

typedef struct {
  int      log[MOCK_LOG_MAX];   /* байт MOSI (0..255) або EV_* */
  int      n_log;
  uint8_t  miso[MOCK_MISO_MAX]; /* черга відповідей; після кінця — miso_idle */
  int      n_miso, miso_pos;
  uint8_t  miso_idle;
  int      selected;
  int      fail_transfer;       /* !=0 -> transfer повертає цей код */
  uint32_t delay_total_us;
} mock_spi_t;

void      mock_spi_init(mock_spi_t *m);
void      mock_spi_push_miso(mock_spi_t *m, const uint8_t *b, int n);
spi_dev_t mock_spi_dev(mock_spi_t *m);

/* Журнал як рядок "S 06 D S 05 D ..." для зручних TEST_ASSERT_EQUAL_STRING */
const char *mock_spi_log_str(const mock_spi_t *m);

#endif
