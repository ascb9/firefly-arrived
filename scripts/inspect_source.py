from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw,ImageFont
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'analysis/refine';A.mkdir(parents=True,exist_ok=True)
source=R/'source/original.mp4'
raw=A/'source_small.rgb'
if not raw.exists():
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-vf','scale=160:90','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24',str(raw)],check=True)
frames=np.memmap(raw,dtype='uint8',mode='r').reshape(-1,90,160,3)
pts=np.load(R/'analysis/source_pts.npy')
font=ImageFont.truetype(str(R/'assets/DejaVuSans.ttf'),17)
groups={
 'verse':[37.3,38.2,39.0,39.9,40.9,41.8,42.7,43.6,44.5,45.4,46.3,47.2,48.1,49.0,49.9,50.8,51.7,52.6,53.5,54.4,55.3,56.2,57.1,58.0,58.9,59.8,60.7,61.6,62.5,63.4,64.3,65.2,66.1,67.0,67.9,68.8,69.7,70.6,71.5,72.4,73.3,74.2,75.1,76.0,76.9,77.8,78.7,79.6,80.5],
 'cake':[113,113.5,114,114.5,115,115.5,116,116.5,117,118,120,122,124,126,128,130,132,134,134.5,135,135.5,136,136.5,137,138,140,142,144,146,148],
 'chorus':[153.43+i*.44 for i in range(25)]+[165.3+i*.44 for i in range(20)],
 'lying':[181.8,182.2,182.6,183.0,184,187,192,198,203,209],
 'fast':[212.95+i*.44 for i in range(57)],
 'ending':[240.2,242.2,242.65,243.1,243.55,244,244.5,245,278,279,280,281,282,283,284,285,286,287,288,289,290.3,290.8,291.4,292,292.6,293.2,293.8,294.5,295.2,296,297,298,299,300]
}
for name,times in groups.items():
    board=Image.new('RGB',(1536,((len(times)+3)//4)*238),'#e6e6e6');d=ImageDraw.Draw(board)
    for k,t in enumerate(times):
        target=A/f's_{t:07.3f}.jpg'
        if not target.exists():
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(source),'-frames:v','1','-vf','scale=768:432',str(target)],check=True)
        im=Image.open(target);im.thumbnail((384,216));x=k%4*384;y=k//4*238
        board.paste(im,(x,y));d.text((x+5,y+218),f'{t:.3f}',font=font,fill='#222222')
    board.save(A/f'{name}.jpg',quality=93)
print('Contact sheets written',len(frames),'frames')
