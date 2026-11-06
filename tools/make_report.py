# Генерує docs/report.md і docs/report.docx з одного джерела (далі LibreOffice -> PDF).
# Запуск з кореня репозиторію: python3 tools/make_report.py
import os, re
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

R = 'https://github.com/ivan32232323/STM32-Lab1'
C = lambda sha: f'{R}/commit/{sha}'
STUDENT, GROUP, COURSE, TEACHER = 'Шведенко І.', 'ІО-32', '4', 'Гордієнко Н.Ю.'
VIDEO = '[посилання на відео буде додано]'

TITLE = [
    ('c', 'Міністерство освіти і науки України'),
    ('c', 'Національний технічний університет України'),
    ('c', '«Київський політехнічний інститут імені Ігоря Сікорського»'),
    ('gap', 1),
    ('c', 'Факультет інформатики та обчислювальної техніки'),
    ('gap', 1),
    ('c', 'Кафедра обчислювальної техніки'),
    ('gap', 2),
    ('cb', 'Лабораторна робота №1'),
    ('c', 'з дисципліни «Системне програмування»'),
    ('c', '«Налаштування середовища розробки та bring-up STM32-платформи»'),
    ('gap', 6),
    ('r', 'Виконав:'), ('r', f'студент {COURSE} курсу'), ('r', f'групи {GROUP}'), ('r', STUDENT),
    ('gap', 1),
    ('r', 'Перевірив:'), ('r', TEACHER),
    ('gap', 8),
    ('c', 'Київ — 2026'),
]

B = []
def h1(t): B.append(('h1', t))
def h2(t): B.append(('h2', t))
def p(t): B.append(('p', t))
def code(t): B.append(('code', t))
def img(path, w, cap): B.append(('img', path, w, cap))
def tbl(rows, widths=None): B.append(('tbl', rows, widths))
def bul(items): B.append(('bul', items))

B.append(('center', 'Лабораторна робота №1'))
B.append(('center', 'Налаштування середовища розробки та bring-up STM32-платформи'))
p('**Мета:** розібратися з повним циклом embedded-розробки під STM32: зібрати відтворюваний тулчейн '
  '(Docker + arm-none-eabi-gcc + HAL), запустити прошивку в симуляторі Wokwi і отримати першу відповідь по UART. '
  'На практиці перевірити роботу I²C, ADC, PWM, GPIO і виводу в UART, ідентифікувати датчик за регістром, '
  'а не «на око», і оформити вимоги до власного проєкту у вигляді PRD.')
p('На старті я розумів мету як «побачити hello у терміналі». Під час роботи вона уточнилася: головне — щоб кожен крок '
  'можна було перевірити. Кожна ініціалізація звітує HAL-статус, MPU-6050 підтверджується читанням WHO_AM_I, '
  'а сигнали на шинах — записом логічного аналізатора.')
p(f'**Репозиторій:** {R}')
p(f'**PRD:** {R}/blob/lab1/docs/PRD.md')
p(f'**Pull request (здача):** {R}/pulls')
p(f'**Відео:** {VIDEO}')
p('**Форма виконання:** B (симулятор Wokwi). **Тема проєкту:** №6 «Motion-Mirroring Teleoperator» — дзеркалення руху руки на сервоприводах.')

h1('2. Розподіл обов\'язків')
p('Робота виконана одноосібно, таблиця не потрібна.')

h1('3. Процес виконання')
h2('3.1. Журнал роботи')
tbl([['Дата', 'Що зроблено', 'Коміт'],
     ['06.11', 'Встановлено VS Code + Wokwi, Git, Docker Desktop (install-tools.bat); Dockerfile з arm-none-eabi-gcc, кореневий Makefile', '429a85b'],
     ['06.11', 'Обрано Nucleo-C031C6 (єдина Nucleo-64 у Wokwi), скелет CubeMX-проєкту: .ioc, HAL STM32C0, CMSIS, startup, linker', '436cd39'],
     ['06.11', 'printf через USART2, ініціалізація I2C1/ADC1/TIM3/GPIO з перевіркою HAL_OK, I²C-скан, WHO_AM_I, tick N', '118b3d7'],
     ['06.11', 'diagram.json: MPU-6050, потенціометр, 2 серво, кнопка, logic analyzer; wokwi.toml', '23d77d3'],
     ['06.11', 'docs/hardware-components.md з посиланнями на сторінки datasheet; docs/PRD.md', '66d72e3, 47c7058'],
     ['06.11', 'Перший запуск у Wokwi, діагностика читання MPU-6050 через wokwi.vcd, обхід (soft-I²C fallback)', '86c7d85'],
     ['06.11', 'Скриншоти, декодування I²C і PWM з VCD, вирізки datasheet, звіт', 'acc949b, e992338'],
     ], [2.0, 11.0, 3.5])

h2('3.2. Docker-тулчейн')
p('Образ `stm32-build` на базі ubuntu:22.04 з gcc-arm-none-eabi, newlib і srecord (`docker/Dockerfile`). '
  'Збірка запускається командою `make build`: кореневий `Makefile` викликає `docker run … make -C firmware all`. '
  'На Windows прапорець `--user $(id -u):$(id -g)` не передається (Docker Desktop сам мапить права), '
  'для систем без make є `build.bat`.')
code('make image   # один раз: docker build -t stm32-build docker/\n'
     'make build   # docker run --rm -v $(PWD):/workspace -w /workspace stm32-build make -C firmware all\n'
     'make flash   # для Wokwi: свіжий ELF + перезапуск симулятора\n'
     'make monitor # для Wokwi: Serial Monitor у VS Code')
code('LD  build/firmware.elf\n   text    data     bss     dec     hex filename\n  25612     112    2320   28044    6d8c build/firmware.elf')
p('Прошивка займає 25,6 КБ flash з 32 КБ і 2,4 КБ RAM з 12 КБ. Дві чисті збірки поспіль дають однаковий MD5 `firmware.bin` '
  '(`-ffile-prefix-map` прибирає шляхи хоста з DWARF).')
p(f'Коміт: {C("429a85b")}')

h2('3.3. STM32CubeMX')
tbl([['Периферія', 'Параметри', 'Виводи'],
     ['USART2', '115200 8N1, ST-Link VCP', 'PA2 (TX) / PA3 (RX), AF1'],
     ['I2C1', 'Standard Mode 100 kHz, Timing = 0x20303E5D', 'PB8 (SCL, D15) / PB9 (SDA, D14), AF6'],
     ['TIM3 CH1, CH2', 'PWM 50 Hz: Prescaler = 47 (1 МГц), Period = 19999 (20 мс)', 'PA6 (D12) / PA7 (D11), AF1'],
     ['ADC1', 'IN0, 12 біт, sampling 39.5 cycles', 'PA0 (A0)'],
     ['GPIO', 'кнопка MODE: input pull-up; LD4: output', 'PA10 (D2) / PA5 (D13)'],
     ], [3.0, 8.0, 5.5])
p('SYSCLK = HCLK = PCLK = 48 MHz від HSI48 (HSIDIV /1). Проєкт має структуру CubeMX з тулчейном Makefile, '
  'файл `firmware/firmware.ioc` збережено в репозиторії.')
p('[Скриншоти CubeMX Pinout і Clock Configuration буде додано.]')
p(f'Коміт: {C("436cd39")}')

h2('3.4. Перший запуск у Wokwi')
p('printf перенаправлено в USART2 через `_write()` (`Core/Src/syscalls.c`). Налаштовано `wokwi.toml` '
  '(`firmware/build/firmware.hex`, `elf`) і `diagram.json`. Під час старту прошивка звітує статус кожної ініціалізації:')
code('=== hello from STM32 ===\nLR1 bring-up | MCU STM32C031C6 | SYSCLK = 48000000 Hz\n'
     '[ OK ] MX_USART2_UART_Init    -> HAL_OK\n[ OK ] MX_I2C1_Init           -> HAL_OK\n'
     '[ OK ] MX_ADC1_Init           -> HAL_OK\n[ OK ] MX_TIM3_Init           -> HAL_OK\n'
     '[ OK ] HAL_TIM_PWM_Start CH1  -> HAL_OK\n[ OK ] HAL_TIM_PWM_Start CH2  -> HAL_OK\n'
     'I2C1 scan: 0x68  (1 device(s))\n'
     'HW I2C1 read: st=1 err=0x20 id=0x00 -> fallback to bit-bang I2C\n'
     'soft-I2C read: st=0 id=0x68\n'
     'MPU-6050 WHO_AM_I (0x75) = 0x68  [soft-I2C] -> identified\n'
     'tick 1 | mode=MANUAL pot=0 pitch=0 roll=0 pwm1=1000 pwm2=1500\ntick 2 | ...')
p(f'Коміти: {C("118b3d7")}, {C("23d77d3")}')

h2('3.5. Компоненти і datasheets')
p('У `docs/hardware-components.md` для кожного компонента вказано інтерфейс, адресу, ключові регістри, живлення '
  'і номер сторінки datasheet. Нижче — сторінки, на які спирається bring-up.')
img('docs/datasheets/mpu6050-rm-p45-who-am-i.png', 13.5,
    '1. InvenSense. MPU-6000/MPU-6050 Register Map and Descriptions, RM-MPU-6000A-00, rev 4.2, с. 45 — WHO_AM_I (0x75) = 0x68.')
img('docs/datasheets/mpu6050-rm-p40-pwr-mgmt1.png', 13.5,
    '2. Там само, с. 40 — PWR_MGMT_1 (0x6B): після ввімкнення SLEEP = 1, пишемо 0x00.')
img('docs/datasheets/mpu6050-rm-p29-accel.png', 13.5,
    '3. Там само, с. 29 — ACCEL_XOUT_H…ACCEL_ZOUT_L (0x3B–0x40), ±2 g = 16384 LSB/g.')
img('docs/datasheets/mpu6050-ps-p15-i2c-addr.png', 13.5,
    '4. InvenSense. MPU-6000/MPU-6050 Product Specification, PS-MPU-6000A-00, rev 3.4, с. 15 — I²C 100/400 кГц, адреса 1101000 (AD0 = 0).')
img('docs/datasheets/mpu6050-ps-p14-current.png', 13.5,
    '5. Там само, с. 14 — VDD 2.375–3.46 В, струм 3.8 мА: живлення від 3V3 Nucleo достатньо.')
img('docs/datasheets/mpu6050-ps-p35-i2c-protocol.png', 13.5,
    '6. Там само, с. 35 — протокол I²C: S, адреса + R/W, ACK, Sr, STOP.')
tbl([['Компонент', 'Інтерфейс', 'Ключові параметри', 'Джерело'],
     ['STM32C031C6', 'USART2, I2C1, ADC1, TIM3', 'AF1 USART2 PA2/PA3, AF6 I2C1 PB8/PB9, AF1 TIM3 PA6/PA7', 'DS13867 rev 4, «Alternate function mapping»'],
     ['Nucleo-C031C6', 'ST-Link VCP', 'VCP = USART2 PA2/PA3, LD4 = PA5', 'UM2953, розд. 6.9–6.10'],
     ['MPU-6050', 'I²C @0x68', 'WHO_AM_I 0x75, PWR_MGMT_1 0x6B, ACCEL 0x3B', 'RM-MPU-6000A с. 29, 40, 45; PS-MPU-6000A с. 14–15'],
     ['SG90 ×2', 'PWM 50 Гц', '1.0 мс = −90°, 1.5 мс = 0°, 2.0 мс = +90°; 4.8–6 В', 'TowerPro SG90 datasheet'],
     ['Потенціометр 10 кОм', 'ADC', '0…3.3 В → 0…4095', '—'],
     ['Кнопка', 'GPIO', 'pull-up, активний 0, антидребезг 20 мс', '—'],
     ], [3.0, 2.8, 6.2, 4.5])
p(f'Коміт: {C("66d72e3")}')

h2('3.6. Сенсори і перевірка шин')
p('До `diagram.json` додано MPU-6050 (I²C), потенціометр (ADC), два серво SG90 (PWM), кнопку MODE (GPIO) і логічний '
  'аналізатор на D15/SCL, D14/SDA, D12/PWM, PA2/UART TX. Кнопка перемикає режим MANUAL → MIRROR. У режимі MIRROR кути '
  'нахилу з акселерометра перераховуються в ширину імпульсу серво: 1500 + кут · 500 / 90 мкс.')
img('docs/screenshots/wokwi-mirror.png', 15.5,
    'Wokwi: режим MIRROR. accel Y = 1.45 g → roll = atan2(1.45, 1) = 55° → pwm1 = 1805 мкс; accel X < 0 → pitch = 31° → pwm2 = 1672 мкс. Обидва серво повернуті.')
p('Декодована транзакція WHO_AM_I. Запис Wokwi Logic Analyzer (`wokwi.vcd`) розібрано скриптом `tools/vcd_plot.py`: '
  '`S | 0xD0 ACK | 0x75 ACK | Sr | 0xD1 ACK | 0x68 NACK | P`. Це стандартне читання регістра (PS-MPU-6000A с. 35–36), '
  'датчик повернув 0x68. NACK на останньому байті ставить майстер, так і має бути.')
img('docs/screenshots/logic-i2c-whoami.png', 16.5, 'I²C: читання WHO_AM_I з MPU-6050 (SCL = PB8, SDA = PB9).')
img('docs/screenshots/logic-pwm.png', 16.5,
    'PWM на D12 (TIM3_CH1): період 20 000 мкс, у записі зустрічаються імпульси 1000, 1500 і 1805 мкс — MANUAL, нейтраль і MIRROR 55°.')
p(f'Коміти: {C("86c7d85")}, {C("e992338")}')

h2('3.7. Проблеми та їх вирішення')
PROBS = [
 ('У Wokwi немає Nucleo-F411RE / F446RE',
  'у diagram.json немає такого типу плати, ELF під Cortex-M4 не стартує.',
  'Wokwi симулює з лінійки STM32 лише Nucleo-C031C6, Nucleo-L031K6 і Blue Pill.',
  'ціль — STM32C031C6 (Cortex-M0+, 48 МГц): HAL STM32C0, `-mcpu=cortex-m0plus` без FPU, стартап і лінкер для C031. '
  'Піни взято на роз\'ємі Arduino (D11/D12/D14/D15/A0), бо на F411RE вони мають ті самі функції.', '436cd39'),
 ('fatal error: m-profile/cmsis_gcc_m.h: No such file or directory',
  'перша збірка падає на кожному .c у cmsis_gcc.h:1011.',
  'заголовки ядра взято з CMSIS 6, а HAL STM32C0 очікує CMSIS 5.x з плоскою структурою Include/.',
  'взято Drivers/CMSIS/Include з того самого STM32Cube FW-пакета, що й HAL (приклад wokwi/stm32-hello-wokwi).', '436cd39'),
 ('implicit declaration of function \'HAL_TIM_MspPostInit\'',
  'попередження компілятора в MX_TIM3_Init().',
  'CubeMX оголошує цю функцію в main.h, а при перенесенні оголошення загубилося.',
  'додано прототип у Core/Inc/main.h, збірка з -Wall без попереджень.', '118b3d7'),
 ('На Windows немає make, а --user $(id -u) ламає docker run',
  '`make build` з методички не працює в PowerShell: Docker отримує `--user :`.',
  '`--user` потрібен лише на Linux; Docker Desktop на Windows мапить права через WSL2.',
  'у Makefile гілка `ifeq ($(OS),Windows_NT)` без `--user`, Make ставиться через winget, додано build.bat.', '429a85b'),
 ('VS Code «Опубликовать Branch» нічого не робить',
  'після натискання не з\'являється вибір private/public, у журналі Git немає спроби push.',
  'у репозиторію ще не було remote, а діалог створення репозиторію GitHub-розширення не відкрився.',
  'репозиторій створено на github.com, `git remote add origin …`, після чого публікація гілок main і lab1 пройшла.', ''),
 ('Прошивка займає 27 КБ з 32 КБ flash',
  'printf + atan2f/sqrtf на Cortex-M0+ без FPU.',
  'soft-float бібліотека і повний newlib printf.',
  '`-specs=nano.specs`, `--gc-sections`, кути виводяться цілими. Для fusion-фільтра у ЛР2 — фіксована кома або F446RE з FPU.', '118b3d7'),
 ('HAL_I2C_Mem_Read до MPU-6050 у Wokwi повертає HAL_TIMEOUT',
  'I²C-скан бачить 0x68, але WHO_AM_I = 0x00, `HAL_I2C_GetError() = 0x20` (TIMEOUT). Роздільні Master_Transmit + Master_Receive дають те саме.',
  'розбір wokwi.vcd: фаза запису (0xD0 ACK, 0x75 ACK) проходить, але після адреси читання 0xD1 ACK модель I2C STM32C0 у Wokwi не генерує тактів SCL для байта даних. Це обмеження симулятора, а не схеми.',
  'апаратний I2C1 лишився для ініціалізації і скану; якщо апаратне читання не вдається, вмикається програмний I²C на тих самих пінах через HAL_GPIO. '
  'Перша версія теж читала 0x00: модель не повертає рівень лінії для open-drain виходу, тому SDA на час читання перемикається у вхід з pull-up. '
  'Після цього WHO_AM_I = 0x68. На реальній Nucleo fallback не вмикається.', '86c7d85'),
]
for i, (t, s, c, f, sha) in enumerate(PROBS, 1):
    B.append(('prob', i, t, s, c, f, sha))

h1('4. Висновок')
p('Навчився:')
bul(['збирати прошивку STM32 в ізольованому Docker-середовищі і робити збірку відтворюваною (однаковий MD5 між збірками);',
     'будувати дерево тактування HSI48 → SYSCLK → AHB/APB і розуміти, як від нього залежать BRR USART, Timing I²C і PSC таймера;',
     'прив\'язувати периферію до пінів через alternate functions (AF1 USART2/TIM3, AF6 I2C1) і MSP-шар HAL;',
     'перенаправляти printf у UART через _write() з newlib;',
     'налаштовувати таймер так, щоб CCR дорівнював ширині імпульсу серво в мікросекундах (PSC = 47, ARR = 19999);',
     'перевіряти I²C-пристрій за адресою та ідентифікаційним регістром і доводити, де саме ламається транзакція, за записом логічного аналізатора.'])
p('Куди рухаюся в ЛР2: драйвер MPU-6050 з гіроскопом, комплементарний → Mahony-фільтр, вимірювання латентності '
  '«рух IMU → оновлення PWM» через GPIO-toggle і логічний аналізатор (FR-03, < 50 мс), мертва зона і rate-limit (FR-06), UART CLI.')
p('Що зробив би інакше: одразу перевірив би список плат і периферії, яку підтримує Wokwi, перед вибором MCU; '
  'генерував би HAL і CMSIS одним пакетом через CubeMX; з першого коміту додав би CI з `make build`.')

h1('5. Матеріали та посилання')
B.append(('ol', [
 'InvenSense. MPU-6000/MPU-6050 Register Map and Descriptions, RM-MPU-6000A-00, rev 4.2. 46 с.',
 'InvenSense. MPU-6000/MPU-6050 Product Specification, PS-MPU-6000A-00, rev 3.4, 19.08.2013. 52 с.',
 'STMicroelectronics. STM32C031x4/x6 Datasheet, DS13867, rev 4. https://www.st.com/en/microcontrollers-microprocessors/stm32c031c6.html',
 'STMicroelectronics. RM0490 Reference manual: STM32C0x1. https://www.st.com/en/microcontrollers-microprocessors/stm32c031c6.html#documentation',
 'STMicroelectronics. STM32 Nucleo-64 boards (MB1717), user manual UM2953. https://www.st.com/resource/en/user_manual/um2953-stm32-nucleo64-board-mb1717-stmicroelectronics.pdf',
 'STMicroelectronics. STM32CubeC0 HAL driver. https://github.com/STMicroelectronics/stm32c0xx-hal-driver',
 'STMicroelectronics. CMSIS device STM32C0. https://github.com/STMicroelectronics/cmsis-device-c0',
 'TowerPro. SG90 Micro Servo datasheet. http://www.ee.ic.ac.uk/pcheung/teaching/DE1_EE/stores/sg90_datasheet.pdf',
 'Wokwi. diagram.json File Format. https://docs.wokwi.com/diagram-format',
 'Wokwi. STM32 Nucleo-64 C031C6 (simulation features). https://docs.wokwi.com/parts/board-st-nucleo-c031c6',
 'Wokwi. stm32-hello-wokwi — приклад HAL-проєкту. https://github.com/wokwi/stm32-hello-wokwi',
 'Wokwi. VS Code extension — Getting started. https://docs.wokwi.com/vscode/getting-started',
 'Docker. docker run reference. https://docs.docker.com/reference/cli/docker/container/run/',
]))

SHA = re.compile(r'^[0-9a-f]{7}$')

def md():
    o = ['---', 'title: "Лабораторна робота №1"', '---', '']
    for k, t in TITLE:
        if k == 'gap': o.append('')
        else: o.append((f'**{t}**' if k == 'cb' else t) + '  ')
    o += ['', '---', '']
    for b in B:
        k = b[0]
        if k == 'center': o += [f'### {b[1]}', '']
        elif k == 'h1': o += [f'# {b[1]}', '']
        elif k == 'h2': o += [f'## {b[1]}', '']
        elif k == 'p': o += [b[1], '']
        elif k == 'code': o += ['```', b[1], '```', '']
        elif k == 'img': o += [f'![{b[3]}]({os.path.relpath(b[1], "docs")})', '', f'*{b[3]}*', '']
        elif k == 'tbl':
            rows = b[1]
            o += ['| ' + ' | '.join(rows[0]) + ' |', '|' + '---|' * len(rows[0])]
            for r in rows[1:]:
                cells = []
                for x in r:
                    parts = [y.strip() for y in x.split(',')]
                    if all(SHA.match(y) for y in parts):
                        x = ', '.join(f'[{y}]({C(y)})' for y in parts)
                    cells.append(x)
                o.append('| ' + ' | '.join(cells) + ' |')
            o.append('')
        elif k == 'bul': o += [f'- {x}' for x in b[1]] + ['']
        elif k == 'ol': o += [f'{i}. {x}' for i, x in enumerate(b[1], 1)] + ['']
        elif k == 'prob':
            _, i, t, s, c, f, sha = b
            o += [f'### Проблема {i}: {t}', '', f'**Симптом:** {s}', '', f'**Причина:** {c}', '',
                  f'**Фікс:** {f}', '', (f'Коміт: {C(sha)}' if sha else 'Коміт: — (зміна лише в налаштуваннях .git/config)'), '']
    return '\n'.join(o)

doc = Document()
st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(14)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
st.paragraph_format.space_after = Pt(4); st.paragraph_format.line_spacing = 1.15
for s in doc.sections:
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(2.5), Cm(1.5), Cm(2), Cm(2)

def runs(par, text, size=None):
    for part in re.split(r'(\*\*.*?\*\*|`.*?`)', text):
        if not part: continue
        if part.startswith('**'):
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith('`'):
            r = par.add_run(part[1:-1]); r.font.name = 'Consolas'; r.font.size = Pt(12); continue
        else:
            r = par.add_run(part)
        if size: r.font.size = Pt(size)

for k, t in TITLE:
    if k == 'gap':
        for _ in range(t): doc.add_paragraph().paragraph_format.space_after = Pt(0)
        continue
    par = doc.add_paragraph(); par.paragraph_format.space_after = Pt(0)
    par.alignment = WD_ALIGN_PARAGRAPH.RIGHT if k == 'r' else WD_ALIGN_PARAGRAPH.CENTER
    r = par.add_run(t); r.bold = (k == 'cb')
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
    elif k == 'p':
        par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; runs(par, b[1])
    elif k == 'code':
        par = doc.add_paragraph(); par.paragraph_format.line_spacing = 1.0
        e = OxmlElement('w:shd'); e.set(qn('w:val'), 'clear'); e.set(qn('w:fill'), 'F2F2F2')
        par._p.get_or_add_pPr().append(e)
        r = par.add_run(b[1]); r.font.name = 'Consolas'; r.font.size = Pt(10)
    elif k == 'img':
        par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER; par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(b[1], width=Cm(b[2]))
        cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(b[3]); r.italic = True; r.font.size = Pt(12)
    elif k == 'tbl':
        rows, widths = b[1], b[2]
        t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                cell = t.cell(i, j); cell.text = ''
                r = cell.paragraphs[0].add_run(val); r.font.size = Pt(12); r.bold = (i == 0)
                if widths: cell.width = Cm(widths[j])
        doc.add_paragraph()
    elif k in ('bul', 'ol'):
        for x in b[1]:
            par = doc.add_paragraph(style='List Bullet' if k == 'bul' else 'List Number'); runs(par, x)
    elif k == 'prob':
        _, i, t, s, c, f, sha = b
        par = doc.add_paragraph(); par.paragraph_format.space_before = Pt(8); par.paragraph_format.keep_with_next = True
        par.add_run(f'Проблема {i}: {t}').bold = True
        for lab, val in (('Симптом', s), ('Причина', c), ('Фікс', f)):
            par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; runs(par, f'**{lab}:** {val}')
        doc.add_paragraph(f'Коміт: {C(sha)}' if sha else 'Коміт: — (зміна лише в налаштуваннях .git/config)')

open('docs/report.md', 'w', encoding='utf-8').write(md())
doc.save('docs/report.docx')
print('ok')
