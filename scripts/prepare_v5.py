"""Extract complete artwork cells, rigid registration only, no region compositing."""
from pathlib import Path
import shutil,json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'assets/animation_v5';O.mkdir(exist_ok=True)
G=R/'assets/generated'
INPUTS={'firefly':('exec-e14e5289-8f11-4812-92a7-30b3fa931f71.png',6,4),'stelle':('exec-f4331a31-85d9-4bf2-b167-7a9dfbaec628.png',6,3)}
meta={}
for family,(filename,cols,rows) in INPUTS.items():
 source=G/(family+'_fullbody_v5.png');sheet=Image.open(source).convert('RGBA');cells=[];anchors=[]
 for k in range(cols*rows):
  c=k%cols;r=k//cols;sp=sheet.crop((round(c*sheet.width/cols),round(r*sheet.height/rows),round((c+1)*sheet.width/cols),round((r+1)*sheet.height/rows)))
  a=np.array(sp.getchannel('A'));lab,n=ndi.label(a>24);sizes=np.bincount(lab.ravel());sizes[0]=0;keep=ndi.binary_dilation(np.isin(lab,np.flatnonzero(sizes>sizes.max()*.008)),iterations=1);a[~keep]=0;sp.putalpha(Image.fromarray(a));yy,xx=np.nonzero(a>100);bottom=float(np.percentile(yy,99.9));footx=float(np.median(xx[yy>bottom-9]));cells.append(sp);anchors.append((footx,bottom))
 # Identical scale for every cell, entire drawing translated as a rigid object.
 fixed_height=600;scale=564/np.median([y-np.min(np.nonzero(np.array(s.getchannel('A'))>100)[0]) for s,(x,y) in zip(cells,anchors)])
 paths=[]
 for k,(sp,(x,y)) in enumerate(zip(cells,anchors)):
  im=Image.new('RGBA',(700 if family=='stelle' else 600,fixed_height))
  sp=sp.resize((round(sp.width*scale),round(sp.height*scale)),Image.Resampling.LANCZOS)
  im.alpha_composite(sp,(round(im.width/2-x*scale),round(592-y*scale)))
  p=O/f'{family}_{k:03d}.png';im.save(p);paths.append(p.relative_to(R).as_posix())
 if family=='stelle':times=[290.29,290.48,290.65,290.73,290.83,290.94,291.05,291.16,291.27,291.38,291.50,291.62,291.76,291.93,292.10,292.32,292.58,292.90]
 else:times=[290.29,290.43,290.58,290.75,290.94,291.12,291.31,291.50,291.69,291.88,292.07,292.26,292.45,292.64,292.83,293.02,293.21,293.40,293.59,293.78,293.97,294.16,294.35,294.55]
 meta[family]={'frames':paths,'times':times,'registration':'whole drawing rigid translation, one common scale; no masks, locks, local layers or morphing'}

(O/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print({k:len(v['frames']) for k,v in meta.items()})
