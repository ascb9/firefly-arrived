"""Deterministic 2D cutout composition with original PTS and unmodified audio.

Usage: python scripts/render_v1.py --preview
       python scripts/render_v1.py --render
All character/new key art is imagegen. Pillow is used only as the compositor.
"""
from pathlib import Path
from functools import lru_cache
import argparse, bisect, json, math, random, subprocess, sys, time
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
W,H=1280,720
BG='#fffdf9'; INK='#6b5227'; MINT='#52b79b'; GOLD='#ecc257'; DARK='#171d1b'
DATA=json.loads((ROOT/'timeline.json').read_text())
FRAMES=DATA['frames']; TIMES=[e['time'] for e in FRAMES]
SOURCE=ROOT/'source/original.mp4'
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)
SP={p.stem:Image.open(p).convert('RGBA') for p in (ROOT/'assets/sprites').glob('*.png')}

@lru_cache(maxsize=150)
def font(size,latin=False):
    path=ROOT/'assets'/('Latin-BoldItalic.ttf' if latin else 'ZCOOLKuaiLe-Regular.ttf')
    return ImageFont.truetype(str(path),int(size))

@lru_cache(maxsize=600)
def word_image(text,size,fill=MINT,latin=True,stroke=0,outline=INK):
    f=font(size,latin);bb=f.getbbox(text,stroke_width=stroke)
    im=Image.new('RGBA',(bb[2]-bb[0]+16,bb[3]-bb[1]+16),(0,0,0,0))
    d=ImageDraw.Draw(im);d.text((8-bb[0],8-bb[1]),text,font=f,fill=fill,stroke_width=stroke,stroke_fill=outline)
    return im

def text(canvas,string,x,y,size=40,fill=INK,latin=False,anchor='left',maxwidth=None,stroke=0,outline=INK):
    im=word_image(string,size,fill,latin,stroke,outline)
    if maxwidth and im.width>maxwidth:
        im=im.resize((int(maxwidth),int(im.height*maxwidth/im.width)),Image.Resampling.LANCZOS)
    if anchor=='center':x-=im.width/2
    canvas.paste(im,(round(x),round(y)),im)
    return im.width,im.height

@lru_cache(maxsize=340)
def resized(name,h,angle=0,mirror=False):
    src=SP[name];h=max(12,int(h));w=max(1,round(src.width*h/src.height))
    im=src.resize((w,h),Image.Resampling.LANCZOS)
    if mirror:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if angle:im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    return im

def actor(canvas,name,cx,cy,h=420,anchor='bottom',angle=0,mirror=False):
    # Quantisation keeps camera micro-motion smooth without endless re-scaling.
    sp=resized(name,int(round(h/4))*4,int(angle),mirror)
    x=round(cx-sp.width/2)
    y=round(cy-sp.height if anchor=='bottom' else cy-sp.height/2 if anchor=='center' else cy)
    canvas.paste(sp,(x,y),sp)
    return (x,y,x+sp.width,y+sp.height)

def bubble(canvas,s,cx,y,width=None,burst=False):
    label=word_image(s,31,INK,False)
    bw=max(90,label.width+28) if not width else width;bh=label.height+23
    cx=max(bw/2+10,min(W-bw/2-10,cx));y=max(8,min(626,y))
    dr=ImageDraw.Draw(canvas)
    if burst:
        pts=[]
        for j in range(24):
            a=math.pi*2*j/24;r=1 if j%2==0 else .88
            pts.append((cx+math.cos(a)*bw/2*r,y+bh/2+math.sin(a)*bh/2*r))
        dr.polygon(pts,fill=BG,outline=INK,width=3)
    else:dr.rounded_rectangle((cx-bw/2,y,cx+bw/2,y+bh),radius=23,fill=BG,outline=INK,width=3)
    dr.polygon([(cx-8,y+bh-2),(cx+4,y+bh+15),(cx+12,y+bh-2)],fill=BG,outline=INK,width=2)
    canvas.paste(label,(round(cx-label.width/2),round(y+(bh-label.height)/2)),label)

@lru_cache(maxsize=8)
def radial(dark=False,phase=0):
    im=Image.new('RGB',(W,H),DARK if dark else BG);d=ImageDraw.Draw(im)
    rng=random.Random(302+phase);cx=640;cy=355
    color='#37443b' if dark else '#d6d1bd'
    for i in range(135):
        a=rng.random()*2*math.pi;inner=rng.uniform(260,430);outer=1500
        d.line((cx+math.cos(a)*inner,cy+math.sin(a)*inner,cx+math.cos(a)*outer,cy+math.sin(a)*outer),fill=color,width=rng.choice([1,1,2,3]))
    return im

def particles(canvas,t,dark=False,count=13,quiet=False):
    d=ImageDraw.Draw(canvas)
    for i in range(count):
        x=(i*177+85+24*math.sin(t*.55+i))%W
        y=(i*131+62-((t*(8 if dark else 4)+i*22)%H))%H
        radius=2+int(2*(.5+.5*math.sin(t*2.1+i*1.8)))
        if quiet:radius=2
        col=['#95d2ab','#acd9b8','#68bda2','#b9dec0'][i%4] if not dark else ['#b4e8a1','#72d4b0','#daef98','#91dfb9'][i%4]
        if dark:
            d.ellipse((x-radius*3,y-radius*3,x+radius*3,y+radius*3),fill='#253b2d')
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=col)

def stars(canvas,t):
    d=ImageDraw.Draw(canvas)
    for j in range(3):
        u=(t*.28+j*.33)%1;x=1100-u*480;y=150+j*145+40*math.sin(t*.8+j)
        for q in range(10):
            aa=q*math.tau/10;r=(28 if q%2==0 else 10)*(0.8+.2*math.sin(t*2+j))
            if q==0:pts=[]
            pts.append((x+r*math.cos(aa),y+r*math.sin(aa)))
        d.polygon(pts,fill='#c0e0ac',outline='#8dbb95')

@lru_cache(maxsize=1)
def title_frame():
    im=Image.open(ROOT/'assets/generated/title_art.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
    # Literal title and controlled typography; it is not model-generated text.
    text(im,'FIREFLY HAS ARRIVED!',55,70,30,'#508f7b',True,maxwidth=570,stroke=1,outline=BG)
    a=word_image('流萤',170,'#70c7a4',False,10,INK)
    b=word_image('来了哦',158,'#f1d77c',False,10,INK)
    # White outside outline keeps text legible over the title burst.
    a=a.rotate(9,Image.Resampling.BICUBIC,expand=True);b=b.rotate(7,Image.Resampling.BICUBIC,expand=True)
    im.paste(a,(30,144),a);im.paste(b,(20,350),b)
    text(im,'流萤 × 星',67,616,33,'#385d50',False,stroke=3,outline=BG)
    return im

def big_word(canvas,w,t,dark=False,y=291,size=106):
    # Preserve original phonetic-word staging rather than adding narrative pages.
    col='#81d7ab' if dark else MINT
    tw,th=text(canvas,w,W/2,y,size,col,True,'center',maxwidth=1250)
    return tw,th

def source_actor(canvas,p,t,mode,k=0,total=1):
    name=p['sprite'];x0,y0,x1,y1=p['box'];cx=(x0+x1)*W/320
    if mode=='intro':
        if y1>=88:
            # Source characters are deliberately cropped at the bottom edge.
            h=370;top=y0*H/90+12
            bb=actor(canvas,name,cx,top,h,'top')
        else:
            h=430;foot=min(620,y1*H/90+22)
            bb=actor(canvas,name,cx,foot,h)
        bubble(canvas,'啪—' if name=='arrival' else '咚咚',cx,max(25,bb[1]-72))
        return
    if mode in ('words_white','yeah_white'):
        height=410 if name not in ('cake_a','cake_b') else 310
        if name in ('float','flail'):height=330
        bb=actor(canvas,name,640,610,height)
    elif mode in ('verse','cake_verse'):
        cx=max(735,min(1152,cx));height=420
        if total>2:height=310;cx=765+k*165
        if name in ('cake_a','cake_b','camera_seated'):height=300
        if name=='puddle':height=175
        if name in ('float','flail'):height=325
        foot=min(646,max(546,y1*H/90+12))
        if name in ('run_a','run_b'):
            # Keep feet motion in the two drawn poses. Translate only 3 pixels.
            cx+=3*math.sin(t*8)
        # Intentional secret-identity gag, then return to the same layout.
        if (54.25<=t<54.65) or (143.45<=t<143.8):name='sam_jump';height=395
        if 134.45<=t<136.2:name='offer_cake';height=390
        if 72.15<=t<72.82:name='photo';height=410
        bb=actor(canvas,name,cx,foot,height)
    else:
        bb=actor(canvas,name,cx,640,470)
    labels={'arrival':'来啦！','surprise':'欸？','cheer':'耶！','point':'看这里','run_a':'咻咻咻','run_b':'咻咻咻','cake_a':'橡木蛋糕卷','cake_b':'好吃！','idea':'闪亮亮','flail':'哇啊！','bashful':'诶嘿','walk_a':'哒哒哒','walk_b':'哒哒哒','profile':'星？','bow':'打扰啦','confused':'唔…','jump':'好耶！','float':'梦里飘飘','camera_seated':'拍张照？','offer_cake':'也分给你','photo':'看镜头','sparkler':'小小烟花','wave':'你好呀','turn':'转呀转','puddle':'咕噜咕噜','sam_jump':'是、是我！','wow':'呼哇！'}
    if mode!='yeah_white' and total<4:
        bubble(canvas,labels.get(name,'好耶'),(bb[0]+bb[2])/2,max(18,bb[1]-80),burst=name in ('cheer','idea','flail','sam_jump'))

def stelle_reaction(canvas,t,event):
    name='stelle_game'
    if event%7 in (2,3):name='stelle_look'
    if event%13==3:name='stelle_wow'
    if event%17 in (14,15,16):name='stelle_smile'
    if (54.25<=t<55.2) or (143.45<=t<144.2):name='stelle_wow'
    dr=ImageDraw.Draw(canvas)
    dr.rounded_rectangle((420,380,467,785),radius=30,outline=INK,width=4)
    # Preserve the monitor edge and fixed spectator role of the source layout.
    dr.line((23,237,23,720),fill=INK,width=5)
    dr.line((24,237,50,239),fill=INK,width=4)
    if 134.45<=t<138.8:
        actor(canvas,'stelle_cake',268,732,500)
        if 136.2<=t<138.8:bubble(canvas,'谢谢，流萤',279,145)
    else:actor(canvas,name,276,738,620)

def little_piano(canvas,t):
    if not (116.4<t<148.3):return
    x=1210-((t-116.4)*30)%1020;y=340
    d=ImageDraw.Draw(canvas);d.rectangle((x,y,x+150,y+53),fill=BG,outline=INK,width=3)
    for j in range(12):d.line((x+j*12,y,x+j*12,y+37),fill=INK,width=1)
    for j in [1,2,4,5,6,8,9,11]:d.rectangle((x+j*12-4,y,x+j*12+2,y+25),fill=INK)
    d.line((x+10,y+53,x+8,y+106),fill=INK,width=4);d.line((x+135,y+53,x+143,y+106),fill=INK,width=4)
    text(canvas,'♪',x+20,y-44,32,INK,False)

def photo_wall(t):
    im=Image.new('RGB',(W,H),'#edf1ec');d=ImageDraw.Draw(im)
    shift=int(t*21)%340
    for row in range(4):
        for col in range(5):
            x=col*335-shift-100;y=row*204-68
            card=Image.new('RGB',(307,174),BG)
            dc=ImageDraw.Draw(card);dc.rectangle((7,7,300,137),fill='#dfecdf')
            name=['wave','cake_b','photo','stelle_bin','sparkler','selfie'][((col+row)*3+row)%6]
            actor(card,name,154,140,127)
            card=card.rotate(-8,Image.Resampling.BICUBIC,expand=True,fillcolor='#edf1ec')
            im.paste(card,(x,y))
    return im

def frame(e):
    t=e['time'];mode=e['shot'];ev=e['event'];qt=round(t*12)/12
    dark=mode in ('super_chorus','ready','words_dark','lyric_dark','lyric_card_dark')
    canvas=Image.new('RGB',(W,H),DARK if dark else BG)
    if mode in ('intro','intro_impact','greeting','verse_impact','ending_impact','lyric_impact'):
        if mode!='intro':canvas=radial(False,ev%2).copy()
        particles(canvas,qt,count=8,quiet=True)
    if mode=='intro':
        for k,p in enumerate(e['poses']):source_actor(canvas,p,t,mode,k,len(e['poses']))
    elif mode=='intro_impact':
        height=520+200*max(0,(t-22.92)/.9)
        actor(canvas,'cheer' if ev%2 else 'idea',640,760,height)
        bubble(canvas,'流萤来啦！',640,54,burst=True)
    elif mode in ('title','title_return'):
        canvas=title_frame().copy()
        particles(canvas,qt,count=9)
        actor(canvas,'run_a' if ev%2 else 'run_b',1110+15*math.sin(qt*4),704,185)
        if ev%5<2:actor(canvas,'cheer',430,414,171)
        if mode=='title_return' and 279.25<t<287.8:
            actor(canvas,'wave',318,651-18*math.sin(qt*3),270)
            if t>282.0:actor(canvas,'stelle_wave',115,704,200)
    elif mode=='greeting':
        actor(canvas,'wave',620,776,690)
        bubble(canvas,'星，我来啦',613,24,burst=True)
    elif mode in ('verse','cake_verse'):
        if (51.48<t<55.98):canvas=radial(False,ev%2).copy()
        particles(canvas,qt,count=8,quiet=True)
        little_piano(canvas,t)
        stelle_reaction(canvas,t,ev)
        if mode=='verse' and 37.07<=t<39.55:
            dr=ImageDraw.Draw(canvas)
            dr.rectangle((985,123,1162,635),outline=INK,width=4)
            dr.polygon([(1162,123),(1233,166),(1233,616),(1162,635)],fill=BG,outline=INK,width=4)
            dr.ellipse((1211,376,1221,386),fill=INK)
        pp=e['poses'][:3]
        if not pp:pp=[{'sprite':'arrival','box':[99,18,145,81]}]
        for k,p in enumerate(pp):source_actor(canvas,p,t,mode,k,len(pp))
        if 58.0<t<59.0:
            actor(canvas,'transformer',1150,497,95)
            text(canvas,'变身器？！',1000,642,26,INK,False)
        if 62.02<t<63.32:
            # Recreate the source's submerged gag as a dream puddle.
            canvas=Image.new('RGB',(W,H),BG);stelle_reaction(canvas,t,ev)
            actor(canvas,'puddle',908,609,199);bubble(canvas,'咕噜咕噜…',910,298)
        if 138.1<t<140.2:actor(canvas,'stelle_bin',610,707,172)
    elif mode=='verse_impact':
        actor(canvas,'idea' if ev%2 else 'cheer',640,654,467)
        bubble(canvas,'普通的一天，也很开心！',640,46,burst=True)
    elif mode in ('words_white','yeah_white','words_dark'):
        if dark:canvas=radial(True,ev%2).copy()
        particles(canvas,qt,dark,count=15 if dark else 8,quiet=not dark)
        big_word(canvas,e['word'] or 'Yeah',t,dark,y=282 if dark else 288,size=112 if dark else 107)
        for p in e['poses']:
            if dark:
                h=670 if p['sprite'] not in ('float','flail','cake_a','cake_b') else 500
                actor(canvas,p['sprite'],640+150*math.sin(qt*.75),800,h)
                bubble(canvas,{'cake_a':'橡木蛋糕卷！','wave':'星，看我！','turn':'转呀转','bashful':'萤光闪闪'}.get(p['sprite'],'好耶！'),790,35,burst=ev%3==0)
            else:source_actor(canvas,p,t,mode)
        if mode=='yeah_white':actor(canvas,'sam_helmet',1015,636,94)
    elif mode=='chorus':
        for y in (8,371):
            text(canvas,'Hai! Hai! Hai!',-12,y,172,MINT,True,maxwidth=1450)
        particles(canvas,qt,count=13)
        # Three drawn microphone mouth states, switched at source events.
        mouth=['sing_a','sing_b','sing_rest'][ev%3]
        actor(canvas,mouth,250,789,638)
        count=max(1,min(4,e['chorus_count']))
        for j in range(count):
            name='jump' if ev%2 else 'cheer'
            # One brief rear-row SAM cameo, retaining the heroine foreground.
            if j==3 and 173.1<t<174.0:name='sam_jump'
            foot=585-7*(ev%2)
            actor(canvas,name,560+j*215,foot,440)
            bubble(canvas,'嗨！',560+j*215,48,burst=True)
        if 163.4<t<165.0:actor(canvas,'stelle_wave',1142,712,184)
        if t>179.346:
            wash=Image.new('RGB',(W,H),BG)
            canvas=Image.blend(canvas,wash,min(1,(t-179.346)/1.35))
    elif mode=='super_chorus':
        canvas=radial(True,0).copy();particles(canvas,qt,True,count=32)
        shift=int((qt-181.75)*65)%560
        text(canvas,'LA LA LA LA LA',640-shift,280,154,'#86c8a5',True,'center',maxwidth=2100)
        text(canvas,'Super Chorus Time',640,617,39,GOLD,True,'center')
        actor(canvas,'float',640,545,478,'center',angle=round(7*math.sin(qt*.7)))
        stars(canvas,qt)
        if 198.0<t<201.4:
            actor(canvas,'sparkler',1027,657,247)
    elif mode=='ready':
        text(canvas,'Are you ready?',640,291,101,'#87d0a9',True,'center',maxwidth=1100)
        actor(canvas,'sam_helmet',1030,646,97)
        particles(canvas,qt,True,count=11)
    elif mode=='lyric_dark':
        canvas=radial(True,0).copy();particles(canvas,qt,True,count=26)
        if t<240.006:
            big_word(canvas,'Yeah',t,True,size=205,y=229)
            actor(canvas,'jump',640,604,490)
        elif t<242.209:
            text(canvas,'一点萤光',640,310,112,MINT,False,'center')
        elif t<244.845:
            text(canvas,'闪耀着',330,290,126,MINT,False,'center')
            actor(canvas,'sparkler',880,643,425)
        elif t<247.047:
            actor(canvas,'sing_a' if ev%2 else 'sing_b',372,747,597)
            text(canvas,'挑选',983,258,91,MINT,False,'center')
            text(canvas,'温柔的话',983,389,87,MINT,False,'center',maxwidth=485)
        else:
            actor(canvas,'sing_a',640,795,861)
            text(canvas,'与你分享',640,337,98,MINT,False,'center',stroke=4,outline=DARK)
    elif mode in ('lyric_card_dark','lyric_card_white'):
        text(canvas,'难过的时候',640,235,89,MINT,False,'center')
        text(canvas,'寂寞的时候',640,367,89,MINT,False,'center')
        particles(canvas,qt,dark,count=10)
    elif mode=='lyric_impact':
        text(canvas,'我会在这里',640,25,128,MINT,False,'center',maxwidth=1230)
        actor(canvas,'determined',640,818,635)
        bubble(canvas,'放心交给我吧',990,253,burst=True)
    elif mode=='photo_wall':
        canvas=photo_wall(qt)
        actor(canvas,'float',646,558,461,'center',angle=5)
        line='继续我们的故事' if t<259.592 else '因为星光相连'
        text(canvas,line,640,603,75,MINT,False,'center',stroke=4,outline=BG,maxwidth=1150)
    elif mode=='forever':
        text(canvas,'一直  一直',640,78,145,MINT,False,'center',maxwidth=1220)
        for j in range(4):actor(canvas,'cheer' if ev%2 else 'jump',220+j*280,679,348)
    elif mode=='collage':
        for row in range(3):
            for col in range(7):
                nm=['wave','cake_a','photo','jump','stelle_bin','sparkler','selfie'][(row*3+col)%7]
                actor(canvas,nm,70+col*190,205+row*248,225,angle=(col%3-1)*7)
        wash=Image.new('RGB',(W,H),BG);canvas=Image.blend(canvas,wash,.68)
        text(canvas,'和我们' if t<267.801 else '在你身边',640,278,148,MINT,False,'center',maxwidth=1200)
    elif mode=='lyric_close':
        actor(canvas,'sing_a' if ev%2 else 'sing_b',640,842,900)
        text(canvas,'迈步向前',640,317,110,MINT,False,'center',stroke=3,outline=BG)
    elif mode=='ending_impact':
        text(canvas,'请看着我',640,34,135,MINT,False,'center')
        actor(canvas,'wave_bust',640,789,701)
        bubble(canvas,'星，拍一张吧？',281,255,burst=True)
    elif mode=='headphones':
        canvas=radial(False,0).copy()
        nm='stelle_headphones' if t<290.724 else 'stelle_headphones_wow'
        actor(canvas,nm,329,881,1000)
        bubble(canvas,'耳机！',917,296,burst=True)
        if t>=291.391:bubble(canvas,'啊—！',971,441,burst=True)
        particles(canvas,qt,count=7)
    elif mode=='credits':
        particles(canvas,qt,count=17)
        text(canvas,'流萤来了哦',640,74,77,INK,False,'center')
        text(canvas,'原曲 / 原作  GYARI',640,221,37,INK,False,'center',maxwidth=1150)
        text(canvas,'Akari ga Yattekita zo',640,283,36,INK,True,'center')
        text(canvas,'角色  《崩坏：星穹铁道》流萤 · 星 · 萨姆',640,363,35,INK,False,'center')
        text(canvas,'二创画面  GPT image  /  V1',640,423,32,INK,False,'center')
        actor(canvas,'selfie',641,705,236)
    return canvas

def previews():
    samples=[2,12,22.5,27,37.5,42.5,47.5,54.4,58.3,62.3,67.5,72.5,82.5,94.2,117.5,135.0,138.6,154.5,164.0,175,188,199,212,217,226,242.8,246,254,257.5,264.5,268,270.5,274,283,291.7,297]
    audit=Image.new('RGB',(1600,((len(samples)+3)//4)*258),'#dfebe0');d=ImageDraw.Draw(audit)
    f=ImageFont.truetype(str(ROOT/'assets/DejaVuSans.ttf'),18)
    for k,t in enumerate(samples):
        i=min(range(len(TIMES)),key=lambda j:abs(TIMES[j]-t));im=frame(FRAMES[i])
        im.save(OUT/f'preview_{k+1:02d}.jpg',quality=90)
        im.thumbnail((400,225),Image.Resampling.LANCZOS);x=k%4*400;y=k//4*258
        audit.paste(im,(x,y));d.text((x+8,y+230),f'{t:.2f}s {FRAMES[i]["shot"]}',font=f,fill='#2f503d')
    audit.save(OUT/'V1_storyboard.jpg',quality=91)
    print('Preview storyboard:',OUT/'V1_storyboard.jpg')

def render():
    dst=OUT/'流萤来了哦_V1.mp4';log=OUT/'render_ffmpeg.log'
    # The uploaded video's video stream is only the timing carrier here. The
    # complete new canvas covers it at 0,0. Nearest framesync pairs each drawn
    # frame to the matching original PTS (source clock is millisecond-rounded).
    graph='[0:v]scale=1280:720[clock];[clock][1:v]overlay=x=0:y=0:shortest=1:ts_sync_mode=nearest:format=auto,scale=1920:1080:flags=lanczos,format=yuv420p[v]'
    cmd=['ffmpeg','-hide_banner','-y','-i',str(SOURCE),'-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate','30000/1001','-i','pipe:0','-filter_complex',graph,'-map','[v]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','21','-threads','4','-fps_mode','passthrough','-enc_time_base','1:16000','-video_track_timescale','16000','-c:a','copy','-movflags','+faststart','-metadata','title=流萤来了哦 — V1','-metadata','comment=Firefly / Stelle fan PV. Character art: GPT image. Original music and timing: GYARI.',str(dst)]
    start=time.monotonic()
    with log.open('w') as err:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
        try:
            for i,e in enumerate(FRAMES):
                proc.stdin.write(frame(e).tobytes())
                if i%450==0:
                    print(f'render {i}/{len(FRAMES)} source_time={e["time"]:.3f} elapsed={time.monotonic()-start:.1f}s',flush=True)
        except BrokenPipeError:
            raise RuntimeError(log.read_text()[-4000:])
        finally:
            if proc.stdin:proc.stdin.close()
        status=proc.wait()
    if status:raise RuntimeError(log.read_text()[-4000:])
    print('Completed:',dst,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--render',action='store_true');args=p.parse_args()
    if args.preview:previews()
    if args.render:render()
    if not(args.preview or args.render):p.print_help()
