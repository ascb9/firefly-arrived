"""Crop imagegen atlases and translate the source clip into a timed shot/pose map.

This script does compositing preparation only; all character artwork is GPT image
output. The original is used for timing, pose references and layout measurements.
"""
from pathlib import Path
import csv, hashlib, json, subprocess
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'analysis'
G = ROOT / 'assets/generated'
S = ROOT / 'assets/sprites'
S.mkdir(parents=True, exist_ok=True)

NAMES = {
 'firefly_poses_a.png': ['arrival','surprise','cheer','point','run_a','run_b','cake_a','cake_b','idea','flail','bashful','sing_full'],
 'firefly_poses_b.png': ['walk_a','walk_b','profile','bow','confused','jump','float','camera_seated','offer_cake','photo','sparkler','wave'],
 'firefly_poses_c.png': ['sing_a','sing_b','sing_rest','device','wow','turn','puddle','determined','stelle_headphones','stelle_headphones_wow','wave_bust','selfie'],
 'stelle_sam.png': ['stelle_game','stelle_look','stelle_wow','stelle_smile','stelle_cake','stelle_photo','stelle_bin','stelle_wave','sam_wave','sam_jump','sam_helmet','transformer'],
}

def extract_atlases():
    manifest = []
    for filename, names in NAMES.items():
        im = Image.open(G / filename).convert('RGBA')
        for k, name in enumerate(names):
            col, row = k % 4, k // 4
            box = (round(col*im.width/4),round(row*im.height/3),round((col+1)*im.width/4),round((row+1)*im.height/3))
            if name == 'puddle':
                box = (690,495,1115,724)
            cell = im.crop(box)
            # Remove fragments of a neighbouring cell, retaining the dominant
            # figure and nearby hand-drawn accent components. Keep native alpha.
            alpha = np.array(cell.getchannel('A'))
            labs, count = ndi.label(alpha > 20)
            areas = np.bincount(labs.ravel()); areas[0] = 0
            major = int(areas.argmax())
            occupied = labs == major
            if occupied.any():
                yy, xx = np.nonzero(occupied)
                center = np.array([yy.mean(), xx.mean()])
                keep = occupied.copy()
                for j, sl in enumerate(ndi.find_objects(labs), 1):
                    if sl is None or j == major: continue
                    yy2, xx2 = np.nonzero(labs[sl] == j)
                    yy2 += sl[0].start; xx2 += sl[1].start
                    edge = (yy2.min()<2 or xx2.min()<2 or yy2.max()>cell.height-3 or xx2.max()>cell.width-3)
                    dist = np.linalg.norm(np.array([yy2.mean(),xx2.mean()])-center)
                    if (not edge) and dist < max(cell.size)*.64 and areas[j] > 14:
                        keep |= labs == j
                # Two-pixel fringe includes antialiasing of retained components.
                keep = ndi.binary_dilation(keep,iterations=2)
                alpha[~keep] = 0
                cell.putalpha(Image.fromarray(alpha))
            bb = cell.getbbox()
            if not bb: raise RuntimeError('Empty sprite: '+name)
            cell = cell.crop(bb)
            pad = Image.new('RGBA',(cell.width+12,cell.height+12),(0,0,0,0))
            pad.alpha_composite(cell,(6,6)); pad.save(S/(name+'.png'))
            manifest.append({'name':name,'file':'assets/sprites/'+name+'.png','source':'assets/generated/'+filename,'atlas_cell':k+1,'size':list(pad.size),'art':'GPT image','alpha':True})
    (ROOT/'assets/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    # One bounded asset inspection board.
    fw = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    out = Image.new('RGB',(1600,8*224),'#f8fbf5'); d=ImageDraw.Draw(out)
    for k,m in enumerate(manifest):
        sp=Image.open(ROOT/m['file']);sp.thumbnail((190,190),Image.Resampling.LANCZOS)
        x=(k%8)*200; y=(k//8)*224
        out.paste(sp,(x+(200-sp.width)//2,y+(195-sp.height)//2),sp)
        d.text((x+4,y+199),m['name'],font=fw,fill='#665022')
    out.crop((0,0,1600,6*224)).save(A/'sprite_audit.jpg')
    return manifest

def shot(t):
    if t < 20.954: return 'intro'
    if t < 23.824: return 'intro_impact'
    if t < 36.169: return 'title'
    if t < 37.070: return 'greeting'
    if t < 77.644: return 'verse'
    if t < 81.181: return 'verse_impact'
    if t < 109.409: return 'words_white'
    if t < 112.879: return 'yeah_white'
    if t < 149.983: return 'cake_verse'
    if t < 153.420: return 'verse_impact'
    if t < 181.748: return 'chorus'
    if t < 209.976: return 'super_chorus'
    if t < 212.879: return 'ready'
    if t < 238.038: return 'words_dark'
    if t < 248.381: return 'lyric_dark'
    if t < 251.718: return 'lyric_card_dark'
    if t < 252.352: return 'lyric_card_white'
    if t < 255.422: return 'lyric_impact'
    if t < 263.830: return 'photo_wall'
    if t < 266.066: return 'forever'
    if t < 269.536: return 'collage'
    if t < 272.672: return 'lyric_close'
    if t < 277.377: return 'ending_impact'
    if t < 290.290: return 'title_return'
    if t < 294.900: return 'headphones'
    return 'credits'

def source_colors(im):
    r,g,b=np.moveaxis(im.astype('int16'),-1,0)
    brown=(r<195)&(g<177)&(b<151)&(r>g*.90)&(g>b*.96)&(r>45)
    orange=(r>218)&(g>103)&(g<223)&(b<101)&(r-g>24)
    return brown,orange

def body_boxes(im,t,mode):
    brown,orange=source_colors(im)
    if mode in ('intro','intro_impact'): roi=np.ones((90,160),bool)
    elif mode in ('verse','cake_verse'): roi=np.indices((90,160))[1]>69
    else: roi=np.ones((90,160),bool)
    labels,n=ndi.label(ndi.binary_dilation((brown|orange)&roi,iterations=1))
    boxes=[]
    for k,sl in enumerate(ndi.find_objects(labels),1):
        if sl is None: continue
        seed=int(((labels[sl]==k)&orange[sl]).sum())
        x0,x1=sl[1].start,sl[1].stop; y0,y1=sl[0].start,sl[0].stop
        if seed>3 and y1-y0>18 and x1-x0>5 and x1-x0<106:
            boxes.append([x0,y0,x1,y1])
    if mode in ('verse','cake_verse'):
        boxes=[b for b in boxes if (b[0]+b[2])/2>76]
    if mode in ('intro','intro_impact'):
        return sorted(boxes,key=lambda b:b[0])[:4]
    if mode in ('verse','cake_verse') and boxes:
        return sorted(boxes,key=lambda b:b[0])[:4]
    # Kinetic typography may touch the outline. A tightly constrained centre
    # reference window gives stable pose comparisons in these scenes.
    if mode in ('words_white','yeah_white','verse_impact'):
        return [[51,21,111,80]]
    return boxes

def signature(im,box):
    x0,y0,x1,y1=box
    patch=im[max(0,y0):min(90,y1),max(0,x0):min(160,x1)]
    if not patch.size:return np.zeros(48*48,dtype=np.float32)
    brown,orange=source_colors(patch)
    mask=brown|orange
    small=Image.fromarray((mask*255).astype('uint8')).resize((48,48),Image.Resampling.BILINEAR)
    return np.asarray(small,dtype=np.float32).ravel()/255

POSE_REFS=[(36.3,'wave'),(37.4,'bow'),(42.2,'cheer'),(43.1,'float'),
 (44.25,'idea'),(45.3,'walk_a'),(46.8,'profile'),(48.4,'arrival'),
 (50.4,'confused'),(51.5,'turn'),(52.2,'turn'),(54.25,'idea'),
 (55.5,'run_a'),(57.2,'bashful'),(58.3,'offer_cake'),(60.3,'flail'),
 (62.3,'puddle'),(64.4,'idea'),(66.3,'run_a'),(67.2,'run_b'),
 (72.4,'photo'),(78.3,'wave'),(80.0,'idea'),(82.3,'bashful'),
 (84.2,'cake_b'),(86.2,'float'),(88.1,'flail'),(90.2,'walk_a'),
 (92.2,'surprise'),(94.0,'cake_a'),(98.3,'cake_b'),(100.3,'float'),
 (102.3,'flail'),(104.3,'wow'),(106.2,'cheer')]

WORD_REFS=[(82.3,'PIKAPIKA'),(84.1,'NICONICO'),(86.2,'DEDE-N'),
 (88.2,'BATABATA'),(90.2,'TEKUTEKU'),(92.2,'O?'),(94.1,'ITADAKIMASU'),
 (97.1,'MOFUMOFU'),(101.1,'UZUZU'),(102.3,'BATABATA'),
 (104.3,'GYUNGYU-N'),(106.2,'JA-N!'),(110.3,'Yeah'),(216.1,'GOROGORO'),
 (229.1,'NADENADE'),(235.8,'TATAN!')]

def analyse():
    src=ROOT/'source/original.mp4'
    if not (A/'source_all_small.rgb').exists():
        subprocess.run(['ffmpeg','-v','error','-i',str(src),'-vf','scale=160:90','-fps_mode','passthrough','-pix_fmt','rgb24','-f','rawvideo',str(A/'source_all_small.rgb')],check=True)
    if not (A/'source_pts.npy').exists():
        ss=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','csv=p=0',str(src)]).decode()
        ts=np.array([float(x.strip().split(',')[0]) for x in ss.splitlines() if x.strip().split(',')[0]])
        np.save(A/'source_pts.npy',ts)
    ts=np.load(A/'source_pts.npy')
    frames=np.memmap(A/'source_all_small.rgb',dtype=np.uint8,mode='r').reshape(-1,90,160,3)
    if len(ts)!=len(frames):raise RuntimeError('Source PTS/frame mismatch')
    dif=np.zeros(len(ts),np.float32)
    for i in range(1,len(ts)):dif[i]=np.abs(frames[i].astype('int16')-frames[i-1].astype('int16')).mean()
    cut_indices=[0]
    for i in np.flatnonzero(dif>3.0):
        if ts[i]-ts[cut_indices[-1]]>.07:cut_indices.append(int(i))
    # Exact source frame times are preserved, even when the rebuild uses a
    # reduced number of drawn poses. No audio-driven rescaling is performed.
    templates=[]
    refsheet=Image.new('RGB',(1200,((len(POSE_REFS)+7)//8)*170),'#ffffff');dr=ImageDraw.Draw(refsheet)
    fnt=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    for k,(t,name) in enumerate(POSE_REFS):
        idx=int(np.argmin(abs(ts-t))); im=frames[idx]
        boxes=body_boxes(im,t,shot(t))
        box=boxes[-1] if boxes else [80,18,145,83]
        if name=='puddle':box=[83,48,132,81]
        templates.append(signature(im,box))
        x=k%8*150;y=k//8*170;crop=Image.fromarray(im).crop(tuple(box));crop.thumbnail((140,145))
        refsheet.paste(crop,(x,y));dr.text((x+3,y+146),f'{t:.1f} {name}',font=fnt,fill='#665022')
    refsheet.save(A/'source_pose_references.jpg')
    templates=np.stack(templates)
    word_templates=[]
    for t,word in WORD_REFS:
        im=frames[int(np.argmin(abs(ts-t)))];_,om=source_colors(im)
        word_templates.append(np.asarray(Image.fromarray(om.astype('uint8')*255).resize((80,45)),np.float32).ravel()/255)
    word_templates=np.stack(word_templates)
    entries=[]; lastboxes=[]; event=0; cutset=set(cut_indices)
    for i,(t,im) in enumerate(zip(ts,frames)):
        if i in cutset:event+=1
        mode=shot(float(t)); poses=[]; word=''
        if mode in ('intro','intro_impact','verse','cake_verse','greeting','verse_impact','words_white','yeah_white'):
            boxes=body_boxes(im,float(t),mode)
            if not boxes:
                if mode in ('verse','cake_verse'):boxes=lastboxes if lastboxes else [[93,20,144,80]]
                elif mode=='greeting':boxes=[[42,10,126,95]]
                elif mode=='intro':boxes=[]
                elif mode=='intro_impact':boxes=[[37,8,124,91]]
                else:boxes=[[51,21,111,80]]
            lastboxes=boxes if mode in ('verse','cake_verse') else []
            for box in boxes:
                vec=signature(im,box); di=((templates-vec[None,:])**2).mean(1)
                cat=POSE_REFS[int(di.argmin())][1]
                if mode=='intro':cat='arrival' if event%2 else 'surprise'
                if mode=='intro_impact':cat='cheer' if event%2 else 'idea'
                if mode=='greeting':cat='wave'
                if mode=='verse_impact':cat='idea' if event%2 else 'cheer'
                if cat in ('run_a','run_b'):cat='run_a' if event%2 else 'run_b'
                if mode=='cake_verse' and float(t)<140.3:cat='cake_a' if event%2 else 'cake_b'
                poses.append({'sprite':cat,'box':box})
        if mode in ('words_white','words_dark','yeah_white'):
            _,om=source_colors(im)
            vec=np.asarray(Image.fromarray(om.astype('uint8')*255).resize((80,45)),np.float32).ravel()/255
            di=((word_templates-vec[None,:])**2).mean(1); word=WORD_REFS[int(di.argmin())][1]
            mapping={'PIKAPIKA':'bashful','NICONICO':'cake_b','DEDE-N':'float','NORONORO':'confused','TEKUTEKU':'walk_a','O?':'surprise','ITADAKIMASU':'cake_a','NADENADE':'wave','MOFUMOFU':'bashful','UZUZU':'confused','TATAN!':'wave','DOKIDOKI':'bashful','BATABATA':'flail','GYUNGYU-N':'wow','JA-N!':'cheer','Yeah':'float','WAKUWAKU':'idea','GOROGORO':'turn','SHA-N!':'turn'}
            if mode=='words_dark':poses=[{'sprite':mapping[word],'box':[40,10,120,94]}]
            if mode=='words_white':poses=[{'sprite':mapping[word],'box':[52,21,110,80]}]
            if word=='TEKUTEKU':poses[0]['sprite']='walk_a' if event%2 else 'walk_b'
            if mode=='yeah_white':word='Yeah';poses=[{'sprite':'float','box':[50,18,111,82]}]
        if mode=='chorus':
            _,om=source_colors(im)
            lab,n=ndi.label(om)
            cc=[]
            for sl in ndi.find_objects(lab):
                if sl is None:continue
                yy=(sl[0].start+sl[0].stop)/2;xx=(sl[1].start+sl[1].stop)/2
                hh=sl[0].stop-sl[0].start;ww=sl[1].stop-sl[1].start
                if xx>48 and 45<yy<72 and 2<hh<16 and ww>4:cc.append(xx)
            # Preserve the measured one/two/three/four-person entry pattern.
            steps=[(153.420,1),(154.221,2),(157.754,3),(161.290,4),
                   (165.729,1),(169.266,2),(172.803,3),(176.340,4)]
            count=1
            for at,c in steps:
                if float(t)>=at:count=c
        else:count=0
        entries.append({'frame':i,'time':round(float(t),6),'shot':mode,'event':event,'poses':poses,'word':word,'chorus_count':count})
    data={'project':'流萤来了哦 V1','source_video_duration':301.0,'source_audio_duration':301.0985,'source_frames':len(ts),'fps':'30000/1001','time_base':'1/16000','cut_indices':cut_indices,'frames':entries}
    (ROOT/'timeline.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
    # Compact reviewer-friendly shot table, not 9,021 separate lines.
    groups=[]
    for e in entries:
        if not groups or groups[-1]['shot']!=e['shot']:
            if groups:groups[-1]['end']=e['time']
            groups.append({'start':e['time'],'end':301.0,'shot':e['shot']})
    with (ROOT/'docs/shot_timeline.csv').open('w',newline='',encoding='utf-8-sig') as f:
        wr=csv.DictWriter(f,fieldnames=['start','end','shot']);wr.writeheader();wr.writerows(groups)
    (A/'source_analysis.json').write_text(json.dumps({'source_frames':len(ts),'source_pts_first':float(ts[0]),'source_pts_last':float(ts[-1]),'source_event_count':len(cut_indices),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'shot_groups':groups},ensure_ascii=False,indent=2))
    print(json.dumps({'sprites':48,'frames':len(ts),'source_events':len(cut_indices),'shots':len(groups)},ensure_ascii=False))

if __name__=='__main__':
    extract_atlases();analyse()
