#include "servo_map.h"

static int32_t clamp(int32_t v, int32_t lo, int32_t hi) { return v < lo ? lo : (v > hi ? hi : v); }

/* Округлення до найближчого: ±(x + d/2)/d */
static int32_t div_round(int32_t n, int32_t d) { return n >= 0 ? (n + d / 2) / d : -((-n + d / 2) / d); }

int32_t servo_deg_to_us(int32_t deg)
{
  deg = clamp(deg, -90, 90);
  return SERVO_MID_US + div_round(deg * (SERVO_MAX_US - SERVO_MID_US), 90);
}

int32_t servo_us_to_deg(int32_t us)
{
  us = clamp(us, SERVO_MIN_US, SERVO_MAX_US);
  return div_round((us - SERVO_MID_US) * 90, SERVO_MAX_US - SERVO_MID_US);
}

int32_t servo_pot_to_us(uint16_t adc)
{
  if (adc > 4095u) adc = 4095u;
  return SERVO_MIN_US + div_round((int32_t)adc * (SERVO_MAX_US - SERVO_MIN_US), 4095);
}

void servo_filter_init(servo_filter_t *f, int32_t us)
{
  f->out_us = clamp(us, SERVO_MIN_US, SERVO_MAX_US);
  f->held_deg = servo_us_to_deg(f->out_us);
}

int32_t servo_filter_step(servo_filter_t *f, int32_t target_deg, uint32_t dt_ms)
{
  target_deg = clamp(target_deg, -90, 90);
  /* мертва зона: ігнорувати тремтіння |Δ| < 2° відносно утримуваного кута */
  int32_t d = target_deg - f->held_deg;
  if (d < 0) d = -d;
  if (d >= SERVO_DEADBAND_DEG) f->held_deg = target_deg;

  int32_t goal = servo_deg_to_us(f->held_deg);
  /* обмеження швидкості: 300 °/с = 300·500/90 мкс/с */
  int32_t max_step = (int32_t)((SERVO_MAX_RATE_DPS * (SERVO_MAX_US - SERVO_MID_US) / 90) * dt_ms / 1000u);
  if (max_step < 1) max_step = 1;
  int32_t step = clamp(goal - f->out_us, -max_step, max_step);
  f->out_us += step;
  return f->out_us;
}
