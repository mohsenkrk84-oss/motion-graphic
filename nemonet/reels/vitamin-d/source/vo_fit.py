import json, subprocess, sys
segs=[(0.0,1.21),(1.54,3.20),(3.52,5.22),(5.50,7.24),(7.64,9.04),(9.20,10.84),(11.06,11.67),(12.01,15.18),(15.54,17.15),(17.40,18.81),(19.14,21.52)]
pad=0.04; gap=0.10
parts=[]; t=0; starts=[]
for s,e in segs:
    s0=max(0,s-pad); e0=e+pad
    starts.append(t); parts.append((s0,e0)); t+=e0-s0+gap
total=t-gap; target=19.45; k=max(1.0,total/target)
print("total",round(total,2),"factor",round(k,3))
starts=[x/k for x in starts]
f=[];labels=[]
for i,(s,e) in enumerate(parts):
    f.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,apad=pad_dur={gap}[p{i}]"); labels.append(f"[p{i}]")
f.append("".join(labels)+f"concat=n={len(parts)}:v=0:a=1,atempo={k:.4f},afade=t=in:d=0.02[out]")
subprocess.run(["ffmpeg","-y","-loglevel","error","-i","vo.mp3","-filter_complex",";".join(f),"-map","[out]","-ar","44100","vo_edit.wav"],check=True)
st=[round(x,3) for x in starts]
sc=[0.0, st[2]-0.15, st[4]-0.45, st[7]-0.15, st[8]-0.1, st[10]-0.1, 20.0]
tim=dict(seg_starts=st,scenes=[round(x,3) for x in sc],s1_sub=st[1],
  s3_cards=[round(st[i]-sc[2],3) for i in (4,5,6)], s5_split=round(st[9]-sc[4]-0.1,3))
json.dump(tim,open("timing.json","w"),indent=1); print(json.dumps(tim))
