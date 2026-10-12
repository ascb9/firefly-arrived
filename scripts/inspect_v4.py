"""Bounded review of the exact source intervals and existing V3 face geometry."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];A=R/'analysis/refine_v4';A.mkdir(parents=True,exist_ok=True)
T=[36.19,36.36,36.62,36.87,109.43,109.57,109.87,110.12,110.55,111.03,111.63,112.30,149.55,149.99,150.36,150.81,151.35,151.82,152.12,152.49,152.88,153.20,181.80,182.40,182.55,182.75,183.0,183.4,290.3,290.55,290.8,291.05,291.45,291.8,292.1,292.5,293,293.5]
def extract(t):
 p=A/f'source_{t:.3f}.jpg';subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-ss',str(t),'-i',str(R/'source/original.mp4'),'-frames:v','1','-vf','scale=960:540','-threads','1',str(p)],check=True);return p
def main():
 with ThreadPoolExecutor(max_workers=4) as pool:paths=list(pool.map(extract,T))
 f=ImageFont.truetype(str(R/'assets/DejaVuSans.ttf'),16);board=Image.new('RGB',(1920,((len(T)+3)//4)*292),'#e8e8e8');d=ImageDraw.Draw(board)
 for k,(t,p) in enumerate(zip(T,paths)):
  im=Image.open(p).resize((480,270));x=k%4*480;y=k//4*292;board.paste(im,(x,y));d.text((x+7,y+272),f'{t:.3f}s source',font=f,fill='#304234')
 board.save(A/'source_review_v4.jpg',quality=94)
 names=['turnwave','caught','blush0','blush1','blush2','bin_back','bin_turn1','bin_turn2','bin_turn3','wave_bust','jyan','tatan_hold']
 refs=Image.new('RGB',(1600,600),'#fffdf9');d=ImageDraw.Draw(refs)
 for k,name in enumerate(names):
  im=Image.open(R/'assets/sprites'/(name+'.png'));im.thumbnail((253,253));x=k%6*266;y=k//6*300;refs.paste(im,(x+(266-im.width)//2,y),im);d.text((x+10,y+263),name,font=f,fill='#6b5227')
 refs.save(A/'input_refs_v4.jpg',quality=94)
 im=Image.open(R/'assets/sprites/sing_fixed.png').convert('RGBA');qa=Image.new('RGB',im.size,'#fffdf9');qa.paste(im,(0,0),im);d=ImageDraw.Draw(qa)
 for x in range(0,qa.width,25):d.line((x,130,x,285),fill='#c9ded7',width=1);d.text((x+1,132),str(x),font=f,fill='#699180')
 for y in range(150,285,25):d.line((70,y,290,y),fill='#c9ded7',width=1);d.text((73,y),str(y),font=f,fill='#699180')
 for label,x,y,color in [('V3',.5*im.width,.518*im.height,'#dd774d'),('V4',.485*im.width,.550*im.height,'#387ed1')]:
  d.ellipse((x-3,y-3,x+3,y+3),outline=color,width=2);d.text((x+5,y+3),label,font=f,fill=color)
 qa.resize((qa.width*2,qa.height*2)).save(A/'sing_face_calibration_v4.png')
 print('V4 source review',len(T),'frames')
if __name__=='__main__':main()
