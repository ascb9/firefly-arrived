"""V3: source-timed held poses, fixed bodies with GPT-drawn mouth parts, new sets.

python scripts/render_v3.py --preview
python scripts/render_v3.py --render
"""
from pathlib import Path
from functools import lru_cache
import argparse,bisect,json,math,subprocess,time
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import render_v2 as V
B=V.B;R=B.ROOT;W,H=B.W,B.H;BG,INK,MINT,GOLD,DARK=B.BG,B.INK,B.MINT,B.GOLD,B.DARK
D=json.loads((R/'timeline_v3.json').read_text());FRAMES=D['frames'];TIMES=[e['time'] for e in FRAMES];SP=B.SP;OUT=R/'output';PERIOD=60/136
ENV=json.loads((R/'docs/vocal_envelope_v3.json').read_text())['segments']
MOUTH_CONFIG={'sing_fixed':(.500,.518,.108,0),'lie_fixed':(.629,.365,.082,-32),'point_fixed':(.480,.357,.100,0)}

@lru_cache(maxsize=8)
def backdrop(name,fade=0):
 im=Image.open(R/'assets/generated'/(name+'.png')).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
 if fade:im=Image.blend(im,Image.new('RGB',(W,H),BG if name=='express_cabin_v3' else '#202c49'),fade)
 return im

def meteors(im,t):
 d=ImageDraw.Draw(im,'RGBA')
 for j in range(3):
  u=((t-181.748)+j*1.91)%5.8
  if not .45<u<1.72:continue
  p=(u-.45)/1.27;x=1120-j*220-p*390;y=38+j*32+p*175;alpha=round(150*math.sin(math.pi*p))
  d.line((x+75,y-34,x,y),fill=(221,243,248,alpha),width=2)
  d.line((x+38,y-17,x,y),fill=(240,247,249,min(230,alpha+50)),width=3)
  d.ellipse((x-2,y-2,x+2,y+2),fill=(251,249,219,min(255,alpha+60)))

def rooftop(t,fade=.20):
 im=backdrop('secret_base_v3',fade).copy();meteors(im,t);return im

def source_cx(e,default=945):
 if e['poses']:
  p=max(e['poses'],key=lambda p:(p['box'][2]-p['box'][0])*(p['box'][3]-p['box'][1]));return max(735,min(1110,(p['box'][0]+p['box'][2])*4))
 return default

def held_cx(e):
 # Source analysis boxes can include the drifting piano. Lock the character's
 # transform to the first frame of each authored cue, rather than tracking it.
 k=bisect.bisect_left(TIMES,e['caption_onset_v3']);return source_cx(FRAMES[k])

def fixed_stelle(im,e,mini=False):
 # One image, one transform, and no time-dependent body or head changes.
 if mini:B.actor(im,'bin_back',154,712,216)
 else:B.actor(im,'bin_back',244,771,604)

V.stelle=fixed_stelle

def intro(im,e):
 t=e['time']
 if t>=2.002:
  B.actor(im,'arrival',172,526,365,'top');V.callout(im,'ぱー',172,448,size=29)
 if t>=1.768:
  B.actor(im,'surprise',1108,452,370,'top');V.callout(im,'ドン',1108,374,size=29)
 if t>=8.809:
  name=e['sprite_v3'] or 'surprise';h=458;foot=691
  if t>=20.287:h=606;foot=790
  bb=B.actor(im,name,649,foot,h);V.callout(im,e['caption_v3'],649,max(16,bb[1]-70),e['caption_burst_v3'])
 return im

def intro_impact(e):
 t=e['time']
 if t>=22.923:
  im=V.title().copy();u=min(1,(t-22.923)/.72);return Image.blend(Image.new('RGB',(W,H),BG),im,u*u*(3-2*u))
 im=B.radial(False,0).copy();B.actor(im,'star_bust',640,872,846)
 if t>=21.622:
  if t<22.289:name,label='bata0','うん'
  else:name,label='tatan','シャキーン'
  # Each accent enters once and holds; no two-image ping-pong.
  B.actor(im,name,640,688,390);V.callout(im,label,640,222,True)
 return im

def cabin_verse(e):
 t=e['time'];im=backdrop('express_cabin_v3',.57).copy();V.kafka(im,t);fixed_stelle(im,e)
 name=e['sprite_v3'];label=e['caption_v3'];onset=e['caption_onset_v3'] or t;dt=max(0,t-onset)
 if 37.070<=t<38.372:
  # The drawn door and pushing hand form the opening pose; a single exit into room.
  u=max(0,min(1,(t-37.070)/1.302));s=u*u*(3-2*u)
  if u<.30:
   bb=B.actor(im,'entry_push',1120,635,419)
  elif u<.78:
   bb=B.actor(im,'entry_walk',1114-150*s,636,406)
  else:bb=B.actor(im,'entry_stop',963,638,403)
  V.callout(im,'失礼します',min(1100,1120-150*s),160,False,size=29);return im
 if name in ('hop_left','hop_right') and t>=65.299:
  # Original performance: a single static train-hop image changes side on cuts.
  cx=held_cx(e);bb=B.actor(im,name,cx,649,417)
  V.callout(im,label,cx,180,False,size=30);return im
 if name=='table_lean':
  B.actor(im,name,932,649,410);V.callout(im,label,932,168,True);return im
 if name=='submerged':
  B.actor(im,name,927,646,195);d=ImageDraw.Draw(im,'RGBA')
  if t<63.530:
   for j in range(2):
    yy=524-((t-61.328)*20+j*16)%30;d.ellipse((919+j*22,yy,926+j*22,yy+7),outline=(94,156,131,130),width=2)
  else:
   angle=(t-63.530)*math.tau*2.3;d.arc((810,610,1046,657),round(math.degrees(angle)),round(math.degrees(angle))+175,fill=(91,156,139,130),width=3)
  V.callout(im,label,926,348,e['caption_burst_v3']);return im
 if name=='splash_up':
  u=min(1,dt/.233);foot=643-30*math.sin(math.pi*u);B.actor(im,name,931,foot,447);V.callout(im,label,934,133,True);return im
 if name=='hop_land':
  u=min(1,dt/.35);foot=645+7*math.sin(math.pi*u);B.actor(im,name,1016,foot,413);V.callout(im,label,1016,163,True);return im
 if 64.631<=t<65.299:
  B.actor(im,'hop_land',1037,647,386);B.actor(im,'jyan',785,634,401);V.callout(im,'やったぁ',785,123,True);V.callout(im,'しゅたっ',1037,192,True);return im
 cx=source_cx(e);height=401;foot=646
 if name in ('den','goro0','guru0'):height=321;foot=553
 if name=='puddle':height=194
 if name in ('starjump','jyan'):foot=617
 if name in ('entry_walk','hop_left','hop_right'):height=413
 bb=B.actor(im,name or 'arrival',cx,foot,height);V.callout(im,label,cx,max(21,bb[1]-74),e['caption_burst_v3'],size=29)
 return im

def verse_impact(e):
 t=e['time'];im=Image.new('RGB',(W,H),BG)
 if t>=80.514:B.big_word(im,"Let's go",t,size=125,y=282);return im
 if t<77.978:name,label='hop_doki','ドキッ!!'
 elif t<78.412:name,label='tatan_hold','タタン'
 elif t<78.979:name,label='sneeze','へっぷしゅ!!!'
 elif t<79.413:name,label='goro0','ゴロゴロ'
 else:name,label='landed','じゅん！';im=B.radial(False,0).copy()
 B.actor(im,name,640,657 if name!='goro0' else 535,436 if name!='goro0' else 250);V.callout(im,label,640,138 if name!='goro0' else 236,True)
 return im

def cake_verse(e):
 t=e['time'];im=backdrop('express_cabin_v3',.57).copy();V.kafka(im,t);fixed_stelle(im,e)
 name=e['sprite_v3'];label=e['caption_v3']
 if name=='chew':V.native(im,'chew'+str(V.chew_index(t)),939,639,1.06);V.callout(im,label,939,218)
 elif name=='chew7':V.native(im,'chew7',939,639,1.06);V.callout(im,label,939,218)
 else:
  cx=held_cx(e);B.actor(im,name,cx,649,417);V.callout(im,label,cx,180,size=30)
 return im

def vocal_energy(t):
 for seg in ENV:
  if seg['start']<=t<seg['end']:return float(np.interp(t,seg['times'],seg['opening']))
 return .5

def syllable_nodes(t,kind):
 if kind=='la':
  u=((t-181.748)/PERIOD)%1
  nodes=[(0,0),(.10,7),(.24,3),(.53,3),(.78,4),(.93,0),(1,0)]
 else:
  a,b,sequence=kind
  q=max(0,min(.999,(t-a)/(b-a)));nodes=[(i/len(sequence),v) for i,v in enumerate(sequence)]+[(1,0)];u=q
 k=min(len(nodes)-2,max(0,bisect.bisect_right([n[0] for n in nodes],u)-1))
 prev,nxt=nodes[k][1],nodes[k+1][1];span=nodes[k+1][0]-nodes[k][0];fraction=(u-nodes[k][0])/span
 # Articulation holds its vowel, then makes a short smooth transition to the next.
 blend=max(0,min(1,(fraction-.64)/.36));blend=blend*blend*(3-2*blend)
 return prev,nxt,blend

@lru_cache(maxsize=1024)
def mouth_layer(index,width,energy,angle):
 sp=SP['mouth'+str(index)];h=max(4,round(sp.height*width/sp.width))
 if index!=0:h=max(5,round(h*(.58+.42*energy/8)))
 sp=sp.resize((width,h),Image.Resampling.LANCZOS)
 if angle:sp=sp.rotate(angle,Image.Resampling.BICUBIC,expand=True)
 layer=Image.new('RGBA',(180,160),(0,0,0,0));layer.alpha_composite(sp,((180-sp.width)//2,(160-sp.height)//2));return layer

def blend_alpha(first,second,mix):
 # Interpolate premultiplied color so transparent atlas pixels leave no dark halo.
 a=np.asarray(first,dtype=np.float32)/255;b=np.asarray(second,dtype=np.float32)/255
 alpha=a[:,:,3:]*(1-mix)+b[:,:,3:]*mix
 color=(a[:,:,:3]*a[:,:,3:]*(1-mix)+b[:,:,:3]*b[:,:,3:]*mix)/np.maximum(alpha,1e-6)
 return Image.fromarray(np.clip(np.concatenate([color,alpha],axis=2)*255,0,255).astype(np.uint8),'RGBA')

def vocal_actor(im,name,cx,foot,h,t,kind):
 bb=B.actor(im,name,cx,foot,h);rx,ry,rw,angle=MOUTH_CONFIG[name];x=bb[0]+(bb[2]-bb[0])*rx;y=bb[1]+(bb[3]-bb[1])*ry
 width=max(12,round((bb[2]-bb[0])*rw/2)*2);energy=round(vocal_energy(t)*8);i,j,mix=syllable_nodes(t,kind)
 first=mouth_layer(i,width,energy,angle);second=mouth_layer(j,width,energy,angle);mouth=blend_alpha(first,second,mix)
 im.paste(mouth,(round(x-90),round(y-80)),mouth)
 return x,y

def music_notes(im,t,mouth,start,period=PERIOD):
 k=int((t-start)/period);x0,y0=mouth
 for j in range(max(0,k-3),k+1):
  born=start+j*period;age=t-born
  if not 0<=age<1.55 or vocal_energy(born+.09)<.13:continue
  u=age/1.55;x=x0+7+u*103+8*math.sin(u*math.pi);y=y0-10-u*111
  sp=V.jpimage('♪' if j%2 else '♫',round(26+12*math.sin(math.pi*u)),GOLD if j%2 else '#b8d5ab',1,'#635538')
  a=sp.getchannel('A').point(lambda a:round(a*min(1,age/.10)*math.sqrt(max(0,1-u))));sp=sp.copy();sp.putalpha(a);im.paste(sp,(round(x),round(y)),sp)

def super_chorus(e):
 t=e['time'];im=rooftop(t,.20)
 B.text(im,'LA LA LA LA LA',640,206,147,'#d6e4c1',True,'center',maxwidth=2300,stroke=2,outline='#334664')
 B.text(im,'Super Chorus Time',640,656,29,'#f5d788',True,'center',stroke=1,outline='#384761')
 mouth=vocal_actor(im,'lie_fixed',667,567,442,t,'la');music_notes(im,t,mouth,181.748)
 if t<182.315:im=Image.blend(im,Image.new('RGB',(W,H),BG),max(0,1-(t-181.748)/.567))
 return im

def lyric_dark(e):
 t=e['time'];im=rooftop(t,.42)
 if t<240.006:B.big_word(im,'Yeah',t,True,size=205,y=229);B.actor(im,'jyan',640,654,502);V.callout(im,'Yeah',640,22,True)
 elif t<242.209:V.jp(im,'ひとつの光が',640,306,94,'#b9e9cb',True,maxwidth=1160,stroke=2,outline='#283448')
 elif t<244.845:V.jp(im,'輝いて',640,286,146,'#b9e9cb',True,stroke=2,outline='#283448');V.sparkle_spin(im,t)
 elif t<247.047:
  V.jp(im,'言葉',986,240,92,'#b9e9cb',True);V.jp(im,'選んで',986,380,86,'#b9e9cb',True)
  a=Image.new('RGBA',(W,H),(0,0,0,0));mouth=vocal_actor(a,'sing_fixed',358,763,623,t,(244.845,247.047,[1,1,3,4,7,0,4,4]));music_notes(a,t,mouth,244.845,.36)
  if t<245.245:
   opacity=(t-244.845)/.4;a.putalpha(a.getchannel('A').point(lambda p:round(p*opacity)));small=Image.new('RGBA',(W,H),(0,0,0,0));B.actor(small,'jyan',766,633,245);small.putalpha(small.getchannel('A').point(lambda p:round(p*(1-opacity))));im.paste(small,(0,0),small)
  im.paste(a,(0,0),a)
 else:
  mouth=vocal_actor(im,'sing_fixed',640,816,877,t,(247.047,248.381,[6,6,5,3,1,1]));music_notes(im,t,mouth,247.047,.35)
  V.jp(im,'紡いだの',640,327,99,'#b9e9cb',True,stroke=3,outline='#283448')
 return im

def lyric_impact(e):
 t=e['time'];im=B.radial(False,0).copy();word='私が' if t<253.553 else 'いるから';V.jp(im,word,640,60,182,MINT,True,maxwidth=1230)
 if t<253.553:
  mouth=vocal_actor(im,'point_fixed',640,829,649,t,(252.352,253.553,[3,3,5,1,3,3]))
 else:
  u=min(1,(t-253.553)/1.869);smooth=u*u*(3-2*u);mouth=vocal_actor(im,'point_fixed',640,832+154*smooth,650+292*smooth,t,(253.553,255.422,[5,7,3,3,3,3]))
 return im

def caught(e):
 t=e['time'];u=t-290.290;im=backdrop('express_cabin_v3',.79).copy()
 if u<.434:star='bin_back';name='turnwave'
 elif u<1.101:star='bin_turn1';name='turnwave'
 elif u<1.45:star='bin_turn2';name='caught'
 elif u<2.10:star='bin_turn2';name='blush0'
 elif u<3.35:star='bin_turn3';name='blush1'
 else:star='bin_turn3';name='blush2'
 # The bin stays anchored; the turn happens once before Firefly's blush reaction.
 B.actor(im,star,242,756,551);B.actor(im,name,825,749,625)
 if 1.101<=u<2.00:V.callout(im,'あー！',825,27,True,size=40)
 if u>=4.6:V.jp(im,'原曲・映像原案  GYARI',640,26,26,INK,True);B.text(im,'Akari ga Yattekita zo',640,69,25,INK,True,'center')
 if t>300.25:im=Image.blend(im,Image.new('RGB',(W,H),BG),min(1,(t-300.25)/.72))
 return im

def frame(e):
 t=e['time'];mode=e['shot']
 if mode=='intro':return intro(Image.new('RGB',(W,H),BG),e)
 if mode=='intro_impact':return intro_impact(e)
 if mode=='verse':return cabin_verse(e)
 if mode=='cake_verse':return cake_verse(e)
 if mode=='verse_impact' and t<82:return verse_impact(e)
 if mode=='super_chorus':return super_chorus(e)
 if mode=='ready':
  im=rooftop(t,.42);B.text(im,'Are you ready?',640,291,101,'#c2e8cc',True,'center',maxwidth=1100,stroke=2,outline='#253547');return im
 if mode=='words_dark':im=rooftop(t,.56);V.quick(im,e);return im
 if mode=='lyric_dark':return lyric_dark(e)
 if mode=='lyric_card_dark':
  im=rooftop(t,.65);V.jp(im,'辛いときも',640,238,88,'#c2e8cc',True);V.jp(im,'寂しいときも',640,370,88,'#c2e8cc',True);return im
 if mode=='lyric_impact':return lyric_impact(e)
 if mode=='lyric_close':
  im=Image.new('RGB',(W,H),BG);vocal_actor(im,'sing_fixed',640,848,905,t,(269.536,272.672,[5,6,1,1,1,1]));V.jp(im,'行くよ',640,315,124,MINT,True,stroke=3);return im
 if mode in ('headphones','credits'):return caught(e)
 return V.frame(e)

SAMPLES=[2.2,8.9,9.4,11.6,15.6,19.6,21.05,21.9,22.5,23.4,37.12,37.65,38.25,40.0,61.7,63.7,64.10,64.4,64.8,65.6,66.5,67.4,71.3,72.6,77.7,78.08,78.6,79.1,79.6,80.7,113.5,125,136,155.25,182.5,182.7,183.0,187.1,193.0,207,214.3,221.3,242.6,243.35,245.3,245.8,246.4,247.7,252.5,252.9,253.3,253.8,254.3,255.1,284.2,290.35,290.98,291.5,292,292.8,294.2,298.5]

def previews():
 board=Image.new('RGB',(1600,((len(SAMPLES)+3)//4)*258),'#e0e8dd');d=ImageDraw.Draw(board);f=B.font(17,True)
 for k,t in enumerate(SAMPLES):
  idx=min(len(FRAMES)-1,bisect.bisect_left(TIMES,t));im=frame(FRAMES[idx]);im.save(OUT/f'v3_preview_{k+1:02d}.jpg',quality=93);im.thumbnail((400,225),Image.Resampling.LANCZOS);x=k%4*400;y=k//4*258;board.paste(im,(x,y));d.text((x+8,y+231),f'{t:.2f}s {FRAMES[idx]["shot"]}',font=f,fill='#365044')
 board.save(OUT/'V3_storyboard.jpg',quality=94);print('V3 preview complete',len(SAMPLES),flush=True)

def render():
 dst=OUT/'流萤来了哦_V3_演出精修.mp4';log=OUT/'render_v3_ffmpeg.log';graph='[0:v]scale=1280:720[clock];[clock][1:v]overlay=x=0:y=0:shortest=1:ts_sync_mode=nearest:format=auto,scale=1920:1080:flags=lanczos,format=yuv420p[v]'
 cmd=['ffmpeg','-hide_banner','-y','-i',str(B.SOURCE),'-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate','30000/1001','-i','pipe:0','-filter_complex',graph,'-map','[v]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','20','-threads','4','-fps_mode','passthrough','-enc_time_base','1:16000','-video_track_timescale','16000','-c:a','copy','-movflags','+faststart','-metadata','title=流萤来了哦 — V3 演出精修',str(dst)];start=time.monotonic()
 with log.open('w') as err:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
  try:
   for i,e in enumerate(FRAMES):
    proc.stdin.write(frame(e).tobytes())
    if i%600==0:print(f'render {i}/{len(FRAMES)} source_time={e["time"]:.3f} elapsed={time.monotonic()-start:.1f}s',flush=True)
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
