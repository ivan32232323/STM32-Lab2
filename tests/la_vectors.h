/**
 * la_vectors.h — тестові вектори, витягнуті з записів логічного аналізатора.
 * Згенеровано tools/extract_vectors.py (декодери i2c та uart sigrok-cli) із
 * записів у docs/captures. НЕ редагувати вручну.
 */
#ifndef LA_VECTORS_H
#define LA_VECTORS_H
#include <stdint.h>

typedef struct {
  const char *source;        /* файл запису                          */
  uint8_t bus_bytes[14];     /* байти SDA у фазі читання 0x3B..0x48  */
  int16_t uart_raw[7];       /* ax, ay, az, temp, gx, gy, gz з UART  */
  int32_t uart_temp_cdeg;    /* temp_c із рядка self-test × 100      */
} la_vec_t;

static const la_vec_t la_vec[] = {
  { "session-A_i2c-spi-uart-pwm.vcd",
    { 0xE0, 0x00, 0x00, 0x00, 0x37, 0x6C, 0xEF, 0x5C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 },
    { -8192, 0, 14188, -4260, 0, 0, 0 }, 2400 },
};
#define LA_VEC_N (sizeof la_vec / sizeof la_vec[0])

#endif
