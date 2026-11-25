/* USER CODE BEGIN Header */
/**
 * main.h — заголовок Core (структура як у STM32CubeMX).
 * Номери пінів НЕ дублюються тут: єдине джерело — Platform/board.h.
 */
/* USER CODE END Header */
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

#include "stm32c0xx_hal.h"

/* USER CODE BEGIN Includes */
#include "board.h"
/* USER CODE END Includes */

void Error_Handler(void);
void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* USER CODE BEGIN EFP */
/* USER CODE END EFP */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
