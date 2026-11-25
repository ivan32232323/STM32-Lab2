"""vcdlib.py — мінімальний парсер VCD (Wokwi Logic Analyzer) і вимірювання таймінгів.

Використовується tools/la_measure.py і tools/vcd_slice.py. Без залежностей.
Час у VCD Wokwi — наносекунди ($timescale 1ns).
"""
import re


class Vcd:
    def __init__(self, path):
        self.names = {}          # id -> name
        self.order = []          # ids у порядку оголошення
        self.ev = {}             # name -> [(t_ns, level)]
        self.header = []
        t = 0
        with open(path) as f:
            in_hdr = True
            for line in f:
                s = line.strip()
                if in_hdr:
                    self.header.append(line)
                    m = re.match(r'\$var\s+wire\s+1\s+(\S+)\s+(\S+)', s)
                    if m:
                        self.names[m.group(1)] = m.group(2)
                        self.order.append(m.group(1))
                        self.ev[m.group(2)] = []
                    if s.startswith('$enddefinitions'):
                        in_hdr = False
                    continue
                if not s:
                    continue
                if s[0] == '#':
                    t = int(s[1:])
                elif s[0] in '01' and s[1:] in self.names:
                    name = self.names[s[1:]]
                    lst = self.ev[name]
                    v = int(s[0])
                    if lst and lst[-1][1] == v:
                        continue
                    if lst and lst[-1][0] == t:
                        lst[-1] = (t, v)
                    else:
                        lst.append((t, v))
        self.t_end = t

    def edges(self, name, t0=0, t1=None, level=None):
        """Моменти фронтів (level=1 — наростаючі, 0 — спадаючі, None — усі)."""
        t1 = self.t_end if t1 is None else t1
        out = []
        prev = None
        for t, v in self.ev[name]:
            if prev is not None and t0 <= t <= t1 and (level is None or v == level):
                out.append(t)
            prev = v
        return out

    def level_at(self, name, t):
        v = None
        for a, b in self.ev[name]:
            if a > t:
                break
            v = b
        return v

    def pulses(self, name, t0=0, t1=None, level=1):
        """[(t_start, width)] імпульсів заданого рівня у вікні."""
        t1 = self.t_end if t1 is None else t1
        out, start = [], None
        for t, v in self.ev[name]:
            if t < t0 or t > t1:
                continue
            if v == level:
                start = t
            elif start is not None:
                out.append((start, t - start))
                start = None
        return out


def bursts(times, gap_ns):
    """Розбити послідовність моментів на «пачки», розділені паузою > gap_ns."""
    out, cur = [], []
    for t in times:
        if cur and t - cur[-1] > gap_ns:
            out.append(cur)
            cur = []
        cur.append(t)
    if cur:
        out.append(cur)
    return out


def stats(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return {'n': n, 'min': xs[0], 'max': xs[-1], 'median': xs[n // 2], 'mean': sum(xs) / n}
