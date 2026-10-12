"""Meaningful checks for rigid ending elements, face axis and vocal cadence."""
from pathlib import Path
import bisect,hashlib,json,math
import numpy as np
from PIL import Image
import render_v4 as V
R=Path(__file__).resolve().parents[1]
def digest(im):return hashlib.sha256(im.tobytes()).hexdigest()
def event(t):return V.FRAMES[bisect.bisect_left(V.TIMES,t)]
def region(family,box):
 hs=[]
 for path in V.ANIM[family]['frames']:
  with Image.open(R/path) as im:im.load();hs.append(digest(im.crop(box)))
 return len(set(hs))==1
def fixed_mouth(name,cx,foot,h,times,kind):
 bodies=[];mouths=[]
 for t in times:
  im=Image.new('RGBA',(V.W,V.H));x,y=V.vocal_actor(im,name,cx,foot,h,t,kind);box=(round(x-90),round(y-80),round(x+90),round(y+80));mouths.append(digest(im.crop(box)));a=np.array(im);a[box[1]:box[3],box[0]:box[2]]=0;bodies.append(hashlib.sha256(a.tobytes()).hexdigest())
 return {'body_outside_mouth_identical':len(set(bodies))==1,'distinct_mouth_samples':len(set(mouths))}
def main():
 config=V.C.MOUTH_CONFIG['sing_fixed'];sp=V.SP['sing_fixed'];x=config[0]*sp.width;y=config[1]*sp.height;expected_x=189.5+(y-196.5)*13/93;axis=math.degrees(math.atan2(13,93))
 asset_count=0
 for p in (R/'assets/sprites').glob('*.png'):
  with Image.open(p) as im:im.load();assert im.mode=='RGBA'
  asset_count+=1
 c={'all_sprite_pngs_valid':True,'total_sprite_parts':asset_count,'new_gpt_pose_parts':len(json.loads((R/'assets/manifest_v4.json').read_text())),
 'ending_firefly_drawn_frames':len(V.ANIM['firefly']['frames']),'ending_stelle_drawn_frames':len(V.ANIM['stelle']['frames']),
 'firefly_boots_identical_all_ending_frames':region('firefly',(0,520,600,600)),
 'stelle_bin_lower_body_identical_all_ending_frames':region('stelle',(0,420,290,600)),
 'ending_pose_indices_monotonic':all(np.all(np.diff([V.animation_index(k,t) for t in np.arange(290.29,300,.02)])>=0) for k in ['firefly','stelle']),
 'sing_mouth_native_face_axis_error_px':round(abs(x-expected_x),4),'sing_mouth_eye_axis_rotation_error_deg':round(abs(config[3]-axis),4),
 'sing_body_mouth_only':fixed_mouth('sing_fixed',358,763,623,[245.2,245.4,245.6,245.8,246,246.2],(244.845,247.047,[1,1,3,4,7,0,4,4])),
 'closeup_body_mouth_only':fixed_mouth('sing_fixed',640,848,905,[269.7,270.1,270.5,270.9,271.3,271.7],(269.536,272.672,[5,6,1,1,1,1])),
 'chorus_body_mouth_only':fixed_mouth('lie_fixed',667,567,442,[182.4,182.55,182.7,182.85,183,183.15],'la'),
 'chorus_sustained_vowel':len({V.mouth_state(t,'la')[0] for t in np.arange(182.4,188,.01)})==1,
 'chorus_opening_period_s':V.C.PERIOD*2,'chorus_jaw_cycles_per_second':1/(V.C.PERIOD*2),
 'yo_source_onsets':[36.169,36.603],'impact_source_onsets':[149.983,150.317,150.751,151.318,151.752],
 'source_onsets_are_native_frame_times':all(t in V.TIMES for t in [36.169,36.603,109.409,109.509,149.983,150.317,150.751,151.318,151.752,291.391]),
 'preview_representative_frames':len(V.SAMPLES)}
 (R/'docs/performance_checks_v4.json').write_text(json.dumps(c,ensure_ascii=False,indent=2));print(json.dumps(c,ensure_ascii=False,indent=2))
 assert all(v for v in c.values() if isinstance(v,bool))
 assert c['sing_mouth_native_face_axis_error_px']<2 and c['sing_mouth_eye_axis_rotation_error_deg']<1
 for k in ['sing_body_mouth_only','closeup_body_mouth_only','chorus_body_mouth_only']:assert c[k]['body_outside_mouth_identical'] and c[k]['distinct_mouth_samples']>=3
if __name__=='__main__':main()
