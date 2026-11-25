/* test_mpu6050.c — драйвер MPU-6050 на FAKE шині I2C (без заліза). */
#include "unity.h"
#include "mpu6050.h"
#include "fake_i2c.h"
#include "la_vectors.h"

static fake_i2c_t fk;
static i2c_bus_t bus;
static mpu6050_t dev;

void setUp(void)
{
  fake_i2c_init(&fk, 0x68);
  fk.regs[MPU6050_REG_WHO_AM_I] = 0x68;
  fk.regs[MPU6050_REG_PWR_MGMT_1] = 0x40;          /* після reset: SLEEP=1 (RM 4.28) */
  bus = fake_i2c_bus(&fk);
  dev.bus = &bus;
  dev.addr = 0x68;
}
void tearDown(void) {}

static void test_read_id_ok(void)
{
  uint8_t id = 0;
  TEST_ASSERT_EQUAL_INT(BUS_OK, mpu6050_read_id(&dev, &id));
  TEST_ASSERT_EQUAL_HEX8(0x68, id);
}

static void test_init_wakes_and_configures(void)
{
  TEST_ASSERT_EQUAL_INT(BUS_OK, mpu6050_init(&dev));
  TEST_ASSERT_EQUAL_HEX8(0x01, fk.regs[MPU6050_REG_PWR_MGMT_1]);   /* SLEEP=0, CLKSEL=1 */
  TEST_ASSERT_EQUAL_HEX8(0x03, fk.regs[MPU6050_REG_CONFIG]);
  TEST_ASSERT_EQUAL_HEX8(0x09, fk.regs[MPU6050_REG_SMPLRT_DIV]);
  TEST_ASSERT_EQUAL_HEX8(0x00, fk.regs[MPU6050_REG_GYRO_CONFIG]);
  TEST_ASSERT_EQUAL_HEX8(0x00, fk.regs[MPU6050_REG_ACCEL_CONFIG]);
  TEST_ASSERT_EQUAL_INT(5, fk.n_writes);
}

static void test_init_unexpected_id(void)
{
  fk.regs[MPU6050_REG_WHO_AM_I] = 0x70;                            /* напр. MPU-6500 */
  TEST_ASSERT_EQUAL_INT(BUS_BADID, mpu6050_init(&dev));
  TEST_ASSERT_EQUAL_INT(0, fk.n_writes);                          /* нічого не пише */
}

static void test_init_nack_wrong_address(void)
{
  dev.addr = 0x69;                                                 /* AD0=1, а slave на 0x68 */
  TEST_ASSERT_EQUAL_INT(BUS_NACK, mpu6050_init(&dev));
}

static void test_init_timeout_midway(void)
{
  fk.force = BUS_TIMEOUT; fk.fail_after = 2;                       /* ID і 1-й запис ok, далі timeout */
  TEST_ASSERT_EQUAL_INT(BUS_TIMEOUT, mpu6050_init(&dev));
}

static void test_read_raw_propagates_error(void)
{
  mpu6050_raw_t r;
  fk.force = BUS_NACK;
  TEST_ASSERT_EQUAL_INT(BUS_NACK, mpu6050_read_raw(&dev, &r));
  TEST_ASSERT_EQUAL_INT(BUS_ARG, mpu6050_read_raw(&dev, NULL));
  TEST_ASSERT_EQUAL_INT(BUS_ARG, mpu6050_read_id(NULL, NULL));
}

static void test_parse_big_endian_signed(void)
{
  const uint8_t b[14] = { 0x80, 0x00, 0x7F, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x83, 0xFF, 0x7D, 0x12, 0x34 };
  mpu6050_raw_t r;
  mpu6050_parse(b, &r);
  TEST_ASSERT_EQUAL_INT16(-32768, r.ax);
  TEST_ASSERT_EQUAL_INT16(32767, r.ay);
  TEST_ASSERT_EQUAL_INT16(-1, r.az);
  TEST_ASSERT_EQUAL_INT16(0, r.temp);
  TEST_ASSERT_EQUAL_INT16(131, r.gx);
  TEST_ASSERT_EQUAL_INT16(-131, r.gy);
  TEST_ASSERT_EQUAL_INT16(0x1234, r.gz);
}

/* RM-MPU-6000A-00 §4.18: T = TEMP_OUT/340 + 36.53 */
static void test_temperature_formula_datasheet(void)
{
  TEST_ASSERT_EQUAL_INT32(3653, mpu6050_temp_cdeg(0));     /* 36.53 °C */
  TEST_ASSERT_EQUAL_INT32(3653 + 100, mpu6050_temp_cdeg(340));
  TEST_ASSERT_EQUAL_INT32(2400, mpu6050_temp_cdeg(-4260)); /* 24.00 °C — значення моделі Wokwi */
  TEST_ASSERT_EQUAL_INT32(3653 - 100, mpu6050_temp_cdeg(-340));
}

/* ±2 g -> 16384 LSB/g, ±250 °/с -> 131 LSB/(°/с) (RM §4.17, §4.19) */
static void test_convert_sensitivity(void)
{
  mpu6050_raw_t r = { 16384, -8192, 0, 0, 131, -1310, 0 };
  mpu6050_data_t d;
  mpu6050_convert(&r, &d);
  TEST_ASSERT_EQUAL_INT32(1000, d.ax_mg);
  TEST_ASSERT_EQUAL_INT32(-500, d.ay_mg);
  TEST_ASSERT_EQUAL_INT32(1000, d.gx_mdps);
  TEST_ASSERT_EQUAL_INT32(-10000, d.gy_mdps);
}

/* Тестові вектори з логічного аналізатора: 14 байтів, побачених на SDA під час
 * читання 0x3B..0x48 (docs/captures/analysis.md §A2), мають дати ті самі
 * значення, що прошивка вивела в UART (рядок CAP;i2c;...;raw=...). */
static void test_la_vectors_match_uart(void)
{
  for (unsigned k = 0; k < LA_VEC_N; k++) {
    fake_i2c_init(&fk, 0x68);
    for (unsigned i = 0; i < 14; i++) fk.regs[0x3B + i] = la_vec[k].bus_bytes[i];
    mpu6050_raw_t r;
    TEST_ASSERT_EQUAL_INT(BUS_OK, mpu6050_read_raw(&dev, &r));
    const int16_t got[7] = { r.ax, r.ay, r.az, r.temp, r.gx, r.gy, r.gz };
    TEST_ASSERT_EQUAL_INT16_ARRAY(la_vec[k].uart_raw, got, 7);
    mpu6050_data_t d;
    mpu6050_convert(&r, &d);
    TEST_ASSERT_EQUAL_INT32(la_vec[k].uart_temp_cdeg, d.temp_cdeg);
  }
}

int main(void)
{
  UNITY_BEGIN();
  RUN_TEST(test_read_id_ok);
  RUN_TEST(test_init_wakes_and_configures);
  RUN_TEST(test_init_unexpected_id);
  RUN_TEST(test_init_nack_wrong_address);
  RUN_TEST(test_init_timeout_midway);
  RUN_TEST(test_read_raw_propagates_error);
  RUN_TEST(test_parse_big_endian_signed);
  RUN_TEST(test_temperature_formula_datasheet);
  RUN_TEST(test_convert_sensitivity);
  RUN_TEST(test_la_vectors_match_uart);
  return UNITY_END();
}
