#!/usr/bin/env python3
"""check_pinout.py — узгодженість трьох описів розводки:
   firmware/Platform/board.h  <->  firmware/firmware.ioc  <->  diagram.json
(і, як наслідок, docs/pinout.md, таблиця якого згенерована з тих самих даних).
Повертає 1 при розбіжності (для CI).
"""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

# Arduino/morpho-імена плати Wokwi board-st-nucleo-c031c6 -> пін МК (wokwi-boards/st-nucleo-c031c6)
NUCLEO = {'D0': 'PB7', 'D1': 'PB6', 'D2': 'PA10', 'D3': 'PB3', 'D4': 'PB10', 'D5': 'PB4',
          'D6': 'PB5', 'D7': 'PA15', 'D8': 'PA9', 'D9': 'PC7', 'D10': 'PB0', 'D11': 'PA7',
          'D12': 'PA6', 'D13': 'PA5', 'D14': 'PB9', 'D15': 'PB8',
          'A0': 'PA0', 'A1': 'PA1', 'A2': 'PA4', 'A3': 'PB1', 'A4': 'PA11', 'A5': 'PA12'}

# сигнал board.h -> (очікуваний сигнал/мітка в .ioc, вивід пристрою в diagram.json або None)
EXPECT = {
    'VCP_TX':     ('USART2_TX',  '$serialMonitor:RX'),
    'VCP_RX':     ('USART2_RX',  '$serialMonitor:TX'),
    'I2C_SCL':    ('I2C1_SCL',   'imu:SCL'),
    'I2C_SDA':    ('I2C1_SDA',   'imu:SDA'),
    'SPI_SCK':    ('SPI1_SCK',   'flash:CLK'),
    'SPI_MISO':   ('SPI1_MISO',  'flash:DO'),
    'SPI_MOSI':   ('SPI1_MOSI',  'flash:DI'),
    'FLASH_CS':   ('FLASH_CS',   'flash:CS'),
    'POT':        ('ADC1_IN0',   'pot:SIG'),
    'SERVO_PAN':  ('S_TIM3_CH1', 'servo_pan:PWM'),
    'SERVO_TILT': ('S_TIM3_CH2', 'servo_tilt:PWM'),
    'LED':        ('LED',        None),
    'BTN':        ('BTN',        'btn:1.l'),
    'PROBE_ADC':  ('PROBE_ADC',  None),
    'PROBE_LOOP': ('PROBE_LOOP', None),
}


def board_pins():
    txt = open(os.path.join(ROOT, 'firmware/Platform/board.h'), encoding='utf-8').read()
    d = dict(re.findall(r'#define\s+BOARD_(\w+)\s+(\S+)', txt))
    out = {}
    for sig in EXPECT:
        pin = d.get(sig + '_PIN')
        port = d.get(sig + '_PORT')
        if port is None:   # спільний порт групи: I2C_SCL -> I2C_PORT, VCP_TX -> VCP_TX_PORT
            port = d.get(sig.split('_')[0] + '_PORT')
        if pin is None or port is None:
            out[sig] = None
            continue
        out[sig] = 'P' + port[-1] + pin.replace('GPIO_PIN_', '')
    return out


def ioc_pins():
    kv = {}
    for line in open(os.path.join(ROOT, 'firmware/firmware.ioc'), encoding='utf-8'):
        if '=' in line:
            k, v = line.rstrip('\r\n').split('=', 1)
            kv[k] = v
    res = {}
    for k, v in kv.items():
        m = re.match(r'(P[A-F]\d+)[^.]*\.(Signal|GPIO_Label)$', k)
        if m:
            res.setdefault(m.group(1), set()).add(v)
    return res


def diagram_pins():
    d = json.load(open(os.path.join(ROOT, 'diagram.json'), encoding='utf-8'))
    res = {}
    for a, b, *_ in d['connections']:
        for x, y in ((a, b), (b, a)):
            if y.startswith('nucleo:'):
                p = y.split(':', 1)[1]
                res.setdefault(x, set()).add(NUCLEO.get(p, p))
    return res


def main():
    bp, ip, dp = board_pins(), ioc_pins(), diagram_pins()
    errs = []
    for sig, (ioc_sig, dev) in EXPECT.items():
        pin = bp.get(sig)
        if not pin:
            errs.append(f'{sig}: немає в board.h')
            continue
        if ioc_sig not in ip.get(pin, set()):
            errs.append(f'{sig}: board.h={pin}, але в .ioc у {pin} {sorted(ip.get(pin, []))} (очікується {ioc_sig})')
        if dev and pin not in dp.get(dev, set()):
            errs.append(f'{sig}: board.h={pin}, але в diagram.json {dev} -> {sorted(dp.get(dev, []))}')
        print(f'  {sig:<11} {pin:<5} ioc:{ioc_sig:<11} diagram:{dev or "-"}')
    for e in errs:
        print('PINOUT ERROR', e)
    print(f'check_pinout: {len(EXPECT)} сигналів, розбіжностей: {len(errs)}')
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
