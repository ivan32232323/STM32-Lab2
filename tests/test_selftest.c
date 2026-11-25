/* test_selftest.c — режим самоперевірки на fake-платформі: формат виводу,
 * fallback HW->SW I2C, реакція на відсутність пристроїв. */
#include "unity.h"
#include "selftest.h"
#include "fake_platform.h"
#include "fake_i2c.h"
#include "mock_spi.h"
#include <string.h>

static fake_i2c_t hw, sw;
static i2c_bus_t hw_bus, sw_bus;
static mock_spi_t ms;
static spi_dev_t spi;
static selftest_ctx_t ctx;

static void imu_regs(fake_i2c_t *f)
{
  fake_i2c_init(f, 0x68);
  f->regs[0x75] = 0x68;
  const uint8_t burst[14] = { 0, 0, 0, 0, 0x40, 0x00, 0xEF, 0x5C, 0, 0, 0, 0, 0, 0 };
  memcpy(&f->regs[0x3B], burst, 14);
}

/* Відповіді «ідеальної» W25Q64 для повного прогону self-test */
static void flash_script(mock_spi_t *m)
{
  static const uint8_t jedec[] = { 0xFF, 0xEF, 0x40, 0x17 };
  mock_spi_push_miso(m, jedec, 4);                     /* read_jedec */
  mock_spi_push_miso(m, jedec, 4);                     /* init       */
  static const uint8_t erase[] = { 0xFF, 0xFF, 0x02, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00 };
  mock_spi_push_miso(m, erase, sizeof erase);
  uint8_t rd[4 + 16];
  memset(rd, 0xFF, sizeof rd);                         /* blank check */
  mock_spi_push_miso(m, rd, sizeof rd);
  static const uint8_t pp[] = { 0xFF, 0xFF, 0x02 };
  mock_spi_push_miso(m, pp, 3);
  uint8_t hdr[4 + 16];
  memset(hdr, 0xFF, sizeof hdr);
  mock_spi_push_miso(m, hdr, 4 + 16);                  /* 02 + addr + 16 data */
  static const uint8_t ready[] = { 0xFF, 0x00 };
  mock_spi_push_miso(m, ready, 2);
  uint8_t back[4 + 16];
  memset(back, 0xFF, 4);
  for (unsigned i = 0; i < 16; i++) back[4 + i] = (uint8_t)(0x5Au ^ (i * 0x11u));
  mock_spi_push_miso(m, back, sizeof back);
}

void setUp(void)
{
  fake_platform_reset();
  imu_regs(&hw); imu_regs(&sw);
  hw_bus = fake_i2c_bus(&hw); sw_bus = fake_i2c_bus(&sw);
  mock_spi_init(&ms); spi = mock_spi_dev(&ms);
  fp.i2c_hw = &hw_bus; fp.i2c_sw = &sw_bus; fp.spi = &spi;
  memset(&ctx, 0, sizeof ctx);
}
void tearDown(void) {}

static void test_format_line(void)
{
  char b[96];
  st_format(b, sizeof b, "MPU6050", "who_am_i", ST_PASS, "0x68", "0x68");
  TEST_ASSERT_EQUAL_STRING("ST;MPU6050;who_am_i;PASS;0x68;0x68\r\n", b);
  st_format(b, sizeof b, "X", "y", ST_WARN, NULL, NULL);
  TEST_ASSERT_EQUAL_STRING("ST;X;y;WARN;;\r\n", b);
}

static void test_plausibility_criteria(void)
{
  uint32_t n;
  TEST_ASSERT_TRUE(st_accel_norm_ok(0, 0, 1000, &n));
  TEST_ASSERT_EQUAL_UINT32(1000, n);
  TEST_ASSERT_TRUE(st_accel_norm_ok(-500, 0, 866, &n));        /* нахил 30°, |a| = 1 g */
  TEST_ASSERT_FALSE(st_accel_norm_ok(0, 0, 0, &n));            /* «нулі» з шини */
  TEST_ASSERT_FALSE(st_accel_norm_ok(0, 0, 1100, &n));         /* +10 % */
  TEST_ASSERT_TRUE(st_temp_ok(2400));
  TEST_ASSERT_FALSE(st_temp_ok(3653));                         /* raw = 0 -> 36.53 °C: підозріло */
  TEST_ASSERT_TRUE(st_gyro_still_ok(0, -4999, 4999));
  TEST_ASSERT_FALSE(st_gyro_still_ok(5000, 0, 0));
}

static void test_full_pass_with_hw_i2c(void)
{
  flash_script(&ms);
  TEST_ASSERT_EQUAL_INT(0, selftest_run(&ctx));
  TEST_ASSERT_TRUE(ctx.imu_ok);
  TEST_ASSERT_TRUE(ctx.flash_ok);
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;I2C1;bus;INFO;hal-i2c1;"));
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;MPU6050;temp_c;PASS;24.00;"));
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;W25Q64;readback;PASS;0/16_diff;"));
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;SUMMARY;all;PASS;pass=15 fail=0 warn=0;"));
  TEST_ASSERT_EQUAL_UINT32(1500, fp.servo[SERVO_PAN]);           /* після тесту — нейтраль */
}

static void test_hw_i2c_timeout_falls_back_to_sw(void)
{
  hw.force = BUS_TIMEOUT;
  fp.i2c_hw_err = 0x20;
  flash_script(&ms);
  selftest_run(&ctx);
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;I2C1;hw_read;WARN;timeout err=0x20"));
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;I2C1;bus;INFO;soft-i2c;fallback"));
  TEST_ASSERT_EQUAL_PTR(&sw_bus, ctx.imu.bus);
  TEST_ASSERT_TRUE(ctx.imu_ok);
}

static void test_no_devices_reports_fail_without_hang(void)
{
  hw.force = BUS_NACK; sw.force = BUS_NACK;                      /* IMU від'єднано */
  /* SPI: MISO = FF (чипа немає) */
  TEST_ASSERT_EQUAL_INT(2, selftest_run(&ctx));                  /* who_am_i + jedec */
  TEST_ASSERT_FALSE(ctx.imu_ok);
  TEST_ASSERT_FALSE(ctx.flash_ok);
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;MPU6050;who_am_i;FAIL;"));
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;W25Q64;jedec_id;FAIL;0xFFFFFF;"));
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;SUMMARY;all;FAIL;"));
}

static void test_servo_ccr_mismatch_detected(void)
{
  flash_script(&ms);
  fp.servo_stuck = 1;                                           /* таймер «не пише» CCR */
  TEST_ASSERT_EQUAL_INT(2, selftest_run(&ctx));
  TEST_ASSERT_NOT_NULL(strstr(fp.out, "ST;SERVO_PAN;ccr_1000;FAIL;"));
}

static void test_every_line_is_parseable(void)
{
  flash_script(&ms);
  selftest_run(&ctx);
  int lines = 0;
  for (char *l = strtok(fp.out, "\n"); l; l = strtok(NULL, "\n")) {
    int semis = 0;
    for (char *c = l; *c; c++) semis += (*c == ';');
    TEST_ASSERT_EQUAL_INT_MESSAGE(5, semis, l);                  /* рівно 6 полів */
    TEST_ASSERT_EQUAL_INT(0, strncmp(l, "ST;", 3));
    lines++;
  }
  TEST_ASSERT_EQUAL_INT(19, lines);
}

int main(void)
{
  UNITY_BEGIN();
  RUN_TEST(test_format_line);
  RUN_TEST(test_plausibility_criteria);
  RUN_TEST(test_full_pass_with_hw_i2c);
  RUN_TEST(test_hw_i2c_timeout_falls_back_to_sw);
  RUN_TEST(test_no_devices_reports_fail_without_hang);
  RUN_TEST(test_servo_ccr_mismatch_detected);
  RUN_TEST(test_every_line_is_parseable);
  return UNITY_END();
}
