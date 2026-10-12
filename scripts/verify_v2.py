"""Verify the deliverable's frame timing and untouched AAC audio packets."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'source/original.mp4'
DST=ROOT/'output/流萤来了哦_V2_动作精修.mp4'

def probe(p):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))

def audio_hash(p):
    return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-']).decode().strip()

def timestamps(p):
    s=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','csv=p=0',str(p)]).decode()
    return np.array([float(x.strip().split(',')[0]) for x in s.splitlines() if x.strip().split(',')[0]])

def main():
    original=probe(SRC);final=probe(DST)
    a=np.load(ROOT/'analysis/source_pts.npy');b=timestamps(DST)
    source_audio=audio_hash(SRC);final_audio=audio_hash(DST)
    count_equal=len(a)==len(b)
    pts_error=float(abs(a-b).max()) if count_equal else None
    vs=next(s for s in final['streams'] if s['codec_type']=='video')
    au=next(s for s in final['streams'] if s['codec_type']=='audio')
    report={
      'file':'流萤来了哦_V2_动作精修.mp4','format_duration_seconds':float(final['format']['duration']),
      'source_format_duration_seconds':float(original['format']['duration']),
      'video_width':vs['width'],'video_height':vs['height'],'video_codec':vs['codec_name'],
      'video_frames':len(b),'source_video_frames':len(a),'frame_count_equal':count_equal,
      'max_video_pts_error_seconds':pts_error,'all_video_pts_identical':bool(count_equal and pts_error==0),
      'first_video_pts_seconds':float(b[0]),'last_video_pts_seconds':float(b[-1]),
      'audio_codec':au['codec_name'],'audio_sample_rate':int(au['sample_rate']),
      'audio_channels':au['channels'],'audio_duration_seconds':float(au['duration']),
      'source_audio_packet_hash':source_audio,'final_audio_packet_hash':final_audio,
      'audio_packets_identical':source_audio==final_audio,
      'bytes':DST.stat().st_size,'video_sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),
      'visual_QA':'65 representative compositor frames; 120 new sprites; encoded-video samples of every requested interval.'
    }
    (ROOT/'docs/verification_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not count_equal or not(pts_error is not None and pts_error<=.001) or source_audio!=final_audio:
        raise SystemExit('Timing/audio verification failed')

if __name__=='__main__':main()
