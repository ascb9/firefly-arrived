"""Extract bounded encoded-video samples of every requested V3 interval."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'output';SRC=O/'流萤来了哦_V3_演出精修.mp4'
T=[2.2,19.6,22.5,37.12,37.65,61.7,65.6,66.5,71.3,78.6,113.5,138.75,155.25,182.7,187.1,245.3,247.7,252.5,254.3,290.35,290.98,291.5,292.8,294.2]
def extract(pair):
 k,t=pair;dst=O/f'v3_encoded_{k+1:02d}.jpg'
 subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-ss',str(t),'-i',str(SRC),'-frames:v','1','-vf','scale=960:540','-threads','1','-q:v','2',str(dst)],check=True)
 return t,dst
def main():
 with ThreadPoolExecutor(max_workers=4) as pool:items=list(pool.map(extract,enumerate(T)))
 board=Image.new('RGB',(1600,((len(T)+3)//4)*258),'#e0e8dd');d=ImageDraw.Draw(board);f=ImageFont.truetype(str(R/'assets/DejaVuSans.ttf'),17)
 for k,(t,dst) in enumerate(items):
  im=Image.open(dst).convert('RGB');im.thumbnail((400,225),Image.Resampling.LANCZOS);x=k%4*400;y=k//4*258;board.paste(im,(x,y));d.text((x+8,y+231),f'{t:.2f}s encoded',font=f,fill='#365044')
 board.save(O/'V3_encoded_review.jpg',quality=94)
 (R/'docs/encoded_review_samples_v3.json').write_text(json.dumps({'video':SRC.name,'sample_seconds':T,'frames':len(items),'method':'Decode final H.264 MP4 with FFmpeg at requested source-clock times.'},ensure_ascii=False,indent=2))
 print('Encoded video samples:',len(items))
if __name__=='__main__':main()
