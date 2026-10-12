"""Build six reviewed V4 deliverables; videos are delivered separately from ZIP."""
from pathlib import Path
import hashlib,json,shutil,zipfile
R=Path(__file__).resolve().parents[1];OUT=R.parent/'deliverables_v4';OUT.mkdir(exist_ok=True)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as file:
  for block in iter(lambda:file.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def main():
 check=json.loads((R/'docs/verification_v4.json').read_text());video=R/'output'/check['file']
 assert check['all_video_pts_identical'] and check['audio_packets_identical']
 assert digest(video)==check['video_sha256'],'Verification is stale; rerun verify_v4.py.'
 assert (R/'output/V4_encoded_review.jpg').exists()
 report=R/'docs/精修说明与问题清单_V4.md';s=report.read_text();marker='<!-- FINAL_VERIFICATION -->'
 if marker in s:s=s[:s.index(marker)]
 s+='\n'+marker+'\n\n## 最终导出实测\n\n'
 s+='| 项目 | 结果 |\n| --- | --- |\n'
 s+=f"| 文件长度 | {check['format_duration_seconds']:.4f} 秒（5:01），与原片一致 |\n"
 s+=f"| 输出 | {check['video_width']}×{check['video_height']}，H.264 |\n"
 s+=f"| 视频帧 | {check['video_frames']}，与原片一致 |\n"
 s+=f"| 逐帧 PTS 最大误差 | {check['max_video_pts_error_seconds']:.3f} 秒 |\n"
 s+=f"| AAC 音频数据 | 与原片 SHA-256 一致；{check['audio_sample_rate']} Hz，双声道 |\n"
 s+=f"| 成片大小 | {check['bytes']/1e6:.2f} MB |\n"
 s+='\n成片 SHA-256：`'+check['video_sha256']+'`。\n'
 report.write_text(s)
 def included(path):
  rel=path.relative_to(R)
  if '__pycache__' in rel.parts or path.suffix in {'.pyc','.f32','.tmp','.partial'}:return False
  if rel.parts[0]=='output':return path.name in {'V4_storyboard.jpg','V4_encoded_review.jpg','render_v4_ffmpeg.log'}
  if path.name=='FILEHASHES.sha256':return False
  return True
 files=sorted(p for p in R.rglob('*') if p.is_file() and included(p))
 sums=R/'FILEHASHES.sha256';sums.write_text('\n'.join(digest(p)+'  '+p.relative_to(R).as_posix() for p in files)+'\n')
 zipped=OUT/'流萤来了哦_V4_工程与素材.zip'
 with zipfile.ZipFile(zipped,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files+[sums]:z.write(p,'firefly_arrived_v4/'+p.relative_to(R).as_posix())
 with zipfile.ZipFile(zipped) as z:
  assert z.testzip() is None
  sprites=[n for n in z.namelist() if n.startswith('firefly_arrived_v4/assets/sprites/') and n.endswith('.png')]
  assert len(sprites)==282
 targets=[(video,OUT/video.name),(report,OUT/'流萤来了哦_V4_精修说明.md'),(R/'output/V4_encoded_review.jpg',OUT/'流萤来了哦_V4_重点镜头预览.jpg'),(R/'docs/verification_v4.json',OUT/'流萤来了哦_V4_核验结果.json'),(R/'output/流萤来了哦_V4_修改片段预览.mp4',OUT/'流萤来了哦_V4_修改片段预览.mp4')]
 for src,dst in targets:shutil.copy2(src,dst)
 print(json.dumps({'zip_files':len(files)+1,'zip_integrity':'passed','sprites':len(sprites),'deliverables':[{'name':p.name,'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(OUT.iterdir()) if p.is_file()]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
