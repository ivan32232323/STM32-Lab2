# Генерує docs/lab2-report.md і docs/lab2-report.docx з одного джерела; PDF — через LibreOffice:
#   python3 tools/make_report2.py && soffice --headless --convert-to pdf --outdir docs docs/lab2-report.docx
# Після push заповніть COMMITS (короткі хеші) і REPO — посилання на коміти з'являться у звіті.
import json
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

REPO = 'https://github.com/ivan32232323/STM32-Lab2'
STUDENT, GROUP, COURSE, TEACHER = 'Шведенко Іван Олексійович', 'ІО-32', '4', 'Гордієнко Н.Ю.'
VIDEO = 'https://drive.google.com/file/d/1WGseqAj6XfJlsJEBB2kJuO001eRFltR2/view?usp=sharing'
# ключ -> короткий хеш коміту (заповнити після push; None -> «коміт: див. файл ...»)
COMMITS = {
    'pinout': '890696a', 'timing': '890696a',
    'layers': 'a801bed', 'spi': 'a801bed', 'softi2c': 'a801bed', 'temp': 'a801bed',
    'size': '855d672', 'binutils': '855d672', 'chip': '5b92333', 'tests': '0521f69',
    'ci': 'c16411d', 'captures': '152e091',
}

M = json.load(open('docs/captures/measurements.json'))
IMG = 'docs/lab_2/img'


def C(key, files):
    sha = COMMITS.get(key)
    return f'{REPO}/commit/{sha}' if sha else f'файли: {files}'


TITLE = [
    ('c', 'Міністерство освіти і науки України'),
    ('c', 'Національний технічний університет України'),
    ('c', '«Київський політехнічний інститут імені Ігоря Сікорського»'),
    ('gap', 1), ('c', 'Факультет інформатики та обчислювальної техніки'),
    ('gap', 1), ('c', 'Кафедра обчислювальної техніки'),
    ('gap', 2), ('cb', 'Лабораторна робота №2'),
    ('c', 'з дисципліни «Системне програмування вбудованих систем»'),
    ('c', '«Інтеграція сенсорної підсистеми: схема підключення, верифікація'),
    ('c', 'інтерфейсів логічним аналізатором, архітектура програмного проєкту»'),
    ('gap', 5),
    ('r', 'Виконав:'), ('r', f'студент {COURSE} курсу'), ('r', f'групи {GROUP}'), ('r', STUDENT),
    ('gap', 1), ('r', 'Перевірив:'), ('r', TEACHER),
    ('gap', 7), ('c', 'Київ — 2026'),
]

B = []
def h1(t): B.append(('h1', t))
def h2(t): B.append(('h2', t))
def h3(t): B.append(('h3', t))
def p(t): B.append(('p', t))
def code(t): B.append(('code', t))
def img(path, w, cap=''):
    if os.path.exists(path):
        B.append(('img', path, w, cap))
def tbl(rows, widths=None): B.append(('tbl', rows, widths))
def bul(items): B.append(('bul', items))


def us(ns): return f'{ns / 1000:.2f}'


B.append(('center', 'Лабораторна робота №2'))
B.append(('center', 'Інтеграція сенсорної підсистеми'))
p('**Мета:** довести, що апаратна частина продукту Motion-Mirroring Teleoperator фізично й логічно сумісна: '
  'усі пристрої з PRD підключені одночасно без конфліктів пінів і периферії, кожна шина працює згідно з '
  'документацією, що підтверджено не лише логом UART, а й записом логічного аналізатора. Реорганізувати '
  'прошивку в шарову архітектуру, покрити тестами код, що виконується без заліза, і налаштувати CI.')
p('**Форма виконання:** B (Wokwi), Nucleo-C031C6 (STM32C031C6, Cortex-M0+, 48 МГц). Виконано одноосібно.')
p(f'Репозиторій: {REPO}')
p(f'Відео: {VIDEO}')

# ---------------------------------------------------------------- 1
h1('1. Розподіл задач')
p('Робота виконана одноосібно, тому всі шість напрямів розділу 5 методички закріплено за одним виконавцем.')
tbl([['№', 'Напрям', 'Відповідальний', 'Ключові артефакти'],
     ['1', 'Звіт і документація', STUDENT, 'docs/lab2-report.md/.pdf, docs/lab_2/img/'],
     ['2', 'Документація і pinout', STUDENT, 'docs/pinout.md, firmware.ioc, board.h'],
     ['3', 'Робота з апаратурою (Wokwi)', STUDENT, 'diagram.json, chips/w25q64, docs/captures/*.vcd/.sr'],
     ['4', 'Декодування і аналіз', STUDENT, 'docs/captures/analysis.md, *.ann.txt, measurements.json'],
     ['5', 'Структура проєкту і збірка', STUDENT, 'firmware/**, Makefile, docker/, .github/workflows/ci.yml, tools/check_*.py'],
     ['6', 'Тестування', STUDENT, 'tests/**, звіт покриття'],
     ], [1.0, 4.2, 4.6, 6.7])

# ---------------------------------------------------------------- 2
h1('2. Журнал роботи')
tbl([['Дата', 'Що зроблено'],
     ['25.11', 'Аналіз пінів C031 (база CubeMX, плата Wokwi), пошук конфліктів, вибір SPI1 на PB3/PB4/PB5'],
     ['25.11', 'Шарова структура Core/Platform/Devices/App, інтерфейс шин bus.h, драйвери MPU-6050 і W25Q64'],
     ['25.11', 'Модель W25Q64 для Wokwi (Custom Chips API, wasm), diagram.json, self-test і CLI-команди запису'],
     ['25.11', 'Збірка -Os -flto без попереджень, перші записи LA, виправлення SPI і bit-bang I²C за записами'],
     ['25.11', 'Unity-тести, fake/mock/stub, покриття, тест знайшов дефект округлення температури'],
     ['25.11', 'CubeMX .ioc (SPI1, CS#, проби), check_deps/check_pinout, Dockerfile з версіями, CI'],
     ['25.11', 'Фінальні записи (профілі A і B), декодування sigrok-cli/PulseView, аналіз, документація, звіт'],
     ], [2.0, 14.5])

# ---------------------------------------------------------------- 3
h1('3. Аргументація архітектурних рішень (схема підключення)')
p('Повна таблиця «пін МК → функція → пристрій» з AF, роз\'ємами, рівнями, pull-up і джерелами — '
  'docs/pinout.md. Нижче — ключові рішення з посиланнями.')
tbl([['Сигнал', 'Пін (Arduino)', 'AF', 'Пристрій', 'Чому'],
     ['I2C1 SCL/SDA', 'PB8/PB9 (D15/D14)', 'AF6', 'MPU-6050 0x68', 'стандартні I²C-піни Arduino; D0/D1 (PB7/PB6) залишено під UART шилдів'],
     ['SPI1 SCK/MISO/MOSI', 'PB3/PB4/PB5 (D3/D5/D6)', 'AF0', 'W25Q64', 'D13/D12/D11 зайняті LD4 і TIM3 серво; інша повна трійка SPI1 на Arduino'],
     ['CS# flash', 'PB10 (D4)', 'GPIO', 'W25Q64', 'PB10 без AF; програмний CS# тримає 1 інструкцію = 1 інтервал CS#'],
     ['ADC1_IN0', 'PA0 (A0)', 'аналог', 'потенціометр', 'перший аналоговий вхід, не ділить пін із шинами'],
     ['TIM3 CH1/CH2', 'PA6/PA7 (D12/D11)', 'AF1', 'SG90 ×2', 'один таймер, одна частота 50 Гц для обох серво'],
     ['USART2', 'PA2/PA3', 'AF1', 'ST-LINK VCP', 'вже розведено на VCP платою'],
     ['GPIO', 'PA10 (D2), PA5 (D13)', '—', 'кнопка, LD4', 'PC13 (B1) лишено, кнопка оператора — зовнішня'],
     ['Проби LA', 'PB0 (D10), PA9 (D8)', '—', 'маркери ADC і контуру', 'ADC/контур не мають цифрового трафіку'],
     ], [3.0, 3.4, 1.3, 2.6, 6.2])
p('**Чому така шина і частота.** I²C 100 кГц (Standard): при ємності макетки 100–200 пФ і 4.7 кОм '
  't_r ≈ 0.4–0.8 мкс > 300 нс Fast mode; потрібна пропускна — 6.3 кбіт/с, запас ×15. SPI 3 МГц (PCLK/16): '
  'реальний FX2-аналізатор 24 МС/с дає ≥ 8 відліків на біт; W25Q64 допускає 50 МГц для 03h. '
  'Розрахунки TIMINGR, BRR, PSC/ARR — pinout.md §3; вимірювання — розд. 5 нижче.')
p('**Чому окреме живлення серво.** 2 × 360 мА пікового струму SG90 перевищують бюджет USB ST-LINK (500 мА) '
  'і просаджують 5 В → LDO 3V3 → VDDA (шум ADC). Логіка на 3V3: ≈ 16 мА робочих, ≈ 42 мА пікових '
  '(W25Q64 при записі 25 мА). GND зовнішнього 5 В — спільний з GND Nucleo (pinout.md §4).')
p('**Конфлікти:** розібрано 6 типів (pinout.md §5): пін (SPI ↔ LD4/TIM3), периферія (TIM3 — дві однакові частоти), '
  'бортова обв\'язка (LD4, SWD, VCP, B1, HSE/LSE, апаратний NSS), DMA (не використовується; в ЛР3 3 канали DMAMUX), '
  'електричні (подвійні pull-up 4.7 к ∥ 40 к = 4.2 кОм, 0.8 мА < 3 мА), корпус/камера (C031 без DCMI; '
  'на F446 DCMI конфліктує з PB8/PB9, PA6, PB6).')
p('**Відхилені варіанти** (pinout.md §6): R1 — SPI на D13/D12/D11 (LD4 + серво); R2 — I²C на D1/D0 (UART шилдів, '
  'PB6 мультиплексує SPI/TIM); R3 — F446 + OV7670 по DCMI (не симулюється у Wokwi, план для форми A); '
  'R4 — апаратний NSS (не тримає CS# між 06h і 02h); R5 — серво на TIM1 (резерв під input capture).')
p('**Камера (форма B).** OV7670 у Wokwi відсутня, а STM32C031 не має DCMI; GPIO-захоплення 8 біт потребує '
  'PA0…PA7, які зайняті ADC/VCP/LED/серво — розкладка несумісна. Як це перевірити на залізі і що ще не '
  'перевіряється в симуляторі (фронти, pull-up, струм серво, справжній HW I²C) — pinout.md §8.')
h2('3.1. CubeMX: pinout і конфігурація')
img(f'{IMG}/cubemx-pinout.jpg', 16.0, 'Рис. 1 — Pinout у STM32CubeMX (firmware.ioc ЛР2): I2C1, SPI1, TIM3, ADC, USART2, CS#, проби')
img(f'{IMG}/cubemx-spi1.jpg', 16.0, 'Рис. 2 — SPI1: Full-Duplex Master, prescaler 16 → 3.0 Мбіт/с, CPOL Low, CPHA 1 Edge, NSS Software')
img(f'{IMG}/cubemx-i2c1.jpg', 16.0, 'Рис. 3 — I2C1: Standard mode 100 кГц, t_r = t_f = 100 нс → TIMINGR 0x10805D88')
img(f'{IMG}/cubemx-clock.jpg', 16.0, 'Рис. 4 — дерево тактування: HSI48 → SYSCLK = HCLK = PCLK = 48 МГц, I2C1CLK = 48 МГц')

h2('3.2. Інструкція з підключення (для збирання стенда без автора)')
bul(['Живлення вимкнено. Nucleo-C031C6 на макетці; GND Nucleo (CN6) з\'єднати з «мінусовою» шиною макетки.',
     'GY-521 (MPU-6050): VCC → 3V3, GND → GND, SCL → D15, SDA → D14, AD0 → GND (адреса 0x68). XDA/XCL/INT не підключати.',
     'W25Q64 (модуль): VCC → 3V3, GND → GND, CLK → D3, DO → D5, DI → D6, /CS → D4; /WP і /HOLD → 3V3 (на модулі зазвичай підтягнуто).',
     'Потенціометр 10 кОм: крайні виводи → 3V3 і GND, середній → A0.',
     'Серво SG90: оранжевий (PWM) pan → D12, tilt → D11; червоний → +5 В зовнішнього джерела (≥ 1 А); '
     'коричневий → GND джерела І GND Nucleo (спільна земля обов\'язкова).',
     'Кнопка MODE: один вивід → D2, другий → GND (pull-up — внутрішній).',
     'Логічний аналізатор: GND щупа → GND біля МК; канали — за таблицею профілю A або B (pinout.md §1). '
     'Проби D10 (ADC) і D8 (контур) — лише для профілю B.',
     'Перевірка до живлення: мультиметром — немає КЗ 3V3–GND і 5V–GND; між D4 і 3V3 ~10 кОм (pull-up /CS).',
     'Прошити (make flash / Wokwi ▶), відкрити UART 115200: має бути ST;SUMMARY;all;PASS. '
     'Будь-який FAIL — див. рядок пристрою (наприклад who_am_i FAIL → перевірити SDA/SCL і AD0).'])

# ---------------------------------------------------------------- 4
h1('4. Підключення і перевірка пристроїв (self-test)')
p('Усі пристрої працюють в одній прошивці одночасно. На старті режим самоперевірки виводить у UART рядки '
  'формату ST;<пристрій>;<перевірка>;<рівень>;<значення>;<критерій> (розбирає tools/parse_selftest.py, '
  'повертає 1 при FAIL). Фрагмент, декодований із лінії TX логічним аналізатором (фінальна прошивка):')
code(open('docs/captures/uart_vcp_full-session.log').read().split('CAPTURE;begin')[0].strip())
tbl([['Пристрій', 'Ідентифікація', 'Мінімальна ініціалізація', 'Перевірка правдоподібності', 'Результат'],
     ['MPU-6050', 'WHO_AM_I = 0x68', 'PWR_MGMT_1=1, CONFIG=3, SMPLRT_DIV=9, ±2 g, ±250 °/с',
      '|a| = 1 g ± 5 %; T у 15…35 °C; |ω| < 5 °/с у спокої; pitch = 30° при моделі, нахиленій на 30°',
      '|a| = 999 мг, 24.00 °C, ω = 0, pitch = 30'],
     ['W25Q64', 'JEDEC = EF 40 17', 'з JEDEC → ємність 8 МБ',
      'стирання → 16 × FF; запис 16 Б → читання збігається побайтово', '0/16 відмінностей'],
     ['Потенціометр', '—', 'ADC 12 біт, 39.5 цикла', 'два послідовні заміри відрізняються ≤ 8 LSB; 0…4095 → 1000…2000 мкс',
      '2050, 2050 → 1501 мкс'],
     ['Серво ×2', '—', 'TIM3 50 Гц', 'CCR = заданому; на LA ширина 1000/2000 мкс, період 20 мс', '1000.0/2000.0 мкс'],
     ['Кнопка', '—', 'pull-up', 'у спокої — 1 (released)', 'released'],
     ], [2.4, 2.6, 3.8, 5.0, 2.7])
img(f'{IMG}/wokwi-mirror-profileB.jpg', 16.5, 'Рис. 5 — Wokwi: усі пристрої на одній схемі, режим MIRROR (pitch=30 → tilt 1667 мкс)')
img(f'{IMG}/wokwi-selftest-uart.jpg', 12.5, 'Рис. 5а — термінал Wokwi (USART2): вивід self-test і сценарію запису')

# ---------------------------------------------------------------- 5
h1('5. Аналіз записів логічного аналізатора')
p('Записи: wokwi-logic-analyzer (8 каналів, VCD з кроком 1 нс). Два профілі підключення щупів (A — шини, '
  'B — PWM/проби/кнопка), бо сигналів 11 > 8 каналів. Сценарій запису відтворюваний: після self-test прошивка '
  'сама виконує cap i2c / cap nack / cap spi / cap adc (ті самі команди доступні в UART). Вирізки, .sr-сесії '
  'PulseView і текстові анотації sigrok-cli — docs/captures/; повний аналіз — docs/captures/analysis.md.')
tbl([['Інтерфейс', 'Файл', 'Дискретизація', 'Тригер / маркер', 'Канали'],
     ['I²C', 'i2c_mpu6050_whoami-burst14.sr', '50 МГц', 'START (SDA↓ при SCL=1)', 'SCL, SDA'],
     ['I²C аномалії', 'i2c_mpu6050_hw-read-stall_anomaly.sr, i2c_mpu6050_nack-0x69_anomaly.sr', '50 МГц', 'START', 'SCL, SDA'],
     ['SPI', 'spi_w25q64_jedec-wren-erase-pp-read.sr', '50 МГц', 'CS#↓', 'SCK, MOSI, MISO, CS#'],
     ['UART', 'uart_vcp_selftest.sr', '10 МГц', 'старт-біт', 'UART_TX'],
     ['PWM', 'pwm_servo-pan_1000us-2000us.sr', '1 МГц', 'фронт PWM', 'PWM_PAN, PWM_TILT'],
     ['ADC', 'adc_pot_probe-pb0_cap-adc.sr', '10 МГц', 'PB0↑', 'PROBE_ADC, PROBE_LOOP, UART_TX'],
     ['Латентність', 'mirror_latency_btn-loop-i2c-pwm.sr', '10 МГц', 'BTN↓', 'BTN, PROBE_LOOP, SCL, SDA, PWM_TILT'],
     ], [2.3, 6.0, 2.0, 3.4, 3.3])
p('Частота дискретизації — щонайменше 4, бажано 8–10 відліків на найкоротший біт: SPI 3 МГц → ≥ 24 МС/с (взято 50); '
  'I²C 100 кГц → ≥ 1 МС/с; UART 115200 → ≥ 0.5 МС/с. Верхня межа реального FX2-аналізатора — 24 МС/с, звідси '
  'вибір SPI ≤ 3–6 МГц. Без спільної землі аналізатор міряє напругу відносно «чужого» нуля: поріг 1.4 В плаває '
  'разом зі зсувом, фронти губляться або подвоюються — навіть якщо «щось видно».')
for f, cap in [('pv-i2c.png', 'Рис. 6 — PulseView, декодер I²C: WHO_AM_I і burst 14 байтів (i2c_mpu6050_whoami-burst14.sr)'),
               ('pv-i2c-zoom.png', 'Рис. 6а — PulseView: S, AW 68, Wr, ACK, DW 75, Sr, AR 68, DR 68, NACK, P — біти кожного байта'),
               ('pv-spi.png', 'Рис. 7 — PulseView, стек декодерів SPI + SPI flash/EEPROM: JEDEC (9F → EF 40 17), RDSR, WREN, Sector Erase, BUSY'),
               ('pv-spi-pp.png', 'Рис. 7а — PulseView: WREN → RDSR (WEL) → Page program → RDSR (BUSY/ready) → Read data «LR2-SPI!»'),
               ('pv-uart.png', 'Рис. 8 — PulseView, декодер UART 115200 8N1 (ASCII): «ST;BEGIN;lab2;INFO;sysclk=48000000…»'),
               ('pv-pwm.png', 'Рис. 9 — PulseView, декодер PWM: період 20.0 мс, duty 5 % (1000 мкс) і 10 % (2000 мкс)')]:
    img(f'{IMG}/{f}', 16.5, cap)

h2('5.1. I²C — MPU-6050')
code('S | 68+W ACK | 75 ACK | Sr | 68+R ACK | 68 NACK | P                                   (WHO_AM_I)\n'
     'S | 68+W ACK | 3B ACK | Sr | 68+R ACK | E0 00 00 00 37 6C EF 5C 00 00 00 00 00 00 NACK | P')
p('Збігається з «Burst Read Sequence» PS-MPU-6000A §9.3: Sr після адреси регістру, ACK після кожного байта крім '
  'останнього. Розбір: ACCEL_X = 0xE000 = −8192 → −0.500 g; ACCEL_Z = 0x376C = 14188 → 0.866 g; TEMP = 0xEF5C = −4260 → '
  '24.00 °C; GYRO = 0. |a| = 1.000 g, pitch = 30.0° — саме так нахилено модель у diagram.json. Ці байти — тестовий '
  'вектор (tests/la_vectors.h): тест подає їх у драйвер і отримує ті самі raw, що прошивка вивела в UART.')
img(f'{IMG}/la-i2c-manual.png', 16.5, 'Рис. 10 — ручне декодування за формою сигналу: START, A6…A0 = 1101000, R/W = 0, ACK, 0x75, ACK')
s = M['i2c_soft']; h = M['i2c_hw_attempt']
tbl([['Параметр', 'Розрахунок', 'Виміряно'],
     ['T_SCL HW I2C1', '10.0 мкс (TIMINGR 0x10805D88)', f'{us(h["scl_period_ns"]["median"])} мкс (t_HIGH = t_LOW = 5.0 мкс — модель)'],
     ['T_SCL bit-bang', '≤ 10 мкс', f'{us(s["scl_period_ns"]["median"])} мкс (87 кГц)'],
     ['WHO_AM_I (4 Б)', '≈ 414 мкс', f'{s["whoami_dur_us"]:.0f} мкс'],
     ['Burst 14 Б (+2 Б)', '≈ 1.86 мс', f'{s["burst_dur_us"] / 1000:.2f} мс'],
     ['Пауза між транзакціями', '—', f'{s["gap_whoami_to_burst_us"]:.0f} мкс'],
     ['PROBE_LOOP↑ → START', '—', '62.4 мкс (спершу ADC)'],
     ['Контур MIRROR', '≤ 5 мс (FR-04)', f'{M["mirror"]["mirror_loop_width_us"]["median"] / 1e6:.2f} мс'],
     ], [4.5, 5.5, 6.5])
h3('Аномалія 1: HAL_I2C_Mem_Read у Wokwi обривається після адреси регістру')
p('На шині: S | 68+W ACK | 75 ACK — і далі нічого (немає Sr, 0xD1, тактів SCL, STOP). HAL повертає HAL_ERROR, '
  'HAL_I2C_GetError() = 0x20 (TIMEOUT). Розбіжність між HAL («чекаю RXNE») і шиною (транзакція зупинилась, лінія '
  'залишилась «зайнятою»). Дефект моделі STM32C0 у Wokwi (скан IsDeviceReady працює). Self-test фіксує WARN і '
  'перемикає вказівник шини на bit-bang реалізацію на тих самих пінах — драйвер не змінюється.')
img(f'{IMG}/la-i2c-hw-anomaly.png', 16.5, 'Рис. 11 — апаратний I²C: фаза читання відсутня')
h3('Аномалія 2 (навмисна): неправильна адреса 0x69')
p(f'cap nack: S | 69+W NACK | P за {M["i2c_nack"]["dur_us"]:.0f} мкс — на 9-му такті SDA = 1, master одразу видає STOP; '
  'драйвер повертає BUS_NACK (−1), UART: CAP;nack;addr=0x69;st=-1. Так виглядала б помилка AD0 = 3V3.')

h2('5.2. SPI — W25Q64')
code('#0  9F FF FF FF  -> FF EF 40 17        JEDEC ID\n'
     '#2  06 | #3 05 FF -> 02 (WEL)          WRITE ENABLE окремим CS#\n'
     '#4  20 00 20 00                        SECTOR ERASE 0x002000\n'
     '#5..#27 05 FF -> 03 (×23, кожні 2 мс)  BUSY; #28 05 FF -> 00 через 45.7 мс\n'
     '#29 06 | #30 05 -> 02 | #31 02 00 20 00 4C 52 32 2D 53 50 49 21  PAGE PROGRAM "LR2-SPI!"\n'
     '#32 05 -> 03 | #33 05 -> 00            BUSY < 1.4 мс\n'
     '#34 03 00 20 00 -> 4C 52 32 2D 53 50 49 21   READ = "LR2-SPI!"')
p('Відповідає Instruction Set Table W25Q64JV: опкод, 24-бітна адреса MSB-first, дані; 06h — в окремому інтервалі '
  'CS#, запис/стирання стартують по CS#↑, після завершення WEL скидається (SR1 03 → 00). Mode 0: SCK у спокої 0, '
  'вибірка по ↑; декодер з cpha=1 дає MISO = DE 80 2F (зсув на біт) — режим підтверджено записом.')
img(f'{IMG}/la-spi-sequence.png', 16.5, 'Рис. 12 — SPI: JEDEC ID і послідовність WREN / RDSR / Page Program / RDSR')
sp = M['spi']; sb = M['spi_before_fix']
tbl([['Параметр', 'Розрахунок', 'Виміряно'],
     ['f_SCK', '48/16 = 3.0 МГц (333 нс)', f'{sp["sck_period_ns"]["mean"]:.0f} нс (2.98 МГц), крок моделі 25 нс'],
     ['Пауза між байтами (tx)', '—', f'{us(sp["intra_txn_gap_ns"]["median"])} мкс (до виправлення {us(sb["intra_txn_gap_ns"]["median"])} мкс)'],
     ['CS#↓ → SCK / SCK → CS#↑', '≥ 5 нс (t_SLCH, t_CHSH)', '19 мкс / 44 мкс'],
     ['tSE (модель)', '45 мс тип., ≤ 400 мс', '≈ 45.7 мс'],
     ['tPP (модель)', '0.4 мс тип., ≤ 3 мс', '< 1.4 мс (крок опитування)'],
     ], [4.5, 5.5, 6.5])

h2('5.3. UART')
p(f'115200 8N1, BRR = 417 → 8.688 мкс/біт; найкоротший інтервал між фронтами на записі {M["uart"]["min_edge_ns"] / 1000:.3f} мкс '
  f'(крок моделі 25 нс). Кадр 10 біт = 86.9 мкс, між початками символів 92.9 мкс (пауза HAL). Self-test до '
  f'ST;SUMMARY займає {M["uart"]["selftest_text_ms"]:.0f} мс (включно зі стиранням flash 45 мс і PWM-тестом 120 мс). '
  'Текст, декодований sigrok-cli з лінії TX, побайтово збігається з терміналом Wokwi.')

h2('5.4. PWM')
img(f'{IMG}/la-pwm.png', 16.5, 'Рис. 13 — PWM: період 20 мс, 1000 мкс → 2000 мкс (self-test)')
tbl([['Параметр', 'Розрахунок', 'Виміряно'],
     ['Період', '(ARR+1) × 1 мкс = 20.000 мс', '20.000 мс'],
     ['Ширина CCR = 1000/1500/2000', '1000/1500/2000 мкс', '1000.0/1500.0/2000.0 мкс (duty 5/7.5/10 %)'],
     ['Потенціометр 2050', '1500.6 → 1501 мкс', '1501.0 мкс'],
     ['MIRROR pitch = 30°', '1666.7 → 1667 мкс', '1667.0 мкс'],
     ['Крок 300 °/с за 20 мс', '33 мкс', '1533, 1566, 1599, 1632, 1665, 1667'],
     ], [4.5, 5.5, 6.5])
p('Спостереження: перший імпульс після старту — pan 1505.75 мкс, tilt 1496.25 мкс: канали вмикаються двома '
  'викликами HAL_TIM_PWM_Start з інтервалом 9.5 мкс при вже запущеному лічильнику; для серво несуттєво.')

h2('5.5. ADC і латентність контуру')
a = M['adc']; mi = M['mirror']
p(f'ADC не має трафіку — момент вимірювання позначає PB0: 1 перед HAL_ADC_Start, 0 після читання. Ширина маркера '
  f'{a["probe_width_ns"]["median"] / 1000:.1f} мкс (повний виклик HAL; саме перетворення — 2.17 мкс за розрахунком), '
  f'період у контурі {a["loop_period_ns"]["median"] / 1e6:.3f} мс. Перехід MANUAL → MIRROR: брязкіт кнопки '
  f'{mi["bounce_us"] / 1000:.2f} мс (7 фронтів) → одне перемикання (антидребезг 20 мс); перший контур через '
  f'{mi["btn_to_first_mirror_loop_ms"]:.1f} мс; контур {mi["mirror_loop_width_us"]["median"] / 1e6:.2f} мс; перший '
  f'імпульс з новою шириною через {mi["loop_to_pwm_edge_ms"]:.1f} мс від початку контуру. Латентність IMU → PWM '
  '≤ 23.6 мс (FR-03: < 50 мс, ціль ≤ 25 мс).')
img(f'{IMG}/la-mirror-latency.png', 16.5, 'Рис. 14 — кнопка → контур (PA9) → I²C → PWM tilt')

# ---------------------------------------------------------------- 6
h1('6. Структура проєкту')
code('firmware/Core      CubeMX: MX_*_Init, MSP, IRQ → app_main()     (USER CODE: 2 рядки)\n'
     'firmware/Drivers   HAL v1.4.1 + CMSIS (не редагуються, VERSIONS.md)\n'
     'firmware/Platform  board.h (усі піни/AF/хендли) + platform.c (порт + шини над HAL)\n'
     'firmware/Devices   bus.h, mpu6050.c, w25q.c — без HAL\n'
     'firmware/App       app.c, selftest.c, attitude.c, servo_map.c, cli.c — без HAL\n'
     'tests/             Unity + doubles;  chips/ модель W25Q64;  tools/ перевірки й аналіз')
img(f'{IMG}/component-diagram.png', 16.5, 'Рис. 15 — component diagram (lab-report-format §2.7)')
p('**Правило залежностей:** App → Devices, platform.h; Devices → лише bus.h; Platform → HAL, bus.h; Core → Platform, '
  'app.h. Перевіряється не «на честь», а скриптом tools/check_deps.py у make check і CI: кожен #include '
  'класифікується за шаром; негативний тест (#include "stm32c0xx_hal.h" у App/servo_map.c) дає '
  '«DEPS ERROR App/servo_map.c:1: App -> HAL заборонено», код 1. Друга лінія — хостові тести без -I на HAL.')
p('**Доступ до шини:** драйвер отримує const i2c_bus_t* / spi_dev_t* (вказівники на функції + ctx) у структурі '
  'контексту пристрою і не знає про HAL_I2C_Mem_Read. На цілі — plat_i2c_hw()/plat_i2c_sw()/plat_flash_spi(); '
  'у тестах — fake_i2c / mock_spi.')
p('**Знання про плату** — лише в Platform/board.h; відповідність board.h ↔ firmware.ioc ↔ diagram.json перевіряє '
  'tools/check_pinout.py (15 сигналів, 0 розбіжностей). Код CubeMX: власне — тільки в USER CODE; MX_*_Init беруть '
  'константи з board.h; новий пін у .ioc без board.h ловить check_pinout.')
p('**Бібліотеки і збірка:** HAL-модулі увімкнено поштучно з поясненням у hal_conf.h (EXTI вимкнено), у Makefile — '
  'явний список HAL_USED. Версії: HAL v1.4.1 (коміт 038bed9f), Unity v2.6.0 (sha256), тулчейн у Dockerfile з '
  'версіями apt-пакетів. Власний код: -Wall -Wextra -Werror -Wshadow -Wdouble-promotion; HAL: -isystem і лише '
  '-Wno-unused-parameter. Результат — 0 попереджень, 26.9 КБ / 32 КБ flash (-Os -flto), 2.3 КБ / 12 КБ RAM.')
code('$ make NATIVE=1 ci\n'
     '  FLASH: 27284 B / 32 KB (83.26 %)      RAM: 2296 B / 12 KB\n'
     'check_deps: 73 #include перевірено, порушень: 0\n'
     'check_pinout: 15 сигналів, розбіжностей: 0\n'
     '36 Tests 0 Failures\n'
     'lines: 99.4% (321 out of 323)   functions: 100.0%   branches: 75.7%')
img(f'{IMG}/docker-ci-build.png', 15.0, 'Рис. 15а — make ci у Docker-образі stm32-build:lab2: збірка прошивки без попереджень')
img(f'{IMG}/docker-ci-coverage.png', 13.0, 'Рис. 15б — make ci у Docker-образі stm32-build:lab2 (Windows, Docker Desktop): 36 тестів, покриття 99.4 %')

# ---------------------------------------------------------------- 7
h1('7. Тестування')
p('make test збирає тести звичайним gcc (без плати і без HAL). Double-и: fake_i2c (регістровий файл MPU-6050 з '
  'інжекцією NACK/timeout), mock_spi (журнал CS#/байтів + черга MISO — для перевірки ПОСЛІДОВНОСТІ команд), '
  'fake_platform (stub-и UART/ADC/серво).')
tbl([['Набір', 'Тестів', 'Що перевіряє'],
     ['test_mpu6050', '10', 'WHO_AM_I, послідовність init, BADID, NACK (0x69), timeout посеред init, big-endian, '
      'приклад з datasheet T = raw/340 + 36.53, чутливість ±2 g/±250 °/с, вектори з LA'],
     ['test_w25q', '9', 'JEDEC/ємність, MISO FF/00 → BADID, WREN окремим CS# перед 02h/20h, перевірка WEL, '
      'вирівнювання сектора, BUSY + timeout tPP, межа сторінки, адреса MSB-first, CS#↑ при помилці'],
     ['test_app_logic', '10', 'кут ↔ мкс, потенціометр, мертва зона ±2°, 300 °/с, кути з accel, фільтр, isqrt, CLI'],
     ['test_selftest', '7', 'формат рядків, критерії, повний PASS, fallback HW→SW I²C, відсутні пристрої, CCR, парсинг'],
     ], [3.2, 1.6, 11.7])
code('журнал mock SPI для page_program(0x012345, {A5,5A}):\n'
     '"S 06 D S 05 FF D S 02 01 23 45 A5 5A D S 05 FF D w S 05 FF D"   (S = CS#↓, D = CS#↑, w = очікування)')
p('**Покриття** (gcovr): Devices/ і App/ (без app.c) — 99.4 % рядків, 100 % функцій, 75.7 % гілок. Поріг CI — 90 % '
  'рядків: драйвери й логіка — чистий C, тож поріг досяжний без компромісів, а нижчий пропустив би непокриті '
  'гілки помилок. Свідомо не покриваються Core/ (CubeMX), Platform/ (тонкий шар над HAL — перевіряється self-test і LA) '
  'і app.c (цикл з таймінгом — перевірено інтеграційно, розд. 5.5).')
p('**Дефект, знайдений тестом:** test_temperature_formula_datasheet: «Expected 2400 Was 2401». Ціле ділення '
  '(raw·100)/340 відкидає дріб у бік нуля: для raw = −4260 прошивка друкувала 24.01 °C замість 24.00. '
  'Виправлено округленням до найближчого; запис LA до виправлення (raw-profileA-boot.vcd) показує 24.01, після — 24.00.')
p('**CI:** .github/workflows/ci.yml на кожен pull request — make image, make build, make check, make coverage; '
  'артефакти — ELF/HEX/MAP і HTML-звіт покриття.')

# ---------------------------------------------------------------- 8
h1('8. Журнал проблем')
PROBS = [
 ('стандартний SPI Arduino зайнятий', 'D13/D12/D11 (PA5/PA6/PA7) — це SPI1 Arduino, але на них LD4 і серво TIM3 з ЛР1.',
  'перебір AF у базі CubeMX: друга повна трійка SPI1 на Arduino — PB3/PB4/PB5 (D3/D5/D6, AF0); CS# — PB10 (без AF).',
  C('pinout', 'docs/pinout.md, firmware/Platform/board.h, firmware.ioc')),
 ('у Wokwi немає SPI-flash', 'у бібліотеці частин Wokwi відсутня W25Q64 — SPI нема з ким перевірити.',
  'власна модель на Custom Chips API (chips/w25q64.chip.c → wasm, clang). Перша збірка важила 264 КБ: з --import-memory '
  'lld записує .bss (256 КБ масив) як нулі в DATA. Пам\'ять взято через memory.grow під час init → 2.7 КБ.',
  C('chip', 'chips/w25q64.chip.c, chips/Makefile, wokwi.toml')),
 ('прошивка не влазить у flash', 'з -Og і новими драйверами — 30.8 КБ з 32 КБ (94 %); з -flto лінкер: '
  'undefined reference to _sbrk.', 'root cause: newlib викликає _sbrk з libc.a, яку LTO не бачить, і LTO викидає '
  'функцію. Фікс: -Os -flto, а syscalls.c/sysmem.c — з -fno-lto. Результат 26.9 КБ (81 %).',
  C('size', 'firmware/Makefile (OPT, NO_LTO_OBJ)')),
 ('ld: unrecognized option --no-warn-rwx-segments', 'binutils 2.38 (ubuntu 22.04, той самий, що в Docker) '
  'не знає ключа з binutils 2.39.', 'ключ додається лише якщо `ld --help` його містить (LD_RWX у Makefile).',
  C('binutils', 'firmware/Makefile')),
 ('паузи ~60 мкс між байтами SPI', 'на LA байт триває 2.4 мкс, а між байтами 56–115 мкс (медіана 60) — '
  'ефективно 16 КБ/с замість 375 КБ/с.', 'spi_transfer() викликав HAL_SPI_TransmitReceive на кожен байт. Один '
  'виклик на буфер (Transmit / TransmitReceive in-place з 0xFF) → медіана 4.6 мкс.',
  C('spi', 'firmware/Platform/platform.c: spi_transfer()')),
 ('bit-bang I²C 14 кГц замість 100', 'LA: T_SCL = 71 мкс.', 'затримка SW_HALF_LOOPS = 18 підбиралась «на око»; '
  'фактично цикл у моделі ~1.9 мкс на ітерацію. Підібрано за LA: SW_HALF_LOOPS = 1 → 11.5 мкс (87 кГц) ≤ 100 кГц.',
  C('softi2c', 'firmware/Platform/platform.c')),
 ('температура 24.01 °C замість 24.00', 'тест з прикладом datasheet падає: Expected 2400 Was 2401.',
  'ціле ділення відкидає дріб у бік нуля; округлення до найближчого (±170 перед /340).',
  C('temp', 'firmware/Devices/mpu6050.c: mpu6050_temp_cdeg()')),
 ('TIMINGR у коді і в .ioc розійшлися', 'у main.c ЛР1 0x20303E5D, у .ioc — 0x10805D88; ручна правка .ioc не '
  'діє — CubeMX перераховує TIMINGR, поки Custom Timing = Disabled.', 'взято значення CubeMX (t_r = t_f = 100 нс) '
  'в board.h — одне джерело; на LA T_SCL = 10.0 мкс в обох випадках.', C('timing', 'firmware/Platform/board.h, firmware.ioc')),
 ('тести не перезбирались після зміни драйвера; gcov «overwriting profile data»', 'make test показував старий FAIL; '
  'gcov сварився на .gcda від попередньої збірки.', 'залежності тестів від SRC_<тест> через .SECONDEXPANSION; '
  'перед прогоном видаляються *.gcda.', C('tests', 'tests/Makefile')),
 ('покриття 0 % у Docker при зелених тестах', 'make ci у контейнері: усі 36 тестів PASS, але gcovr показує 0 з 323 рядків.',
  'у tests/build лишилися бінарники, зібрані у VM: gcc вшиває в них абсолютний шлях для .gcda, тож у контейнері '
  'лічильники писались у неіснуючий каталог, а make вважав бінарники актуальними. make coverage тепер спершу '
  'виконує make -C tests clean.', C('ci', 'Makefile (ціль coverage)')),
 ('запис LA без початку сесії', 'у raw-profileA-boot-v2.vcd перший фронт UART на 33 мс замість 0.9 мс.',
  'Wokwi for VS Code перезапускає симуляцію при зміні firmware.hex (перезбирання під час роботи). Фінальні записи '
  'зроблено «з нуля»: зупинка → ▶ → ■ без перезбирань між ними; повнота перевіряється (перший рядок UART на 0.89 мс).',
  C('captures', 'docs/captures/README.md')),
]
for i, (t, s_, f, link) in enumerate(PROBS, 1):
    B.append(('prob', i, t, s_, f, link))

# ---------------------------------------------------------------- 9
h1('9. Внесок учасників')
tbl([['Учасник', 'Напрями', 'Внесок'],
     [STUDENT, '1, 2, 3, 4, 5, 6', '100 % (одноосібно)']], [6.0, 4.0, 6.5])

h1('10. Відповіді на контрольні питання (коротко)')
QA = [
 ('Datasheet / RM / UM', 'Datasheet МК — які AF має пін у корпусі (PB3 = SPI1_SCK AF0 у LQFP48); RM — як працює блок '
  '(SPI1 від PCLK, BR = /2…/256, NSS soft); UM плати — що вже під\'єднано (PA5 = LD4, D3 = PB3). Рішення «SPI на D3/D5/D6, '
  'CS = D4» потребувало всіх трьох.'),
 ('Open-drain на I²C', 'Будь-який пристрій може лише тягнути лінію в 0; 1 — пасивна (pull-up). Push-pull при ACK або '
  'clock stretching дає КЗ виходів 1↔0; на LA — «сходинка» проміжного рівня або 1 там, де slave мав дати ACK.'),
 ('Номінал pull-up', 'R_min = (V_DD − V_OL)/3 мА ≈ 1 кОм; R_max = t_r/(0.8473·C_b) ≈ 5.9 кОм при 200 пФ і 1 мкс. '
  'Кілька модулів — опори паралельно (4.7 ∥ 4.7 = 2.35 кОм), зростає струм нуля; третій-четвертий модуль — відпаяти.'),
 ('SCCB vs I²C', 'SCCB не гарантує ACK (9-й біт «don\'t care») і не підтримує repeated START — HAL_I2C_Mem_Read з Sr '
  'та перевіркою ACK отримає NACK/AF; потрібні окремі Transmit + Receive і ігнорування NACK.'),
 ('CPOL/CPHA', 'CPOL — рівень SCK у спокої, CPHA — по якому фронту захоплення. W25Q64 — mode 0 (або 3); на записі SCK у '
  'спокої 0, декодер з cpha=0 дає EF 40 17, з cpha=1 — DE 80 2F.'),
 ('Програмний CS#', 'Апаратний NSS master тримає 0 весь час увімкнення SPI; flash потребує окремий інтервал CS# на кожну '
  'інструкцію (06h окремо від 02h), запис стартує по CS#↑.'),
 ('Мінімальна частота дискретизації', '≥ 4 (краще 8–10) відліки на найкоротший біт: SPI 3 МГц → ≥ 24 МС/с; I²C 100 кГц '
  '→ ≥ 1 МС/с; UART 115200 → ≥ 0.5 МС/с. Зверху обмежує USB-пропускна FX2 (24 МС/с на 8 каналах).'),
 ('APB і частоти периферії', 'Усі блоки тактуються від PCLK = 48 МГц: UART BRR = 48 МГц/115200 = 417; SPI 48/16 = 3 МГц; '
  'TIM3 48 МГц/(47+1) = 1 МГц → ARR 19999 = 20 мс. Зменшення APB вдвічі вдвічі зменшить SPI і змусить змінити BRR/PSC.'),
 ('Серво не від 3V3', 'Струм рушання 360 мА на серво > можливостей LDO/USB, імпульси струму дають шум на VDDA і можуть '
  'скинути МК (BOR). Земля спільна — бо PWM-рівень вимірюється відносно землі серво.'),
 ('Шари', 'Core → Platform/App; Platform → HAL; Devices → bus.h; App → Devices + platform.h. Гарантує check_deps.py у CI '
  'і відсутність -I на HAL у збірці тестів.'),
 ('Доступ до шини', 'Через i2c_bus_t/spi_dev_t (вказівники на функції + ctx) у структурі пристрою; у тесті — та сама '
  'структура з функціями fake_i2c / mock_spi.'),
 ('Fake vs mock', 'Fake — робоча спрощена реалізація зі станом (регістри MPU-6050), перевіряємо стан; mock — записує '
  'взаємодію і перевіряє її порядок. Для W25Q64 потрібен саме mock: «06h в окремому CS# перед 02h» — властивість '
  'послідовності, а не результату.'),
 ('Що не покривається', 'Core (згенерований), Platform (тонкий шар над HAL — перевіряється self-test + LA), app.c (таймінг '
  'головного циклу — інтеграційно у Wokwi).'),
]
for i, (q, a_) in enumerate(QA, 1):
    p(f'**{i}. {q}.** {a_}')

h1('11. Висновок')
p('Усі пристрої PRD (MPU-6050, W25Q64, потенціометр, 2 серво, кнопка, UART) працюють в одній прошивці одночасно; '
  'self-test дає 15 PASS / 0 FAIL / 1 WARN (WARN — задокументований дефект моделі I²C у Wokwi з автоматичним '
  'обходом). Кожна шина підтверджена записом LA і декодуванням: I²C 100 кГц, SPI mode 0 3 МГц, UART 115200, '
  'PWM 20 мс / 1–2 мс; виміряні таймінги збігаються з розрахунком. Записи LA знайшли два дефекти прошивки '
  '(побайтовий SPI, повільний bit-bang I²C), тести — третій (округлення температури). Прошивка має шарову '
  'структуру з автоматичною перевіркою залежностей, тести з покриттям 99 % і CI; розкладка пінів не потребує '
  'змін у ЛР3–ЛР6 (вільні DMA-канали, TIM1/TIM14/16/17, ADC-входи).')

h1('12. Джерела')
B.append(('ol', [
 'STMicroelectronics. STM32C031x4/x6 Datasheet, DS13867 rev 4.',
 'STMicroelectronics. RM0490 Reference manual STM32C0x1.',
 'STMicroelectronics. UM2953 STM32 Nucleo-64 board (MB1717).',
 'STMicroelectronics. STM32_open_pin_data (база пінів CubeMX), github.com/STMicroelectronics/STM32_open_pin_data.',
 'STMicroelectronics. stm32c0xx-hal-driver v1.4.1 (github.com/STMicroelectronics/stm32c0xx-hal-driver).',
 'InvenSense. MPU-6000/MPU-6050 Product Specification PS-MPU-6000A-00 rev 3.4; Register Map RM-MPU-6000A-00 rev 4.2.',
 'Winbond. W25Q64JV 3V 64M-bit Serial Flash datasheet.',
 'NXP. UM10204 I²C-bus specification and user manual, rev 7.',
 'TowerPro. SG90 Micro Servo datasheet.',
 'sigrok. PulseView / sigrok-cli / libsigrokdecode — sigrok.org/wiki.',
 'Wokwi. Logic Analyzer, Custom Chips API, diagram.json — docs.wokwi.com; wokwi-boards (st-nucleo-c031c6).',
 'ThrowTheSwitch. Unity v2.6.0; J. Grenning, Test-Driven Development for Embedded C.',
]))

# =============================================================== render
SHA = re.compile(r'^[0-9a-f]{7}$')


def md():
    o = ['---', 'title: "Лабораторна робота №2"', '---', '']
    for k, t in TITLE:
        o.append('' if k == 'gap' else ((f'**{t}**' if k == 'cb' else t) + '  '))
    o += ['', '---', '']
    for b in B:
        k = b[0]
        if k == 'center': o += [f'### {b[1]}', '']
        elif k == 'h1': o += [f'# {b[1]}', '']
        elif k == 'h2': o += [f'## {b[1]}', '']
        elif k == 'h3': o += [f'#### {b[1]}', '']
        elif k == 'p': o += [b[1], '']
        elif k == 'code': o += ['```', b[1], '```', '']
        elif k == 'img': o += [f'![]({os.path.relpath(b[1], "docs")})', ''] + ([f'*{b[3]}*', ''] if b[3] else [])
        elif k == 'tbl':
            rows = b[1]
            o += ['| ' + ' | '.join(rows[0]) + ' |', '|' + '---|' * len(rows[0])]
            o += ['| ' + ' | '.join(c.replace('|', '\\|') for c in r) + ' |' for r in rows[1:]] + ['']
        elif k == 'bul': o += [f'- {x}' for x in b[1]] + ['']
        elif k == 'ol': o += [f'{i}. {x}' for i, x in enumerate(b[1], 1)] + ['']
        elif k == 'prob':
            _, i, t, s_, f, link = b
            o += [f'**Проблема {i}: {t}**  ', f'Симптом: {s_}  ', f'Root cause / фікс: {f}  ', f'Коміт: {link}', '']
    return '\n'.join(o)


doc = Document()
st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(14)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
st.paragraph_format.space_after = Pt(4); st.paragraph_format.line_spacing = 1.15
for s in doc.sections:
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(2.5), Cm(1.5), Cm(2), Cm(2)


def runs(par, text, size=None):
    for part in re.split(r'(\*\*.*?\*\*)', text):
        if not part:
            continue
        r = par.add_run(part[2:-2] if part.startswith('**') else part)
        r.bold = part.startswith('**')
        if size: r.font.size = Pt(size)


for k, t in TITLE:
    if k == 'gap':
        for _ in range(t): doc.add_paragraph().paragraph_format.space_after = Pt(0)
        continue
    par = doc.add_paragraph(); par.paragraph_format.space_after = Pt(0)
    par.alignment = WD_ALIGN_PARAGRAPH.RIGHT if k == 'r' else WD_ALIGN_PARAGRAPH.CENTER
    par.add_run(t).bold = (k == 'cb')
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def heading(text, size):
    par = doc.add_paragraph(); par.paragraph_format.space_before = Pt(10); par.paragraph_format.keep_with_next = True
    r = par.add_run(text); r.bold = True; r.font.size = Pt(size)


for b in B:
    k = b[0]
    if k == 'center':
        par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER; par.add_run(b[1]).bold = True
    elif k == 'h1': heading(b[1], 15)
    elif k == 'h2': heading(b[1], 14)
    elif k == 'h3': heading(b[1], 13)
    elif k == 'p':
        par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; runs(par, b[1])
    elif k == 'code':
        par = doc.add_paragraph(); par.paragraph_format.line_spacing = 1.0
        e = OxmlElement('w:shd'); e.set(qn('w:val'), 'clear'); e.set(qn('w:fill'), 'F2F2F2')
        par._p.get_or_add_pPr().append(e)
        r = par.add_run(b[1]); r.font.name = 'Consolas'; r.font.size = Pt(8.5)
    elif k == 'img':
        par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER; par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(b[1], width=Cm(b[2]))
        if b[3]:
            c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; runs(c, b[3], 12)
    elif k == 'tbl':
        rows, widths = b[1], b[2]
        t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'; t.autofit = False
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                cell = t.cell(i, j); cell.text = ''
                r = cell.paragraphs[0].add_run(val); r.font.size = Pt(10.5); r.bold = (i == 0)
                if widths: cell.width = Cm(widths[j])
        doc.add_paragraph()
    elif k in ('bul', 'ol'):
        for x in b[1]:
            par = doc.add_paragraph(style='List Bullet' if k == 'bul' else 'List Number'); runs(par, x)
    elif k == 'prob':
        _, i, t, s_, f, link = b
        par = doc.add_paragraph(); par.paragraph_format.space_before = Pt(8); par.paragraph_format.keep_with_next = True
        par.add_run(f'Проблема {i}: {t}').bold = True
        for lab, val in (('Симптом: ', s_), ('Root cause / фікс: ', f), ('Коміт: ', link)):
            q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q.add_run(lab).italic = True; q.add_run(val)

open('docs/lab2-report.md', 'w', encoding='utf-8').write(md())
doc.core_properties.author = STUDENT
doc.core_properties.title = 'Лабораторна робота №2'
doc.save('docs/lab2-report.docx')
print('ok')
