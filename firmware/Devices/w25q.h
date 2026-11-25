/**
 * w25q.h — драйвер SPI NOR flash Winbond W25Q64JV, лише через spi_dev_t.
 * Джерело: Winbond W25Q64JV datasheet rev. J — розділ «Instructions» (Instruction
 * Set Table 1) і «AC Electrical Characteristics» (tPP, tSE).
 */
#ifndef W25Q_H
#define W25Q_H

#include "bus.h"

#define W25Q_CMD_WRITE_ENABLE   0x06u
#define W25Q_CMD_WRITE_DISABLE  0x04u
#define W25Q_CMD_READ_SR1       0x05u
#define W25Q_CMD_READ_DATA      0x03u  /* fR ≤ 50 МГц */
#define W25Q_CMD_PAGE_PROGRAM   0x02u
#define W25Q_CMD_SECTOR_ERASE   0x20u  /* 4 КБ */
#define W25Q_CMD_JEDEC_ID       0x9Fu

#define W25Q_SR1_BUSY           0x01u
#define W25Q_SR1_WEL            0x02u

#define W25Q_MANUF_WINBOND      0xEFu
#define W25Q64_JEDEC_ID         0xEF4017u   /* EF, тип 40 (SPI), ємність 17h = 2^23 Б */

#define W25Q_PAGE_SIZE          256u
#define W25Q_SECTOR_SIZE        4096u

/* Максимальні часи («AC Electrical Characteristics»): tPP ≤ 3 мс, tSE ≤ 400 мс. Опитування BUSY
 * з кроком poll_us; ліміт ітерацій = max / poll_us. */
#define W25Q_POLL_US            100u
#define W25Q_TPP_MAX_US         3000u
#define W25Q_TSE_MAX_US         400000u

typedef struct {
  const spi_dev_t *spi;
  uint32_t capacity;       /* байт; заповнюється w25q_init з JEDEC ID */
} w25q_t;

int w25q_read_jedec(const w25q_t *f, uint32_t *id);  /* 0xMMTTCC          */
int w25q_init(w25q_t *f);                            /* ID + capacity      */
int w25q_read_sr1(const w25q_t *f, uint8_t *sr);
int w25q_wait_ready(const w25q_t *f, uint32_t timeout_us);
int w25q_write_enable(const w25q_t *f);
int w25q_read(const w25q_t *f, uint32_t addr, uint8_t *buf, size_t n);
/* Не перетинає межу сторінки 256 Б (інакше адреса «загортається», розд. «Page Program») */
int w25q_page_program(const w25q_t *f, uint32_t addr, const uint8_t *data, size_t n);
int w25q_sector_erase(const w25q_t *f, uint32_t addr);

#endif
