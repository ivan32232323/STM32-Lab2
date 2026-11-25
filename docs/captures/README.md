# docs/captures — записи логічного аналізатора (форма B, Wokwi)

## Як відтворити

1. `make build` (або `NATIVE=1 make build`) → `firmware/build/firmware.hex`.
2. VS Code → відкрити `diagram.json` → ▶ (Wokwi). Прошивка сама виконує сценарій запису:
   self-test (WHO_AM_I, burst, JEDEC, erase/program/read, ADC, PWM 1000/2000 мкс), потім
   `CAPTURE;begin` → `cap i2c`, `cap nack`, `cap spi`, `cap adc` → `CAPTURE;end`.
   Ті самі транзакції повторюються командами в Serial Monitor:

   | Команда | Що з'являється на шині |
   |---|---|
   | `st` | повний self-test |
   | `cap i2c` | WHO_AM_I + burst 0x3B..0x48 (14 Б) |
   | `cap nack` | WHO_AM_I на 0x69 → NACK |
   | `cap spi` | 9Fh, 05h, 06h+20h (стирання 0x2000), BUSY, 06h+02h «LR2-SPI!», 03h |
   | `cap adc` | 10 перетворень ADC з маркером PB0 кожні 10 мс |
   | `cap pwm <мкс>` | фіксована ширина pan (500…2500 мкс) до `tel on` |
   | `i2c hw` / `i2c sw` | вибір реалізації шини I²C для наступних команд |
   | `mode` (або кнопка MODE) | MANUAL ↔ MIRROR |

3. Зупинити симуляцію ■ → Wokwi пише `wokwi.vcd` (див. `vcdFile` у `wokwi.toml`).
4. Профіль B: тимчасово скопіювати `docs/captures/diagram-profile-B.json` у `diagram.json`, перезапустити,
   через 3 с натиснути MODE і зупинити. Потім повернути `diagram.json`.
5. `python3 tools/la_analyze.py` нарізає вирізки, конвертує їх у `.sr` (PulseView) і експортує анотації `.ann.txt`.
   Окремо: `python3 tools/extract_vectors.py > tests/la_vectors.h` і `python3 tools/make_diagrams.py`.

## Файли

| Файл | Що це |
|---|---|
| `session-A_i2c-spi-uart-pwm.vcd` | повна сесія профілю A (фінальна прошивка, IMU нахилено на 30°) |
| `session-B_pwm-probes-mirror.vcd` | повна сесія профілю B (PWM ×2, PB0, PA9, кнопка → MIRROR) |
| `raw-profileA-boot.vcd` | перша сесія ДО виправлень (побайтовий SPI, повільний bit-bang I²C, температура 24.01) — доказ для журналу проблем |
| `raw-profileA-boot-v2.vcd` | після виправлення SPI/I²C, але з неповним початком (Wokwi перезапустив симуляцію після перезбирання) |
| `<інтерфейс>_<пристрій>_<операція>.{vcd,sr,ann.txt}` | вирізки, сесії PulseView і анотації декодерів |
| `measurements.json` | усі виміряні таймінги (`tools/la_analyze.py`) |
| `uart_vcp_full-session.log` | повний текст UART сесії A, декодований з лінії TX |
| `analysis.md` | аналіз: зіставлення з datasheet, таймінги, ручне декодування, аномалії |
| `diagram-profile-B.json` | схема з іншим підключенням щупів LA (пристрої й піни — ті самі) |

Відкрити в PulseView: *File → Open* → `*.sr`. Для `.vcd`: *Import Value Change Dump*; downsample 20 (50 МГц)
для I²C/SPI, 100 для UART. Далі додати декодери I²C (SCL, SDA), SPI (CLK = SCK, MOSI, MISO, CS#, mode 0),
UART (115200 8N1) і PWM.
