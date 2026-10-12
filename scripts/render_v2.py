"""V2: GPT-image key poses + deterministic 2D animation, source PTS/audio unchanged.

python scripts/render_v2.py --preview
python scripts/render_v2.py --render
"""
from pathlib import Path
from functools import lru_cache
import argparse,bisect,json,math,random,subprocess,time
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import render_v1 as B

R=B.ROOT;W,H=B.W,B.H;BG=B.BG;INK=B.INK;MINT=B.MINT;GOLD=B.GOLD;DARK=B.DARK
DATA=json.loads((R/'timeline_v2.json').read_text());FRAMES=DATA['frames'];TIMES=[e['time'] for e in FRAMES]
SP=B.SP;OUT=R/'output';SOURCE=B.SOURCE
MAN={m['name']:m for m in json.loads((R/'assets/manifest_v2.json').read_text())}

@lru_cache(maxsize=80)
def jpfont(size):
 f=ImageFont.truetype(str(R/'assets/NotoSansJP.ttf'),int(size))
 try:f.set_variation_by_axes([750])
 except Exception:pass
 return f

@lru_cache(maxsize=350)
def jpimage(s,size,fill=INK,stroke=0,outline=BG):
 f=jpfont(size);bb=f.getbbox(s,stroke_width=stroke);im=Image.new('RGBA',(bb[2]-bb[0]+16,bb[3]-bb[1]+16),(0,0,0,0))
 ImageDraw.Draw(im).text((8-bb[0],8-bb[1]),s,font=f,fill=fill,stroke_width=stroke,stroke_fill=outline)
 return im

def jp(im,s,x,y,size=40,fill=INK,center=False,maxwidth=None,stroke=0,outline=BG):
 sp=jpimage(s,size,fill,stroke,outline)
 if maxwidth and sp.width>maxwidth:sp=sp.resize((int(maxwidth),round(sp.height*maxwidth/sp.width)),Image.Resampling.LANCZOS)
 im.paste(sp,(round(x-sp.width/2 if center else x),round(y)),sp)
 return sp.width,sp.height

def callout(im,s,cx,y,burst=False,size=31):
 """Single vocal/action caption above Firefly, never a two-person chat UI."""
 lab=jpimage(s,size);bw=max(82,lab.width+28);bh=lab.height+20
 cx=max(bw/2+12,min(W-bw/2-12,cx));y=max(8,min(610,y));d=ImageDraw.Draw(im)
 if burst:
  points=[]
  for k in range(26):
   a=k*math.tau/26;r=1 if k%2==0 else .85;points.append((cx+math.cos(a)*bw/2*r,y+bh/2+math.sin(a)*bh/2*r))
  d.polygon(points,fill=BG,outline=INK,width=3)
 else:d.rounded_rectangle((cx-bw/2,y,cx+bw/2,y+bh),radius=19,fill=BG,outline=INK,width=3)
 im.paste(lab,(round(cx-lab.width/2),round(y+(bh-lab.height)/2)),lab)

def native(im,name,cx,foot,scale=1.2,angle=0,mirror=False,anchor='bottom'):
 return B.actor(im,name,cx,foot,SP[name].height*scale,anchor,angle,mirror)

def marks(im,x,y,t,color=MINT,amount=3):
 d=ImageDraw.Draw(im)
 for i in range(amount):
  a=math.tau*i/max(1,amount)+.1;rad=23+4*math.sin(t*9+i);d.line((x+math.cos(a)*rad,y+math.sin(a)*rad,x+math.cos(a)*(rad+13),y+math.sin(a)*(rad+13)),fill=color,width=4)

def chew_index(t):
 q=(t-112.879)%3.536
 boundaries=[.15,.30,.56,.80,1.06,1.30,1.58,1.82,2.08,2.34,2.60,2.92,3.15,3.35,3.536]
 frames=[0,1,2,3,4,3,2,4,3,2,4,5,6,7,5]
 return frames[min(bisect.bisect_right(boundaries,q),len(frames)-1)]

@lru_cache(maxsize=16)
def bin_anchor(name,mirror=False):
 a=np.array(SP[name]);m=(a[:,:,3]>100)&(np.max(a[:,:,:3],2)-np.min(a[:,:,:3],2)<14)&(a[:,:,0]>65)&(a[:,:,0]<192)
 m[:int(a.shape[0]*.44)]=False
 yy,xx=np.nonzero(m)
 if len(xx):x=float(np.median(xx));bottom=float(np.percentile(yy,99))
 else:x=SP[name].width*.67;bottom=SP[name].height-8
 if mirror:x=SP[name].width-x
 return x,bottom

def bin_actor(im,name,t,scale=1.42,x=338,foot=744):
 mirror=name=='bin1';src=SP[name];ax,ay=bin_anchor(name,mirror)
 sp=B.resized(name,round(src.height*scale/4)*4,0,mirror);factor=sp.height/src.height
 px=round(x-ax*factor);py=round(foot-ay*factor)
 im.paste(sp,(px,py),sp)

def stelle(im,e,mini=False):
 t=e['time'];start=37.070
 if t<38.15:name='bin0'
 elif t<38.65:name='bin1'
 elif t<39.05:name='bin6'
 else:
  cycle=['bin2','bin3','bin2','bin4','bin2','bin3','bin5','bin7']
  name=cycle[int((t-start)/.72)%len(cycle)]
 if 43.0<t<43.55 or 54.25<t<54.85 or 61.8<t<62.3:name='bin6'
 if 116.8<t<117.5:name='bin4'
 if 134.3<t<135.1:name='bin6'
 if 135.1<=t<136.5:name='bin7'
 if e.get('run_direction')=='left' and t-e.get('run_onset',t)<.2:name='bin6'
 bin_actor(im,name,t,.58 if mini else 1.42,130 if mini else 338,714 if mini else 744)

def kafka(im,t):
 if not 116.4<=t<149.7:return
 # Source piano enters from the LEFT and drifts behind the two foreground actors.
 x=-90+(t-116.4)*42.0;y=242+6*math.sin((t-116.4)*.65)
 name=['kafka0','kafka1','kafka2','kafka1','kafka3','kafka1'][int((t-116.4)*6)%6]
 B.actor(im,name,x,y,216,'center')
 d=ImageDraw.Draw(im)
 for j in range(2):
  xx=x+20+j*37;yy=y-130-6*math.sin(t*2+j);jp(im,'♪',xx,yy,23,INK)

def keyboard(im,t):
 # A short cutout tap loop, using a drawn seated Firefly behind a simple keyboard.
 shift=[0,-3,0,3][int((t-71.004)*10)%4];B.actor(im,'camera_seated',948,649+shift,329)
 d=ImageDraw.Draw(im);d.rectangle((841,525,1068,566),fill='#f5f2e8',outline=INK,width=3)
 for j in range(15):d.line((843+j*15,525,843+j*15,553),fill=INK,width=1)
 for j in [1,2,4,5,7,8,10,11,13]:d.rectangle((840+j*15,525,845+j*15,542),fill=INK)
 d.line((862,566,852,650),fill=INK,width=4);d.line((1047,566,1057,650),fill=INK,width=4)
 callout(im,'タカタカ',949,269)

def verse_pose(p,t):
 n=p['sprite']
 if 37.07<=t<39.55:return 'bow','失礼します',False
 if 42.12<=t<42.98:return 'jyan','ジャーン',True
 if 42.98<=t<43.84:return 'den','でーん',True
 if 44.75<=t<45.7:return 'confused','ん？',False
 if 45.7<=t<47.65:return ('walk0' if int(t*7)%2 else 'walk1'),'てくてく',False
 if 47.65<=t<48.45:return 'turnwave','え〜い！',False
 if 48.45<=t<49.4:return 'point','ね〜え',False
 if 49.4<=t<50.2:return 'oh','ねえってば',False
 if 50.2<=t<50.95:return 'starjump','やっ',True
 if 56.9<=t<57.88:return 'nico0','にへへへ',False
 if 57.88<=t<58.65:return 'sun0','ふぅ',False
 mapped={'arrival':('clap1','しゅた',True),'cheer':('jyan','ジャーン',True),'idea':('kira0','ぎゅん',True),'point':('tatan','タタン',True),'walk_a':('walk0','てくてく',False),'walk_b':('walk1','てくてく',False),'profile':('turnwave','ちょっ',False),'turn':('starjump','しゅた',True),'float':('den','でーん',True),'flail':('bata0','ばたばた',True),'surprise':('oh','おっ',False),'confused':('confused','ん？',False),'bashful':('nico1','にへへ',False),'bow':('bow','失礼します',False),'run_a':('run0','ザカザカ',False),'run_b':('run2','ザカザカ',False),'offer_cake':('tatan','タタン',True),'camera_seated':('camera_seated','タカタカ',False),'photo':('photo','パシャ',True),'cake_a':('chew2','もぐもぐ',False),'cake_b':('chew4','もぐもぐ',False),'puddle':('puddle','ぶくぶく…',False)}
 return mapped.get(n,(n,'しゅた',True))

def verse(im,e):
 t=e['time'];kafka(im,t);stelle(im,e)
 if e['shot']=='cake_verse':
  if t<137.07:
   idx=chew_index(t);native(im,'chew'+str(idx),939,639,1.06)
   callout(im,'もぐもぐ',939,218)
  elif t<138.07:
   native(im,'chew7',939,639,1.06);callout(im,'うま〜い！',939,218,True)
  elif 142.5<=t<144.0:
   native(im,'chew7',937,639,1.06);callout(im,'ごちそうさまでした',937,218)
  else:
   k=int((t-138.07)/.88);left=k%2==0;cx=842 if left else 1030;phase=int(t*12)%4
   native(im,'run'+str(phase),cx,641-5*(phase%2),1.1,mirror=left);callout(im,'ザカザカ',cx,218)
  return
 if e.get('run_direction')=='keyboard':keyboard(im,t);return
 if e.get('run_direction') in ('left','right'):
  left=e['run_direction']=='left';cx=812 if left else 1039;dt=t-e['run_onset'];phase=int(dt*12)%4
  cx+=(-1 if left else 1)*(min(dt,.70)*48-17)
  native(im,'run'+str(phase),cx,644-5*(phase%2),1.12,mirror=left)
  callout(im,'ザカザカ',cx,212);return
 if 61.328<=t<64.015:
  B.actor(im,'puddle',951,634,219)
  d=ImageDraw.Draw(im);d.ellipse((848,615,1060,647),outline=MINT,width=2)
  for j in range(3):
   yy=580-((t*23+j*24)%72);x=932+j*27;d.ellipse((x,yy,x+7,yy+7),outline=MINT,width=2)
  callout(im,'ぶくぶく…',951,327);return
 if 37.07<=t<39.55:
  d=ImageDraw.Draw(im);d.rectangle((1020,137,1170,636),outline=INK,width=4)
  d.polygon([(1170,137),(1240,169),(1240,615),(1170,636)],fill=BG,outline=INK,width=4);d.ellipse((1220,375,1230,385),fill=INK)
 pp=e['poses'][:3] or [{'sprite':'arrival','box':[100,20,146,80]}]
 for j,p in enumerate(pp):
  name,label,burst=verse_pose(p,t);cx=max(754,min(1120,(p['box'][0]+p['box'][2])*4))
  if len(pp)>1:cx=742+j*184
  scale=1.07 if len(pp)==1 else .78
  if name in ('den','bata0','bata1'):scale=1.16 if len(pp)==1 else .88
  foot=644
  if name in ('jyan','starjump'):
   q=(t*2.26)%1;foot-=18*math.sin(math.pi*q)
  if 54.25<=t<54.53:name='samhead2';label='しゅた';burst=True
  bb=native(im,name,cx,foot,scale)
  callout(im,label,cx,bb[1]-74,burst)

PAIR={
'KIRAKIRA':(['kira0','kira1'],'キラキラ',True),'PIKAPIKA':(['pika0','pika1'],'ピカピカ',True),
'MOFUMOFU':(['mofu0','mofu1'],'もふもふ',False),'NADENADE':(['nade0','nade1'],'なでなで',False),
'GURUGURU':(['guru0','guru1'],'グルグル',True),'GOROGORO':(['goro0','goro1'],'ゴロゴロ',False),
'WAKUWAKU':(['waku0','waku1'],'わくわく',False),'UZUZU':(['uzu0','uzu1'],'うずうず',True),
'NORONORO':(['noro0','noro1'],'ノロノロ',False),'URORO':(['uro0','uro1'],'ウロウロ',False),
'TEKUTEKU':(['teku0','teku1'],'てくてく',False),'KOSOKOSO':(['koso0','koso1'],'コソコソ',False),
'SUNSUN':(['sun0','sun1'],'すんすん',False),'PEROPERO':(['pero0','pero1'],'ぺろぺろ',False),
'NICONICO':(['nico0','nico1'],'にこにこ',False),'BATABATA':(['bata0','bata1'],'バタバタ',True),
'GYU-N':(['gyu0','gyu1'],'ぎゅーん',True),'GYUNGYU-N':(['gyu1','gyu0'],'ぎゅんぎゅーん',True),
'PIKO-N':(['pikon'],'ぴこーん',True),'DE-N':(['den'],'でーん',True),'DEDE-N':(['bata1'],'ででーん',True),
'DOKODOKO':(['doko'],'ドコドコ',True),'SYA-N':(['shan','jyan'],'シャーン',True),
'TATAN!':(['tatan'],'タタン',True),'KA!':(['ka'],'カッ',True),'DO-N':(['don'],'どーん',False),
'DO!':(['don'],'どっ',True),'JA-N!':(['jyan'],'ジャーン',True),'AE?':(['confused'],'あぇ？',False),
'HA!':(['oh'],'はっ',True),'O?':(['oh'],'おっ',False),'O!?':(['oh'],'おっ',False),'OI?':(['oi'],'おい？',False),
'GASAGASA':(['gasa'],'ガサガサ',False),'WWWWWW':(['bata1'],'わわわわっ',True),
'NE!':(['wave_bust'],'ね！',True),'ITADAKIMASU':(['chew7'],'いただきます',False),
'MOGU':(['chew2'],'もぐもぐ',False),'MOGUMOGU':(['chew4','chew_zoom'],'もぐもぐ',False)
}
for word,key in [('KIRAKIRA','kira'),('PIKAPIKA','pika'),('MOFUMOFU','mofu'),('NADENADE','nade'),('GURUGURU','guru'),('GOROGORO','goro'),('WAKUWAKU','waku'),('UZUZU','uzu'),('NORONORO','noro'),('URORO','uro'),('TEKUTEKU','teku'),('KOSOKOSO','koso')]:
 PAIR[word][0].append(key+'2')
OCC={}
for cue_group in ('white','dark'):
 counts={}
 for t,w in DATA['editorial_cues'][cue_group]:
  OCC[float(t)]=counts.get(w,0);counts[w]=counts.get(w,0)+1

def quick(im,e):
 t=e['time'];dark=e['shot']=='words_dark';w=e['word'];onset=e['performance_onset'] or t;dt=max(0,t-onset)
 if w=="Let's go":B.big_word(im,w,t,True,size=149,y=282);return
 names,label,burst=PAIR.get(w,(['jyan'],'ジャーン',True));variant=OCC.get(onset,0)%len(names);name=names[variant]
 if w in ('MOGU','MOGUMOGU'):
  name='chew'+str([2,3,4,3][int(dt*9)%4])
  if dark and onset>=227.427:name='chew_zoom'
 # Keep the letters behind the character, as in the source's kinetic typography.
 B.big_word(im,w,t,dark,size=107 if not dark else 121,y=288)
 if w=='NE!':
  im.paste(B.radial(False,0),(0,0));B.actor(im,'wave_bust',656,820,825);callout(im,'ね！',311,185,True,size=54);return
 scale=1.17 if not dark else 1.73
 if name in ('guru0','guru1','guru2'):scale=1.35 if not dark else 1.78
 if name in ('chew_zoom',):scale=1.75 if dark else 1.22
 if w=='MOGU':scale=.5
 if dark and w=='MOGUMOGU' and onset>=227.427:scale=2.22
 cx=640;foot=619 if not dark else 819
 if w in ('BATABATA','DEDE-N'):foot=570 if not dark else 668
 if w in ('GURUGURU','GOROGORO','DE-N'):foot=571 if not dark else 616
 if w in ('TEKUTEKU','KOSOKOSO'):cx+=(-1 if variant%2 else 1)*min(dt,.35)*60
 # A brief ease-out landing accent; the main motion comes from drawn poses.
 foot-=14*math.exp(-dt*22)*math.sin(dt*38)
 bb=native(im,name,cx,foot,scale)
 if dark:y=21
 else:y=max(18,bb[1]-72)
 callout(im,label,cx,y,burst)

@lru_cache(maxsize=1)
def title():
 im=Image.open(R/'assets/generated/title_art.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
 B.text(im,'FIREFLY HAS ARRIVED!',55,65,30,'#508f7b',True,maxwidth=570,stroke=1,outline=BG)
 for s,size,col,pos in [('流萤',170,'#70c7a4',(30,138)),('来了哦',157,'#f1d77c',(20,335))]:
  lab=B.word_image(s,size,col,False,10,INK).rotate(8,Image.Resampling.BICUBIC,expand=True);im.paste(lab,pos,lab)
 return im

def title_motion(im,e):
 t=e['time'];returning=e['shot']=='title_return';B.particles(im,t,count=8)
 if not returning:
  phase=int(t*12)%4;native(im,'run'+str(phase),1138,713,.44,mirror=(int(t/.88)%2==0));return
 # The miniature steps along the visible wand rather than floating over the title.
 u=t-277.377
 if u<2:cx=1175-u*250;name='run'+str(int(t*12)%4);foot=675-8*math.sin(t*14);mir=True
 elif u<5.2:cx=666;name=['clap0','clap1','jyan','turnwave'][int((u-2)*2.26)%4];foot=651;mir=False
 elif u<7.9:cx=618;name=['nico0','turnwave'][int((u-5.2)*2)%2];foot=640;mir=False
 else:cx=830+min(390,(u-7.9)*115);name='run'+str(int(t*12)%4);foot=665;mir=False
 native(im,name,cx,foot,.53,mirror=mir)
 if 281.8<=t<288.8:
  stelle(im,e,mini=True)

def hai(im,e):
 t=e['time'];count=e['hai_count'];onset=e['hai_onset'] or 153.754;dt=max(0,t-onset)
 for y in (9,374):B.text(im,'Hai! Hai! Hai!',-20,y,172,MINT,True,maxwidth=1480)
 # Corresponding source layout: large bust foreground LEFT; repeated figures behind.
 positions=[(685,563),(899,563),(1113,563),(480,554)]
 if count:
  for j in range(min(count,3)):
   x,foot=positions[j];pop=math.sin(min(1,dt/.20)*math.pi)*19 if j==count-1 else 0
   name='samhead'+str((int((t-153.754)*4.53)+j)%4)
   native(im,name,x,foot-pop,.90)
   callout(im,'はい！',x,39,True)
 # Device is drawn INTO all singing keyframes, not a microphone overlay.
 name=['device0','device1','device2','device1'][int((t-153.754)*9.06)%4]
 native(im,name,254,779,1.70)
 if count==4:
  x,foot=positions[3];pop=math.sin(min(1,dt/.20)*math.pi)*19
  native(im,'samhead'+str((int((t-153.754)*4.53)+3)%4),x,foot-pop,.90)
  callout(im,'はい！',x,39,True)
 if t<153.754:im=Image.blend(im,Image.new('RGB',(W,H),BG),max(0,1-(t-153.42)/.334))
 if t>179.346:im=Image.blend(im,Image.new('RGB',(W,H),BG),min(1,(t-179.346)/1.47))
 return im

@lru_cache(maxsize=64)
def spin_glow(name,h):
 sp=B.resized(name,h);a=sp.getchannel('A');gl=Image.new('RGBA',sp.size,(168,222,155,0));gl.putalpha(a.point(lambda q:int(q*.22)));return gl.filter(ImageFilter.GaussianBlur(9))

def sparkle_spin(im,t):
 u=t-242.209;phase=int(u*8)%8;name='spin'+str(phase);cx=796;foot=659;h=469
 glow=spin_glow(name,h);im.paste(glow,(round(cx-glow.width/2),round(foot-glow.height)),glow)
 # Hand-drawn elliptical trails, two sparkler tips, two revolutions in this beat.
 d=ImageDraw.Draw(im);theta=u*math.tau*.86
 for side in (0,math.pi):
  pts=[]
  for k in range(20):
   a=theta+side-k*.06;pts.append((cx+254*math.cos(a),360+49*math.sin(a)-k*.8))
  d.line(pts,fill='#a4d7b2',width=2);d.line(pts[:12],fill='#f0d97e',width=3)
  for k in range(8):
   a=theta+side-k*.09;xx=cx+253*math.cos(a);yy=360+49*math.sin(a)+k*3
   rr=2 if k%2 else 3;d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill='#ffda88')
 B.actor(im,name,cx,foot,h)
 callout(im,'Yeah',cx,20,True,size=34)

def caught_ending(im,t):
 u=t-290.29
 if u<.63:name='turnwave';cx=820
 elif u<1.1:name='caught';cx=820
 elif u<1.72:name='blush0';cx=820
 elif u<2.85:name='blush1';cx=820
 elif u<4.6:name='blush2';cx=820
 else:name=['blush2','blush0','blush2','blush1'][int((u-4.6)*.72)%4];cx=820
 if u<.52:star='stelle_peek'
 elif u<1.0:star='stelle_recoil'
 else:star='stelle_giggle'
 B.actor(im,star,298,755,538)
 B.actor(im,name,cx,750,650)
 if .65<=u<1.1:marks(im,938,144,t,INK)
 if 1.1<=u<2.4:callout(im,'あー！',815,22,True,size=40)
 if u>=4.6:
  # Credits are compact and leave the final character acting on screen.
  jp(im,'原曲・映像原案  GYARI',640,30,26,INK,True)
  B.text(im,'Akari ga Yattekita zo',640,75,25,INK,True,'center')
 B.particles(im,t,count=6,quiet=True)
 if t>300.25:im=Image.blend(im,Image.new('RGB',(W,H),BG),min(1,(t-300.25)/.72))
 return im

def frame(e):
 t=e['time'];mode=e['shot'];ev=e['event'];qt=round(t*12)/12
 dark=mode in ('super_chorus','ready','words_dark','lyric_dark','lyric_card_dark')
 im=Image.new('RGB',(W,H),DARK if dark else BG)
 if mode=='intro':
  for k,p in enumerate(e['poses']):
   x0,y0,x1,y1=p['box'];cx=(x0+x1)*4;name=['turnwave','clap0','clap1','kira0'][(ev+k)%4]
   if y1>=88:bb=B.actor(im,name,cx,y0*8+12,370,'top')
   else:bb=B.actor(im,name,cx,min(620,y1*8+22),418)
   callout(im,'ちょっ' if (ev+k)%2 else 'ちょっと',cx,max(22,bb[1]-71))
 elif mode=='intro_impact':
  im=B.radial(False,ev%2).copy();B.actor(im,'jyan' if ev%2 else 'tatan',640,790,560+130*max(0,(t-22.92)/.9));callout(im,'じゃん！',640,34,True)
 elif mode in ('title','title_return'):
  im=title().copy();title_motion(im,e)
 elif mode=='greeting':
  im=B.radial(False,0).copy();B.actor(im,'wave_bust',640,790,680);callout(im,'おっ',640,26,True)
 elif mode in ('verse','cake_verse'):
  if 51.48<t<56.1:im=B.radial(False,ev%2).copy()
  verse(im,e)
 elif mode=='verse_impact':
  im=B.radial(False,ev%2).copy();B.actor(im,'jyan' if ev%2 else 'tatan',640,671,480)
  callout(im,'どん！',640,41,True)
  if (79.7<t<81.181) or (152.3<t<153.42):im=Image.new('RGB',(W,H),BG);B.big_word(im,"Let's go",t,size=125,y=282)
 elif mode in ('words_white','words_dark'):
  if dark:im=B.radial(True,0).copy();B.particles(im,qt,True,count=7)
  quick(im,e)
 elif mode=='yeah_white':
  B.big_word(im,'Yeah',t,size=207,y=238)
  B.actor(im,'jyan',640,668,447);callout(im,'Yeah',640,103,True)
 elif mode=='chorus':im=hai(im,e)
 elif mode=='super_chorus':
  im=Image.new('RGB',(W,H),DARK);B.particles(im,qt,True,count=15)
  shift=int((qt-181.748)*58)%550;B.text(im,'LA LA LA LA LA',640-shift,289,155,'#a6d3a8',True,'center',maxwidth=2250)
  B.text(im,'Super Chorus Time',640,589,34,GOLD,True,'center')
  # The original's closed-eye, open-mouth, sideways supine gag is preserved.
  name='lie0' if int((t-181.748)*2.26)%5 not in (2,4) else 'lie1'
  native(im,name,669,546,1.78,angle=0)
  if 181.748<=t<182.315:im=Image.blend(im,Image.new('RGB',(W,H),BG),max(0,1-(t-181.748)/.567))
 elif mode=='ready':
  B.text(im,'Are you ready?',640,291,101,'#87d0a9',True,'center',maxwidth=1100);B.particles(im,qt,True,count=7)
 elif mode=='lyric_dark':
  im=B.radial(True,0).copy();B.particles(im,qt,True,count=15)
  if t<240.006:B.big_word(im,'Yeah',t,True,size=205,y=229);B.actor(im,'jyan',640,654,502);callout(im,'Yeah',640,22,True)
  elif t<242.209:jp(im,'ひとつの光が',640,306,94,MINT,True,maxwidth=1160)
  elif t<244.845:
   jp(im,'輝いて',640,286,146,MINT,True);sparkle_spin(im,t)
  elif t<247.047:
   B.actor(im,'sing_a' if int(t*9)%2 else 'sing_b',358,763,623);jp(im,'言葉',983,242,92,MINT,True);jp(im,'選んで',983,380,86,MINT,True)
  else:B.actor(im,'sing_a' if int(t*9)%2 else 'sing_b',640,816,877);jp(im,'紡いだの',640,327,99,MINT,True,stroke=3,outline=DARK)
 elif mode in ('lyric_card_dark','lyric_card_white'):
  jp(im,'辛いときも',640,238,88,MINT,True);jp(im,'寂しいときも',640,370,88,MINT,True)
 elif mode=='lyric_impact':
  im=B.radial(False,0).copy();jp(im,'私が' if t<253.553 else 'いるから',640,40,152,MINT,True,maxwidth=1230)
  B.actor(im,'tatan' if ev%2 else 'jyan',640,827,635)
 elif mode=='photo_wall':
  im=B.photo_wall(qt);native(im,'lie0',646,559,1.28)
  jp(im,'続く物語' if t<259.592 else '星の絆で繋ぐから',640,605,67,MINT,True,stroke=4,maxwidth=1190)
 elif mode=='forever':
  jp(im,'ずっと  ずっと',640,65,128,MINT,True,maxwidth=1240);B.actor(im,'jyan',640,695,350);callout(im,'ずっと！',640,261,True)
 elif mode=='collage':
  seq=['kira0','pika1','mofu0','nade1','guru0','goro1','waku0','uzu1','noro0','uro1','teku0','koso1','sun0','pero1','nico0','bata1','doko','shan','tatan','jyan']
  for row in range(3):
   for col in range(7):B.actor(im,seq[(row*7+col)%len(seq)],70+col*190,210+row*245,230)
  im=Image.blend(im,Image.new('RGB',(W,H),BG),.73);jp(im,'私たちと' if t<267.801 else '貴方で',640,269,144,MINT,True,maxwidth=1240)
 elif mode=='lyric_close':
  B.actor(im,'sing_a' if int(t*9)%2 else 'sing_b',640,848,905);jp(im,'行くよ',640,315,124,MINT,True,stroke=3)
 elif mode=='ending_impact':
  im=B.radial(False,0).copy();jp(im,'見ていてね',640,33,129,MINT,True,maxwidth=1210);B.actor(im,'wave_bust',640,813,741);callout(im,'ね！',288,227,True,size=42)
 elif mode in ('headphones','credits'):im=caught_ending(im,t)
 return im

def previews():
 samples=[2,12,22.5,27,37.5,38.5,42.5,43.5,54.4,62.3,65.6,66.5,67.4,71.6,82.4,86.7,91.9,113.04,113.45,113.95,116.9,125,134.5,136,153.90,154.35,154.80,155.25,155.70,182.6,212.95,213.7,214.2,214.9,215.4,216.0,218.0,218.9,221.3,228.3,232.7,242.3,242.6,243,243.35,243.7,244.05,244.4,246,254,257.5,264.5,268,270.5,274,279.1,282.6,284.2,290.55,291.04,291.65,292.5,294.1,297.0,299.1]
 board=Image.new('RGB',(1600,((len(samples)+3)//4)*258),'#e0e8dd');d=ImageDraw.Draw(board);f=B.font(17,True)
 for k,t in enumerate(samples):
  idx=bisect.bisect_left(TIMES,t);im=frame(FRAMES[min(idx,len(FRAMES)-1)]);im.save(OUT/f'v2_preview_{k+1:02d}.jpg',quality=91)
  im.thumbnail((400,225),Image.Resampling.LANCZOS);x=k%4*400;y=k//4*258;board.paste(im,(x,y));d.text((x+8,y+231),f'{t:.2f}s {FRAMES[idx]["shot"]}',font=f,fill='#365044')
 board.save(OUT/'V2_storyboard.jpg',quality=93);print('Preview complete',len(samples),flush=True)

def render():
 dst=OUT/'流萤来了哦_V2_动作精修.mp4';log=OUT/'render_v2_ffmpeg.log'
 graph='[0:v]scale=1280:720[clock];[clock][1:v]overlay=x=0:y=0:shortest=1:ts_sync_mode=nearest:format=auto,scale=1920:1080:flags=lanczos,format=yuv420p[v]'
 cmd=['ffmpeg','-hide_banner','-y','-i',str(SOURCE),'-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate','30000/1001','-i','pipe:0','-filter_complex',graph,'-map','[v]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','20','-threads','4','-fps_mode','passthrough','-enc_time_base','1:16000','-video_track_timescale','16000','-c:a','copy','-movflags','+faststart','-metadata','title=流萤来了哦 — V2 动作精修','-metadata','comment=Character art: GPT image. Original music and timing: GYARI.',str(dst)]
 start=time.monotonic()
 with log.open('w') as err:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
  try:
   for i,e in enumerate(FRAMES):
    proc.stdin.write(frame(e).tobytes())
    if i%450==0:print(f'render {i}/{len(FRAMES)} source_time={e["time"]:.3f} elapsed={time.monotonic()-start:.1f}s',flush=True)
  except BrokenPipeError:raise RuntimeError(log.read_text()[-4000:])
  finally:proc.stdin.close()
  status=proc.wait()
 if status:raise RuntimeError(log.read_text()[-4000:])
 print('Completed:',dst,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--render',action='store_true');args=p.parse_args()
 if args.preview:previews()
 if args.render:render()
 if not(args.preview or args.render):p.print_help()
