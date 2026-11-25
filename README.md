# STM32 · ЛР2 — інтеграція сенсорної підсистеми (форма B, Wokwi) · Motion-Mirroring Teleoperator

Прошивка на STM32 HAL для **Nucleo-C031C6** у симуляторі Wokwi: MPU-6050 (I²C), W25Q64 (SPI, власна модель
Wokwi), потенціометр (ADC), 2 серво (PWM), кнопка, UART. Шарова архітектура, хостові тести, CI.

## Швидкий старт

```bash
make image      # один раз: Docker-образ з тулчейном (версії зафіксовано)
make build      # firmware/build/firmware.{elf,hex,bin}; -Wall -Wextra -Werror, 0 попереджень
make test       # хостові тести (Unity), плата не потрібна
make coverage   # + покриття Devices/ і App/ (поріг 90 % рядків)
make check      # правило залежностей шарів + узгодженість pinout
make ci         # усе разом (те саме запускає GitHub Actions)
NATIVE=1 make … # без Docker, якщо тулчейн встановлено локально
```
Потім у VS Code відкрийте `diagram.json` і натисніть ▶ (Wokwi). На старті прошивка виводить self-test у UART
у форматі `ST;<пристрій>;<перевірка>;<PASS|FAIL|WARN|INFO>;<значення>;<критерій>`
(розбір: `python3 tools/parse_selftest.py <лог>`).

## Структура

```
firmware/Core/      CubeMX: MX_*_Init, MSP, IRQ → app_main()
firmware/Drivers/   ST HAL v1.4.1 + CMSIS (VERSIONS.md)
firmware/Platform/  board.h (усі піни) + platform.c (HAL-реалізації шин і порту)
firmware/Devices/   bus.h, mpu6050.c, w25q.c — без HAL
firmware/App/       app, selftest, attitude, servo_map, cli — без HAL
chips/              модель W25Q64 для Wokwi (C → wasm)
tests/              Unity-тести, doubles (fake I2C, mock SPI, stub-платформа)
tools/              check_deps, check_pinout, la_analyze, extract_vectors, make_diagrams, make_report2
docs/pinout.md        pinout, адреси, бюджет живлення, параметри шин, відхилені варіанти
docs/architecture.md  шари, правило залежностей, component diagram, тестування
docs/captures/        записи LA (.vcd/.sr), анотації, analysis.md
docs/lab2-report.md   звіт (PDF: docs/lab2-report.pdf)
```

## Розводка (повна таблиця — docs/pinout.md)

| Сигнал | Пін (Arduino) | Периферія |
|---|---|---|
| VCP TX/RX | PA2 / PA3 | USART2 115200 8N1 |
| MPU-6050 SCL/SDA | PB8 (D15) / PB9 (D14) | I2C1 AF6, 0x68, 100 кГц |
| W25Q64 SCK/MISO/MOSI | PB3 (D3) / PB4 (D5) / PB5 (D6) | SPI1 AF0, mode 0, 3 МГц |
| W25Q64 CS# | PB10 (D4) | GPIO (програмний CS#) |
| Потенціометр | PA0 (A0) | ADC1_IN0 |
| Серво pan / tilt | PA6 (D12) / PA7 (D11) | TIM3_CH1/CH2, 50 Гц |
| Кнопка MODE | PA10 (D2) | GPIO in, pull-up |
| LED LD4 | PA5 (D13) | GPIO out |
| Проби LA: ADC / контур | PB0 (D10) / PA9 (D8) | GPIO out |
