/**
 * board.h — ЄДИНЕ місце знань про плату Nucleo-C031C6 (MB1717).
 *
 * Кожен рядок відповідає рядку таблиці docs/pinout.md; перевіряється
 * скриптом tools/check_pinout.py (board.h <-> firmware.ioc <-> diagram.json).
 * Включається лише з Core/ і Platform/ (App/ і Devices/ — заборонено,
 * див. tools/check_deps.py).
 */
#ifndef BOARD_H
#define BOARD_H

#include "stm32c0xx_hal.h"

/*        сигнал             порт   пін            AF                    Nucleo         */
/* USART2 -> ST-Link VCP */
#define BOARD_VCP_TX_PORT    GPIOA
#define BOARD_VCP_TX_PIN     GPIO_PIN_2   /* AF1 USART2_TX   -> ST-Link VCP  */
#define BOARD_VCP_RX_PORT    GPIOA
#define BOARD_VCP_RX_PIN     GPIO_PIN_3   /* AF1 USART2_RX                    */
#define BOARD_VCP_AF         GPIO_AF1_USART2

/* I2C1 -> MPU-6050 */
#define BOARD_I2C_PORT       GPIOB
#define BOARD_I2C_SCL_PIN    GPIO_PIN_8   /* AF6 I2C1_SCL    D15 / CN5-10     */
#define BOARD_I2C_SDA_PIN    GPIO_PIN_9   /* AF6 I2C1_SDA    D14 / CN5-9      */
#define BOARD_I2C_AF         GPIO_AF6_I2C1
#define BOARD_I2C_TIMING     0x10805D88u  /* 100 кГц @ I2CCLK 48 МГц (CubeMX, tr=tf=100 нс), docs/pinout.md §5 */

/* SPI1 -> W25Q64 */
#define BOARD_SPI_PORT       GPIOB
#define BOARD_SPI_SCK_PIN    GPIO_PIN_3   /* AF0 SPI1_SCK    D3  / CN9-4      */
#define BOARD_SPI_MISO_PIN   GPIO_PIN_4   /* AF0 SPI1_MISO   D5  / CN9-6      */
#define BOARD_SPI_MOSI_PIN   GPIO_PIN_5   /* AF0 SPI1_MOSI   D6  / CN9-7      */
#define BOARD_SPI_AF         GPIO_AF0_SPI1
#define BOARD_FLASH_CS_PORT  GPIOB
#define BOARD_FLASH_CS_PIN   GPIO_PIN_10  /* GPIO out, CS#   D4  / CN9-5      */
#define BOARD_SPI_PRESC      SPI_BAUDRATEPRESCALER_16   /* 48/16 = 3 МГц     */

/* ADC1 -> потенціометр */
#define BOARD_POT_PORT       GPIOA
#define BOARD_POT_PIN        GPIO_PIN_0   /* ADC1_IN0        A0  / CN8-1      */
#define BOARD_POT_CHANNEL    ADC_CHANNEL_0

/* TIM3 -> серво */
#define BOARD_SERVO_PORT     GPIOA
#define BOARD_SERVO_PAN_PIN  GPIO_PIN_6   /* AF1 TIM3_CH1    D12 / CN5-5      */
#define BOARD_SERVO_TILT_PIN GPIO_PIN_7   /* AF1 TIM3_CH2    D11 / CN5-4      */
#define BOARD_SERVO_AF       GPIO_AF1_TIM3
#define BOARD_SERVO_PSC      (48u - 1u)    /* 48 МГц / 48 = 1 МГц, 1 тік = 1 мкс */
#define BOARD_SERVO_ARR      (20000u - 1u) /* 20 мс -> 50 Гц                    */

/* GPIO */
#define BOARD_LED_PORT       GPIOA
#define BOARD_LED_PIN        GPIO_PIN_5   /* LD4 (бортовий)  D13 / CN5-6      */
#define BOARD_BTN_PORT       GPIOA
#define BOARD_BTN_PIN        GPIO_PIN_10  /* вхід, pull-up   D2  / CN9-3      */
#define BOARD_PROBE_ADC_PORT GPIOB
#define BOARD_PROBE_ADC_PIN  GPIO_PIN_0   /* службовий вихід D10 / CN5-3      */
#define BOARD_PROBE_LOOP_PORT GPIOA
#define BOARD_PROBE_LOOP_PIN GPIO_PIN_9   /* службовий вихід D8  / CN5-1      */

/* Хендли периферії (визначені в Core/Src/main.c, CubeMX) */
extern I2C_HandleTypeDef  hi2c1;
extern SPI_HandleTypeDef  hspi1;
extern UART_HandleTypeDef huart2;
extern ADC_HandleTypeDef  hadc1;
extern TIM_HandleTypeDef  htim3;

#endif
