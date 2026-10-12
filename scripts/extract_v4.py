"""Extract GPT-drawn V4 key poses with original alpha intact."""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];S=R/'assets/sprites';G=R/'assets/generated';M=[]
def extract(source,cols,rows,names):
 im=Image.open(G/(source+'.png')).convert('RGBA')
 for k,name in enumerate(names):
  col=k%cols;row=k//cols
  sp=im.crop((round(col*im.width/cols),round(row*im.height/rows),round((col+1)*im.width/cols),round((row+1)*im.height/rows)))
  a=np.array(sp.getchannel('A'));lab,n=ndi.label(a>24);sizes=np.bincount(lab.ravel());sizes[0]=0
  cutoff=max(16,round(sizes.max()*.012))
  keep=np.isin(lab,np.flatnonzero(sizes>=cutoff));keep=ndi.binary_dilation(keep,iterations=1);a[~keep]=0;sp.putalpha(Image.fromarray(a))
  bb=sp.getbbox()
  if not bb:raise ValueError('Empty '+name)
  bb=(max(0,bb[0]-5),max(0,bb[1]-5),min(sp.width,bb[2]+5),min(sp.height,bb[3]+5));sp=sp.crop(bb);dst=S/(name+'.png');tmp=dst.with_suffix('.partial');sp.save(tmp,format='PNG');tmp.replace(dst)
  with Image.open(dst) as verified:verified.load()
  M.append({'name':name,'file':'assets/sprites/'+name+'.png','source':'assets/generated/'+source+'.png','cell':k+1,'size':list(sp.size),'art':'GPT image','alpha':True})
def main():
 extract('ending_firefly_a_v4',4,3,['endff'+str(k).zfill(2) for k in range(12)])
 extract('ending_firefly_b_v4',4,3,['endff'+str(k).zfill(2) for k in range(12,24)])
 extract('ending_stelle_v4',4,3,['endstar'+str(k).zfill(2) for k in range(12)])
 extract('ending_firefly_mid_a_v4',4,3,['endffmid_a'+str(k).zfill(2) for k in range(12)])
 extract('ending_firefly_mid_b_v4',4,3,['endffmid_b'+str(k).zfill(2) for k in range(12)])
 extract('ending_stelle_mid_v4',3,2,['endstarmid'+str(k).zfill(2) for k in range(6)])
 extract('accents_v4',4,4,['yo0','yo1','yo2','yo3','yeah0','yeah1','yeah2','yeah3','yeah4','yeah5','im_doki','im_tatan','im_pre_sneeze','im_sneeze','im_roll','im_jyan'])
 (R/'assets/manifest_v4.json').write_text(json.dumps(M,ensure_ascii=False,indent=2))
 board=Image.new('RGB',(1600,((len(M)+7)//8)*218),'#fffdf9');d=ImageDraw.Draw(board);f=ImageFont.truetype(str(R/'assets/DejaVuSans.ttf'),14)
 for k,rec in enumerate(M):
  sp=Image.open(R/rec['file']);sp.thumbnail((192,185));x=k%8*200;y=k//8*218;board.paste(sp,(x+(200-sp.width)//2,y),sp);d.text((x+8,y+190),rec['name'],font=f,fill='#6b5227')
 board.save(R/'analysis/refine_v4/new_keyposes_v4.jpg',quality=94);print('V4 AI key poses:',len(M),flush=True)
if __name__=='__main__':main()
