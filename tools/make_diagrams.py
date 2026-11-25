#!/usr/bin/env python3
"""make_diagrams.py — рисунки для звіту ЛР2 (docs/lab_2/img/):
  component-diagram.png      — компонентна діаграма шарів
  la-i2c-manual.png          — ручне декодування WHO_AM_I за формою сигналу
  la-i2c-hw-anomaly.png      — апаратний I2C у Wokwi: немає фази читання
  la-spi-sequence.png        — WREN / RDSR / Page Program / BUSY
  la-pwm.png                 — PWM 1000 і 2000 мкс
  la-mirror-latency.png      — кнопка -> контур -> I2C -> PWM tilt
Потрібен matplotlib. Дані — вирізки з docs/captures/*.vcd (tools/la_analyze.py).
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcdlib import Vcd  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CAP = os.path.join(ROOT, 'docs', 'captures')
IMG = os.path.join(ROOT, 'docs', 'lab_2', 'img')
os.makedirs(IMG, exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})


def series(v, ch, t0, t1, scale=1e3):
    xs, ys = [(0)], [v.level_at(ch, t0)]
    last = ys[0]
    for t, lv in v.ev[ch]:
        if t <= t0:
            continue
        if t > t1:
            break
        x = (t - t0) / scale
        xs += [x, x]
        ys += [last, lv]
        last = lv
    xs.append((t1 - t0) / scale)
    ys.append(last)
    return xs, ys


def waves(v, chans, t0, t1, ax, scale=1e3, colors=None):
    for i, ch in enumerate(chans):
        x, y = series(v, ch, t0, t1, scale)
        base = (len(chans) - 1 - i) * 1.6
        ax.plot(x, [base + 0.9 * k for k in y], lw=1.1, color=(colors or {}).get(ch, 'C%d' % i))
        ax.text(-0.01 * (t1 - t0) / scale, base + 0.45, ch, ha='right', va='center', fontsize=8)
    ax.set_yticks([])
    ax.set_ylim(-0.4, len(chans) * 1.6)
    for s in ('left', 'right', 'top'):
        ax.spines[s].set_visible(False)


def component_diagram():
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 64)

    def box(x, y, w, h, title, body, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4', fc=fc, ec='#333', lw=1))
        ax.text(x + w / 2, y + h - 2, title, ha='center', va='top', fontweight='bold', fontsize=10)
        ax.text(x + w / 2, y + h - 5.5, body, ha='center', va='top', fontsize=8, linespacing=1.4)

    box(2, 46, 60, 15, 'App/  (без HAL)', 'app.c — цикл 50 Гц, режими MANUAL/MIRROR, FR-09\n'
        'selftest.c   attitude.c   servo_map.c   cli.c', '#e3f2fd')
    box(2, 26, 38, 15, 'Devices/  (без HAL)', 'mpu6050.c      w25q.c\n«bus.h»: i2c_bus_t, spi_dev_t', '#e8f5e9')
    box(44, 26, 18, 15, '«platform.h»', 'порт для App:\nчас, UART, ADC,\nсерво, GPIO, шини', '#fff8e1')
    box(2, 5, 60, 16, 'Platform/', 'platform.c: plat_i2c_hw (HAL) | plat_i2c_sw (bit-bang)\n'
        '| plat_flash_spi (HAL SPI + CS#) | ADC/TIM/UART\nboard.h — усі піни, AF, хендли', '#fff3e0')
    box(68, 40, 30, 21, 'Core/  (CubeMX)', 'main.c: MX_*_Init()\n→ app_main()\nMSP, IRQ, syscalls\n'
        'USER CODE лише 2 рядки', '#f3e5f5')
    box(68, 5, 30, 28, 'Drivers/  (ST)', 'STM32C0 HAL v1.4.1\nCMSIS\n(не редагуються,\nVERSIONS.md)', '#eceff1')
    box(68, -14 + 14, 0, 0, '', '', 'none')

    def arrow(x1, y1, x2, y2, txt='', dash=False):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', lw=1.2, ls='--' if dash else '-', color='#333'))
        if txt:
            ax.text((x1 + x2) / 2 + 0.8, (y1 + y2) / 2, txt, fontsize=7, color='#555')

    arrow(20, 46, 20, 41.5)                      # App -> Devices
    arrow(53, 46, 53, 41.5)                      # App -> platform.h
    arrow(20, 26, 20, 21.5, 'bus.h реалізує', True)    # Platform implements bus
    arrow(53, 21.5, 53, 26, 'реалізує', True)    # platform.c implements platform.h
    arrow(68, 52, 62.5, 52, 'app_main()')        # Core -> App
    arrow(68, 44, 62.5, 15, 'board.h')           # Core -> Platform
    arrow(62.5, 10, 68, 12, 'HAL')               # Platform -> HAL
    arrow(83, 40, 83, 33.5, 'HAL')               # Core -> HAL
    ax.text(2, 1, 'Суцільна стрілка — #include (дозволений напрямок, перевіряє tools/check_deps.py); '
            'пунктир — реалізація інтерфейсу.\nУ хостових тестах bus.h/platform.h реалізують tests/doubles '
            '(fake_i2c, mock_spi, fake_platform) замість Platform/.', fontsize=7.5, color='#333', va='bottom')
    fig.savefig(os.path.join(IMG, 'component-diagram.png'), dpi=160, bbox_inches='tight')
    plt.close(fig)


def i2c_manual():
    v = Vcd(os.path.join(CAP, 'i2c_mpu6050_whoami-burst14.vcd'))
    s = v.edges('SDA', level=0)[0]
    t0, t1 = s - 15_000, s + 240_000
    fig, ax = plt.subplots(figsize=(11, 3.2))
    waves(v, ['SCL', 'SDA'], t0, t1, ax)
    rises = v.edges('SCL', t0, t1, 1)
    labels = ['0', '1', '1', '0', '1', '0', '0', '0', 'ACK', '0', '1', '1', '1', '0', '1', '0', '1', 'ACK']
    names = ['A6', 'A5', 'A4', 'A3', 'A2', 'A1', 'A0', 'R/W', '9', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'D1', 'D0', '9']
    for i, t in enumerate(rises[:18]):
        x = (t - t0) / 1e3
        sda = v.level_at('SDA', t)
        ax.axvline(x, color='#bbb', lw=0.5, zorder=0)
        ax.text(x, 3.3, f'{names[i]}\n{sda}', ha='center', fontsize=7,
                color='#c62828' if 'ACK' in labels[i] else '#1565c0')
    ax.text((s - t0) / 1e3, 3.9, 'START\n(SDA↓ при SCL=1)', ha='center', fontsize=7, color='#2e7d32')
    ax.set_xlabel('час, мкс (від початку вирізки)')
    ax.set_title('Ручне декодування: адреса 1101000 (0x68) + W(0) → 0xD0, ACK; байт 01110101 = 0x75 (WHO_AM_I), ACK')
    fig.savefig(os.path.join(IMG, 'la-i2c-manual.png'), dpi=160, bbox_inches='tight')
    plt.close(fig)


def i2c_hw_anomaly():
    v = Vcd(os.path.join(CAP, 'i2c_mpu6050_hw-read-stall_anomaly.vcd'))
    fig, ax = plt.subplots(figsize=(11, 2.8))
    waves(v, ['SCL', 'SDA'], 0, v.t_end, ax)
    ax.set_xlabel('час, мкс')
    ax.set_title('HAL_I2C_Mem_Read у Wokwi (STM32C0): START, 0xD0 ACK, 0x75 ACK — далі ні Sr, ні тактів SCL, ні STOP')
    fig.savefig(os.path.join(IMG, 'la-i2c-hw-anomaly.png'), dpi=160, bbox_inches='tight')
    plt.close(fig)


def spi_seq():
    v = Vcd(os.path.join(CAP, 'spi_w25q64_jedec-wren-erase-pp-read.vcd'))
    lows = v.pulses('CS', level=0)
    fig, axs = plt.subplots(2, 1, figsize=(11, 6))
    t0, t1 = lows[0][0] - 10_000, lows[0][0] + lows[0][1] + 10_000
    waves(v, ['CS', 'SCK', 'MOSI', 'MISO'], t0, t1, axs[0])
    axs[0].set_title('JEDEC ID: CS#↓, MOSI 9F, MISO EF 40 17, CS#↑ (mode 0: SCK у спокої 0, вибірка по ↑)')
    axs[0].set_xlabel('мкс')
    # знайти PP: транзакція, перша з 4+ байтів після WREN, що йде після стирання
    long = [p for p in lows if p[1] > 200_000]
    pp = long[-2] if len(long) >= 2 else lows[-2]
    i = lows.index(pp)
    a, b = lows[i - 2][0] - 10_000, lows[i + 1][0] + lows[i + 1][1] + 10_000
    waves(v, ['CS', 'SCK', 'MOSI', 'MISO'], a, b, axs[1])
    axs[1].set_title('Page Program: [06h WREN] [05h → WEL=1] [02h 00 20 00 «LR2-SPI!»] [05h → BUSY]')
    axs[1].set_xlabel('мкс')
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, 'la-spi-sequence.png'), dpi=160, bbox_inches='tight')
    plt.close(fig)


def pwm():
    v = Vcd(os.path.join(CAP, 'pwm_servo-pan_1000us-2000us.vcd'))
    fig, ax = plt.subplots(figsize=(11, 2.6))
    waves(v, ['PWM_PAN', 'PWM_TILT'], 0, v.t_end, ax, scale=1e6)
    for t, w in v.pulses('PWM_PAN'):
        ax.text(t / 1e6 + w / 2e6, 2.75, f'{w / 1e3:.0f}', ha='center', fontsize=7)
    ax.set_xlabel('час, мс')
    ax.set_title('TIM3 PWM: період 20.000 мс; pan — 3 імпульси 1000 мкс, потім 2000 мкс (self-test); tilt — 1500 мкс')
    fig.savefig(os.path.join(IMG, 'la-pwm.png'), dpi=160, bbox_inches='tight')
    plt.close(fig)


def mirror():
    v = Vcd(os.path.join(CAP, 'mirror_latency_btn-loop-i2c-pwm.vcd'))
    fig, ax = plt.subplots(figsize=(11, 3.4))
    waves(v, ['BTN', 'PROBE_LOOP', 'SCL', 'PWM_TILT'], 0, v.t_end, ax, scale=1e6)
    for t, w in v.pulses('PWM_TILT'):
        if w > 1_510_000:
            ax.text(t / 1e6, 0.95, f'{w / 1e3:.0f}', fontsize=7, ha='left')
    ax.set_xlabel('час, мс')
    ax.set_title('MANUAL→MIRROR: брязкіт кнопки, контур 3.6 мс кожні 20 мс, PWM tilt 1500→1667 мкс з кроком 33 мкс (300 °/с)')
    fig.savefig(os.path.join(IMG, 'la-mirror-latency.png'), dpi=160, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    component_diagram()
    i2c_manual()
    i2c_hw_anomaly()
    spi_seq()
    pwm()
    mirror()
    print('ok:', sorted(os.listdir(IMG)))
