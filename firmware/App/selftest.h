/**
 * selftest.h — режим bring-up / самоперевірки (ЛР2 п.4.2, FR-08).
 *
 * Формат виводу (по рядку на перевірку, поля через ';', придатно для
 * tools/parse_selftest.py та будь-якого CSV-парсера):
 *   ST;<пристрій>;<перевірка>;<PASS|FAIL|WARN|INFO>;<значення>;<критерій>
 * Перший рядок  ST;BEGIN;...   останній  ST;SUMMARY;all;<PASS|FAIL>;pass=N fail=M warn=K;
 */
#ifndef SELFTEST_H
#define SELFTEST_H

#include <stdint.h>
#include "bus.h"
#include "mpu6050.h"
#include "w25q.h"

typedef enum { ST_PASS, ST_FAIL, ST_WARN, ST_INFO } st_level_t;

typedef struct {
  int pass, fail, warn;
} st_counts_t;

/* Форматування одного рядка у buf (без UART) — тестується на хості */
int  st_format(char *buf, unsigned len, const char *dev, const char *check,
               st_level_t lvl, const char *value, const char *crit);
void st_emit(st_counts_t *c, const char *dev, const char *check,
             st_level_t lvl, const char *value, const char *crit);

/* Критерії фізичної правдоподібності (окремо, щоб тестувати) */
int st_accel_norm_ok(int32_t ax_mg, int32_t ay_mg, int32_t az_mg, uint32_t *norm_mg); /* 1 g ± 5 % */
int st_temp_ok(int32_t cdeg);                                                         /* 15…35 °C  */
int st_gyro_still_ok(int32_t gx, int32_t gy, int32_t gz);                             /* |ω| < 5 °/с */

typedef struct {
  mpu6050_t imu;          /* bus вибирається під час self-test (HW або SW)   */
  w25q_t    flash;
  int       imu_ok, flash_ok;
  st_counts_t counts;
} selftest_ctx_t;

/* Повний прогін; повертає кількість FAIL */
int selftest_run(selftest_ctx_t *ctx);

#endif
