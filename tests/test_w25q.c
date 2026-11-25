/* test_w25q.c — послідовність команд драйвера W25Q64 на MOCK шині SPI.
 * Журнал: S = CS#↓, D = CS#↑, w = очікування (опитування BUSY), XX = байт MOSI. */
#include "unity.h"
#include "w25q.h"
#include "mock_spi.h"
#include <string.h>

static mock_spi_t m;
static spi_dev_t spi;
static w25q_t f;

void setUp(void)
{
  mock_spi_init(&m);
  spi = mock_spi_dev(&m);
  f.spi = &spi;
  f.capacity = 0;
}
void tearDown(void) {}

static void test_jedec_id_and_capacity(void)
{
  const uint8_t id[] = { 0xEF, 0x40, 0x17 };
  mock_spi_push_miso(&m, (const uint8_t[]){ 0xFF }, 1);           /* під час байта команди */
  mock_spi_push_miso(&m, id, 3);
  TEST_ASSERT_EQUAL_INT(BUS_OK, w25q_init(&f));
  TEST_ASSERT_EQUAL_UINT32(8u * 1024u * 1024u, f.capacity);
  TEST_ASSERT_EQUAL_STRING("S 9F FF FF FF D", mock_spi_log_str(&m));
}

static void test_jedec_floating_miso_is_bad_id(void)
{
  /* немає чипа: MISO висить у 1 -> FF FF FF */
  TEST_ASSERT_EQUAL_INT(BUS_BADID, w25q_init(&f));
  mock_spi_init(&m); m.miso_idle = 0x00;                           /* або притиснутий до 0 */
  TEST_ASSERT_EQUAL_INT(BUS_BADID, w25q_init(&f));
}

static void test_page_program_sequence_wren_first(void)
{
  /* відповіді MISO: [05 -> SR1=WEL] ... [05 -> BUSY|WEL] [05 -> 0] */
  const uint8_t miso[] = { 0xFF, 0xFF, 0x02,   /* WREN: 06; RDSR: 05 -> 02 */
                           0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, /* 02 A2 A1 A0 D0 D1 */
                           0xFF, 0x03,         /* RDSR -> BUSY */
                           0xFF, 0x00 };       /* RDSR -> ready */
  mock_spi_push_miso(&m, miso, sizeof miso);
  const uint8_t data[2] = { 0xA5, 0x5A };
  TEST_ASSERT_EQUAL_INT(BUS_OK, w25q_page_program(&f, 0x012345, data, 2));
  TEST_ASSERT_EQUAL_STRING(
    "S 06 D S 05 FF D S 02 01 23 45 A5 5A D S 05 FF D w S 05 FF D",
    mock_spi_log_str(&m));
}

static void test_sector_erase_aligns_address_and_waits(void)
{
  const uint8_t miso[] = { 0xFF, 0xFF, 0x02, 0xFF, 0xFF, 0xFF, 0xFF,
                           0xFF, 0x03, 0xFF, 0x03, 0xFF, 0x00 };
  mock_spi_push_miso(&m, miso, sizeof miso);
  TEST_ASSERT_EQUAL_INT(BUS_OK, w25q_sector_erase(&f, 0x001FFF));
  TEST_ASSERT_EQUAL_STRING(
    "S 06 D S 05 FF D S 20 00 10 00 D S 05 FF D w S 05 FF D w S 05 FF D",
    mock_spi_log_str(&m));
}

static void test_wren_not_latched_aborts_program(void)
{
  /* WP# активний / обрив MOSI: після 06h біт WEL лишається 0 */
  const uint8_t miso[] = { 0xFF, 0xFF, 0x00 };
  mock_spi_push_miso(&m, miso, sizeof miso);
  const uint8_t d = 0;
  TEST_ASSERT_EQUAL_INT(BUS_ERROR, w25q_page_program(&f, 0, &d, 1));
  TEST_ASSERT_EQUAL_STRING("S 06 D S 05 FF D", mock_spi_log_str(&m));  /* 02h не надсилався */
}

static void test_busy_forever_times_out(void)
{
  m.miso_idle = 0x03;                       /* BUSY|WEL назавжди */
  TEST_ASSERT_EQUAL_INT(BUS_TIMEOUT, w25q_wait_ready(&f, W25Q_TPP_MAX_US));
  TEST_ASSERT_EQUAL_UINT32(W25Q_TPP_MAX_US, m.delay_total_us);   /* не довше за tPP max */
}

static void test_page_boundary_rejected(void)
{
  uint8_t d[16] = { 0 };
  TEST_ASSERT_EQUAL_INT(BUS_ARG, w25q_page_program(&f, 0x0000F8, d, 16));  /* 0xF8+16 > 0x100 */
  TEST_ASSERT_EQUAL_INT(BUS_ARG, w25q_page_program(&f, 0, d, 0));
  TEST_ASSERT_EQUAL_INT(0, m.n_log);        /* на шину нічого не пішло */
}

static void test_read_sends_address_msb_first(void)
{
  const uint8_t miso[] = { 0xFF, 0xFF, 0xFF, 0xFF, 'L', 'R', '2' };
  mock_spi_push_miso(&m, miso, sizeof miso);
  uint8_t buf[3];
  TEST_ASSERT_EQUAL_INT(BUS_OK, w25q_read(&f, 0x002000, buf, 3));
  TEST_ASSERT_EQUAL_STRING("S 03 00 20 00 FF FF FF D", mock_spi_log_str(&m));
  TEST_ASSERT_EQUAL_MEMORY("LR2", buf, 3);
}

static void test_bus_error_still_releases_cs(void)
{
  m.fail_transfer = BUS_TIMEOUT;
  uint32_t id;
  TEST_ASSERT_EQUAL_INT(BUS_TIMEOUT, w25q_read_jedec(&f, &id));
  TEST_ASSERT_EQUAL_STRING("S D", mock_spi_log_str(&m));        /* CS# не «завис» у low */
}

int main(void)
{
  UNITY_BEGIN();
  RUN_TEST(test_jedec_id_and_capacity);
  RUN_TEST(test_jedec_floating_miso_is_bad_id);
  RUN_TEST(test_page_program_sequence_wren_first);
  RUN_TEST(test_sector_erase_aligns_address_and_waits);
  RUN_TEST(test_wren_not_latched_aborts_program);
  RUN_TEST(test_busy_forever_times_out);
  RUN_TEST(test_page_boundary_rejected);
  RUN_TEST(test_read_sends_address_msb_first);
  RUN_TEST(test_bus_error_still_releases_cs);
  return UNITY_END();
}
