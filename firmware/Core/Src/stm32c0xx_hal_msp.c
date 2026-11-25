/**
 * stm32c0xx_hal_msp.c — MSP: тактування модулів і alternate functions пінів
 * (як генерує CubeMX). Номери AF — DS13867 табл. «Port A/B alternate function
 * mapping»; значення беруться з Platform/board.h.
 */
#include "main.h"

void HAL_MspInit(void)
{
  __HAL_RCC_SYSCFG_CLK_ENABLE();
  __HAL_RCC_PWR_CLK_ENABLE();
}

void HAL_UART_MspInit(UART_HandleTypeDef *huart)
{
  GPIO_InitTypeDef g = {0};
  if (huart->Instance == USART2) {
    __HAL_RCC_USART2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();
    g.Pin       = BOARD_VCP_TX_PIN | BOARD_VCP_RX_PIN;   /* PA2 TX, PA3 RX, AF1 */
    g.Mode      = GPIO_MODE_AF_PP;
    g.Pull      = GPIO_NOPULL;
    g.Speed     = GPIO_SPEED_FREQ_LOW;
    g.Alternate = BOARD_VCP_AF;
    HAL_GPIO_Init(BOARD_VCP_TX_PORT, &g);
  }
}

void HAL_I2C_MspInit(I2C_HandleTypeDef *hi2c)
{
  GPIO_InitTypeDef g = {0};
  if (hi2c->Instance == I2C1) {
    __HAL_RCC_GPIOB_CLK_ENABLE();
    g.Pin       = BOARD_I2C_SCL_PIN | BOARD_I2C_SDA_PIN;  /* PB8 SCL, PB9 SDA, AF6 */
    g.Mode      = GPIO_MODE_AF_OD;                        /* I2C: лише open-drain  */
    /* Основні підтяжки 4.7 кОм — на модулі GY-521. Внутрішні ~40 кОм (DS13867
     * R_PU) лише страхують шину без модуля / у Wokwi: паралельно 4.7 кОм дають
     * 4.2 кОм, що в межах UM10204 для 100 кГц (див. docs/pinout.md §6). */
    g.Pull      = GPIO_PULLUP;
    g.Speed     = GPIO_SPEED_FREQ_LOW;
    g.Alternate = BOARD_I2C_AF;
    HAL_GPIO_Init(BOARD_I2C_PORT, &g);
    __HAL_RCC_I2C1_CLK_ENABLE();
  }
}

void HAL_I2C_MspDeInit(I2C_HandleTypeDef *hi2c)
{
  if (hi2c->Instance == I2C1) {
    __HAL_RCC_I2C1_CLK_DISABLE();
    HAL_GPIO_DeInit(BOARD_I2C_PORT, BOARD_I2C_SCL_PIN | BOARD_I2C_SDA_PIN);
  }
}

void HAL_SPI_MspInit(SPI_HandleTypeDef *hspi)
{
  GPIO_InitTypeDef g = {0};
  if (hspi->Instance == SPI1) {
    __HAL_RCC_SPI1_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    g.Pin       = BOARD_SPI_SCK_PIN | BOARD_SPI_MISO_PIN | BOARD_SPI_MOSI_PIN; /* PB3/PB4/PB5 AF0 */
    g.Mode      = GPIO_MODE_AF_PP;
    g.Pull      = GPIO_NOPULL;
    g.Speed     = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = BOARD_SPI_AF;
    HAL_GPIO_Init(BOARD_SPI_PORT, &g);
  }
}

void HAL_ADC_MspInit(ADC_HandleTypeDef *hadc)
{
  GPIO_InitTypeDef g = {0};
  if (hadc->Instance == ADC1) {
    __HAL_RCC_ADC_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();
    g.Pin  = BOARD_POT_PIN;          /* PA0 -> ADC1_IN0 */
    g.Mode = GPIO_MODE_ANALOG;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(BOARD_POT_PORT, &g);
  }
}

void HAL_TIM_Base_MspInit(TIM_HandleTypeDef *htim)
{
  if (htim->Instance == TIM3) {
    __HAL_RCC_TIM3_CLK_ENABLE();
  }
}

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim)
{
  GPIO_InitTypeDef g = {0};
  if (htim->Instance == TIM3) {
    __HAL_RCC_GPIOA_CLK_ENABLE();
    g.Pin       = BOARD_SERVO_PAN_PIN | BOARD_SERVO_TILT_PIN;  /* PA6 CH1, PA7 CH2, AF1 */
    g.Mode      = GPIO_MODE_AF_PP;
    g.Pull      = GPIO_NOPULL;
    g.Speed     = GPIO_SPEED_FREQ_LOW;
    g.Alternate = BOARD_SERVO_AF;
    HAL_GPIO_Init(BOARD_SERVO_PORT, &g);
  }
}
