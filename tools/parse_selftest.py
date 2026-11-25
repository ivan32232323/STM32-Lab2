#!/usr/bin/env python3
"""parse_selftest.py — автоматичний розбір виводу режиму самоперевірки.

  python3 tools/parse_selftest.py docs/captures/uart_vcp_full-session.log
Читає рядки 'ST;<пристрій>;<перевірка>;<рівень>;<значення>;<критерій>' з будь-якого
UART-логу (Wokwi Serial Monitor, picocom, декодований sigrok-cli), друкує таблицю
й повертає 1, якщо є FAIL або немає рядка SUMMARY (придатно для CI на HIL-стенді).
"""
import sys


def main(path):
    rows, summary = [], None
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.strip()
        if not line.startswith('ST;'):
            continue
        f = line.split(';')
        if len(f) != 6:
            print('ПОМИЛКА ФОРМАТУ:', line)
            return 1
        _, dev, check, lvl, val, crit = f
        if dev == 'SUMMARY':
            summary = (lvl, val)
        else:
            rows.append((dev, check, lvl, val, crit))
    w = max(len(r[0]) + len(r[1]) for r in rows) + 2 if rows else 10
    for dev, check, lvl, val, crit in rows:
        print(f'{dev + "." + check:<{w}} {lvl:<5} {val:<24} {crit}')
    if not summary:
        print('немає ST;SUMMARY — self-test не завершився')
        return 1
    print('SUMMARY:', *summary)
    return 0 if summary[0] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
