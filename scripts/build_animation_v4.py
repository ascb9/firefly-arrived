"""Register clean GPT-drawn intermediate poses; keep the bin and boots still.

Final animation uses the actual drawn poses. No optical or face-shape morphing.
"""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw,ImageFont
from performance_v4 import FF_KEYS,STAR_KEYS
R=Path(__file__).resolve().parents[1];S=R/'assets/sprites';O=R/'assets/animation_v4';O.mkdir(exist_ok=True)
def scaled(sp,h):return sp.resize((round(sp.width*h/sp.height),h),Image.Resampling.LANCZOS)
def paste(dst,src,x,y):dst.alpha_composite(src,(round(x),round(y)))
def ff_plate(name):
 sp=scaled(Image.open(S/(name+'.png')).convert('RGBA'),564);a=np.array(sp.getchannel('A'));yy,xx=np.nonzero((a>150)&(np.indices(a.shape)[0]>sp.height*.87));ax=float(np.median(xx)) if len(xx) else sp.width/2
 im=Image.new('RGBA',(600,600));paste(im,sp,300-ax,592-sp.height);return im
def bin_metrics(sp):
 a=np.array(sp);h,w=a.shape[:2];yy,xx=np.indices((h,w));mask=(a[:,:,3]>180)&(a[:,:,:3].max(2)-a[:,:,:3].min(2)<18)&(a[:,:,0]>75)&(a[:,:,0]<198)&(xx<w*.46)&(yy>h*.44);y,x=np.nonzero(mask)
 if len(x)<30:raise ValueError('Could not locate bin')
 return float(np.median(x)),float(np.percentile(y,99)),float(np.percentile(y,99)-np.percentile(y,2))
def star_plates():
 sprites=[Image.open(S/(name+'.png')).convert('RGBA') for t,name in STAR_KEYS];base=sprites[0];ax,ay,bh=bin_metrics(base);factor=564/base.height;anchor=(177,555);result=[]
 for sp in sprites:
  x,y,h=bin_metrics(sp);f=factor*bh/h;part=scaled(sp,max(20,round(sp.height*f)));real=part.height/sp.height;im=Image.new('RGBA',(700,600));paste(im,part,anchor[0]-x*real,anchor[1]-y*real);result.append(im)
 yy,xx=np.indices((600,700));editable=((xx>275)&(yy<315))|((xx>460)&(yy<389));editable[(xx<315)&(yy>258)]=False
 return result,ndi.gaussian_filter(editable.astype(np.float32),1.8),anchor
def lock(base,im,mask):
 a=np.array(base,dtype=np.float32)/255;b=np.array(im,dtype=np.float32)/255;m=mask[:,:,None];alpha=a[:,:,3:]*(1-m)+b[:,:,3:]*m
 rgb=(a[:,:,:3]*a[:,:,3:]*(1-m)+b[:,:,:3]*b[:,:,3:]*m)/np.maximum(alpha,1e-6)
 out=np.uint8(np.rint(np.clip(np.concatenate((rgb,alpha),2)*255,0,255)));raw_a=np.array(base);raw_b=np.array(im);out[mask==0]=raw_a[mask==0];out[mask==1]=raw_b[mask==1]
 return Image.fromarray(out,'RGBA')
def save_png(im,path):
 tmp=path.with_suffix('.partial');im.save(tmp,format='PNG');tmp.replace(path)
 with Image.open(path) as verified:verified.load()
def family(name,keys,plates,mask,anchor=None):
 base=plates[0];paths=[]
 for k,plate in enumerate(plates):
  dst=O/f'{name}_{k:03d}.png';save_png(lock(base,plate,mask),dst);paths.append(dst.relative_to(R).as_posix())
 return {'keyframes':len(plates),'steps_per_interval':1,'frames':paths,'source_pose_names':[name for t,name in keys],'source_times_s':[t for t,name in keys],'size':list(base.size),'bin_anchor':anchor,'method':'actual GPT-drawn poses, rigid bin/feet registration; no shape warp','locked_regions':'planted boots' if name=='firefly' else 'bin/lid/arm rim/lower body'}
def main():
 for prefix in ['firefly_','stelle_']:
  for p in O.glob(prefix+'*.png'):p.unlink()
 ff=[ff_plate(name) for t,name in FF_KEYS];yy,xx=np.indices((600,600));fm=ndi.gaussian_filter((yy<484).astype(np.float32),2);star,sm,anchor=star_plates()
 manifest={'method':'clean GPT-drawn primary and intermediate poses with rigid registration','families':{'firefly':family('firefly',FF_KEYS,ff,fm),'stelle':family('stelle',STAR_KEYS,star,sm,anchor)}}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));previews=[]
 for spec in manifest['families'].values():
  for idx in np.linspace(0,len(spec['frames'])-1,12).astype(int):previews.append((spec['frames'][idx],Image.open(R/spec['frames'][idx]).convert('RGBA')))
 board=Image.new('RGB',(1600,((len(previews)+7)//8)*216),'#fffdf9');d=ImageDraw.Draw(board);f=ImageFont.truetype(str(R/'assets/DejaVuSans.ttf'),12)
 for k,(name,sp) in enumerate(previews):
  sp.thumbnail((196,184));x=k%8*200;y=k//8*216;board.paste(sp,(x+(200-sp.width)//2,y),sp);d.text((x+4,y+191),Path(name).stem,font=f,fill='#6b5227')
 board.save(R/'analysis/refine_v4/ending_motion_v4.jpg',quality=94);print('Ending clean drawn poses:',{k:len(v['frames']) for k,v in manifest['families'].items()},flush=True)
if __name__=='__main__':main()
