"""Separate GPT image atlas components for conventional 2D composition."""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];G=R/'assets/generated';S=R/'assets/sprites';M=[]
def save_part(im,box,name,source,cell):
 part=im.crop(tuple(round(v) for v in box)).convert('RGBA');a=np.array(part.getchannel('A'));labs,n=ndi.label(a>24);sz=np.bincount(labs.ravel());sz[0]=0
 keep=np.isin(labs,[i for i in range(1,n+1) if sz[i]>=5]);keep=ndi.binary_dilation(keep,iterations=1);a[~keep]=0;part.putalpha(Image.fromarray(a));bound=part.getbbox()
 if not bound:raise ValueError('Empty artwork '+name)
 bound=(max(0,bound[0]-6),max(0,bound[1]-6),min(part.width,bound[2]+6),min(part.height,bound[3]+6));part=part.crop(bound);part.save(S/(name+'.png'))
 M.append({'name':name,'file':'assets/sprites/'+name+'.png','source':'assets/generated/'+source+'.png','atlas_cell':cell,'native_size':list(part.size),'art':'GPT image','alpha':True})
spec=[('entry_stelle_v3',4,3,['bin_back','bin_turn1','bin_turn2','bin_turn3','entry_push','entry_walk','entry_stop','crouch','landed','doki','sneeze','point_open']),('train_hop_v3',4,2,['submerged','splash_up','hop_land','table_lean','hop_left','hop_right','hop_doki','tatan_hold'])]
for source,cols,rows,names in spec:
 im=Image.open(G/(source+'.png')).convert('RGBA')
 for k,name in enumerate(names):
  x=k%cols;y=k//cols;save_part(im,(x*im.width/cols,y*im.height/rows,(x+1)*im.width/cols,(y+1)*im.height/rows),name,source,k+1)
source='vocal_parts_v3';im=Image.open(G/(source+'.png')).convert('RGBA')
for k in range(8):
 row=k//4;col=k%4;y0=.465 if row==0 else .75;y1=.75 if row==0 else 1
 save_part(im,(col*im.width/4,y0*im.height,(col+1)*im.width/4,y1*im.height),'mouth'+str(k),source,k+5)
source='vocal_bases_v3';im=Image.open(G/(source+'.png')).convert('RGBA');a=np.array(im.getchannel('A'));labs,n=ndi.label(a>24);sz=np.bincount(labs.ravel());sz[0]=0
main=sorted(range(1,n+1),key=lambda i:sz[i],reverse=True)[:4];main.sort(key=lambda i:ndi.center_of_mass(a>24,labs,i)[0]);objects=ndi.find_objects(labs)
for k,(name,label) in enumerate(zip(['sing_fixed','lie_fixed','point_fixed','star_bust'],main)):
 sl=objects[label-1];y0=sl[0].start-10;y1=sl[0].stop+10;save_part(im,(0,max(0,y0),im.width,min(im.height,y1)),name,source,k+1)
source='point_full_v3';im=Image.open(G/(source+'.png')).convert('RGBA');M=[rec for rec in M if rec['name']!='point_fixed'];save_part(im,(0,0,im.width,im.height),'point_fixed',source,1)
(R/'assets/manifest_v3.json').write_text(json.dumps(M,ensure_ascii=False,indent=2))
out=Image.new('RGB',(1600,((len(M)+7)//8)*225),'#fffdf9');d=ImageDraw.Draw(out);f=ImageFont.truetype(str(R/'assets/DejaVuSans.ttf'),15)
for k,rec in enumerate(M):
 sp=Image.open(R/rec['file']);sp.thumbnail((194,190));x=k%8*200;y=k//8*225;out.paste(sp,(x+(200-sp.width)//2,y),sp);d.text((x+7,y+197),rec['name'],font=f,fill='#6b5227')
out.save(R/'analysis/review/new_assets_v3.jpg',quality=94);print('New final sprite parts:',len(M))
