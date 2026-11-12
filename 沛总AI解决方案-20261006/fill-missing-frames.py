from pathlib import Path
import json,subprocess,tempfile
R=Path(__file__).parent
P=json.load(open(R/'页面读取记录.json'))
base=Path('/Volumes/EXTERNAL/FDE自媒体研究/沛总AI解决方案-20261006/临时帧');base.mkdir(parents=True,exist_ok=True)
for rec in P:
 target=R/(rec['id']+'-字幕复核.json');d=json.load(open(target))
 existing={int(x['time']) for x in d['rows']};missing=sorted(set(range(d['frame_count']))-existing)
 if not missing:continue
 assert all(x%24==0 for x in missing),missing
 tmp=Path(tempfile.mkdtemp(prefix='fill-',dir=base))
 cmd=['/Users/USER/.local/bin/ffmpeg','-hide_banner','-loglevel','error','-i',rec['download'],'-vf',"fps=1,select='not(mod(n,24))'",'-fps_mode','vfr',str(tmp/'frame-%06d.jpg')]
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode!=0:raise RuntimeError(p.stderr)
 frames=sorted(tmp.glob('*.jpg'));assert len(frames)==len(missing),(len(frames),len(missing))
 (R/(rec['id']+'-补帧记录.json')).write_text(json.dumps({'missing_times':missing,'temporary_frames':[str(x) for x in frames],'reason':'多图片OCR输出首帧无分隔头，补读每批首帧'},ensure_ascii=False,indent=2))
 for t,f in zip(missing,frames):
  o=subprocess.run([str(R/'ocr-with-band'),str(f)],capture_output=True,text=True)
  assert o.returncode==0 and 'ERROR:' not in o.stdout,(rec['id'],t,o.stdout[:100])
  d['rows'].append({'time':t,'text':o.stdout.strip(),'repair':'每批首帧独立补读'})
  f.unlink()
 tmp.rmdir();d['rows'].sort(key=lambda x:x['time']);d['coverage']='全时段每秒取帧画面文字，已补齐每批首帧；不是音频逐字稿'
 assert len(d['rows'])==d['frame_count']
 target.write_text(json.dumps(d,ensure_ascii=False,indent=2));print('FILLED',rec['id'],len(missing),flush=True)
print('All 45 frame inventories complete',flush=True)
