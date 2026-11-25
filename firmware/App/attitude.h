/**
 * attitude.h — нахил кисті з акселерометра + комплементарний фільтр з гіроскопом
 * (FR-01). Чисті функції, вхід — фізичні одиниці з Devices/mpu6050.
 */
#ifndef ATTITUDE_H
#define ATTITUDE_H

#include <stdint.h>

typedef struct {
  float pitch_deg, roll_deg;
  float alpha;          /* вага гіроскопа, 0.98 */
  int   initialized;
} attitude_t;

/* pitch = atan2(−ax, √(ay²+az²)), roll = atan2(ay, az) — AN3461 (NXP), eq. 25/26 */
void attitude_from_accel(int32_t ax_mg, int32_t ay_mg, int32_t az_mg, float *pitch, float *roll);

void attitude_init(attitude_t *a, float alpha);
/* gx/gy — мілі-°/с навколо X (roll) і Y (pitch), dt_ms — період */
void attitude_update(attitude_t *a, int32_t ax_mg, int32_t ay_mg, int32_t az_mg,
                     int32_t gx_mdps, int32_t gy_mdps, uint32_t dt_ms);

/* Цілочисельний квадратний корінь (для |a| у self-test) */
uint32_t isqrt32(uint32_t x);

#endif
