#ifndef FAKE_PLATFORM_H
#define FAKE_PLATFORM_H

#include "platform.h"
#include <stddef.h>

typedef struct {
  uint32_t now_ms;
  char     out[4096];
  size_t   out_len;
  uint16_t adc_value;
  int      adc_fail, adc_reads;
  uint32_t servo[2];
  int      servo_stuck;
  int      led, button, probe[2];
  const i2c_bus_t *i2c_hw, *i2c_sw;
  const spi_dev_t *spi;
  uint32_t i2c_hw_err;
} fake_platform_t;

extern fake_platform_t fp;
void fake_platform_reset(void);

#endif
