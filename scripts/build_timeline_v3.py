"""V3 performance cues, native source PTS, and a reproducible vocal-band envelope."""
from pathlib import Path
import bisect,csv,json,subprocess
import numpy as np
from scipy.signal import butter,sosfiltfilt
R=Path(__file__).resolve().parents[1];A=R/'analysis/review';A.mkdir(parents=True,exist_ok=True)
D=json.loads((R/'timeline_v2.json').read_text());F=D['frames']
intro=[(8.809,'surprise','ドン',False),(9.276,'arrival','おっ',False),(10.043,'surprise','ドン',False),(10.577,'oi','お？',False),(11.044,'surprise','ドン',False),(11.478,'gyu0','ディン',True),(11.812,'surprise','ドン',False),(12.346,'arrival','お〜！',False),(12.779,'surprise','ドン',False),(13.247,'arrival','ぱっ',False),(13.580,'surprise','ドン',False),(14.348,'arrival','ぱっぱー',False),(15.015,'surprise','ドン',False),(15.449,'bata0','ぬん！',True),(15.883,'surprise','ドン',False),(16.350,'arrival','おっ',False),(17.117,'surprise','ドン',False),(17.651,'oi','お？',False),(18.118,'surprise','ドン',False),(18.552,'gyu0','ディン',True),(18.886,'surprise','ドン',False),(19.419,'arrival','お〜！',False),(19.853,'surprise','ドン',False),(20.287,'arrival','ぱっ',False),(20.621,'surprise','ドン',False)]
verse=[(37.070,'entry_push','失礼します',False),(38.372,'entry_walk','サササッ',True),(38.805,'gyu0','しゅしゅしゅっ',True),(39.273,'gyu1','シュッ',True),(39.473,'landed','しゅたっ',True),(39.706,'starjump','しゅびっ',True),(39.940,'den','デデーン',True),(40.374,'starjump','ほっ',False),(40.574,'don','ズドーン',True),(41.041,'tatan','ドカーン',True),(41.909,'jyan','じゃーん！',True),(42.776,'goro0','ゴロゴロ',True),(43.443,'den','デーン',True),(43.877,'landed','じゅん！',True),(44.111,'tatan','タタン',True),(44.545,'confused','んー？',False),(45.879,'turnwave','コソッ',False),(46.313,'profile','ちらっ',False),(46.747,'teku0','てくてく',False),(47.214,'profile','ちらっ',False),(47.648,'arrival','え〜…っと！',False),(48.515,'point','ね〜え',False),(49.416,'oi','ねぇってば',False),(50.517,'gyu1','えい！',True),(50.717,'oh','やっ！',True),(50.951,'bata0','こら！',True),(51.184,'gyu0','シュッ',True),(51.385,'starjump','しゅびっ',True),(51.685,'landed','しゅたっ',True),(51.885,'bashful','キュン',True),(52.386,'hop_left','サササッ',True),(52.786,'landed','じゅん！',True),(52.886,'gyu0','シュッ',True),(53.086,'hop_left','サササッ',True),(53.387,'starjump','しゅびっ',True),(53.787,'starjump','ほっ',False),(54.187,'landed','しゅたっ',True),(54.488,'gyu1','ふん！',True),(54.688,'gyu0','シュッ',True),(54.888,'sneeze','へっぷしゅ!!!',True),(55.489,'bashful','キュン',True),(55.789,'hop_right','サササッ',True),(56.189,'gyu0','ディーン',True),(56.390,'nico0','にへへへ',False),(57.558,'sneeze','ぷっ',False),(58.225,'gasa','ポイッ',False),(58.659,'tatan','ズン',True),(58.892,'puddle','だばだば',True),(59.326,'oh','えっ!?',True),(59.560,'goro0','ゴロゴロ',True),(59.993,'gyu1','キュン！',True),(60.427,'doko','ドドドッ',True),(60.661,'gyu0','ディーン',True),(61.328,'submerged','ぶくぶくぶく…',False),(63.530,'submerged','グルグル',True),(63.964,'splash_up','ポーン！',True),(64.197,'hop_land','しゅたっ',True),(64.631,'jyan','やったぁ',True),(65.299,'hop_left','ガタンゴトン',False),(66.199,'hop_right','ガタンゴトン',False),(67.067,'hop_left','ガタンゴトン',False),(67.968,'hop_right','ガタンゴトントン',False),(68.835,'hop_left','ガタンゴトン',False),(69.736,'hop_right','ガタンゴトン',False),(71.004,'table_lean','ガタッ',True),(72.372,'hop_left','ガタンゴトン',False),(73.273,'hop_right','ガタンゴトン',False),(74.141,'hop_left','ガタンゴトン',False),(75.042,'hop_right','ガタンゴトントン',False),(75.909,'hop_left','ガタンゴトン',False),(76.777,'hop_right','ガタンゴトン',False)]
cake=[(112.879,'chew','もぐもぐ',False),(137.004,'chew7','うま〜い！',False),(137.638,'hop_right','ガタンゴトン',False),(138.538,'hop_left','ガタンゴトン',False),(139.406,'hop_right','ガタンゴトン',False),(140.307,'hop_left','ガタンゴトン',False),(141.174,'hop_right','ガタンゴトン',False),(142.075,'hop_left','ガタンゴトン',False),(142.943,'chew7','ごちそうさまでした',False),(144.711,'hop_right','ガタンゴトン',False),(145.612,'hop_left','ガタンゴトン',False),(146.480,'hop_right','ガタンゴトン',False),(147.381,'hop_left','ガタンゴトン',False),(148.248,'hop_right','ガタンゴトン',False),(149.116,'hop_left','ガタンゴトン',False)]
raw=A/'audio_mono.f32'
if not raw.exists() or raw.stat().st_size<301*16000*4:
 tmp=raw.with_suffix('.tmp');subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(R/'source/original.mp4'),'-vn','-ac','1','-ar','16000','-f','f32le',str(tmp)],check=True);tmp.replace(raw)
x=np.fromfile(raw,np.float32);y=sosfiltfilt(butter(3,[450,2800],btype='bandpass',fs=16000,output='sos'),x)
hop=160;window=480;length=len(y)//hop;centers=np.arange(length)*.01
energy=np.array([np.sqrt(np.mean(y[max(0,i*hop-window//2):min(len(y),i*hop+window//2)]**2)+1e-12) for i in range(length)])
energy=np.convolve(energy,[.15,.2,.3,.2,.15],mode='same')
env=[]
for a,b in [(181.748,209.976),(244.845,248.381),(252.352,255.422),(269.536,272.672)]:
 q=energy[(centers>=a)&(centers<b)];lo,hi=np.percentile(q,[12,92]);norm=np.clip((energy-lo)/(hi-lo+1e-9),0,1)
 env.append({'start':a,'end':b,'times':np.round(centers[(centers>=a)&(centers<b)],3).tolist(),'opening':np.round(norm[(centers>=a)&(centers<b)],4).tolist()})
(R/'docs/vocal_envelope_v3.json').write_text(json.dumps({'method':'450–2800 Hz audio-band RMS, 30 ms window, 10 ms sampling; mouth vowels use editorial syllable timing, not automatic phoneme transcription.','segments':env},ensure_ascii=False,separators=(',',':')))
for e in F:
 e['caption_v3']='';e['sprite_v3']='';e['caption_onset_v3']=None;e['caption_burst_v3']=False
 group=intro if e['shot']=='intro' and e['time']>=8.809 else verse if e['shot']=='verse' else cake if e['shot']=='cake_verse' else None
 if group:
  k=bisect.bisect_right([v[0] for v in group],e['time'])-1
  if k>=0:e['caption_onset_v3'],e['sprite_v3'],e['caption_v3'],e['caption_burst_v3']=group[k]
D['project']='流萤来了哦 V3 演出精修';D['editorial_cues_v3']={'intro':intro,'verse':verse,'cake':cake,'impact':[(20.954,'star_bust',''),(21.622,'bata0','うん'),(22.289,'tatan','シャキーン'),(22.923,'title_fade','')],'verse_impact':[(77.644,'hop_doki','ドキッ!!'),(77.978,'tatan_hold','タタン'),(78.412,'sneeze','へっぷしゅ!!!'),(78.979,'goro0','ゴロゴロ'),(79.413,'landed','じゅん！'),(80.514,'letsgocard',"Let's go")],'fixed_stelle':'All verse/cake/title-mini use one rear-view bin sprite. Head-turn frames are reserved for ending.','background':'Secret rooftop: super chorus and subsequent dark scenes until original white-card transition.'}
(R/'timeline_v3.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
with (R/'docs/performance_cues_v3.csv').open('w',encoding='utf-8-sig',newline='') as file:
 w=csv.writer(file);w.writerow(['section','source_time_s','sprite','caption','burst'])
 for section,rows in D['editorial_cues_v3'].items():
  if isinstance(rows,list):
   for row in rows:w.writerow([section,*row])
print('V3 cues',len(intro),len(verse),'Native frames',len(F),'Vocal-band envelopes',len(env))
