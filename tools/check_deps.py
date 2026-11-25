#!/usr/bin/env python3
"""check_deps.py — формальна перевірка правила залежностей між шарами.

Правило (docs/architecture.md §2):
    Core     -> Platform, App(app.h), HAL
    Platform -> Devices(bus.h), HAL           (не App)
    Devices  -> лише bus.h, власні .h, libc   (не HAL, не Platform, не App)
    App      -> Devices, Platform/platform.h, libc  (не HAL, не board.h)
Будь-яке #include, що порушує матрицю, — помилка; код повернення 1 (для CI).
Запуск: python3 tools/check_deps.py [корінь firmware/]
"""
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'firmware')
LAYERS = ['Core', 'Platform', 'Devices', 'App']
LIBC = {'stdint.h', 'stddef.h', 'stdbool.h', 'string.h', 'stdio.h', 'stdlib.h', 'math.h',
        'errno.h', 'limits.h', 'stdarg.h', 'sys/stat.h', 'sys/times.h', 'time.h', 'signal.h'}

# Що кожен шар має право включати. 'HAL' = заголовки ST (stm32*, *_hal*, cmsis, core_cm*)
ALLOWED = {
    'Core':     {'Core', 'Platform', 'App:app.h', 'HAL', 'libc'},
    'Platform': {'Platform', 'Devices:bus.h', 'HAL', 'libc'},
    'Devices':  {'Devices', 'libc'},
    'App':      {'App', 'Devices', 'Platform:platform.h', 'libc'},
}

INC = re.compile(r'^\s*#\s*include\s*[<"]([^">]+)[">]')


def index_headers():
    owner = {}
    for layer in LAYERS:
        for dp, _, fs in os.walk(os.path.join(ROOT, layer)):
            for f in fs:
                if f.endswith('.h'):
                    owner[f] = layer
    return owner


def classify(name, owner):
    base = os.path.basename(name)
    if name in LIBC:
        return 'libc', base
    if base in owner:
        return owner[base], base
    if re.match(r'(stm32|core_cm|cmsis_|system_stm32)', base):
        return 'HAL', base
    return 'UNKNOWN', base


def allowed(layer, target, base):
    rules = ALLOWED[layer]
    return target in rules or f'{target}:{base}' in rules


def main():
    owner = index_headers()
    errors, checked = [], 0
    for layer in LAYERS:
        for dp, _, fs in os.walk(os.path.join(ROOT, layer)):
            for f in sorted(fs):
                if not f.endswith(('.c', '.h')):
                    continue
                path = os.path.join(dp, f)
                with open(path, encoding='utf-8', errors='replace') as fh:
                    for n, line in enumerate(fh, 1):
                        m = INC.match(line)
                        if not m:
                            continue
                        checked += 1
                        target, base = classify(m.group(1), owner)
                        if not allowed(layer, target, base):
                            rel = os.path.relpath(path, ROOT)
                            errors.append(f'{rel}:{n}: {layer} -> {target} ({m.group(1)}) заборонено')
    for e in errors:
        print('DEPS ERROR', e)
    print(f'check_deps: {checked} #include перевірено, порушень: {len(errors)}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
