---
title: "Лабораторна робота №1"
---

Міністерство освіти і науки України  
Національний технічний університет України  
«Київський політехнічний інститут імені Ігоря Сікорського»  

Факультет інформатики та обчислювальної техніки  

Кафедра обчислювальної техніки  

**Лабораторна робота №1**  
з дисципліни «Системне програмування»  
«Налаштування середовища розробки та bring-up STM32-платформи»  

Виконав:  
студент 4 курсу  
групи ІО-32  
Шведенко Іван Олексійович  

Перевірив:  
Гордієнко Н.Ю.  

Київ — 2026  

---

### Лабораторна робота №1

### Налаштування середовища розробки та bring-up STM32-платформи

**Мета:** розібратися з повним циклом розробки під STM32: налаштувати збірку в Docker, запустити прошивку в симуляторі Wokwi і отримати вивід у UART. Перевірити роботу I²C, ADC, PWM і GPIO, а також описати вимоги до свого проєкту у вигляді PRD.

Репозиторій: https://github.com/ivan32232323/STM32-Lab1

PRD: https://github.com/ivan32232323/STM32-Lab1/blob/lab1/docs/PRD.md

Відео: [посилання на відео буде додано]

# 2. Розподіл обов'язків

Робота виконана одноосібно, таблиця не потрібна.

# 3. Процес виконання

## 3.1. Журнал роботи

| Дата | Що зроблено |
|---|---|
| 06.11 | Встановлено VS Code, плагін Wokwi, Git, Docker Desktop. Створено Dockerfile і кореневий Makefile |
| 06.11 | Створено проєкт під Nucleo-C031C6: HAL, CMSIS, startup, linker, .ioc |
| 06.11 | printf через USART2, ініціалізація I2C1, ADC1, TIM3, GPIO, I²C-скан, WHO_AM_I, вивід tick N |
| 06.11 | Складено diagram.json, docs/hardware-components.md і docs/PRD.md |
| 06.11 | Запуск у Wokwi, налагодження читання MPU-6050, захоплення I²C логічним аналізатором |
| 06.11 | Скриншоти і звіт |

## 3.2. Docker-тулчейн

Образ stm32-build на базі ubuntu:22.04 з arm-none-eabi-gcc. Збірка запускається командою make build і не залежить від налаштувань системи. На Windows без make можна запустити build.bat.

```
make image   # docker build -t stm32-build docker/
make build   # docker run ... stm32-build make -C firmware all
```

```
LD  build/firmware.elf
   text    data     bss     dec     hex filename
  25612     112    2320   28044    6d8c build/firmware.elf
```

Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/41839b3

## 3.3. STM32CubeMX

| Периферія | Параметри | Виводи |
|---|---|---|
| USART2 | 115200 8N1 | PA2 / PA3 |
| I2C1 | Standard Mode, 100 kHz | PB8 (SCL) / PB9 (SDA) |
| TIM3 CH1, CH2 | PWM 50 Hz (Prescaler = 47, Period = 19999) | PA6 / PA7 |
| ADC1 | IN0 | PA0 |
| GPIO | кнопка MODE (pull-up), світлодіод LD4 | PA10 / PA5 |

SYSCLK = 48 MHz. Проєкт з тулчейном Makefile, файл .ioc збережено в репозиторії.

Pinout:

![](screenshots/cubemx-pinout.png)

Clock Configuration:

![](screenshots/cubemx-clock.png)

Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/9efc7ab

## 3.4. Перший запуск у Wokwi

printf перенаправлено в USART2 через функцію _write(). Налаштовано wokwi.toml і diagram.json. Розмір прошивки — 25 612 байт.

```
=== hello from STM32 ===
LR1 bring-up | MCU STM32C031C6 | SYSCLK = 48000000 Hz
[ OK ] MX_USART2_UART_Init    -> HAL_OK
[ OK ] MX_I2C1_Init           -> HAL_OK
[ OK ] MX_ADC1_Init           -> HAL_OK
[ OK ] MX_TIM3_Init           -> HAL_OK
I2C1 scan: 0x68  (1 device(s))
MPU-6050 WHO_AM_I (0x75) = 0x68  [soft-I2C] -> identified
tick 1 | mode=MANUAL pot=0 pitch=0 roll=0 pwm1=1000 pwm2=1500
tick 2 | ...
```

Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/63b031d

## 3.5. Компоненти і datasheets

У docs/hardware-components.md для кожного компонента вказано інтерфейс, адресу, ключові регістри і параметри з номером сторінки datasheet.

![](datasheets/mpu6050-rm-p45-who-am-i.png)

1. InvenSense. MPU-6000/MPU-6050 Register Map and Descriptions, RM-MPU-6000A-00, rev 4.2.

![](datasheets/mpu6050-rm-p40-pwr-mgmt1.png)

![](datasheets/mpu6050-rm-p29-accel.png)

![](datasheets/mpu6050-ps-p15-i2c-addr.png)

2. InvenSense. MPU-6000/MPU-6050 Product Specification, PS-MPU-6000A-00, rev 3.4, 19.08.2013.

![](datasheets/mpu6050-ps-p14-current.png)

![](datasheets/mpu6050-ps-p35-i2c-protocol.png)

Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/aa6f906

## 3.6. Сенсори і перевірка шин

До diagram.json додано MPU-6050, потенціометр, два серво SG90, кнопку і логічний аналізатор. Кнопкою перемикається режим: MANUAL (серво від потенціометра) або MIRROR (серво повторюють нахил MPU-6050).

Робота в режимі MIRROR:

![](screenshots/wokwi-mirror.png)

Декодована транзакція WHO_AM_I (запис з логічного аналізатора Wokwi, wokwi.vcd):

![](screenshots/logic-i2c-whoami.png)

PWM на виводі серво:

![](screenshots/logic-pwm.png)

Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/340da7b

## 3.7. Проблеми та їх вирішення

Проблема 1: у Wokwi немає Nucleo-F411RE / F446RE  
Симптом: у списку плат Wokwi є тільки Nucleo-C031C6 і Nucleo-L031K6.  
Фікс: взяв Nucleo-C031C6, підключив HAL для STM32C0 і змінив у Makefile -mcpu на cortex-m0plus.  
Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/9efc7ab

Проблема 2: збірка падає на m-profile/cmsis_gcc_m.h: No such file or directory  
Симптом: make build -> fatal error у cmsis_gcc.h.  
Фікс: заголовки CMSIS були з іншої версії. Взяв папку CMSIS/Include з того ж пакета, що й HAL.  
Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/9efc7ab

Проблема 3: implicit declaration of function HAL_TIM_MspPostInit  
Симптом: попередження при збірці в MX_TIM3_Init().  
Фікс: додав прототип функції в main.h.  
Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/63b031d

Проблема 4: make build не працює на Windows  
Симптом: у PowerShell немає make, а $(id -u) у Makefile не спрацьовує.  
Фікс: для Windows прибрав --user у Makefile і додав build.bat.  
Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/41839b3

Проблема 5: MPU-6050 — WHO_AM_I = 0x00  
Симптом: I²C-скан бачить 0x68, але HAL_I2C_Mem_Read повертає HAL_ERROR (err = 0x20, timeout). Master_Transmit + Master_Receive дають те саме.  
Фікс: у логічному аналізаторі видно, що після адреси читання 0xD1 немає тактів SCL. Зробив читання програмним I²C на тих самих пінах, SDA під час читання перемикаю на вхід. Після цього WHO_AM_I = 0x68.  
Коміт: https://github.com/ivan32232323/STM32-Lab1/commit/340da7b

# 4. Висновок

Навчився:

- збирати прошивку STM32 в Docker;
- налаштовувати периферію через HAL і виводити printf в UART;
- читати datasheet і reference manual;
- перевіряти I²C-пристрої за адресою та регістром WHO_AM_I і дивитися сигнали в логічному аналізаторі.

Куди рухаюся в ЛР2: почати реалізацію вимог з PRD — читати гіроскоп, додати фільтр для кутів, виміряти затримку від руху датчика до руху серво.

# 5. Матеріали та посилання

1. InvenSense. MPU-6000/MPU-6050 Register Map and Descriptions, RM-MPU-6000A-00, rev 4.2. 46 с.
2. InvenSense. MPU-6000/MPU-6050 Product Specification, PS-MPU-6000A-00, rev 3.4, 19.08.2013. 52 с.
3. STMicroelectronics. STM32C031x4/x6 Datasheet, DS13867. https://www.st.com/en/microcontrollers-microprocessors/stm32c031c6.html
4. STMicroelectronics. RM0490 Reference Manual: STM32C0 series. https://www.st.com/en/microcontrollers-microprocessors/stm32c031c6.html#documentation
5. STMicroelectronics. STM32 Nucleo-64 boards (MB1717), user manual UM2953. https://www.st.com/resource/en/user_manual/um2953-stm32-nucleo64-board-mb1717-stmicroelectronics.pdf
6. TowerPro. SG90 Micro Servo datasheet.
7. Wokwi. Документація: diagram.json, STM32 Nucleo-C031C6. https://docs.wokwi.com
