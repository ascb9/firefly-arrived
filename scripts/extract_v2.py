"""Extract GPT image character artwork; no characters are drawn here."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1];G=R/'assets/generated';S=R/'assets/sprites';A=R/'analysis/refine'
NAMES={
'movement_v2':['run0','run1','run2','run3','walk0','walk1','clap0','clap1','turnwave','skid','coil','starjump'],
'chew_blush_v2':['chew'+str(i) for i in range(8)]+['caught','blush0','blush1','blush2'],
'stelle_trash_v2':['bin'+str(i) for i in range(8)]+['stelle_peek','stelle_giggle','stelle_recoil','bin_close'],
'device_lying_kafka_v2':['device'+str(i) for i in range(4)]+['lie'+str(i) for i in range(4)]+['kafka'+str(i) for i in range(4)],
'sam_sparkler_v2':['samhead'+str(i) for i in range(4)]+['spin'+str(i) for i in range(8)],
'quick_actions_a_v2':['kira0','kira1','pika0','pika1','mofu0','mofu1','nade0','nade1','guru0','guru1','goro0','goro1'],
'quick_actions_b_v2':['waku0','waku1','uzu0','uzu1','noro0','noro1','uro0','uro1','teku0','teku1','koso0','koso1'],
'quick_actions_c_v2':['suya0','suya1','pero0','pero1','nico0','nico1','bata0','bata1','doko','shan','tatan','jyan'],
'quick_actions_d_v2':['gyu0','gyu1','pikon','den','sun0','sun1','oh','oi','gasa','ka','don','chew_zoom'],
'quick_actions_e_v2':['kira2','pika2','mofu2','nade2','guru2','goro2','waku2','uzu2','noro2','uro2','teku2','koso2'],
'device_wing_fix_v2':['device'+str(i) for i in range(4)],
}
manifest=[]
for filename,names in NAMES.items():
 p=G/(filename+'.png')
 if not p.exists():continue
 im=Image.open(p).convert('RGBA');arr=np.array(im);mask=arr[:,:,3]>32;labs,n=ndi.label(mask);sizes=np.bincount(labs.ravel());sizes[0]=0
 majors=sorted(range(1,n+1),key=lambda i:sizes[i],reverse=True)[:len(names)]
 objects=ndi.find_objects(labs);centers={i:ndi.center_of_mass(mask,labs,i) for i in majors}
 majors=sorted(majors,key=lambda i:centers[i][0]);ordered=[]
 cols=2 if len(names)==4 else 4
 for row in range(len(names)//cols):ordered.extend(sorted(majors[row*cols:row*cols+cols],key=lambda i:centers[i][1]))
 # Native connected body bounds allow unequal atlas row heights without clipping.
 for k,label in enumerate(ordered):
  body=objects[label-1];owner=labs==label;cy,cx=centers[label]
  for j,sl in enumerate(objects,1):
   if sl is None or j in majors or sizes[j]<9:continue
   yy=(sl[0].start+sl[0].stop)/2;xx=(sl[1].start+sl[1].stop)/2
   near=min(majors,key=lambda q:((yy-centers[q][0])**2+(xx-centers[q][1])**2))
   if near==label and abs(yy-cy)<im.height*.18 and abs(xx-cx)<im.width*.145:owner|=labs==j
  owner=ndi.binary_dilation(owner,iterations=2);alpha=arr[:,:,3].copy();alpha[~owner]=0
  yy,xx=np.nonzero(owner);x0=max(0,xx.min()-7);y0=max(0,yy.min()-7);x1=min(im.width,xx.max()+8);y1=min(im.height,yy.max()+8)
  layer=im.copy();layer.putalpha(Image.fromarray(alpha));layer=layer.crop((x0,y0,x1,y1));name=names[k]
  box=[body[1].start-x0,body[0].start-y0,body[1].stop-x0,body[0].stop-y0]
  if filename=='device_wing_fix_v2':
   factor=354/layer.height;layer=layer.resize((round(layer.width*factor),354),Image.Resampling.LANCZOS);box=[round(v*factor) for v in box]
  layer.save(S/(name+'.png'));manifest=[m for m in manifest if m['name']!=name]
  manifest.append({'name':name,'file':'assets/sprites/'+name+'.png','source':'assets/generated/'+filename+'.png','atlas_cell':k+1,'native_size':list(layer.size),'body_box':box,'art':'GPT image','alpha':True})
(R/'assets/manifest_v2.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,default=lambda x:int(x)))
f=ImageFont.truetype(str(R/'assets/DejaVuSans.ttf'),14);out=Image.new('RGB',(1600,((len(manifest)+7)//8)*210),'#fffdf9');d=ImageDraw.Draw(out)
for k,m in enumerate(manifest):
 sp=Image.open(R/m['file']);sp.thumbnail((192,174),Image.Resampling.LANCZOS);x=k%8*200;y=k//8*210;out.paste(sp,(x+(200-sp.width)//2,y+2),sp);d.text((x+6,y+180),m['name'],font=f,fill='#634f2e')
out.save(A/'new_sprite_audit.jpg',quality=93);print('New sprites:',len(manifest))
