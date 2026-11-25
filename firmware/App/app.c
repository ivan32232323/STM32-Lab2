/**
 * app.c — головний цикл: self-test на старті, контур 50 Гц, режими
 * MANUAL/MIRROR, FR-09 (втрата IMU -> нейтраль), CLI, телеметрія 1 Гц.
 * Не знає про HAL: лише platform.h, Devices/ і App/.
 */
#include "app.h"
#include "platform.h"
#include "selftest.h"
#include "attitude.h"
#include "servo_map.h"
#include "cli.h"
#include <stdio.h>

#define CTRL_PERIOD_MS   20u    /* FR-04: 50 Гц = частота PWM серво */
#define IMU_LOST_MS      100u   /* FR-09 */
#define DEBOUNCE_MS      20u    /* FR-07 */

static selftest_ctx_t g_st;
static attitude_t     g_att;
static servo_filter_t g_pan, g_tilt;
static int g_mirror, g_tel = 1, g_hold;
static uint16_t g_pot;
static uint32_t g_imu_last_ok;

static void say(const char *fmt_line) { plat_puts(fmt_line); }

static void cap_i2c(void)
{
  uint8_t id = 0;
  mpu6050_raw_t raw;
  int a = mpu6050_read_id(&g_st.imu, &id);
  int b = mpu6050_read_raw(&g_st.imu, &raw);
  char l[112];
  snprintf(l, sizeof l, "CAP;i2c;id=0x%02X;st=%d,%d;raw=%d,%d,%d,%d,%d,%d,%d\r\n", id, a, b,
           raw.ax, raw.ay, raw.az, raw.temp, raw.gx, raw.gy, raw.gz);
  say(l);
}

static void cap_nack(void)
{
  /* Навмисна аномалія: той самий запит WHO_AM_I на адресу 0x69 (AD0=1), якої немає */
  mpu6050_t ghost = { g_st.imu.bus, MPU6050_ADDR_AD0_HIGH };
  uint8_t id = 0;
  int st = mpu6050_read_id(&ghost, &id);
  char l[48];
  snprintf(l, sizeof l, "CAP;nack;addr=0x69;st=%d\r\n", st);
  say(l);
}

static void cap_spi(void)
{
  uint32_t id = 0;
  uint8_t sr = 0, rd[16];
  int a = w25q_read_jedec(&g_st.flash, &id);
  int b = w25q_read_sr1(&g_st.flash, &sr);
  static const uint8_t pat[8] = { 'L', 'R', '2', '-', 'S', 'P', 'I', '!' };
  int c = w25q_sector_erase(&g_st.flash, 0x002000u);
  int d = w25q_page_program(&g_st.flash, 0x002000u, pat, sizeof pat);
  int e = w25q_read(&g_st.flash, 0x002000u, rd, sizeof pat);
  char l[96];
  snprintf(l, sizeof l, "CAP;spi;jedec=0x%06lX;sr1=0x%02X;st=%d,%d,%d,%d,%d;rd=%.8s\r\n",
           (unsigned long)id, sr, a, b, c, d, e, (const char *)rd);
  say(l);
}

static void cap_adc(void)
{
  char l[40];
  for (int i = 0; i < 10; i++) {
    uint16_t v = 0;
    plat_adc_read(&v);
    snprintf(l, sizeof l, "CAP;adc;%d;%u\r\n", i, v);
    say(l);
    plat_delay_ms(10);
  }
}

static void handle(cli_result_t r)
{
  char l[64];
  switch (r.cmd) {
  case CMD_NONE: break;
  case CMD_HELP:
    say("cmds: st | i2c hw|sw | cap i2c|nack|spi|adc | cap pwm <us> | mode | tel on|off\r\n");
    break;
  case CMD_SELFTEST: selftest_run(&g_st); break;
  case CMD_I2C_HW: g_st.imu.bus = plat_i2c_hw(); say("OK;i2c=hw\r\n"); break;
  case CMD_I2C_SW: g_st.imu.bus = plat_i2c_sw(); say("OK;i2c=sw\r\n"); break;
  case CMD_CAP_I2C: cap_i2c(); break;
  case CMD_CAP_NACK: cap_nack(); break;
  case CMD_CAP_SPI: cap_spi(); break;
  case CMD_CAP_ADC: cap_adc(); break;
  case CMD_CAP_PWM:
    g_mirror = 0; g_hold = 1; g_tel = 0;     /* зупинити контур, щоб не перезаписав CCR */
    plat_servo_set_us(SERVO_PAN, (uint32_t)r.arg);
    snprintf(l, sizeof l, "CAP;pwm;pan_us=%ld;hold (send 'tel on' to resume)\r\n", (long)r.arg);
    say(l);
    break;
  case CMD_MODE:
    g_mirror = !g_mirror;
    say(g_mirror ? "MODE;MIRROR\r\n" : "MODE;MANUAL\r\n");
    break;
  case CMD_TEL: g_tel = (int)r.arg; g_hold = 0; say(g_tel ? "OK;tel=on\r\n" : "OK;tel=off\r\n"); break;
  default: say("ERR;unknown command, try 'help'\r\n"); break;
  }
}

static void control_step(uint32_t now)
{
  plat_probe(PROBE_LOOP, 1);
  plat_adc_read(&g_pot);
  if (g_mirror) {
    mpu6050_raw_t raw; mpu6050_data_t d;
    if (g_st.imu_ok && mpu6050_read_raw(&g_st.imu, &raw) == BUS_OK) {
      mpu6050_convert(&raw, &d);
      attitude_update(&g_att, d.ax_mg, d.ay_mg, d.az_mg, d.gx_mdps, d.gy_mdps, CTRL_PERIOD_MS);
      g_imu_last_ok = now;
      plat_servo_set_us(SERVO_PAN,  (uint32_t)servo_filter_step(&g_pan,  (int32_t)g_att.roll_deg,  CTRL_PERIOD_MS));
      plat_servo_set_us(SERVO_TILT, (uint32_t)servo_filter_step(&g_tilt, (int32_t)g_att.pitch_deg, CTRL_PERIOD_MS));
    } else if (now - g_imu_last_ok > IMU_LOST_MS) {
      /* FR-09: безпечний стан */
      servo_filter_init(&g_pan, SERVO_MID_US); servo_filter_init(&g_tilt, SERVO_MID_US);
      plat_servo_set_us(SERVO_PAN, SERVO_MID_US); plat_servo_set_us(SERVO_TILT, SERVO_MID_US);
      plat_led_toggle();
      if (g_imu_last_ok) { say("ALARM;imu_lost;servo=neutral\r\n"); g_imu_last_ok = 0; }
    }
  } else if (!g_hold) {
    int32_t us = servo_pot_to_us(g_pot);
    servo_filter_init(&g_pan, us);
    plat_servo_set_us(SERVO_PAN, (uint32_t)us);
    plat_servo_set_us(SERVO_TILT, SERVO_MID_US);
  }
  plat_probe(PROBE_LOOP, 0);
}

void app_main(void)
{
  say("\r\n=== LR2 Motion-Mirroring Teleoperator ===\r\n");
  selftest_run(&g_st);
  /* Сценарій запису (docs/captures/README.md): ті самі транзакції, що й
   * команди CLI, виконуються один раз після self-test — запис LA
   * відтворюваний без введення команд. Повторити: cap i2c|nack|spi|adc. */
  say("CAPTURE;begin\r\n");
  handle(cli_parse("cap i2c"));
  handle(cli_parse("cap nack"));
  handle(cli_parse("cap spi"));
  handle(cli_parse("cap adc"));
  say("CAPTURE;end\r\ntype 'help' for capture commands\r\n");

  attitude_init(&g_att, 0.98f);
  servo_filter_init(&g_pan, SERVO_MID_US);
  servo_filter_init(&g_tilt, SERVO_MID_US);

  cli_line_t line = { {0}, 0 };
  uint32_t t_ctrl = 0, t_tel = 0, t_btn = 0, ticks = 0;
  int btn_prev = 0;

  for (;;) {
    uint32_t now = plat_millis();

    if (cli_feed(&line, plat_getc())) handle(cli_parse(line.buf));

    int b = plat_button_pressed();               /* FR-07, антидребезг 20 мс */
    if (b != btn_prev && now - t_btn >= DEBOUNCE_MS) {
      t_btn = now; btn_prev = b;
      if (b) handle((cli_result_t){ CMD_MODE, 0 });
    }

    if (now - t_ctrl >= CTRL_PERIOD_MS) { t_ctrl = now; control_step(now); }

    if (g_tel && now - t_tel >= 1000u) {         /* FR-10 */
      t_tel = now; ticks++;
      if (!g_mirror) plat_led_toggle();
      char l[112];
      snprintf(l, sizeof l, "TEL;%lu;mode=%s;pot=%u;pitch=%d;roll=%d;pwm1=%lu;pwm2=%lu;imu=%s\r\n",
               (unsigned long)ticks, g_mirror ? "MIRROR" : "MANUAL", g_pot,
               (int)g_att.pitch_deg, (int)g_att.roll_deg,
               (unsigned long)plat_servo_get_us(SERVO_PAN), (unsigned long)plat_servo_get_us(SERVO_TILT),
               g_st.imu_ok ? "ok" : "lost");
      say(l);
    }
  }
}
