#!/usr/bin/env python3
"""extract_vectors.py — тестові вектори для tests/la_vectors.h із записів LA.

Для кожного запису профілю A:
  * декодер i2c sigrok-cli -> 14 байтів SDA після запису адреси регістру 0x3B;
  * декодер uart -> рядок прошивки 'CAP;i2c;...;raw=ax,ay,az,t,gx,gy,gz' і 'temp_c'.
Тест tests/test_mpu6050.c подає байти з шини у драйвер і порівнює з тим, що
прошивка вивела в UART. Запуск: python3 tools/extract_vectors.py > tests/la_vectors.h
"""
import os
import re
import subprocess
import sys

CAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'captures')
# raw-profileA-boot.vcd знято до виправлення округлення температури (UART: 24.01) — не вектор
FILES = ['session-A_i2c-spi-uart-pwm.vcd']


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def vector(path):
    ann = sh(f'sigrok-cli -I vcd:downsample=20 -i "{path}" -P i2c:scl=SCL:sda=SDA '
             f'-A i2c=data-read:data-write').splitlines()
    vals = [l.split(': ')[-1].strip() for l in ann]
    kinds = ['W' if 'write' in l else 'R' for l in ann]
    bursts = []
    for i, (k, v) in enumerate(zip(kinds, vals)):
        if k == 'W' and v == '3B':
            rd = []
            for k2, v2 in zip(kinds[i + 1:], vals[i + 1:]):
                if k2 != 'R':
                    break
                rd.append(int(v2, 16))
            if len(rd) == 14:
                bursts.append(rd)
    uart = sh(f'sigrok-cli -I vcd:downsample=100 -i "{path}" -P uart:rx=UART_TX:baudrate=115200 -A uart=rx-data')
    text = ''.join(chr(int(l.split()[-1], 16)) for l in uart.splitlines() if l.startswith('uart'))
    m = re.search(r'CAP;i2c;id=0x68;st=0,0;raw=([-\d,]+)', text)
    t = re.search(r'ST;MPU6050;temp_c;PASS;(-?\d+)\.(\d\d)', text)
    raw = [int(x) for x in m.group(1).split(',')]
    temp = int(t.group(1)) * 100 + int(t.group(2))
    # CAP;i2c читає регістри після self-test: беремо останній burst перед рядком CAP;i2c
    return bursts[-1], raw, temp


def main():
    out = ['/**',
           ' * la_vectors.h — тестові вектори, витягнуті з записів логічного аналізатора.',
           ' * Згенеровано tools/extract_vectors.py (декодери i2c та uart sigrok-cli) із',
           ' * записів у docs/captures. НЕ редагувати вручну.',
           ' */',
           '#ifndef LA_VECTORS_H', '#define LA_VECTORS_H', '#include <stdint.h>', '',
           'typedef struct {',
           '  const char *source;        /* файл запису                          */',
           '  uint8_t bus_bytes[14];     /* байти SDA у фазі читання 0x3B..0x48  */',
           '  int16_t uart_raw[7];       /* ax, ay, az, temp, gx, gy, gz з UART  */',
           '  int32_t uart_temp_cdeg;    /* temp_c із рядка self-test × 100      */',
           '} la_vec_t;', '', 'static const la_vec_t la_vec[] = {']
    for f in FILES:
        p = os.path.join(CAP, f)
        if not os.path.exists(p):
            continue
        b, raw, temp = vector(p)
        out.append(f'  {{ "{f}",')
        out.append('    { ' + ', '.join(f'0x{x:02X}' for x in b) + ' },')
        out.append('    { ' + ', '.join(str(x) for x in raw) + f' }}, {temp} }},')
    out += ['};', '#define LA_VEC_N (sizeof la_vec / sizeof la_vec[0])', '', '#endif']
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
