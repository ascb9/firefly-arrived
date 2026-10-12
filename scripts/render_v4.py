"""V4 targeted performance revision; source frame clock and AAC unchanged."""
from pathlib import Path
from functools import lru_cache
import argparse,bisect,csv,json,math,subprocess,time
import numpy as np
from scipy.ndimage import gaussian_filter1d
from PIL import Image,ImageDraw
import render_v3 as C
from performance_v4 import FF_KEYS,STAR_KEYS
B=C.B;V=C.V;R=B.ROOT;W,H=B.W,B.H;BG,INK,MINT,GOLD=C.BG,C.INK,C.MINT,C.GOLD;SP=B.SP;OUT=R/'output'
BASE_FRAME=C.frame;ORIGINAL_VOCAL_ACTOR=C.vocal_actor
FF_TIMES=[t for t,name in FF_KEYS];STAR_TIMES=[t for t,name in STAR_KEYS]
YO_CUES=[(36.169,'yo0'),(36.269,'yo1'),(36.603,'yo2'),(36.770,'yo3')]
YEAH_CUES=[(109.409,'yeah0'),(109.509,'yeah1'),(109.809,'yeah2'),(110.477,'yeah3'),(110.710,'yeah4'),(110.944,'yeah5')]
IMPACT_CUES=[(149.983,'im_doki','ドキッ!!'),(150.317,'im_tatan','タタン'),(150.751,'im_pre_sneeze','へっぷしゅ!!!'),(150.884,'im_sneeze','へっぷしゅ!!!'),(151.318,'im_roll','ゴロゴロ'),(151.752,'im_jyan','じゅん！')]
ANIM=json.loads((R/'assets/animation_v4/manifest.json').read_text())['families']
FRAMES=C.FRAMES;TIMES=C.TIMES
SMOOTH_ENV=[]
for seg in C.ENV:
 s=dict(seg);s['opening']=gaussian_filter1d(np.array(seg['opening']),16 if seg['start']<210 else 7).tolist();SMOOTH_ENV.append(s)
# Native facial landmarks: left eye (143,203), right eye (236,190).
# Face normal is perpendicular to the eye line, rather than the atlas box center.
C.MOUTH_CONFIG['sing_fixed']=(.485,.550,.108,8)

def smoothed_energy(t):
 for seg in SMOOTH_ENV:
  if seg['start']<=t<seg['end']:return float(np.interp(t,seg['times'],seg['opening']))
 return .5

@lru_cache(maxsize=2048)
def mouth_part(index,width,strength,angle):
 sp=SP['mouth'+str(index)];h=max(4,round(sp.height*width/sp.width))
 if index!=0:h=max(3,round(h*max(.06,strength/64)))
 sp=sp.resize((width,h),Image.Resampling.LANCZOS)
 if angle:sp=sp.rotate(angle,Image.Resampling.BICUBIC,expand=True)
 im=Image.new('RGBA',(180,160));im.alpha_composite(sp,((180-sp.width)//2,(160-sp.height)//2));return im

def mouth_state(t,kind):
 e=smoothed_energy(t)
 if kind=='la':
  # One broad jaw motion per two source beats; sustained vowel stays the same.
  phase=((t-181.748)/(C.PERIOD*2))%1
  amplitude=.67+.12*math.sin(math.tau*phase)+.08*(e-.5)
  return 3,max(.43,min(.84,amplitude)),1
 i,j,mix=C.syllable_nodes(t,kind);idx=i if mix<.5 else j
 # A brief jaw relaxation changes vowels without two superimposed outlines.
 relax=math.sin(math.pi*mix)**2
 return idx,max(.11,(.64+.26*e)*(1-.72*relax)),1-.15*relax

def vocal_actor(im,name,cx,foot,h,t,kind):
 if name=='point_fixed':return ORIGINAL_VOCAL_ACTOR(im,name,cx,foot,h,t,kind)
 bb=B.actor(im,name,cx,foot,h);rx,ry,rw,angle=C.MOUTH_CONFIG[name];x=bb[0]+(bb[2]-bb[0])*rx;y=bb[1]+(bb[3]-bb[1])*ry
 idx,amplitude,wide=mouth_state(t,kind);width=max(10,round((bb[2]-bb[0])*rw*wide/2)*2)
 mouth=mouth_part(idx,width,round(amplitude*64),angle);im.paste(mouth,(round(x-90),round(y-80)),mouth)
 return x,y

C.vocal_actor=vocal_actor

def cue_at(rows,t):
 return rows[max(0,bisect.bisect_right([r[0] for r in rows],t)-1)]

def greeting(e):
 t=e['time'];u=t-36.169;im=B.radial(False,0).copy()
 if t<36.603:
  name='yo0' if t<36.269 else 'yo1';h=701+14*math.sin(math.pi*min(1,u/.24));bb=B.actor(im,name,604,853,h)
  V.callout(im,'Yo',604,max(10,bb[1]-73),True,size=40)
 else:
  p=min(1,(t-36.603)/.13);s=p*p*(3-2*p)
  bb=B.actor(im,'yo1',604-169*s,853,702-89*s);V.callout(im,'Yo',435,max(10,bb[1]-72),True,size=33)
  dt=t-36.603;pop=18*math.sin(math.pi*min(1,dt/.28));name='yo2' if dt<.167 else 'yo3';bb=B.actor(im,name,804,865-pop,773+pop)
  V.callout(im,'Yo',834,max(10,bb[1]-70),True,size=42)
 return im

def yeah(e):
 t=e['time'];u=t-109.409;im=Image.new('RGB',(W,H),BG)
 B.big_word(im,'Yeah',t,size=610,y=181)
 name=cue_at(YEAH_CUES,t)[1]
 foot=float(np.interp(t,[109.409,109.509,109.809,110.477,110.710,110.944],[668,647,586,623,666,655]))
 V.native(im,name,640,foot,1.57)
 V.callout(im,'Yeah',640,46,True,size=40)
 if u<.100:im=Image.blend(Image.new('RGB',(W,H),BG),im,max(0,u/.100))
 if t>=111.378:
  incoming=dict(e,shot='cake_verse',sprite_v3='chew',caption_v3='もぐもぐ')
  target=C.cake_verse(incoming);a=min(1,(t-111.378)/1.501);a=a*a*(3-2*a);im=Image.blend(im,target,a)
 return im

def impact(e):
 t=e['time'];onset,name,label=cue_at(IMPACT_CUES,t);dt=t-onset;im=B.radial(False,0).copy() if t>=151.752 else Image.new('RGB',(W,H),BG)
 if name=='im_roll':
  u=min(1,dt/.434);angle=round(-320*u);V.native(im,name,640+17*math.sin(math.pi*u),539,1.04,angle=angle)
  V.callout(im,label,640,234,True)
 else:
  # Anticipation, follow-through and a single settling accent; never ping-pong.
  scale=1.38*(1+.065*math.exp(-dt*13)*math.sin(dt*26));foot=659-14*math.sin(math.pi*min(1,dt/.28))
  if name=='im_pre_sneeze':foot=657
  V.native(im,name,640,foot,scale);V.callout(im,label,640,122,True,size=34)
 return im

@lru_cache(maxsize=180)
def animation_part(family,index,height):
 path=ANIM[family]['frames'][index];im=Image.open(R/path).convert('RGBA');return im.resize((round(im.width*height/im.height),height),Image.Resampling.LANCZOS)

def animation_index(family,t):
 times=FF_TIMES if family=='firefly' else STAR_TIMES;meta=ANIM[family]
 if t>=times[-1]:return len(meta['frames'])-1
 k=max(0,bisect.bisect_right(times,t)-1);u=max(0,min(1,(t-times[k])/(times[k+1]-times[k])))
 return min(len(meta['frames'])-1,k*meta['steps_per_interval']+int(u*meta['steps_per_interval']))

def ending(e):
 t=e['time'];im=C.backdrop('express_cabin_v3',.79).copy()
 idx=animation_index('stelle',t);h=584;sp=animation_part('stelle',idx,h)
 old=B.resized('bin_back',552);ax,ay=V.bin_anchor('bin_back');factor=old.height/SP['bin_back'].height
 target_x=242-old.width/2+ax*factor;target_y=756-old.height+ay*factor
 ca=ANIM['stelle']['bin_anchor'];f=h/ANIM['stelle']['size'][1];im.paste(sp,(round(target_x-ca[0]*f),round(target_y-ca[1]*f)),sp)
 ff=animation_part('firefly',animation_index('firefly',t),668);im.paste(ff,(round(825-ff.width/2),round(753-ff.height)),ff)
 if 291.391<=t<292.290:V.callout(im,'あー！',825,27,True,size=40)
 if t>=294.900:V.jp(im,'原曲・映像原案  GYARI',640,26,26,INK,True);B.text(im,'Akari ga Yattekita zo',640,69,25,INK,True,'center')
 if t>300.25:im=Image.blend(im,Image.new('RGB',(W,H),BG),min(1,(t-300.25)/.72))
 return im

def frame(e):
 mode=e['shot'];t=e['time']
 if mode=='greeting':return greeting(e)
 if mode=='yeah_white':return yeah(e)
 if mode=='verse_impact' and t>=149:return impact(e)
 if mode in ('headphones','credits'):return ending(e)
 if mode=='lyric_close':
  im=Image.new('RGB',(W,H),BG);vocal_actor(im,'sing_fixed',640,848,905,t,(269.536,272.672,[5,6,1,1,1,1]))
  # Keep the foreground lyric above the calibrated lips so the letters do not
  # appear to cut or skew the upper mouth contour.
  V.jp(im,'行くよ',640,260,124,MINT,True,stroke=3);return im
 return BASE_FRAME(e)

SAMPLES=[36.20,36.43,36.64,36.84,109.46,109.62,109.92,110.52,110.80,111.23,111.80,112.50,149.99,150.37,150.80,151.03,151.40,151.81,152.40,153.10,182.40,182.65,183.1,183.45,245.20,245.48,245.78,246.20,269.7,270.2,270.7,271.5,290.35,290.73,291.02,291.27,291.48,291.76,292.14,292.42,292.69,293.03,293.37,293.72,294.05,294.43,294.84,298.5]

def write_timeline():
 data=json.loads((R/'timeline_v3.json').read_text());data['project']='流萤来了哦 V4 表演与口型精修'
 cues={'yo':YO_CUES,'yeah':YEAH_CUES,'impact':IMPACT_CUES,'ending_firefly':FF_KEYS,'ending_stelle':STAR_KEYS}
 data['editorial_cues_v4']=cues;data['mouth_alignment_v4']={'sing_fixed':list(C.MOUTH_CONFIG['sing_fixed']),'eye_landmarks_native':[[143,203],[236,190]],'method':'perpendicular face axis from eye landmarks; no double-outline crossfade'}
 data['chorus_mouth_v4']={'opening_period_seconds':C.PERIOD*2,'cycles_per_second':1/(C.PERIOD*2),'vowel':'sustained AH','audio_smoothing_ms':160,'body':'fixed'}
 (R/'timeline_v4.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
 (R/'docs/vocal_envelope_v4.json').write_text(json.dumps({'method':'160ms smoothing for sustained chorus; 70ms smoothing for short vowels; single-mouth contour with jaw relaxation; manual facial-axis calibration','segments':SMOOTH_ENV},ensure_ascii=False,separators=(',',':')))
 with (R/'docs/performance_cues_v4.csv').open('w',encoding='utf-8-sig',newline='') as file:
  w=csv.writer(file);w.writerow(['section','source_time_s','sprite','caption'])
  for section,rows in cues.items():
   for row in rows:w.writerow([section,*row])

def previews():
 board=Image.new('RGB',(1600,((len(SAMPLES)+3)//4)*258),'#e0e8dd');d=ImageDraw.Draw(board);f=B.font(17,True)
 for k,t in enumerate(SAMPLES):
  e=FRAMES[bisect.bisect_left(TIMES,t)];im=frame(e);im.save(OUT/f'v4_preview_{k+1:02d}.jpg',quality=94);im.thumbnail((400,225),Image.Resampling.LANCZOS);x=k%4*400;y=k//4*258;board.paste(im,(x,y));d.text((x+7,y+232),f'{t:.2f}s {e["shot"]}',font=f,fill='#365044')
 board.save(OUT/'V4_storyboard.jpg',quality=94);print('V4 previews:',len(SAMPLES),flush=True)

def render():
 dst=OUT/'流萤来了哦_V4_表演与口型精修.mp4';log=OUT/'render_v4_ffmpeg.log';graph='[0:v]scale=1280:720[clock];[clock][1:v]overlay=x=0:y=0:shortest=1:ts_sync_mode=nearest:format=auto,scale=1920:1080:flags=lanczos,format=yuv420p[v]'
 cmd=['ffmpeg','-hide_banner','-nostdin','-y','-i',str(B.SOURCE),'-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate','30000/1001','-i','pipe:0','-filter_complex',graph,'-map','[v]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','20','-threads','4','-fps_mode','passthrough','-enc_time_base','1:16000','-video_track_timescale','16000','-c:a','copy','-movflags','+faststart','-metadata','title=流萤来了哦 — V4 表演与口型精修',str(dst)];start=time.monotonic()
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
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--render',action='store_true');args=p.parse_args();write_timeline()
 if args.preview:previews()
 if args.render:render()
 if not(args.preview or args.render):p.print_help()
