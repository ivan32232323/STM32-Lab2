# Побудова графіка з wokwi.vcd (Wokwi Logic Analyzer): python3 tools/vcd_plot.py wokwi.vcd out.png
import sys, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
names={'!':'D0 SCL (PB8)','"':'D1 SDA (PB9)','#':'D2 PWM pan (PA6)','$':'D3 UART TX (PA2)'}
ev={k:[] for k in names}; t=0
for l in open(sys.argv[1]):
    l=l.strip()
    if l.startswith('#'): t=int(l[1:])
    elif len(l)==2 and l[1] in names: ev[l[1]].append((t,int(l[0])))
def series(k,t0,t1):
    xs=[];ys=[];last=None
    for tt,v in ev[k]:
        if tt<t0: last=v; continue
        if tt>t1: break
        if last is not None: xs.append((tt-t0)/1e3); ys.append(last)
        xs.append((tt-t0)/1e3); ys.append(v); last=v
    if last is not None: xs.append((t1-t0)/1e3); ys.append(last)
    return xs,ys
# знайти soft-I2C WHO_AM_I: перший старт SDA після довгої паузи після сканування
sda=[tt for tt,v in ev['"'] if v==0]
scl=ev['!']
# беремо останній блок активності SCL до ~1.6 с: шукаємо пакет з 0xD0 0x75
t_i2c=None
# простий підхід: знайти найбільшу паузу між фронтами SCL у перші 2 с і взяти наступний пакет
edges=[tt for tt,v in scl if tt<3e9]
gaps=[(edges[i+1]-edges[i],edges[i+1]) for i in range(len(edges)-1)]
cands=sorted([g for g in gaps if g[0]>3e6],key=lambda x:x[1])
# перший кадр програмного I2C (WHO_AM_I): SCL-імпульси 20 мкс..2 мс
t_i2c=None
for (a,va),(b,vb) in zip(scl,scl[1:]):
    if va==1 and 20e3<b-a<2e6 and a>1.3e9: t_i2c=a; break
fig,ax=plt.subplots(2,1,figsize=(13,6.5))
# кінець кадру: наступна пауза SCL > 2 мс
end=[e for e in edges if e>t_i2c]
t1=t_i2c
for a,b in zip(end,end[1:]):
    t1=b
    if b-a>2e6: t1=a; break
t0=t_i2c-300e3; t1=t1+300e3
t1=min(t1,t0+9e6)
# декодування байтів кадру
bits=[];sc=1;sd=1;frames=[];cur=[]
allev=sorted([(tt,'!',v) for tt,v in scl]+[(tt,'"',v) for tt,v in ev['"']])
for tt,k,v in allev:
    if tt<t0 or tt>t1: 
        if k=='!': sc=v
        else: sd=v
        continue
    if k=='!':
        if v==1: cur.append(sd)
        sc=v
    else:
        if sc==1 and v==0: cur=[]; frames.append('S')
        if sc==1 and v==1: frames.append(cur); frames.append('P'); cur=[]
        sd=v
dec=[]
for f in frames:
    if isinstance(f,list):
        for i in range(0,len(f)-8,9): dec.append('0x%02X%s'%(int(''.join(map(str,f[i:i+8])),2),'' if f[i+8]==0 else '(NACK)'))
print('decoded',frames[:3],dec)
for i,k in enumerate(['!','"']):
    x,y=series(k,t0,t1); ax[0].plot(x,[v*0.8+ (1-i)*1.2 for v in y],drawstyle='steps-post',lw=1.1)
ax[0].set_yticks([1.6,0.4]); ax[0].set_yticklabels([names['!'],names['"']])
ax[0].set_xlabel('мкс від початку вікна'); ax[0].set_title('I²C1 PB8/PB9 (програмний fallback): транзакція WHO_AM_I до MPU-6050 @0x68 — Wokwi Logic Analyzer')
pw=[tt for tt,v in ev['#'] if v==1]
p0=pw[len(pw)//2]-2e6; p1=p0+60e6
x,y=series('#',p0,p1); ax[1].plot([v/1e3 for v in x],y,drawstyle='steps-post',color='tab:red')
ax[1].set_yticks([0,1]); ax[1].set_xlabel('мс'); ax[1].set_title(names['#']+': PWM 50 Гц (період 20 мс, імпульс 1–2 мс)')
for a in ax: a.grid(alpha=.3)
plt.tight_layout(); plt.savefig(sys.argv[2],dpi=110)
hi=[];lo=[]
for i in range(len(ev['#'])-2):
    (a,va),(b,vb),(c,vc)=ev['#'][i:i+3]
    if va==1: hi.append(b-a); 
print('t_i2c',t_i2c/1e6,'ms; PWM high widths (us):',sorted(set(round(h/1e3) for h in hi))[:10])
