"""Heuristic vs exhaustive video encoding/upload strategy (Task B4)."""
import random,json
CLIP_S=15
RES={'360p':dict(px=1.0,q=40),'480p':dict(px=1.8,q=55),'720p':dict(px=4.0,q=75),'1080p':dict(px=9.0,q=90)}
BR={'360p':[500,800,1200],'480p':[900,1400,2000],'720p':[1800,2800,4000],'1080p':[3500,5500,8000]}
BRADJ=[-8,0,5]; P_ENC=1.5; P_RADIO={'wifi':.8,'4g':2.2,'5g':2.6}
TIMING=['now','wait_wifi','wait_charge']; DELAY={'now':0,'wait_wifi':1800,'wait_charge':3600}; WIFI_MBPS=20.
ENC_TIME_MAX=12.; UP_TIME_MAX=20.; IMPACT_CAP=.12; IMPACT_CAP_LOW=.06; LOW_BAT=15
def evaluate(dev,res,bi,timing):
 px=RES[res]['px']; enc_t=CLIP_S*px*.25/dev['cpu']; br=BR[res][bi]; size_mb=br*CLIP_S/8000.
 net=dev['net']; bw=dev['mbps']
 if timing=='wait_wifi': net,bw='wifi',WIFI_MBPS
 up_t=size_mb*8/bw; e_j=enc_t*P_ENC+up_t*P_RADIO[net]
 impact=0. if timing=='wait_charge' else e_j/(dev['cap_mah']*3.85*3.6)*100
 quality=RES[res]['q']+BRADJ[bi]; latency=DELAY[timing]+enc_t+up_t
 return dict(enc_t=enc_t,up_t=up_t,size_mb=size_mb,energy_j=e_j,impact=impact,quality=quality,latency=latency,net=net)
def cost(dev,ev):
 bf=1. if dev['bat']>=50 else (2. if dev['bat']>=20 else 4.)
 return (100-ev['quality'])+.02*ev['latency']+600*ev['impact']*bf
def exact(dev):
 best=None; n=0
 for res in RES:
  for bi in range(3):
   for tm in TIMING:
    if tm=='wait_wifi' and dev['net']=='wifi': continue
    ev=evaluate(dev,res,bi,tm); n+=1; c=cost(dev,ev)
    if best is None or c<best[0]: best=(c,res,bi,tm,ev)
 return best,n
def heuristic(dev):
 if dev['bat']<LOW_BAT and not dev.get('charging'): timing='wait_charge'
 elif dev['net']!='wifi' and dev['mbps']<5: timing='wait_wifi'
 else: timing='now'
 cap=IMPACT_CAP_LOW if dev['bat']<30 else IMPACT_CAP; chosen=None
 for res in ['1080p','720p','480p','360p']:
  ev0=evaluate(dev,res,0,timing)
  if ev0['enc_t']<=ENC_TIME_MAX:
   for bi in (2,1,0):
    ev=evaluate(dev,res,bi,timing)
    if ev['up_t']<=UP_TIME_MAX and (timing=='wait_charge' or ev['impact']<=cap): chosen=(res,bi,timing,ev); break
  if chosen: break
 return chosen or ('360p',0,timing,evaluate(dev,'360p',0,timing))
def heuristic2(dev):
 if dev['bat']<35 and not dev.get('charging'): timing='wait_charge'
 elif dev['net']!='wifi' and dev['mbps']<5: timing='wait_wifi'
 else: timing='now'
 cap=IMPACT_CAP_LOW if dev['bat']<50 else IMPACT_CAP; enc_cap=60. if timing=='wait_charge' else ENC_TIME_MAX
 for res in ['1080p','720p','480p','360p']:
  ev0=evaluate(dev,res,0,timing)
  if ev0['enc_t']<=enc_cap:
   for bi in (2,1,0):
    ev=evaluate(dev,res,bi,timing)
    if ev['up_t']<=(40. if timing=='wait_charge' else UP_TIME_MAX) and (timing=='wait_charge' or ev['impact']<=cap): return res,bi,timing,ev
 return '360p',0,timing,evaluate(dev,'360p',0,timing)
SAMPLE=[
 dict(name='D1 flagship, Wi-Fi',cpu=3.,bat=85,net='wifi',mbps=40,cap_mah=5000),
 dict(name='D2 flagship, 5G',cpu=3.,bat=60,net='5g',mbps=35,cap_mah=4500),
 dict(name='D3 mid-range, 4G',cpu=1.6,bat=55,net='4g',mbps=12,cap_mah=5000),
 dict(name='D4 mid-range, weak 4G',cpu=1.6,bat=40,net='4g',mbps=3,cap_mah=4500),
 dict(name='D5 low-end, 4G',cpu=.8,bat=70,net='4g',mbps=8,cap_mah=4000),
 dict(name='D6 low-end, low battery',cpu=.8,bat=12,net='4g',mbps=8,cap_mah=3500),
 dict(name='D7 mid-range, 25% battery',cpu=1.6,bat=25,net='4g',mbps=10,cap_mah=4000),
 dict(name='D8 flagship, weak 4G',cpu=3.,bat=75,net='4g',mbps=2,cap_mah=5000)]
def random_device(r):
 net=r.choice(['wifi','4g','4g','5g'])
 mbps={'wifi':r.choice([10,20,40,80]),'4g':r.choice([1.5,3,6,12,25]),'5g':r.choice([20,40,80])}[net]
 return dict(name='rand',cpu=r.choice([.6,.8,1.2,1.6,2.2,3.]),bat=r.choice([8,12,18,25,35,50,70,90]),net=net,mbps=mbps,cap_mah=r.choice([3000,3500,4000,4500,5000]))
def main():
 out={'sample':[],'ex_cfgs':0}
 for d in SAMPLE:
  h=heuristic(d); (c,res,bi,tm,ev),n=exact(d); hc=cost(d,h[3])
  out['sample'].append(dict(dev=d,h=dict(res=h[0],br=BR[h[0]][h[1]],timing=h[2],**h[3]),h_cost=round(hc,2),e=dict(res=res,br=BR[res][bi],timing=tm,**ev),e_cost=round(c,2),n=n))
 r=random.Random(2024); sub=0; gaps=[]; worst=None; N=3000
 for _ in range(N):
  d=random_device(r); h=heuristic(d); hc=cost(d,h[3]); (c,res,bi,tm,ev),_=exact(d)
  if hc>c+1e-9:
   sub+=1; g=hc-c; gaps.append(g)
   if worst is None or g>worst[0]: worst=(g,d,h,(res,bi,tm,ev),hc,c)
 g,d,h,e,hc,c=worst
 out['stat']=dict(N=N,suboptimal=sub,mean_gap=sum(gaps)/len(gaps),max_gap=max(gaps))
 out['worst']=dict(dev=d,h=dict(res=h[0],br=BR[h[0]][h[1]],timing=h[2],**h[3]),h_cost=round(hc,2),e=dict(res=e[0],br=BR[e[0]][e[1]],timing=e[2],**e[3]),e_cost=round(c,2))
 with open('videosim_results.json','w') as f: json.dump(out,f,indent=2)
 for s in out['sample']: print(s['dev']['name'],'| heuristic:',s['h']['res'],s['h']['br'],s['h']['timing'],'cost',s['h_cost'],'| exact:',s['e']['res'],s['e']['br'],s['e']['timing'],'cost',s['e_cost'])
 print(out['stat']); print(out['worst'])
if __name__=='__main__': main()
