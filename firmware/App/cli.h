/**
 * cli.h — команди UART, що відтворюють записані транзакції (ЛР2 п.4.3:
 * «у прошивці має бути режим або команда, що ініціює саме ту транзакцію»).
 * Парсер — чиста функція (тестується на хості).
 */
#ifndef CLI_H
#define CLI_H

#include <stdint.h>

typedef enum {
  CMD_NONE = 0, CMD_UNKNOWN, CMD_HELP, CMD_SELFTEST,
  CMD_I2C_HW, CMD_I2C_SW,
  CMD_CAP_I2C,    /* WHO_AM_I + burst 14 Б з MPU-6050              */
  CMD_CAP_NACK,   /* навмисна аномалія: читання з 0x69 (немає slave) */
  CMD_CAP_SPI,    /* JEDEC ID + erase + WREN/PP + READ               */
  CMD_CAP_PWM,    /* arg = ширина імпульсу pan, мкс                  */
  CMD_CAP_ADC,    /* 10 перетворень з маркером PROBE_ADC             */
  CMD_MODE,       /* перемкнути MANUAL/MIRROR                        */
  CMD_TEL         /* arg = 0/1 телеметрія                            */
} cli_cmd_t;

typedef struct {
  cli_cmd_t cmd;
  int32_t   arg;
} cli_result_t;

/* Розбір одного рядка (без \r\n). */
cli_result_t cli_parse(const char *line);

/* Накопичення символів у рядок; повертає 1, коли рядок завершено (\r або \n). */
typedef struct { char buf[32]; unsigned len; } cli_line_t;
int cli_feed(cli_line_t *l, int ch);

#endif
