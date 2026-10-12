from pathlib import Path
import subprocess,json,urllib.request,gzip,re
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];A=R/'analysis/review';A.mkdir(parents=True,exist_ok=True)
D=json.loads((R/'timeline.json').read_text());F=D['frames'];font=ImageFont.truetype(str(R/'assets/DejaVuSans.ttf'),17)
groups={
 'intro':[F[i]['time']+.055 for i in D['cut_indices'] if 1.7<=F[i]['time']<23.82],
 'verse_all':[F[i]['time']+.06 for i in D['cut_indices'] if 37.07<=F[i]['time']<77.99],
 'singing':[244.85,245.1,245.3,246,247.05,247.7,248.2,251.75,252.38,252.82,253.2,253.55,254,254.7,255.2],
 'chorus':[182,183,185,188,190,192,194,198,204,209],
}
for name,times in groups.items():
 board=Image.new('RGB',(1920,((len(times)+3)//4)*292),'#e6e6e6');d=ImageDraw.Draw(board)
 for k,t in enumerate(times):
  target=A/f'source_{t:.3f}.jpg'
  if not target.exists():subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(R/'source/original.mp4'),'-frames:v','1','-vf','scale=960:540',str(target)],check=True)
  im=Image.open(target).resize((480,270));x=k%4*480;y=k//4*292;board.paste(im,(x,y));d.text((x+5,y+272),f'{t:.3f}',font=font,fill='#222222')
 board.save(A/(name+'.jpg'),quality=93)
 print('Source review',name,len(times),flush=True)
refs=[('secret_base','https://www.bilibili.com/video/BV1i4421w7D9/'),('secret_story','https://www.bilibili.com/video/BV1xm411X7yE/'),('train','https://www.bilibili.com/video/BV17t421b7tq/')]
for name,url in refs:
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'gzip'})
  response=urllib.request.urlopen(req,timeout=20);raw=response.read()
  if raw[:2]==b'\x1f\x8b':raw=gzip.decompress(raw)
  html=raw.decode('utf-8');m=re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',html)
  if not m:m=re.search(r'"pic":"([^"]+)"',html)
  if not m:raise ValueError('No public cover image')
  pic=m.group(1).replace('\\u002F','/').replace('\\/','/');pic=pic if pic.startswith('http') else 'https:'+pic
  data=urllib.request.urlopen(urllib.request.Request(pic,headers={'User-Agent':'Mozilla/5.0','Referer':url}),timeout=20).read();(A/(name+'_reference.jpg')).write_bytes(data)
  print('Game reference',name,len(data),flush=True)
 except Exception as e:print('Reference unavailable',name,type(e).__name__,str(e)[:120],flush=True)
