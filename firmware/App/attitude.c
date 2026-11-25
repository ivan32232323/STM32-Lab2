#include "attitude.h"
#include <math.h>

#define RAD2DEG 57.2957795f

void attitude_from_accel(int32_t ax, int32_t ay, int32_t az, float *pitch, float *roll)
{
  float fx = (float)ax, fy = (float)ay, fz = (float)az;
  *pitch = atan2f(-fx, sqrtf(fy * fy + fz * fz)) * RAD2DEG;
  *roll  = atan2f(fy, fz) * RAD2DEG;
}

void attitude_init(attitude_t *a, float alpha)
{
  a->pitch_deg = a->roll_deg = 0.0f;
  a->alpha = alpha;
  a->initialized = 0;
}

void attitude_update(attitude_t *a, int32_t ax, int32_t ay, int32_t az,
                     int32_t gx_mdps, int32_t gy_mdps, uint32_t dt_ms)
{
  float p_acc, r_acc;
  attitude_from_accel(ax, ay, az, &p_acc, &r_acc);
  if (!a->initialized) {              /* перший зразок — лише акселерометр */
    a->pitch_deg = p_acc; a->roll_deg = r_acc; a->initialized = 1;
    return;
  }
  float dt = (float)dt_ms * 1e-3f;
  a->roll_deg  = a->alpha * (a->roll_deg  + (float)gx_mdps * 1e-3f * dt) + (1.0f - a->alpha) * r_acc;
  a->pitch_deg = a->alpha * (a->pitch_deg + (float)gy_mdps * 1e-3f * dt) + (1.0f - a->alpha) * p_acc;
}

uint32_t isqrt32(uint32_t x)
{
  uint32_t r = 0, bit = 1ul << 30;
  while (bit > x) bit >>= 2;
  while (bit) {
    if (x >= r + bit) { x -= r + bit; r = (r >> 1) + bit; }
    else r >>= 1;
    bit >>= 2;
  }
  return r;
}
