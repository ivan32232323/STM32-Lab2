/**
 * servo_map.h — перетворення кут/ADC -> ширина імпульсу серво, мертва зона,
 * обмеження швидкості (FR-02, FR-05, FR-06). Чисті функції, без HAL.
 */
#ifndef SERVO_MAP_H
#define SERVO_MAP_H

#include <stdint.h>

#define SERVO_MIN_US   1000   /* −90° (SG90 datasheet: 1 мс)   */
#define SERVO_MID_US   1500   /*   0°                          */
#define SERVO_MAX_US   2000   /* +90° (2 мс)                   */
#define SERVO_DEADBAND_DEG   2      /* FR-06 */
#define SERVO_MAX_RATE_DPS 300      /* FR-06 */

int32_t servo_deg_to_us(int32_t deg);            /* −90..+90 -> 1000..2000, з насиченням */
int32_t servo_us_to_deg(int32_t us);
int32_t servo_pot_to_us(uint16_t adc);           /* 0..4095 -> 1000..2000 (FR-05)        */

typedef struct {
  int32_t out_us;      /* поточна команда на серво */
  int32_t held_deg;    /* кут, на якому «стоїть» мертва зона */
} servo_filter_t;

void    servo_filter_init(servo_filter_t *f, int32_t us);
/* Новий цільовий кут; dt_ms — період контуру. Повертає нову ширину імпульсу. */
int32_t servo_filter_step(servo_filter_t *f, int32_t target_deg, uint32_t dt_ms);

#endif
