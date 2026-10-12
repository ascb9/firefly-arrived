"""Targeted pixel checks for the requested held-pose and mouth-only performances."""
from pathlib import Path
import bisect,hashlib,json
import numpy as np
from PIL import Image
import render_v3 as V
R=Path(__file__).resolve().parents[1]
def event(t):return V.FRAMES[bisect.bisect_left(V.TIMES,t)]
def digest(im):return hashlib.sha256(im.tobytes()).hexdigest()
def crop_hash(t,box):return digest(V.frame(event(t)).crop(box))
def cake_actor_hash(t):
 e=event(t);layer=Image.new('RGBA',(V.W,V.H),(0,0,0,0));V.B.actor(layer,e['sprite_v3'],V.held_cx(e),649,417)
 # The pianist legitimately keeps gliding behind this held character.
 mask=np.array(layer.getchannel('A'))==255;visible=np.array(V.frame(e))[mask]
 return hashlib.sha256(visible.tobytes()).hexdigest()
def fixed_mouth_test(name,cx,foot,height,times,kind):
 hashes=[];mouths=[]
 for t in times:
  im=Image.new('RGBA',(V.W,V.H),(0,0,0,0));x,y=V.vocal_actor(im,name,cx,foot,height,t,kind)
  box=(round(x-90),round(y-80),round(x+90),round(y+80));mouths.append(digest(im.crop(box)))
  a=np.array(im);a[box[1]:box[3],box[0]:box[2]]=0;hashes.append(hashlib.sha256(a.tobytes()).hexdigest())
 return {'body_outside_mouth_identical':len(set(hashes))==1,'distinct_mouth_samples':len(set(mouths)),'samples_s':times}
def main():
 times=[2.2,9.4,11.6,15.6,19.6]
 checks={'intro_left_corner_static':len({crop_hash(t,(45,520,285,720)) for t in times})==1,
 'intro_right_corner_static':len({crop_hash(t,(1038,480,1255,720)) for t in times})==1,
 'left_run_pose_static_within_cut':digest(V.frame(event(65.45)))==digest(V.frame(event(65.85))),
 'right_run_pose_static_within_cut':digest(V.frame(event(66.35)))==digest(V.frame(event(66.75))),
 'cake_run_pose_static_within_cut':len({cake_actor_hash(t) for t in [138.75,139.05]})==1,
 'stelle_back_body_static':len({crop_hash(t,(236,510,326,618)) for t in [40,66,120]})==1,
 'super_chorus_mouth_only':fixed_mouth_test('lie_fixed',667,567,442,[182.0,182.12,182.24,182.36,182.48,182.60],'la'),
 'singing_mouth_only':fixed_mouth_test('sing_fixed',358,763,623,[245.3,245.5,245.7,245.9,246.1,246.3],(244.845,247.047,[1,1,3,4,7,0,4,4]))}
 lag=[]
 for k,rows in V.D['editorial_cues_v3'].items():
  if isinstance(rows,list):
   for row in rows:
    t=row[0];lag.append(V.TIMES[bisect.bisect_left(V.TIMES,t)]-t)
 checks['max_caption_cue_grid_lag_seconds']=round(max(lag),6)
 checks['caption_cues_within_one_source_frame']=max(lag)<=.034
 checks['ai_new_sprite_parts']=len(json.loads((R/'assets/manifest_v3.json').read_text()))
 checks['total_sprite_parts']=len(list((R/'assets/sprites').glob('*.png')))
 (R/'docs/performance_checks_v3.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
 print(json.dumps(checks,ensure_ascii=False,indent=2))
 passed=all(v for v in checks.values() if isinstance(v,bool))
 passed=passed and all(checks[k]['body_outside_mouth_identical'] and checks[k]['distinct_mouth_samples']>=3 for k in ['super_chorus_mouth_only','singing_mouth_only'])
 if not passed:raise SystemExit('Performance check failed')
if __name__=='__main__':main()
