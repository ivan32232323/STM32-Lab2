#!/usr/bin/env python3
"""la_analyze.py — розбір записів Wokwi Logic Analyzer для ЛР2.

  python3 tools/la_analyze.py            (з кореня репозиторію; потрібен sigrok-cli)

Вхід:  docs/captures/session-A_i2c-spi-uart-pwm.vcd  (профіль A, diagram.json)
       docs/captures/session-B_pwm-probes-mirror.vcd (профіль B, diagram-profile-B.json)
Вихід (docs/captures/):
  <інтерфейс>_<пристрій>_<операція>.vcd   — вирізка одного сценарію (час від 0)
  <те саме>.sr                             — та сама вирізка у форматі сесії PulseView
  <те саме>.ann.txt                        — експорт анотацій декодера sigrok-cli
  measurements.json                        — виміряні таймінги (для analysis.md)
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcdlib import Vcd, bursts, stats  # noqa: E402

CAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'captures')
A = os.path.join(CAP, 'session-A_i2c-spi-uart-pwm.vcd')
B = os.path.join(CAP, 'session-B_pwm-probes-mirror.vcd')
M = {}


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def slice_vcd(src, name, t0, t1, chans=None, pad=20_000):
    """Вирізати [t0-pad, t1+pad] нс, перерахувати час від 0, лишити chans."""
    v = Vcd(src)
    ids = [i for i in v.order if chans is None or v.names[i] in chans]
    t0 = max(0, t0 - pad)
    t1 = t1 + pad
    out = [l for l in v.header if not l.strip().startswith('$var')
           and not l.strip().startswith('$upscope') and not l.strip().startswith('$enddefinitions')]
    for i in ids:
        out.append(f'$var wire 1 {i} {v.names[i]} $end\n')
    out += ['$upscope $end\n', '$enddefinitions $end\n', '#0\n']
    for i in ids:
        out.append(f'{v.level_at(v.names[i], t0)}{i}\n')
    evs = sorted((t, i, lv) for i in ids for t, lv in v.ev[v.names[i]] if t0 < t <= t1)
    cur = None
    for t, i, lv in evs:
        if t != cur:
            out.append(f'#{t - t0}\n')
            cur = t
        out.append(f'{lv}{i}\n')
    out.append(f'#{t1 - t0}\n')
    path = os.path.join(CAP, name + '.vcd')
    open(path, 'w').write(''.join(out))
    return path


def decode(vcd, name, ds, pd, ann):
    """sigrok-cli: VCD -> .sr і текстовий експорт анотацій (час у мкс)."""
    base = os.path.join(CAP, name)
    sh(f'sigrok-cli -I vcd:downsample={ds} -i "{vcd}" -o "{base}.sr"')
    raw = sh(f'sigrok-cli -I vcd:downsample={ds} -i "{vcd}" -P {pd} -A {ann} --protocol-decoder-samplenum')
    rate_ns = ds  # 1 ns/відлік у VCD Wokwi × downsample
    lines = []
    for l in raw.splitlines():
        rng, _, rest = l.partition(' ')
        a, _, b = rng.partition('-')
        try:
            lines.append(f'{int(a) * rate_ns / 1000:10.3f} us  {rest}')
        except ValueError:
            lines.append(l)
    hdr = (f'# {name}: sigrok-cli -I vcd:downsample={ds} -P {pd} -A {ann}\n'
           f'# частота дискретизації після downsample: {1000 / ds:.0f} МГц ({ds} нс/відлік)\n')
    open(base + '.ann.txt', 'w').write(hdr + '\n'.join(lines) + '\n')
    return lines


def i2c_transactions(v, t0=0, t1=None):
    """Транзакції I2C як списки фронтів SCL між START і STOP (зміна SDA при SCL=1).
    Транзакція без STOP (зависла) закінчується на останньому фронті SCL перед паузою 1 мс."""
    sda = [(t, lv) for t, lv in v.ev['SDA'] if t0 <= t <= (t1 or v.t_end)]
    starts = [t for t, lv in sda if lv == 0 and v.level_at('SCL', t) == 1]
    stops = [t for t, lv in sda if lv == 1 and v.level_at('SCL', t) == 1]
    out = []
    for st in starts:
        if out and st <= out[-1][-1]:      # repeated START усередині попередньої транзакції
            continue
        stop = min([p for p in stops if p > st] + [v.t_end])
        e = v.edges('SCL', st, stop)
        if e:
            out.append(bursts(e, 1_000_000)[0])
    return out


def period_stats(v, ch, t0, t1, level=1):
    e = v.edges(ch, t0, t1, level)
    return stats([b - a for a, b in zip(e, e[1:])])


def uart_text(vcd):
    raw = sh(f'sigrok-cli -I vcd:downsample=100 -i "{vcd}" -P uart:rx=UART_TX:baudrate=115200 '
             f'-A uart=rx-data --protocol-decoder-samplenum')
    out = []
    for l in raw.splitlines():
        rng, _, rest = l.partition(' ')
        out.append((int(rng.split('-')[0]) * 100, chr(int(rest.split()[-1], 16))))
    return out


def find_line(chars, prefix):
    s = ''.join(c for _, c in chars)
    k = s.find(prefix)
    return chars[k][0] if k >= 0 else None


def main():
    va, vb = Vcd(A), Vcd(B)
    ua = uart_text(A)

    # ---------- I2C ----------------------------------------------------
    tr = i2c_transactions(va)
    hw = tr[0]
    M['i2c_hw_attempt'] = {'t_ms': hw[0] / 1e6, 'scl_edges': len(hw),
                           'scl_period_ns': period_stats(va, 'SCL', hw[0], hw[-1])}
    p = slice_vcd(A, 'i2c_mpu6050_hw-read-stall_anomaly', hw[0] - 200_000, hw[-1] + 3_000_000, ['SCL', 'SDA'])
    decode(p, 'i2c_mpu6050_hw-read-stall_anomaly', 20, 'i2c:scl=SCL:sda=SDA', 'i2c')

    t_cap = find_line(ua, 'CAPTURE;begin')
    t_nack = find_line(ua, 'CAP;nack')
    cap_tr = [b for b in tr if t_cap < b[0] < t_nack]
    # cap i2c: WHO_AM_I (1 байт) + burst 14 байтів; cap nack: перша транзакція після рядка CAP;i2c
    t_capi2c = find_line(ua, 'CAP;i2c')
    whoami_burst = [b for b in cap_tr if b[0] < t_capi2c]
    nack = [b for b in tr if t_capi2c < b[0] < t_nack + 5_000_000][:1]
    g0, g1 = whoami_burst[0][0], whoami_burst[-1][-1]
    p = slice_vcd(A, 'i2c_mpu6050_whoami-burst14', g0 - 100_000, g1 + 100_000, ['SCL', 'SDA'])
    ann = decode(p, 'i2c_mpu6050_whoami-burst14', 20, 'i2c:scl=SCL:sda=SDA', 'i2c')
    M['i2c_soft'] = {
        'scl_period_ns': period_stats(va, 'SCL', g0, g1),
        'whoami_dur_us': (whoami_burst[0][-1] - whoami_burst[0][0]) / 1e3,
        'burst_dur_us': (whoami_burst[-1][-1] - whoami_burst[-1][0]) / 1e3,
        'gap_whoami_to_burst_us': (whoami_burst[-1][0] - whoami_burst[0][-1]) / 1e3,
        'burst_bytes': [l.split('Data read: ')[1] for l in ann if 'Data read:' in l][1:15],
    }
    if nack:
        n0, n1 = nack[0][0], nack[0][-1]
        p = slice_vcd(A, 'i2c_mpu6050_nack-0x69_anomaly', n0 - 100_000, n1 + 100_000, ['SCL', 'SDA'])
        decode(p, 'i2c_mpu6050_nack-0x69_anomaly', 20, 'i2c:scl=SCL:sda=SDA', 'i2c')
        M['i2c_nack'] = {'dur_us': (n1 - n0) / 1e3}

    # ---------- SPI ----------------------------------------------------
    cs_lows = va.pulses('CS', level=0)
    t_capspi = find_line(ua, 'CAP;spi')
    cap_cs = [c for c in cs_lows if t_nack < c[0] < t_capspi]
    s0, s1 = cap_cs[0][0], cap_cs[-1][0] + cap_cs[-1][1]
    p = slice_vcd(A, 'spi_w25q64_jedec-wren-erase-pp-read', s0 - 20_000, s1 + 20_000,
                  ['SCK', 'MOSI', 'MISO', 'CS'])
    spi_pd = 'spi:clk=SCK:mosi=MOSI:miso=MISO:cs=CS:cpol=0:cpha=0'
    mo = decode(p, 'spi_w25q64_jedec-wren-erase-pp-read', 20, spi_pd, 'spi=mosi-data')
    mi = decode(p, 'spi_w25q64_jedec-wren-erase-pp-read', 20, spi_pd, 'spi=miso-data')
    csl = [(a - 0, a + w) for a, w in Vcd(p).pulses('CS', level=0)]
    rows, k = [], 0
    for a, b in zip(mo, mi):
        t = float(a.split()[0])
        while k < len(csl) and csl[k][1] / 1e3 < t:
            k += 1
        rows.append((k, t, a.split()[-1], b.split()[-1]))
    txt = ['# spi_w25q64_jedec-wren-erase-pp-read: sigrok-cli -I vcd:downsample=20 -P ' + spi_pd,
           '# 50 МГц (20 нс/відлік); № = інтервал CS# low; час — початок байта', '#  №   час, мкс   MOSI  MISO']
    txt += [f'{n:4d} {t:11.3f}    {x}    {y}' for n, t, x, y in rows]
    open(os.path.join(CAP, 'spi_w25q64_jedec-wren-erase-pp-read.ann.txt'), 'w').write('\n'.join(txt) + '\n')
    sck = va.edges('SCK', s0, s1, 1)
    byts = bursts(sck, 1000)
    intra = [b[0] - a[-1] for a, b in zip(byts, byts[1:]) if b[0] - a[-1] < 30_000]
    M['spi'] = {
        'sck_period_ns': stats([b - a for x in byts for a, b in zip(x, x[1:])]),
        'byte_dur_ns': stats([x[-1] - x[0] for x in byts]),
        'intra_txn_gap_ns': stats(intra),
        'cs_low_us': [round(w / 1e3, 2) for _, w in cap_cs],
        'cs_gaps_us': [round((b[0] - (a[0] + a[1])) / 1e3, 1) for a, b in zip(cap_cs, cap_cs[1:])],
        'n_transactions': len(cap_cs),
    }
    # SPI до оптимізації (той самий сценарій, побайтові виклики HAL) — raw-profileA-boot.vcd
    old = os.path.join(CAP, 'raw-profileA-boot.vcd')
    if os.path.exists(old):
        vo = Vcd(old)
        bo = bursts(vo.edges('SCK', level=1), 1000)
        M['spi_before_fix'] = {'intra_txn_gap_ns': stats([b[0] - a[-1] for a, b in zip(bo, bo[1:])
                                                          if b[0] - a[-1] < 200_000])}

    # ---------- UART ---------------------------------------------------
    t_end_st = find_line(ua, 'ST;SUMMARY')
    p = slice_vcd(A, 'uart_vcp_selftest', 0, t_end_st + 6_000_000, ['UART_TX'])
    decode(p, 'uart_vcp_selftest', 100, 'uart:rx=UART_TX:baudrate=115200', 'uart=rx-data')
    tx = va.edges('UART_TX', 0, t_end_st)
    gaps = [b - a for a, b in zip(tx, tx[1:])]
    M['uart'] = {'min_edge_ns': min(gaps), 'baud_from_min_edge': round(1e9 / min(gaps)),
                 'selftest_text_ms': t_end_st / 1e6}
    open(os.path.join(CAP, 'uart_vcp_full-session.log'), 'w').write(
        ''.join(c for _, c in ua).replace('\r', ''))

    # ---------- PWM (профіль B) ---------------------------------------
    pan = vb.pulses('PWM_PAN')
    t_1000 = next(t for t, w in pan if abs(w - 1_000_000) < 100)
    t_2000_end = next(t for t, w in pan if abs(w - 2_000_000) < 100 and t > t_1000)
    p = slice_vcd(B, 'pwm_servo-pan_1000us-2000us', t_1000 - 25_000_000, t_2000_end + 70_000_000,
                  ['PWM_PAN', 'PWM_TILT'])
    decode(p, 'pwm_servo-pan_1000us-2000us', 1000, 'pwm:data=PWM_PAN', 'pwm=duty-cycle')
    M['pwm'] = {
        'pan_period_ns': period_stats(vb, 'PWM_PAN', 0, vb.t_end),
        'pan_widths_us': sorted({round(w / 1e3, 3) for _, w in pan}),
        'tilt_widths_us': sorted({round(w / 1e3, 3) for _, w in vb.pulses('PWM_TILT')}),
        'first_pulse_ms': [round(pan[0][0] / 1e6, 4), round(vb.pulses('PWM_TILT')[0][0] / 1e6, 4)],
    }

    # ---------- ADC (профіль B, службовий GPIO PB0) ---------------------
    adc = vb.pulses('PROBE_ADC')
    gaps_adc = [b[0] - a[0] for a, b in zip(adc, adc[1:])]
    k = next(i for i, g in enumerate(gaps_adc) if 9_000_000 < g < 12_000_000)    # серія cap adc (10 мс)
    serie = adc[k:k + 10]
    p = slice_vcd(B, 'adc_pot_probe-pb0_cap-adc', serie[0][0] - 2_000_000, serie[-1][0] + 2_000_000,
                  ['PROBE_ADC', 'PROBE_LOOP', 'UART_TX'])
    decode(p, 'adc_pot_probe-pb0_cap-adc', 100, 'uart:rx=UART_TX:baudrate=115200', 'uart=rx-data')
    M['adc'] = {'probe_width_ns': stats([w for _, w in adc]),
                'cap_series_period_ns': stats([b[0] - a[0] for a, b in zip(serie, serie[1:])]),
                'loop_period_ns': period_stats(vb, 'PROBE_LOOP', 0, vb.t_end)}

    # ---------- MIRROR: латентність контуру (профіль B) ----------------
    btn = vb.edges('BTN', level=0)
    loops = vb.pulses('PROBE_LOOP')
    mirror = [(t, w) for t, w in loops if w > 1_000_000]
    tilt = vb.pulses('PWM_TILT')
    first_change = next(t for t, w in tilt if w > 1_510_000)
    loop_before = max(t for t, _ in mirror if t < first_change)
    M['mirror'] = {
        'button_edges_ms': [round(t / 1e6, 4) for t in vb.edges('BTN')[:8]],
        'bounce_us': round((vb.edges('BTN')[-1] - btn[0]) / 1e3, 1) if len(vb.edges('BTN')) > 2 else 0,
        'manual_loop_width_us': stats([w for t, w in loops if w < 1_000_000])['median'] / 1e3,
        'mirror_loop_width_us': stats([w for _, w in mirror]),
        'btn_to_first_mirror_loop_ms': (mirror[0][0] - btn[0]) / 1e6,
        'loop_to_pwm_edge_ms': (first_change - loop_before) / 1e6,
        'tilt_ramp_us': [round(w / 1e3, 1) for t, w in tilt if first_change <= t < first_change + 130_000_000],
    }
    p = slice_vcd(B, 'mirror_latency_btn-loop-i2c-pwm', btn[0] - 2_000_000, first_change + 105_000_000,
                  ['PWM_TILT', 'PROBE_LOOP', 'SCL', 'SDA', 'BTN'])
    decode(p, 'mirror_latency_btn-loop-i2c-pwm', 100, 'i2c:scl=SCL:sda=SDA', 'i2c=address-read:address-write')

    json.dump(M, open(os.path.join(CAP, 'measurements.json'), 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(M, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
