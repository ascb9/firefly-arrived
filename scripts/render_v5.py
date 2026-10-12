"""Complete whole-figure ending redraw; source clock and soundtrack preserved."""
from pathlib import Path
from functools import lru_cache
import bisect,json,subprocess,time
import numpy as np
from PIL import Image,ImageDraw
import render_v4 as P
B=P.B;C=P.C;V=P.V;R=B.ROOT;W,H=B.W,B.H;OUT=R/'output'
META=json.loads((R/'assets/animation_v5/manifest.json').read_text())

@lru_cache(maxsize=1)
def title():
 return Image.open(R/'assets/generated/title_japanese_v5.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
V.title=title

@lru_cache(maxsize=64)
def part(family,index,height):
 sp=Image.open(R/META[family]['frames'][index]).convert('RGBA')
 return sp.resize((round(sp.width*height/sp.height),height),Image.Resampling.LANCZOS)

def index(family,t):
 times=META[family]['times'];return max(0,min(len(times)-1,bisect.bisect_right(times,t)-1))

def ending(e):
 t=e['time'];im=C.backdrop('express_cabin_v3',.79).copy()
 for family,cx,foot,height in [('stelle',304,694,510),('firefly',848,694,584)]:
  sp=part(family,index(family,t),height);im.paste(sp,(round(cx-sp.width/2),round(foot-sp.height)),sp)
 if t>=294.9:
  V.jp(im,'原曲・映像原案  GYARI',640,26,26,P.INK,True)
  B.text(im,'Akari ga Yattekita zo',640,69,25,P.INK,True,'center')
 if t>300.25:im=Image.blend(im,Image.new('RGB',(W,H),P.BG),min(1,(t-300.25)/.72))
 return im

def frame(e):
 if e['shot'] in ('headphones','credits'):return ending(e)
 return P.frame(e)

def preview():
 samples=[22.98,24.4,278,280.2]+np.linspace(290.29,295.2,24).tolist()
 board=Image.new('RGB',(1600,((len(samples)+3)//4)*252),'#fffdf9');d=ImageDraw.Draw(board)
 for k,t in enumerate(samples):
  e=P.FRAMES[bisect.bisect_left(P.TIMES,t)];im=frame(e);im.thumbnail((400,225));x=k%4*400;y=k//4*252
  board.paste(im,(x,y));d.text((x+8,y+231),f'{t:.3f}s',fill='#34241d')
 board.save(OUT/'V5_storyboard.jpg',quality=94)

def render():
 dst=OUT/'流萤来了哦_V5_全身重绘与日文标题.mp4'
 graph='[0:v]scale=1280:720[clock];[clock][1:v]overlay=x=0:y=0:shortest=1:ts_sync_mode=nearest:format=auto,scale=1920:1080:flags=lanczos,format=yuv420p[v]'
 cmd=['ffmpeg','-hide_banner','-nostdin','-y','-i',str(B.SOURCE),'-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate','30000/1001','-i','pipe:0','-filter_complex',graph,'-map','[v]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','20','-threads','4','-fps_mode','passthrough','-enc_time_base','1:16000','-video_track_timescale','16000','-c:a','copy','-movflags','+faststart',str(dst)]
 start=time.monotonic()
 with (OUT/'render_v5.log').open('w') as err:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
  for i,e in enumerate(P.FRAMES):
   proc.stdin.write(frame(e).tobytes())
   if i%900==0:print(f'{i}/{len(P.FRAMES)} elapsed={time.monotonic()-start:.1f}s',flush=True)
  proc.stdin.close()
  if proc.wait():raise RuntimeError('Render failed')
 print(dst,flush=True)
if __name__=='__main__':
 import sys
 preview()
 if '--render' in sys.argv:render()
