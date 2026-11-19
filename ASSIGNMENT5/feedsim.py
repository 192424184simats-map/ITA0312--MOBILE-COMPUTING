"""Exact vs adaptive configuration search for a scrolling media feed (Task B3)."""
import random,json,time
from collections import OrderedDict
FRAME_BUDGET=16.; BASE_FRAME=5.; W_DROP=10.; W_QUAL=.5; W_MEM=.002
def dq(q): return 2.*(1.5**q)
def eq(q): return 1.*(1.4**q)
def make_instance(seed,n=60,dev_slow=None,battery=None):
 r=random.Random(seed); comp=[r.choice([.6,.8,1.,1.2,1.6,2.2]) for _ in range(n)]; seq=[]; i=0
 while i<n:
  seq.append(i)
  if r.random()<.15 and i>=3: i-=r.randint(1,3)
  else: i+=1
 slow=dev_slow if dev_slow is not None else r.choice([1.,1.3,1.7,2.2])
 batt=battery if battery is not None else r.choice([15,30,55,85])
 return dict(n=n,comp=comp,seq=seq,slow=slow,batt=batt,seed=seed)
def lam(batt): return min(3.,max(1.,1+(50-batt)/25.))
QMAX_G=3
def simulate(inst,cfg,counters=None):
 q,c,p=cfg; comp,seq,slow=inst['comp'],inst['seq'],inst['slow']; cache=OrderedDict()
 drops=0; energy=0.; evictions=0; decodes=0
 def insert(j):
  nonlocal evictions
  cache[j]=True; cache.move_to_end(j)
  while len(cache)>c: cache.popitem(last=False); evictions+=1
 for i in seq:
  if i in cache: cache.move_to_end(i); ft=BASE_FRAME
  else: ft=BASE_FRAME+comp[i]*dq(q)*slow; energy+=comp[i]*eq(q); decodes+=1; insert(i)
  if ft>FRAME_BUDGET: drops+=1
  for j in range(i+1,min(i+1+p,inst['n'])):
   if j not in cache: energy+=comp[j]*eq(q); decodes+=1; insert(j)
 frames=len(seq); energy+=W_MEM*c*frames
 cost=W_DROP*drops+lam(inst['batt'])*energy/10.+W_QUAL*((QMAX_G-q)*frames)
 if counters is not None:
  counters['evictions']+=evictions; counters['decodes']+=decodes; counters['frame_steps']+=frames
 return cost,drops,energy
def exact(inst,Q,C,P):
 global QMAX_G
 QMAX_G=Q-1; cnt=dict(evictions=0,decodes=0,frame_steps=0,configs=0); best=None
 for q in range(Q):
  for c in range(1,C+1):
   for p in range(P+1):
    cost,d,e=simulate(inst,(q,c,p),cnt); cnt['configs']+=1
    if best is None or cost<best[0]-1e-12: best=(cost,(q,c,p),d,e)
 return best,cnt
def greedy(inst,Q,C,P,start=None,geometric=True):
 global QMAX_G
 QMAX_G=Q-1; cnt=dict(evictions=0,decodes=0,frame_steps=0,configs=0,q_changes=0,steps=0)
 cur=start or (Q-1,1,0); cost,d,e=simulate(inst,cur,cnt); cnt['configs']+=1; path=[(cur,round(cost,2))]
 while True:
  best=None; q,c,p=cur
  moves=[(q-1,c,p),(q+1,c,p),(q,c-1,p),(q,c+1,p),(q,c,p-1),(q,c,p+1)]
  if geometric: moves += [(q,min(C,2*c),p),(q,max(1,c//2),p),(q,C,p)]
  seen=set()
  for nb in moves:
   if nb in seen or nb==cur or not(0<=nb[0]<Q and 1<=nb[1]<=C and 0<=nb[2]<=P): continue
   seen.add(nb); nc,nd,ne=simulate(inst,nb,cnt); cnt['configs']+=1
   if best is None or nc<best[0]: best=(nc,nb,nd,ne)
  if best is not None and best[0]<cost-1e-12:
   if best[1][0]!=cur[0]: cnt['q_changes']+=1
   cur,cost,d,e=best[1],best[0],best[2],best[3]; cnt['steps']+=1; path.append((cur,round(cost,2)))
  else: break
 return (cost,cur,d,e),cnt,path
def main():
 out={}
 small=[]
 for seed in (101,102,103):
  inst=make_instance(seed); (ec,ecfg,ed,ee),ecnt=exact(inst,4,5,4); (gc,gcfg,gd,ge),gcnt,path=greedy(inst,4,5,4)
  small.append(dict(seed=seed,slow=inst['slow'],batt=inst['batt'],exact_cost=round(ec,2),exact_cfg=ecfg,exact_drops=ed,greedy_cost=round(gc,2),greedy_cfg=gcfg,greedy_drops=gd,match=abs(ec-gc)<1e-9,path=path,ex_configs=ecnt['configs'],gr_configs=gcnt['configs']))
 out['small']=small; mism=[]; gaps=[]
 for seed in range(200,400):
  inst=make_instance(seed); (ec,ecfg,_,_),_=exact(inst,4,5,4); (gc,gcfg,_,_),_,_=greedy(inst,4,5,4)
  if gc>ec+1e-9: mism.append((seed,ec,gc,ecfg,gcfg)); gaps.append((gc-ec)/abs(ec))
 ma=0
 for seed in range(200,400):
  inst=make_instance(seed); (ec,_,_,_),_=exact(inst,4,5,4); (gc,_,_,_),_,_=greedy(inst,4,5,4,geometric=False); ma+=gc>ec+1e-9
 out['scan_additive_mismatch']=ma; out['scan']=dict(total=200,mismatches=len(mism),mean_gap=sum(gaps)/len(gaps) if gaps else 0,max_gap=max(gaps) if gaps else 0)
 if mism:
  mism.sort(key=lambda x:-(x[2]-x[1])/abs(x[1])); seed=mism[0][0]; inst=make_instance(seed)
  (ec,ecfg,ed,ee),_=exact(inst,4,5,4); (gc,gcfg,gd,ge),_,path=greedy(inst,4,5,4)
  out['counter']=dict(seed=seed,slow=inst['slow'],batt=inst['batt'],exact_cost=round(ec,2),exact_cfg=ecfg,exact_drops=ed,greedy_cost=round(gc,2),greedy_cfg=gcfg,greedy_drops=gd,path=path)
  q,c,p=gcfg; nbs=[]
  for nb in [(q-1,c,p),(q+1,c,p),(q,c-1,p),(q,c+1,p),(q,c,p-1),(q,c,p+1)]:
   if 0<=nb[0]<4 and 1<=nb[1]<=5 and 0<=nb[2]<=4:
    nc,_,_=simulate(inst,nb); nbs.append((nb,round(nc,2)))
  out['counter']['final_neighbours']=nbs
  out['counter']['mismatch_list']=[(a,round(b,2),round(cc,2),d,e) for a,b,cc,d,e in mism[:6]]
 scale=[]
 for (n,Q,C,P,seeds) in [(100,4,6,5,5),(200,6,10,8,5),(400,8,16,12,3)]:
  rec=dict(n=n,Q=Q,C=C,P=P,grid=Q*C*(P+1),ex_configs=0,gr_configs=0,ex_decodes=0,gr_decodes=0,ex_evict=0,gr_evict=0,ex_steps=0,gr_steps=0,gr_qchg=0,gaps=[],matches=0,ex_time=0.,gr_time=0.)
  for s in range(seeds):
   inst=make_instance(1000+s,n=n); t0=time.time(); (ec,ecfg,_,_),ecnt=exact(inst,Q,C,P); t1=time.time(); (gc,gcfg,_,_),gcnt,path=greedy(inst,Q,C,P); t2=time.time()
   for key in ('configs',): rec['ex_configs']+=ecnt[key]; rec['gr_configs']+=gcnt[key]
   for key1,key2 in [('decodes','ex_decodes'),('evictions','ex_evict'),('frame_steps','ex_steps')]: rec[key2]+=ecnt[key1]
   for key1,key2 in [('decodes','gr_decodes'),('evictions','gr_evict'),('frame_steps','gr_steps'),('q_changes','gr_qchg')]: rec[key2]+=gcnt[key1]
   rec['gaps'].append((gc-ec)/abs(ec)*100); rec['matches']+=abs(gc-ec)<1e-9
   rec['ex_time']+=t1-t0; rec['gr_time']+=t2-t1
  rec['seeds']=seeds
  for k in ('ex_configs','gr_configs','ex_decodes','gr_decodes','ex_evict','gr_evict','ex_steps','gr_steps','gr_qchg'): rec[k]/=seeds
  rec['mean_gap']=sum(rec['gaps'])/seeds; rec['max_gap']=max(rec['gaps']); rec['ex_time']/=seeds; rec['gr_time']/=seeds; scale.append(rec)
  print('scaled',n,Q,C,P,round(rec['ex_time'],1),'s',flush=True)
 out['scale']=scale
 with open('feedsim_results.json','w') as f: json.dump(out,f,indent=2,default=str)
 print(json.dumps(out['small'],indent=2)); print(out['scan']); print(json.dumps(out.get('counter'),indent=2))
 for s in scale: print({k:(round(v,2) if isinstance(v,float) else v) for k,v in s.items() if k!='gaps'})
if __name__=='__main__': main()
