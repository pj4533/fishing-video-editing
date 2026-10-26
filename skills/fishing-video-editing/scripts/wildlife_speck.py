#!/usr/bin/env python3
"""Sky-speck tracker for a soaring bird too small for VitTrack (6-20 px in 4K, e.g. a far hawk).

Usage: wildlife_speck.py SRC START END anchors.json out_track.txt
  anchors.json: wildlife_track.py keyframes [[t_abs, x, y, w, h], ...] in 3840x2160 px.
Black-hat blob detection on bright sky (half-res), chained frame to frame from each anchor in both
directions. Output is wildlife_track.py format. Run a rolling-median outlier filter before
wildlife_reframe.py: a lost frame can extrapolate far off (seen in testing).
"""
import sys, json, subprocess, numpy as np, cv2
src,a,b=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]); kf=json.load(open(sys.argv[4])); out=sys.argv[5]
FPS=30000/1001; Wd,Hd=1920,1080; s=3840/Wd
raw=subprocess.run(["ffmpeg","-loglevel","error","-ss",f"{a:.3f}","-i",src,"-t",f"{b-a:.3f}","-vf",f"scale={Wd}:{Hd}","-pix_fmt","gray","-f","rawvideo","-"],capture_output=True).stdout
n=len(raw)//(Wd*Hd); F=np.frombuffer(raw[:n*Wd*Hd],np.uint8).reshape(n,Hd,Wd)
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11))
def cands(g):
    bh=cv2.morphologyEx(g,cv2.MORPH_BLACKHAT,k)
    bright=cv2.blur(g,(41,41))>150          # sky only
    m=((bh>14)&bright).astype(np.uint8)
    nl,lab,st,cen=cv2.connectedComponentsWithStats(m)
    c=[]
    for i in range(1,nl):
        ar=st[i,4]
        if 2<=ar<=60: c.append((cen[i][0],cen[i][1],float(bh[lab==i].max()),st[i,2],st[i,3]))
    return c
C=[cands(F[i]) for i in range(n)]
times=[a+i/FPS for i in range(n)]
# bidirectional chaining from each anchor, gate radius grows on misses
def chain(i0,x,y,step):
    res={}; miss=0; i=i0; px,py=x,y; vx=vy=0
    while 0<=i<n:
        R=25+miss*25
        best=None
        for (cx,cy,ct,w,h) in C[i]:
            d=np.hypot(cx-(px+vx),cy-(py+vy))
            if d<R and (best is None or d-ct*0.5<best[0]): best=(d-ct*0.5,cx,cy,w,h)
        if best:
            nvx,nvy=best[1]-px,best[2]-py; vx,vy=0.5*vx+0.5*nvx,0.5*vy+0.5*nvy
            px,py=best[1],best[2]; res[i]=(px,py,best[3],best[4],1); miss=0
        else:
            miss+=1; res[i]=(px+vx,py+vy,0,0,0); px,py=px+vx,py+vy
            if miss>8: break
        i+=step
    return res
kfi=[(min(n-1,max(0,int(round((t-a)*FPS)))),x/s+w/s/2,y/s+h/s/2) for t,x,y,w,h in kf]
pos={}
for j,(i0,x,y) in enumerate(kfi):
    lo=kfi[j-1][0] if j>0 else 0; hi=kfi[j+1][0] if j+1<len(kfi) else n-1
    f=chain(i0,x,y,1); bk=chain(i0,x,y,-1)
    for i,v in list(f.items())+list(bk.items()):
        if lo<=i<=hi:
            dist=abs(i-i0)
            if v[4] and (i not in pos or pos[i][1]>dist or not pos[i][0][4]): pos[i]=(v,dist)
            elif i not in pos: pos[i]=(v,dist)
with open(out,"w") as fo:
    for i in range(n):
        if i in pos:
            v=pos[i][0]; fo.write(f"{times[i]:.4f} {v[0]*s:.1f} {v[1]*s:.1f} {max(v[2],3)*s:.0f} {max(v[3],3)*s:.0f} {1.0 if v[4] else 0.0:.2f} {'ok' if v[4] else 'lost'}\n")
ok=sum(1 for i in pos if pos[i][0][4]); print(f"{n} frames, {len(pos)} covered, {ok} detected")
