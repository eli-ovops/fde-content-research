from pathlib import Path
import json,subprocess,tempfile,time,os
R=Path(__file__).parent
records=json.loads((R/'页面读取记录.json').read_text())
completed=[]
for rec in records:
 if not rec.get('download'):continue
 target=R/(rec['id']+'-字幕复核.json')
 if target.exists():continue
 source=Path(rec['download'])
 if not source.exists():continue
 started=time.time();rows=[]
 tempbase=Path('/Volumes/EXTERNAL/FDE自媒体研究/沛总AI解决方案-20261006/临时帧');tempbase.mkdir(parents=True,exist_ok=True)
 tmp=Path(tempfile.mkdtemp(prefix='frames-',dir=tempbase))
 log=R/(rec['id']+'-帧读取日志.txt')
 p=subprocess.run(['/Users/USER/.local/bin/ffmpeg','-hide_banner','-loglevel','error','-i',str(source),'-vf','fps=1',str(tmp/'frame-%06d.jpg')],capture_output=True,text=True)
 frames=sorted(tmp.glob('frame-*.jpg'))
 manifest=[str(x) for x in frames]
 log.write_text(json.dumps({'source':str(source),'temporary_frames':manifest,'ffmpeg_returncode':p.returncode,'stderr':p.stderr},ensure_ascii=False))
 if p.returncode!=0:print('FAILED_DECODE',rec['id'],p.stderr,flush=True);continue
 for offset in range(0,len(frames),24):
  chunk=frames[offset:offset+24]
  result=subprocess.run([str(R/'ocr-revision2'),*[str(x) for x in chunk]],capture_output=True,text=True)
  parts=result.stdout.split('\n--- ')
  if len(parts)==1:
   # 单帧输出不带分隔标识
   if len(chunk)==1:rows.append({'time':offset,'text':result.stdout.strip()})
   else:rows.append({'time':offset,'error':result.stdout[:400],'count':len(chunk)})
  else:
   for part in parts[1:]:
    path,_,text=part.partition(' ---\n')
    number=int(Path(path).stem.split('-')[1]);rows.append({'time':number-1,'text':text.strip()})
  for row in rows[-len(chunk):]:
   if 'ERROR:' in row.get('text',''):
    fp=tmp/f"frame-{int(row['time'])+1:06d}.jpg"
    fixed=subprocess.run([str(R/'ocr-revision2'),str(fp)],capture_output=True,text=True)
    if fixed.returncode==0 and 'ERROR:' not in fixed.stdout:row['text']=fixed.stdout.strip();row['retry']='单帧独立进程复读'
  for x in chunk:x.unlink()
 tmp.rmdir()
 out={'id':rec['id'],'url':'https://www.douyin.com/video/'+rec['id'],'source':str(source),'sample_interval':1.0,'coverage':'全时段画面文字采样，不是音频逐字稿；短于采样间隔的文字可能遗漏','frame_count':len(frames),'rows':rows,'errors':sum('ERROR:' in x.get('text','') or 'error' in x for x in rows),'elapsed_seconds':round(time.time()-started,2)}
 target.write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print('DONE',rec['id'],len(frames),out['errors'],out['elapsed_seconds'],flush=True)
 completed.append(rec['id'])
print('batch done',len(completed),flush=True)
