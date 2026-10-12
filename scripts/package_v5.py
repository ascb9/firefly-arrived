from pathlib import Path
import json,shutil,zipfile
R=Path(__file__).resolve().parents[1];O=R.parent/'deliverables_v5';O.mkdir(exist_ok=True)
check=json.loads((R/'docs/verification_v5.json').read_text());assert check['all_video_pts_identical'] and check['audio_packets_identical']
targets=[(R/'output'/check['file'],O/check['file']),(R/'output/流萤来了哦_V5_修改片段预览.mp4',O/'流萤来了哦_V5_修改片段预览.mp4'),(R/'docs/精修说明_V5.md',O/'流萤来了哦_V5_精修说明.md'),(R/'output/V5_encoded_review.jpg',O/'流萤来了哦_V5_重点镜头预览.jpg'),(R/'docs/verification_v5.json',O/'流萤来了哦_V5_核验结果.json')]
for src,dst in targets:shutil.copy2(src,dst)
zpath=O/'流萤来了哦_V5_工程与素材.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(R.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(R)
  if '__pycache__' in rel.parts or p.suffix in ('.pyc','.partial','.f32'):continue
  if rel.parts[0]=='output' and p.name not in ('V5_encoded_review.jpg','V5_storyboard.jpg','render_v5.log'):continue
  if p.name=='FILEHASHES.sha256':continue
  z.write(p,'firefly_arrived_v5/'+str(rel))
with zipfile.ZipFile(zpath) as z:assert z.testzip() is None
print(json.dumps([{'file':str(p.resolve()),'bytes':p.stat().st_size} for p in sorted(O.iterdir())],ensure_ascii=False))
