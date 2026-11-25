/**
 * platform.c — реалізація platform.h над STM32 HAL (Nucleo-C031C6).
 * Тут і лише тут прикладний код «зустрічається» з HAL.
 */
#include "platform.h"
#include "board.h"

/* ------------------------------------------------------------------ час */
uint32_t plat_millis(void)          { return HAL_GetTick(); }
void     plat_delay_ms(uint32_t ms) { HAL_Delay(ms); }
uint32_t plat_sysclk_hz(void)       { return HAL_RCC_GetSysClockFreq(); }

/* ----------------------------------------------------------------- UART */
void plat_puts(const char *s)
{
  const char *e = s;
  while (*e) e++;
  if (e != s) HAL_UART_Transmit(&huart2, (const uint8_t *)s, (uint16_t)(e - s), 100);
}

int plat_getc(void)
{
  if (__HAL_UART_GET_FLAG(&huart2, UART_FLAG_ORE)) __HAL_UART_CLEAR_OREFLAG(&huart2);
  if (__HAL_UART_GET_FLAG(&huart2, UART_FLAG_RXNE))
    return (int)(huart2.Instance->RDR & 0xFFu);
  return -1;
}

/* ------------------------------------------------------------------ ADC */
int plat_adc_read(uint16_t *value)
{
  int ok = 0;
  plat_probe(PROBE_ADC, 1);                       /* фронт = старт перетворення */
  if (HAL_ADC_Start(&hadc1) == HAL_OK &&
      HAL_ADC_PollForConversion(&hadc1, 2) == HAL_OK) {
    *value = (uint16_t)HAL_ADC_GetValue(&hadc1);
    ok = 1;
  }
  HAL_ADC_Stop(&hadc1);
  plat_probe(PROBE_ADC, 0);                       /* спад = результат прочитано */
  return ok ? BUS_OK : BUS_TIMEOUT;
}

/* ---------------------------------------------------------------- серво */
static uint32_t servo_ch(servo_id_t ch) { return ch == SERVO_PAN ? TIM_CHANNEL_1 : TIM_CHANNEL_2; }
void plat_servo_set_us(servo_id_t ch, uint32_t us) { __HAL_TIM_SET_COMPARE(&htim3, servo_ch(ch), us); }
uint32_t plat_servo_get_us(servo_id_t ch)          { return __HAL_TIM_GET_COMPARE(&htim3, servo_ch(ch)); }

/* ----------------------------------------------------------------- GPIO */
void plat_led(int on)    { HAL_GPIO_WritePin(BOARD_LED_PORT, BOARD_LED_PIN, on ? GPIO_PIN_SET : GPIO_PIN_RESET); }
void plat_led_toggle(void) { HAL_GPIO_TogglePin(BOARD_LED_PORT, BOARD_LED_PIN); }
int  plat_button_pressed(void) { return HAL_GPIO_ReadPin(BOARD_BTN_PORT, BOARD_BTN_PIN) == GPIO_PIN_RESET; }

void plat_probe(probe_id_t p, int level)
{
  GPIO_TypeDef *port = p == PROBE_ADC ? BOARD_PROBE_ADC_PORT : BOARD_PROBE_LOOP_PORT;
  uint16_t pin       = p == PROBE_ADC ? BOARD_PROBE_ADC_PIN  : BOARD_PROBE_LOOP_PIN;
  if (level) port->BSRR = pin; else port->BRR = pin;
}

/* ============================================================ I2C (HAL) */
static int hal_to_bus(HAL_StatusTypeDef st, const I2C_HandleTypeDef *h)
{
  if (st == HAL_OK) return BUS_OK;
  if (h && (h->ErrorCode & HAL_I2C_ERROR_AF)) return BUS_NACK;
  if (st == HAL_TIMEOUT || (h && (h->ErrorCode & HAL_I2C_ERROR_TIMEOUT))) return BUS_TIMEOUT;
  return BUS_ERROR;
}

static int hw_i2c_write(void *ctx, uint8_t a, const uint8_t *d, size_t n)
{
  I2C_HandleTypeDef *h = ctx;
  return hal_to_bus(HAL_I2C_Master_Transmit(h, (uint16_t)(a << 1), (uint8_t *)d, (uint16_t)n, 10), h);
}

static int hw_i2c_write_read(void *ctx, uint8_t a, const uint8_t *w, size_t wn, uint8_t *r, size_t rn)
{
  I2C_HandleTypeDef *h = ctx;
  if (wn == 1)   /* адреса регістру + repeated START + читання */
    return hal_to_bus(HAL_I2C_Mem_Read(h, (uint16_t)(a << 1), w[0], I2C_MEMADD_SIZE_8BIT, r, (uint16_t)rn, 10), h);
  int st = hal_to_bus(HAL_I2C_Master_Transmit(h, (uint16_t)(a << 1), (uint8_t *)w, (uint16_t)wn, 10), h);
  if (st != BUS_OK) return st;
  return hal_to_bus(HAL_I2C_Master_Receive(h, (uint16_t)(a << 1), r, (uint16_t)rn, 10), h);
}

static const i2c_bus_t i2c_hw = { hw_i2c_write, hw_i2c_write_read, &hi2c1 };
const i2c_bus_t *plat_i2c_hw(void) { return &i2c_hw; }
uint32_t plat_i2c_hw_last_error(void) { return HAL_I2C_GetError(&hi2c1); }

/* ======================================================= I2C (bit-bang) */
/* Обхід дефекту моделі I2C STM32C0 у Wokwi (немає тактів SCL у фазі
 * читання, див. docs/captures/analysis.md §A1). Ті самі піни PB8/PB9,
 * open-drain + pull-up, напівперіод ≈ 5 мкс (~100 кГц). На реальній
 * платі використовується plat_i2c_hw(). */
#define SW_HALF_LOOPS 1u   /* підібрано за LA: див. analysis.md §A3 */
static int sw_active;

static void sw_delay(void) { for (volatile uint32_t i = 0; i < SW_HALF_LOOPS; i++) { } }
#define SCL_H() (BOARD_I2C_PORT->BSRR = BOARD_I2C_SCL_PIN)
#define SCL_L() (BOARD_I2C_PORT->BRR  = BOARD_I2C_SCL_PIN)
#define SDA_H() (BOARD_I2C_PORT->BSRR = BOARD_I2C_SDA_PIN)   /* відпустити (OD) */
#define SDA_L() (BOARD_I2C_PORT->BRR  = BOARD_I2C_SDA_PIN)
#define SDA_R() ((BOARD_I2C_PORT->IDR & BOARD_I2C_SDA_PIN) != 0u)

static void sw_attach(void)
{
  if (sw_active) return;
  HAL_I2C_DeInit(&hi2c1);
  GPIO_InitTypeDef g = {0};
  g.Pin = BOARD_I2C_SCL_PIN | BOARD_I2C_SDA_PIN;
  g.Mode = GPIO_MODE_OUTPUT_OD; g.Pull = GPIO_PULLUP; g.Speed = GPIO_SPEED_FREQ_HIGH;
  SDA_H(); SCL_H();
  HAL_GPIO_Init(BOARD_I2C_PORT, &g);
  sw_active = 1;
}
/* SDA як вхід під час читання: модель Wokwi не повертає рівень OD-виходу в IDR */
static void sda_input(int in)
{
  uint32_t pos = 9u * 2u;   /* PB9 */
  uint32_t m = BOARD_I2C_PORT->MODER & ~(3u << pos);
  BOARD_I2C_PORT->MODER = in ? m : (m | (1u << pos));
}
static void sw_start(void) { sda_input(0); SDA_H(); SCL_H(); sw_delay(); SDA_L(); sw_delay(); SCL_L(); }
static void sw_stop(void)  { sda_input(0); SDA_L(); sw_delay(); SCL_H(); sw_delay(); SDA_H(); sw_delay(); }
static int sw_wbyte(uint8_t b)                      /* 1 = ACK */
{
  sda_input(0);
  for (int i = 7; i >= 0; i--) {
    if (b & (1u << i)) SDA_H(); else SDA_L();
    sw_delay(); SCL_H(); sw_delay(); SCL_L();
  }
  SDA_H(); sda_input(1); sw_delay(); SCL_H(); sw_delay();
  int ack = !SDA_R();
  SCL_L(); sda_input(0);
  return ack;
}
static uint8_t sw_rbyte(int ack)
{
  uint8_t b = 0;
  SDA_H(); sda_input(1);
  for (int i = 0; i < 8; i++) {
    sw_delay(); SCL_H(); sw_delay();
    b = (uint8_t)((b << 1) | (SDA_R() ? 1u : 0u));
    SCL_L();
  }
  sda_input(0);
  if (ack) SDA_L(); else SDA_H();
  sw_delay(); SCL_H(); sw_delay(); SCL_L(); SDA_H();
  return b;
}
static int sw_i2c_write(void *ctx, uint8_t a, const uint8_t *d, size_t n)
{
  (void)ctx; sw_attach();
  sw_start();
  int st = sw_wbyte((uint8_t)(a << 1)) ? BUS_OK : BUS_NACK;
  for (size_t i = 0; st == BUS_OK && i < n; i++) if (!sw_wbyte(d[i])) st = BUS_NACK;
  sw_stop();
  return st;
}
static int sw_i2c_write_read(void *ctx, uint8_t a, const uint8_t *w, size_t wn, uint8_t *r, size_t rn)
{
  (void)ctx; sw_attach();
  sw_start();
  int st = sw_wbyte((uint8_t)(a << 1)) ? BUS_OK : BUS_NACK;
  for (size_t i = 0; st == BUS_OK && i < wn; i++) if (!sw_wbyte(w[i])) st = BUS_NACK;
  if (st == BUS_OK) {
    sw_start();                                    /* repeated START */
    if (!sw_wbyte((uint8_t)((a << 1) | 1u))) st = BUS_NACK;
    for (size_t i = 0; st == BUS_OK && i < rn; i++) r[i] = sw_rbyte(i + 1 < rn);
  }
  sw_stop();
  return st;
}
static const i2c_bus_t i2c_sw = { sw_i2c_write, sw_i2c_write_read, 0 };
const i2c_bus_t *plat_i2c_sw(void) { return &i2c_sw; }

/* ================================================================= SPI */
static void spi_select(void *ctx, int active)
{
  (void)ctx;
  if (active) BOARD_FLASH_CS_PORT->BRR = BOARD_FLASH_CS_PIN;   /* CS# low  */
  else        BOARD_FLASH_CS_PORT->BSRR = BOARD_FLASH_CS_PIN;  /* CS# high */
}

static int spi_transfer(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n)
{
  /* Один виклик HAL на весь буфер: побайтові виклики давали паузу
   * ~60 мкс між байтами (docs/captures/analysis.md §B3). */
  SPI_HandleTypeDef *h = ctx;
  HAL_StatusTypeDef st;
  if (n == 0) return BUS_OK;
  if (n > 0xFFFFu) return BUS_ARG;
  if (tx && rx)  st = HAL_SPI_TransmitReceive(h, (uint8_t *)tx, rx, (uint16_t)n, 10);
  else if (tx)   st = HAL_SPI_Transmit(h, (uint8_t *)tx, (uint16_t)n, 10);
  else {
    for (size_t i = 0; i < n; i++) rx[i] = 0xFFu;   /* фіктивні байти = 0xFF */
    st = HAL_SPI_TransmitReceive(h, rx, rx, (uint16_t)n, 10);   /* in-place: tx-індекс завжди попереду rx */
  }
  return st == HAL_OK ? BUS_OK : BUS_TIMEOUT;
}

static void spi_delay_us(void *ctx, uint32_t us)
{
  (void)ctx;
  uint32_t ms = (us + 999u) / 1000u;   /* SysTick 1 мс — достатньо для tPP/tSE */
  HAL_Delay(ms ? ms : 1u);
}

static const spi_dev_t flash_spi = { spi_select, spi_transfer, spi_delay_us, &hspi1 };
const spi_dev_t *plat_flash_spi(void) { return &flash_spi; }
