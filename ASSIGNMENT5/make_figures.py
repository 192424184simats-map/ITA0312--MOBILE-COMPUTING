"""Generate charts in figure/ from the simulator JSON outputs.
Run after bgsim.py, feedsim.py and videosim.py. Requires matplotlib.
"""
import json
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent; FIG=ROOT/'figure'; FIG.mkdir(exist_ok=True)
def load(name): return json.loads((ROOT/name).read_text())
def save(name): plt.tight_layout(); plt.savefig(FIG/name,dpi=180,bbox_inches='tight'); plt.close()
b=load('bgsim_results.json'); scenarios=['S1 good','S2 stress','S3 perm']; x=range(3); w=.36
fig,ax=plt.subplots(figsize=(8,4.5))
for off,mode,label in [(-w/2,'fifo','FIFO'),(w/2,'prio','Priority')]: ax.bar([i+off for i in x],[b[s][mode]['wasted_kb'] for s in scenarios],w,label=label)
ax.set_xticks(list(x),scenarios); ax.set_ylabel('Wasted upload data (KB)'); ax.set_title('B1 – FIFO vs priority scheduling'); ax.legend(); save('b1_wasted_kb_comparison.png')
m=b['multi']; fig,axes=plt.subplots(1,3,figsize=(12,4))
for ax,key,title in zip(axes,['wasted_kb','crit_mean_latency','energy_mj'],['Wasted KB','Critical latency (ticks)','Energy (mJ)']):
 ax.bar(['FIFO','Priority'],[m['fifo'][key] or 0,m['prio'][key] or 0]); ax.set_title(title); ax.set_ylabel(title)
fig.suptitle('B1 – 30-seed average comparison'); save('b1_multiseed_metrics.png')
fig,ax=plt.subplots(figsize=(7,4.5)); ax.bar(['A','B'],[b['B2'][k]['backlog'] for k in ['A','B']]); ax.set_ylabel('Unfinished items'); ax.set_title('B2 – Adversarial workload comparison'); save('b2_adversarial_backlog.png')
f=load('feedsim_results.json'); n=f['scan']['total']; miss=f['scan']['mismatches']
fig,ax=plt.subplots(figsize=(7,4.5)); ax.bar(['Matches optimum','Misses optimum'],[n-miss,miss]); ax.set_ylabel('Instances (out of 200)'); ax.set_title('B3 – Adaptive search agreement'); save('b3_optimum_match_rate.png')
fig,ax=plt.subplots(figsize=(8,4.5)); ns=[r['n'] for r in f['scale']]
ax.plot(ns,[r['ex_configs'] for r in f['scale']],marker='o',label='Exact'); ax.plot(ns,[r['gr_configs'] for r in f['scale']],marker='o',label='Adaptive')
ax.set_xlabel('Number of feed items'); ax.set_ylabel('Configurations evaluated (average)'); ax.set_title('B3 – Search effort scaling'); ax.legend(); save('b3_search_scaling.png')
v=load('videosim_results.json'); fig,ax=plt.subplots(figsize=(9,4.5)); labels=[r['dev']['name'].replace(', ','\n') for r in v['sample']]; pos=list(range(len(labels)))
ax.bar([i-.18 for i in pos],[r['h_cost'] for r in v['sample']],.36,label='Heuristic'); ax.bar([i+.18 for i in pos],[r['e_cost'] for r in v['sample']],.36,label='Exact')
ax.set_xticks(pos,labels,rotation=25,ha='right'); ax.set_ylabel('Model cost (lower is better)'); ax.set_title('B4 – Heuristic vs exhaustive sample'); ax.legend(); save('b4_sample_cost_comparison.png')
sub=v['stat']['suboptimal']; total=v['stat']['N']; fig,ax=plt.subplots(figsize=(6,4.5)); ax.bar(['Optimal match','Suboptimal'],[total-sub,sub]); ax.set_ylabel('Random profiles'); ax.set_title('B4 – Heuristic over 3,000 profiles'); save('b4_3000_profile_summary.png')
print('Charts generated in',FIG)
