"""Optional static research figure; matplotlib required, core replay has no dependencies."""
import csv
from datetime import datetime,timezone
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

p=Path('outputs/okx_20261023_debug_v0')
rows=list(csv.DictReader((p/'features.csv').open()))
t=[datetime.fromtimestamp(int(r['ts'])/1000,timezone.utc) for r in rows]
fig,ax=plt.subplots(2,1,figsize=(11,7),sharex=True,layout='constrained')
for col,label,color in [('spot_mid','Spot','navy'),('perp_mid','Perpetual','darkorange')]:
    ax[0].plot(t,[float(r[col]) for r in rows],label=label,color=color,lw=.7)
ax[0].set_ylabel('Observed mid (USDT / BTC)');ax[0].legend(loc='upper right')
ax[0].set_title('OKX BTC spot / perpetual | 23 October 2026, 00:00–02:00 UTC',loc='left')
ax[1].plot(t,[float(r['basis_bps']) for r in rows],color='teal',lw=.8)
ax[1].axhline(0,color='black',ls='--',lw=.8)
ax[1].set_ylabel('Basis (bps)');ax[1].set_xlabel('UTC exchange-time replay with 100 ms assumed feed delay')
ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M',tz=timezone.utc))
ax[1].set_title('All sampled basis values negative; V0 generated no orders',loc='left',fontsize=11)
for a in ax:
    a.grid(alpha=.2)
    a.axvspan(t[0],datetime(2026,10,23,0,30,tzinfo=timezone.utc),color='gray',alpha=.1)
fig.suptitle('REAL DATA · ENGINEERING DEBUG · NOT A PROFITABILITY TEST',fontsize=10,color='#555555')
fig.savefig(p/'basis.png',dpi=160)
plt.close(fig)
