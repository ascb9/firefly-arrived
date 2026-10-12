"""A short motion/audio review reel cut from the verified full V4 export."""
from pathlib import Path
import json,subprocess
R=Path(__file__).resolve().parents[1];O=R/'output';SOURCE=O/'流萤来了哦_V5_全身重绘与日文标题.mp4'
WINDOWS=[(22.5,28.5),(277.1,283.1),(290.1,301.0985)]
def main():
 cmd=['ffmpeg','-hide_banner','-nostdin','-y']
 for a,b in WINDOWS:cmd+=['-threads','1','-ss',str(a),'-t',str(b-a),'-i',str(SOURCE)]
 filters=[];inputs=''
 for i in range(len(WINDOWS)):
  filters+=[f'[{i}:v]scale=1280:720,setpts=PTS-STARTPTS[v{i}]',f'[{i}:a]asetpts=PTS-STARTPTS[a{i}]'];inputs+=f'[v{i}][a{i}]'
 filters.append(inputs+f'concat=n={len(WINDOWS)}:v=1:a=1[v][a]')
 dst=O/'流萤来了哦_V5_修改片段预览.mp4'
 cmd+=['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','22','-threads','4','-c:a','aac','-b:a','128k','-movflags','+faststart',str(dst)]
 with (O/'review_reel_ffmpeg.log').open('w') as log:subprocess.run(cmd,stderr=log,check=True)
 (R/'docs/review_reel_v5.json').write_text(json.dumps({'file':dst.name,'source_intervals_s':WINDOWS,'note':'Review-only concatenation; full deliverable retains original AAC packets and frame PTS. No extra annotation overlay.'},ensure_ascii=False,indent=2));print('Review reel complete:',dst)
if __name__=='__main__':main()
