import sys; sys.path.insert(0,'/home/claude/muster/lib')
import mlib2 as M
S=2.4; D=14.9; T=M.Track(D,92); B=112
T.impact(0,0.8); T.groove(0,S,B,'Am',0.8); T.pluck('E5',0.5,0.2,0.5,0.2); T.pluck('C5',0.9,0.2,0.5,0.2)
ch=['Dm','G','Am','F']; up=['D5','B4','E5','C6']; ba=['D2','G2','A2','F2']
for i in range(4):
    t=S*(i+1); T.whoosh(t-0.1,0.2,0.32); T.hit(t,ba[i],0.72); T.groove(t,t+S,B,ch[i],1.0)
    T.pluck(up[i],t+0.12,0.25,0.5,0.2); T.tick(t+0.3,0.12)
T.riser(S*5-0.7,S*5,0.3)
t=S*5; T.impact(t,1.0); T.crash(t,0.25,1.0); T.stab(['C4','E4','G4','C5'],t,0.13,0.6); T.groove(t,D,B,'C',0.95)
for i,n in enumerate(('C5','E5','G5','C6')): T.pluck(n,t+0.4+i*0.12,0.2,0.5,0.2)
T.write('out/musik.wav')
