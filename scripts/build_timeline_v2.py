"""Editorial correction, transcribed from the supplied source video, not OCR guesses."""
from pathlib import Path
import bisect,json,csv
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'timeline.json').read_text());F=D['frames']
white_words=['KIRAKIRA','GYU-N','PIKAPIKA','PIKO-N','MOFUMOFU','NADENADE','NICONICO','GURUGURU','DE-N','GOROGORO','DEDE-N','WAKUWAKU','UZUZU','BATABATA','NORONORO','AE?','URORO','HA!','TEKUTEKU','KOSOKOSO','GASAGASA','SUNSUN','O?','PEROPERO','OI?','ITADAKIMASU','MOGUMOGU','KIRAKIRA','GYU-N','PIKAPIKA','PIKO-N','MOFUMOFU','NADENADE','NICONICO','GURUGURU','DE-N','GOROGORO','DEDE-N','WAKUWAKU','UZUZU','BATABATA','DOKODOKO','SYA-N','TATAN!','SYA-N','GYUNGYU-N','KA!','DO-N','DO!','JA-N!','WWWWWW','NE!']
white_times=[F[i]['time'] for i in D['cut_indices'] if 81.181<=F[i]['time']<109.409]
assert len(white_times)==len(white_words)
dark=[(212.879,"Let's go"),(213.513,'KIRAKIRA'),(213.947,'PIKAPIKA'),(214.414,'MOFUMOFU'),(214.848,'NADENADE'),(215.282,'GURUGURU'),(215.716,'GOROGORO'),(216.183,'WAKUWAKU'),(216.616,'UZUZU'),(217.05,'NORONORO'),(217.484,'URORO'),(217.918,'TEKUTEKU'),(218.385,'KOSOKOSO'),(218.819,'SUNSUN'),(219.252,'PEROPERO'),(219.686,'NICONICO'),(220.153,'BATABATA'),(220.587,'KIRAKIRA'),(221.021,'PIKAPIKA'),(221.488,'MOFUMOFU'),(221.922,'NADENADE'),(222.355,'GURUGURU'),(222.789,'GOROGORO'),(223.256,'WAKUWAKU'),(223.69,'UZUZU'),(224.124,'NORONORO'),(224.558,'URORO'),(224.991,'TEKUTEKU'),(225.459,'O!?'),(225.892,'ITADAKIMASU'),(226.993,'MOGU'),(227.194,'MOGUMOGU'),(227.427,'MOGUMOGU'),(227.661,'KIRAKIRA'),(228.095,'PIKAPIKA'),(228.562,'MOFUMOFU'),(228.995,'NADENADE'),(229.429,'GURUGURU'),(229.863,'GOROGORO'),(230.33,'WAKUWAKU'),(230.764,'UZUZU'),(231.198,'NORONORO'),(231.631,'URORO'),(232.065,'TEKUTEKU'),(232.532,'KOSOKOSO'),(232.966,'SUNSUN'),(233.4,'PEROPERO'),(233.834,'NICONICO'),(234.301,'BATABATA'),(234.701,'DOKODOKO'),(235.168,'SYA-N'),(235.602,'TATAN!'),(236.036,'SYA-N'),(236.47,'GYUNGYU-N'),(237.37,'KA!'),(237.704,'DO-N')]
hai_times=[F[i]['time'] for i in D['cut_indices'] if 153.754<=F[i]['time']<=179.8]
assert all(.40<b-a<.49 for a,b in zip(hai_times,hai_times[1:]))
run=[(65.299,'left'),(66.199,'right'),(67.067,'left'),(67.968,'right'),(68.835,'left'),(69.736,'right'),(71.004,'keyboard'),(72.372,'right'),(73.273,'left'),(74.141,'right'),(75.042,'left'),(75.909,'right'),(76.777,'left')]
for e in F:
 t=e['time'];e['run_direction']='';e['hai_count']=0;e['hai_onset']=None;e['performance_onset']=None;e['performance_index']=0
 if 81.181<=t<109.409:
  k=bisect.bisect_right(white_times,t)-1;e['word']=white_words[k];e['performance_onset']=white_times[k];e['performance_index']=k
 elif 212.879<=t<238.038:
  k=bisect.bisect_right([x[0] for x in dark],t)-1;e['word']=dark[k][1];e['performance_onset']=dark[k][0];e['performance_index']=k
 if 153.754<=t<181.748:
  k=bisect.bisect_right(hai_times,t)-1;e['hai_count']=k%4+1;e['hai_onset']=hai_times[k];e['performance_index']=k
 if 65.299<=t<77.644:
  k=bisect.bisect_right([x[0] for x in run],t)-1;e['run_direction']=run[k][1];e['run_onset']=run[k][0]
D['project']='流萤来了哦 V2 动作精修';D['editorial_cues']={'white':list(zip(white_times,white_words)),'dark':dark,'hai':[(t,k%4+1) for k,t in enumerate(hai_times)],'run':run,'reference':'Supplied original.mp4, native PTS; manual frame review.'}
(R/'timeline_v2.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
with (R/'docs/performance_cues_v2.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['section','source_time_s','word_or_action'])
 for section,items in D['editorial_cues'].items():
  if isinstance(items,list):
   for t,v in items:w.writerow([section,f'{t:.3f}',v])
print('Corrected white cues',len(white_times),'dark cues',len(dark),'hai onsets',len(hai_times),'run switches',len(run))
