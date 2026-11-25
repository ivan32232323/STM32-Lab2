/* test_app_logic.c — прикладна логіка: кути, серво, CLI (чисті функції). */
#include "unity.h"
#include "servo_map.h"
#include "attitude.h"
#include "cli.h"
#include <math.h>
#include <string.h>

void setUp(void) {}
void tearDown(void) {}

/* FR-02: −90..+90° -> 1000..2000 мкс, дискретність ≤ 1° */
static void test_deg_to_us_endpoints_and_clamp(void)
{
  TEST_ASSERT_EQUAL_INT32(1000, servo_deg_to_us(-90));
  TEST_ASSERT_EQUAL_INT32(1500, servo_deg_to_us(0));
  TEST_ASSERT_EQUAL_INT32(2000, servo_deg_to_us(90));
  TEST_ASSERT_EQUAL_INT32(2000, servo_deg_to_us(120));
  TEST_ASSERT_EQUAL_INT32(1000, servo_deg_to_us(-500));
  TEST_ASSERT_EQUAL_INT32(1556, servo_deg_to_us(10));   /* 1500 + 55.6 */
  TEST_ASSERT_EQUAL_INT32(1444, servo_deg_to_us(-10));  /* симетрично */
}

static void test_us_to_deg_roundtrip(void)
{
  for (int d = -90; d <= 90; d++)
    TEST_ASSERT_EQUAL_INT32(d, servo_us_to_deg(servo_deg_to_us(d)));
}

/* FR-05: 0..4095 -> 1000..2000 мкс, лінійно */
static void test_pot_mapping(void)
{
  TEST_ASSERT_EQUAL_INT32(1000, servo_pot_to_us(0));
  TEST_ASSERT_EQUAL_INT32(1500, servo_pot_to_us(2048));
  TEST_ASSERT_EQUAL_INT32(1501, servo_pot_to_us(2050));  /* значення з UART-логу Wokwi */
  TEST_ASSERT_EQUAL_INT32(2000, servo_pot_to_us(4095));
  TEST_ASSERT_EQUAL_INT32(2000, servo_pot_to_us(65535));
}

/* FR-06: мертва зона ±2° — тремтіння ±1° не рухає серво */
static void test_deadband_ignores_tremor(void)
{
  servo_filter_t f;
  servo_filter_init(&f, 1500);
  for (int i = 0; i < 50; i++)
    TEST_ASSERT_EQUAL_INT32(1500, servo_filter_step(&f, (i & 1) ? 1 : -1, 20));
}

/* FR-06: швидкість ≤ 300 °/с -> стрибок 0 -> 90° займає ≥ 300 мс */
static void test_rate_limit(void)
{
  servo_filter_t f;
  servo_filter_init(&f, 1500);
  int steps = 0;
  while (servo_filter_step(&f, 90, 20) < 2000 && steps < 1000) steps++;
  steps++;
  TEST_ASSERT_GREATER_OR_EQUAL_INT(15, steps);          /* 15 × 20 мс = 300 мс */
  TEST_ASSERT_LESS_OR_EQUAL_INT(17, steps);
}

static void test_accel_angles(void)
{
  float p, r;
  attitude_from_accel(0, 0, 1000, &p, &r);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, p);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, r);
  attitude_from_accel(-500, 0, 866, &p, &r);            /* нахил по Y на +30° */
  TEST_ASSERT_FLOAT_WITHIN(0.1f, 30.0f, p);
  attitude_from_accel(0, 707, 707, &p, &r);             /* крен 45° */
  TEST_ASSERT_FLOAT_WITHIN(0.1f, 45.0f, r);
  attitude_from_accel(0, 1000, 0, &p, &r);              /* крен 90° */
  TEST_ASSERT_FLOAT_WITHIN(0.1f, 90.0f, r);
}

/* FR-01: фільтр сходиться до кута акселерометра і не дрейфує без гіроскопа */
static void test_complementary_filter_converges(void)
{
  attitude_t a;
  attitude_init(&a, 0.98f);
  attitude_update(&a, 0, 0, 1000, 0, 0, 20);           /* ініціалізація з accel */
  for (int i = 0; i < 400; i++) attitude_update(&a, -500, 0, 866, 0, 0, 20);   /* 8 с */
  TEST_ASSERT_FLOAT_WITHIN(1.0f, 30.0f, a.pitch_deg);
  /* гіроскоп 10 °/с протягом 1 с при статичному accel: відхилення обмежене */
  for (int i = 0; i < 50; i++) attitude_update(&a, -500, 0, 866, 0, 10000, 20);
  TEST_ASSERT_FLOAT_WITHIN(15.0f, 30.0f, a.pitch_deg);
}

static void test_isqrt(void)
{
  TEST_ASSERT_EQUAL_UINT32(0, isqrt32(0));
  TEST_ASSERT_EQUAL_UINT32(1000, isqrt32(1000000));
  TEST_ASSERT_EQUAL_UINT32(999, isqrt32(999999));
  TEST_ASSERT_EQUAL_UINT32(65535, isqrt32(0xFFFFFFFFu));
}

static void test_cli_parse(void)
{
  TEST_ASSERT_EQUAL_INT(CMD_CAP_I2C, cli_parse("cap i2c").cmd);
  TEST_ASSERT_EQUAL_INT(CMD_CAP_SPI, cli_parse("  cap   spi ").cmd);
  cli_result_t r = cli_parse("cap pwm 1250");
  TEST_ASSERT_EQUAL_INT(CMD_CAP_PWM, r.cmd);
  TEST_ASSERT_EQUAL_INT32(1250, r.arg);
  TEST_ASSERT_EQUAL_INT(CMD_UNKNOWN, cli_parse("cap pwm 99").cmd);     /* поза 500..2500 */
  TEST_ASSERT_EQUAL_INT(CMD_UNKNOWN, cli_parse("cap pwm 12x").cmd);
  TEST_ASSERT_EQUAL_INT(CMD_UNKNOWN, cli_parse("capi2c").cmd);
  TEST_ASSERT_EQUAL_INT(CMD_UNKNOWN, cli_parse("i2c xx").cmd);
  TEST_ASSERT_EQUAL_INT(CMD_I2C_SW, cli_parse("i2c sw").cmd);
  TEST_ASSERT_EQUAL_INT(CMD_TEL, cli_parse("tel off").cmd);
  TEST_ASSERT_EQUAL_INT(CMD_NONE, cli_parse("   ").cmd);
  TEST_ASSERT_EQUAL_INT(CMD_HELP, cli_parse("help").cmd);
}

static void test_cli_feed_line_and_overflow(void)
{
  cli_line_t l = { {0}, 0 };
  const char *in = "st\r";
  int done = 0;
  for (const char *p = in; *p; p++) done = cli_feed(&l, *p);
  TEST_ASSERT_TRUE(done);
  TEST_ASSERT_EQUAL_STRING("st", l.buf);
  for (int i = 0; i < 100; i++) cli_feed(&l, 'a');                    /* переповнення */
  TEST_ASSERT_TRUE(cli_feed(&l, '\n'));
  TEST_ASSERT_EQUAL_size_t(sizeof l.buf - 1, strlen(l.buf));
  TEST_ASSERT_FALSE(cli_feed(&l, -1));
  cli_feed(&l, 'x'); cli_feed(&l, 0x7F); cli_feed(&l, '\r');            /* backspace */
  TEST_ASSERT_EQUAL_STRING("", l.buf);
}

int main(void)
{
  UNITY_BEGIN();
  RUN_TEST(test_deg_to_us_endpoints_and_clamp);
  RUN_TEST(test_us_to_deg_roundtrip);
  RUN_TEST(test_pot_mapping);
  RUN_TEST(test_deadband_ignores_tremor);
  RUN_TEST(test_rate_limit);
  RUN_TEST(test_accel_angles);
  RUN_TEST(test_complementary_filter_converges);
  RUN_TEST(test_isqrt);
  RUN_TEST(test_cli_parse);
  RUN_TEST(test_cli_feed_line_and_overflow);
  return UNITY_END();
}
