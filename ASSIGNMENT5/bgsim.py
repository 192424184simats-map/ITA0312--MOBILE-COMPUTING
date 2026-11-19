"""Constraint-aware background-work scheduler simulation (Tasks B1 and B2).
One simulation tick represents one minute. Model costs are not phone measurements.
"""
import json, random
MAXW=3; BAT_MIN=20; BAT_CRIT_MIN=5; MAX_ATTEMPTS=4
BACKOFF=[1,2,4,8]; RATE={'wifi':300,'cell':120,'none':0}
PER_WORKER_CAP=150; EPK={'wifi':0.5,'cell':1.6}; CRIT_DEADLINE=6; LARGE_ON_CELL=150
class Item:
 def __init__(self,i,arrival,prio,size,sensitive=True,encrypted=True):
  self.id,self.arrival,self.prio,self.size=i,arrival,prio,size
  self.sensitive,self.encrypted=sensitive,encrypted; self.progress=0.; self.attempts=0
  self.not_before=0; self.state='new'; self.done_tick=None; self.deferred=False
def env_good(T=80): return [dict(net='wifi',bat=80,doze=False,perm=True) for _ in range(T)]
def env_stress(T=80):
 E=[]
 for t in range(T):
  net='cell'
  if 20<=t<30: net='wifi'
  if 35<=t<40: net='none'
  if t>=55: net='wifi'
  doze=10<=t<30 and t!=20
  bat=60-48*t/40 if t<40 else (12 if t<50 else min(60,12+4*(t-50)))
  E.append(dict(net=net,bat=round(bat,1),doze=doze,perm=True))
 return E
def env_perm(T=80):
 E=env_good(T)
 for t in range(T): E[t]['net']='wifi' if t%7 else 'cell'; E[t]['perm']=t<25
 return E
def env_flap(T=80,up=4,down=2):
 return [dict(net='wifi' if t%(up+down)<up else 'none',bat=80,doze=False,perm=True) for t in range(T)]
def workload_mixed(n=40,seed=7):
 r=random.Random(seed); items=[]
 for i in range(n):
  a=r.randint(0,39); x=r.random()
  prio,size=(3,r.randint(10,30)) if x<.12 else ((2,r.randint(60,200)) if x<.45 else (1,r.randint(40,120)))
  items.append(Item(i,a,prio,size,True,r.random()<.7))
 items.sort(key=lambda it:(it.arrival,it.id))
 for k,it in enumerate(items): it.id=k
 return items
def workload_A(n=40,size=120):
 return [Item(i,i,3 if i%8==7 and i>=8 else 1,20 if i%8==7 and i>=8 else size) for i in range(n)]
def workload_B(n=40):
 items=[]
 for i in range(n):
  items.append(Item(i,4,1,400) if i<8 else (Item(i,i,3,20) if i%8==7 else Item(i,i,1,40)))
 items.sort(key=lambda it:(it.arrival,it.id))
 for k,it in enumerate(items): it.id=k
 return items
def feasible(it,e,t):
 if it.sensitive and not e['perm']: return 'cancel','permission revoked'
 if it.not_before>t: return 'defer','back-off'
 if e['net']=='none': return 'defer','no network'
 crit=it.prio==3
 if e['bat']<BAT_CRIT_MIN: return 'defer','battery critical'
 if not crit:
  if e['doze']: return 'defer','Doze'
  if e['bat']<BAT_MIN: return 'defer','low battery'
  if e['net']=='cell' and it.size>LARGE_ON_CELL: return 'defer','large on metered'
 return 'ok',''
def score(it,t): return 100*(it.prio==3)+20*it.prio+(t-it.arrival)-it.size/20.
def run(items,env,mode='fifo',T=80,log_decisions=0):
 if mode not in ('fifo','prio'): raise ValueError("mode must be 'fifo' or 'prio'")
 items=[Item(i.id,i.arrival,i.prio,i.size,i.sensitive,i.encrypted) for i in items]
 m=dict(enqueued=0,deferral_decisions=0,deferred_items=0,cancelled_perm=0,cancelled_retry=0,retries=0,success=0,peak_workers=0,wasted_kb=0.,energy_mj=0.,backlog=0,kb_sent=0.)
 running=[]; queue=[]; logs=[]
 for t in range(T):
  e=env[t]
  for it in items:
   if it.arrival==t: it.state='queued'; queue.append(it); m['enqueued']+=1
  if not e['perm']:
   for it in list(queue)+list(running):
    if it.sensitive:
     if it in running: running.remove(it); m['wasted_kb']+=it.progress
     if it in queue: queue.remove(it)
     it.state='cancelled'; m['cancelled_perm']+=1
  for it in list(running):
   v,_=feasible(it,e,t)
   if v!='ok':
    running.remove(it); m['wasted_kb']+=it.progress; it.progress=0; it.attempts+=1; m['retries']+=1
    if it.attempts>=MAX_ATTEMPTS: it.state='cancelled'; m['cancelled_retry']+=1
    else: it.state='queued'; it.not_before=t+BACKOFF[min(it.attempts-1,3)]; queue.append(it)
    if not it.deferred: it.deferred=True; m['deferred_items']+=1
  order=sorted(queue,key=lambda x:(x.arrival,x.id)) if mode=='fifo' else sorted(queue,key=lambda x:-score(x,t))
  for it in order:
   v,why=feasible(it,e,t)
   if v!='ok':
    m['deferral_decisions']+=1
    if not it.deferred: it.deferred=True; m['deferred_items']+=1
    if log_decisions and len(logs)<log_decisions: logs.append((t,it.id,'DEFER',why,e['net'],e['bat']))
    continue
   slots=MAXW-1 if mode=='prio' and it.prio!=3 else MAXW
   if len(running)>=slots: continue
   queue.remove(it); running.append(it); it.state='running'
   if log_decisions and len(logs)<log_decisions: logs.append((t,it.id,'START','',e['net'],e['bat']))
  m['peak_workers']=max(m['peak_workers'],len(running))
  if running and e['net']!='none':
   share=min(PER_WORKER_CAP,RATE[e['net']]/len(running))
   for it in list(running):
    add=min(share,it.size-it.progress); it.progress+=add; m['kb_sent']+=add
    m['energy_mj']+=add*EPK[e['net']]+(0 if it.encrypted else .1*add)
    if it.progress>=it.size-1e-9:
     running.remove(it); it.state='done'; it.done_tick=t; m['success']+=1
 m['backlog']=sum(1 for it in items if it.state in ('queued','running','new') and it.arrival<T)
 crit=[it for it in items if it.prio==3]; cd=[it for it in crit if it.state=='done']
 m['crit_total']=len(crit); m['crit_delivered']=len(cd)
 m['crit_ontime']=sum(it.done_tick-it.arrival+1<=CRIT_DEADLINE for it in cd)
 m['crit_mean_latency']=round(sum(it.done_tick-it.arrival+1 for it in cd)/len(cd),2) if cd else None
 done=[it for it in items if it.state=='done']
 m['mean_latency']=round(sum(it.done_tick-it.arrival+1 for it in done)/len(done),2) if done else None
 for k in ('wasted_kb','energy_mj','kb_sent'): m[k]=round(m[k],1)
 m['useful_kb']=sum(it.size for it in done)
 m['final']='ALL DELIVERED' if m['backlog']==0 and m['cancelled_perm']+m['cancelled_retry']==0 else f"backlog={m['backlog']}, cancelled={m['cancelled_perm']+m['cancelled_retry']}"
 return m,logs
def main():
 out={}; W=workload_mixed()
 for name,E in [('S1 good',env_good()),('S2 stress',env_stress()),('S3 perm',env_perm())]:
  out[name]={}
  for mode in ('fifo','prio'): out[name][mode]=run(W,E,mode)[0]
 E=env_flap(); out['B2']={}
 for name,wl in [('A',workload_A()),('B',workload_B())]:
  m,_=run(wl,E,'prio'); m['n']=len(wl); m['total_kb']=sum(x.size for x in wl); out['B2'][name]=m
 bt=[Item(0,20,2,140),Item(1,20,1,140),Item(2,20,1,100)]
 Eb=[dict(net='cell',bat=70,doze=False,perm=t<21) for t in range(40)]
 out['boundary']={}
 for mode in ('fifo','prio'):
  m,lg=run(bt,Eb,mode,T=40,log_decisions=10); out['boundary'][mode]=m
  if mode=='prio': out['boundary_log']=lg
 multi={'fifo':[],'prio':[]}
 for sd in range(1,31):
  w=workload_mixed(seed=sd)
  for mode in multi: multi[mode].append(run(w,env_stress(),mode)[0])
 def avg(mode,k):
  v=[x[k] for x in multi[mode] if x[k] is not None]; return round(sum(v)/len(v),2) if v else None
 out['multi']={mode:{k:avg(mode,k) for k in ('wasted_kb','retries','crit_mean_latency','mean_latency','energy_mj','deferral_decisions','success')} for mode in multi}
 out['multi']['wins']=dict(wasted_lower=sum(a['wasted_kb']<b['wasted_kb'] for a,b in zip(multi['prio'],multi['fifo'])),wasted_equal=sum(a['wasted_kb']==b['wasted_kb'] for a,b in zip(multi['prio'],multi['fifo'])),wasted_higher=sum(a['wasted_kb']>b['wasted_kb'] for a,b in zip(multi['prio'],multi['fifo'])),crit_lower=sum((a['crit_mean_latency'] or 0)<(b['crit_mean_latency'] or 0) for a,b in zip(multi['prio'],multi['fifo'])),crit_higher=sum((a['crit_mean_latency'] or 0)>(b['crit_mean_latency'] or 0) for a,b in zip(multi['prio'],multi['fifo'])),seeds=30)
 out['log']=run(W,env_stress(),'prio',log_decisions=14)[1]
 with open('bgsim_results.json','w') as f: json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__': main()
