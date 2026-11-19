"""Create report charts after running bgsim.py, feedsim.py, videosim.py.
Requires: pip install matplotlib
"""
import json
from pathlib import Path
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent; F=R/'figure'; F.mkdir(exist_ok=True)
def read(n): return json.loads((R/n).read_text())
def save(n): plt.tight_layout(); plt.savefig(F/n,dpi=180,bbox_inches='tight'); plt.close()
b=read('bgsim_results.json'); ss=['S1 good','S2 stress','S3 perm']; fig,ax=plt.subplots(figsize=(8,4))
for off,key,label in [(-.18,'fifo','FIFO'),(.18,'prio','Priority')]: ax.bar([i+off for i in range(3)],[b[s][key]['wasted_kb'] for s in ss],.36,label=label)
ax.set_xticks(range(3),ss); ax.set_ylabel('Wasted KB'); ax.set_title('B1 – FIFO vs priority'); ax.legend(); save('b1_wasted_kb_comparison.png')
m=b['multi']; fig,axs=plt.subplots(1,3,figsize=(12,4))
for a,k,t in zip(axs,['wasted_kb','crit_mean_latency','energy_mj'],['Wasted KB','Critical latency','Energy (mJ)']): a.bar(['FIFO','Priority'],[m['fifo'][k] or 0,m['prio'][k] or 0]); a.set_title(t)
fig.suptitle('B1 – Multi-seed comparison'); save('b1_multiseed_metrics.png')
fig,ax=plt.subplots(); ax.bar(['A','B'],[b['B2'][k]['backlog'] for k in ['A','B']]); ax.set_title('B2 – Adversarial workload backlog'); save('b2_adversarial_backlog.png')
f=read('feedsim_results.json'); miss=f['scan']['mismatches']; fig,ax=plt.subplots(); ax.bar(['Match','Miss'],[f['scan']['total']-miss,miss]); ax.set_title('B3 – Adaptive match count'); save('b3_optimum_match_rate.png')
fig,ax=plt.subplots(); ns=[x['n'] for x in f['scale']]; ax.plot(ns,[x['ex_configs'] for x in f['scale']],marker='o',label='Exact'); ax.plot(ns,[x['gr_configs'] for x in f['scale']],marker='o',label='Adaptive'); ax.legend(); ax.set_title('B3 – Search scaling'); ax.set_xlabel('Feed items'); ax.set_ylabel('Configurations'); save('b3_search_scaling.png')
v=read('videosim_results.json'); labs=[z['dev']['name'] for z in v['sample']]; xx=range(len(labs)); fig,ax=plt.subplots(figsize=(9,4)); ax.bar([i-.18 for i in xx],[z['h_cost'] for z in v['sample']],.36,label='Heuristic'); ax.bar([i+.18 for i in xx],[z['e_cost'] for z in v['sample']],.36,label='Exact'); ax.set_xticks(list(xx),labs,rotation=25,ha='right'); ax.legend(); ax.set_title('B4 – Sample device cost'); save('b4_sample_cost_comparison.png')
s=v['stat']['suboptimal']; n=v['stat']['N']; fig,ax=plt.subplots(); ax.bar(['Optimal match','Suboptimal'],[n-s,s]); ax.set_title('B4 – 3,000 profiles'); save('b4_3000_profile_summary.png')
print('Charts saved in figure/')
