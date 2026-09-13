from pathlib import Path
from datetime import datetime, timezone
import fcntl, hashlib, json, os, shutil, subprocess, time
W=Path('/root/projects/Kira'); A=W/'kira-admin'
E=W/'review/working/app-29-lease-dispatch-pg03-admission-01/launch-01'
E.mkdir(mode=0o700)
os.umask(0o077)
def now(): return datetime.now(timezone.utc).isoformat()
def record(name,obj):
 with (E/name).open('x') as f: json.dump(obj,f,indent=2); f.write('\n')
def cmd(args,timeout=180):
 r=subprocess.run(args,cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 if r.returncode: raise RuntimeError(f'{args[0]} {args[1:3]} exit{r.returncode}: {r.stderr.decode(errors="replace")[:1200]}')
 return r.stdout
def git(*args):return cmd(['git','-C',str(A),*args])
def gh(*args):return cmd(['gh',*args])
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(p,sha): assert p.is_file() and not p.is_symlink() and digest(p)==sha,str(p)
lock=(W/'.kira-validation/hosted-validation.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
run=None; complete=False; collected=False
record('owner.json',{'at_utc':now(),'pid':os.getpid(),'lock':str(Path(lock.name).relative_to(W)),'scope':'one exact private lease-dispatch-failed2 push/run/collection; no local heavy batch'})
try:
 assert shutil.disk_usage(W).free>=8*1024**3,'8GiB disk floor'
 privacy=json.loads(gh('api','repos/kira-manga/kira-admin'))
 assert privacy['private'] and privacy['permissions']['push']
 assert git('branch','--show-current').decode().strip()=='remediation/app-29-backend-complaints'
 before='bc17ad0e1dd1db509aa6d4e67a54975deef626bd'
 assert git('rev-parse','HEAD').decode().strip()==before
 assert git('ls-remote','--heads','origin','remediation/app-29-backend-complaints').decode().split()[0]==before
 assert not git('diff','--cached','--name-only'), 'Fresh launch requires an empty index; preserve existing staged work'
 active=json.loads(gh('run','list','--repo','kira-manga/kira-admin','--limit','40','--json','databaseId,status,headSha,workflowName'))
 assert not [x for x in active if x['status']!='completed'],'overlapping private hosted run'
 admission=json.loads((E.parent/'primary-admission.json').read_text()); assert admission['authorized'] and admission['attempts']==1
 transport=json.loads((E.parent/'transport.json').read_text())
 check(A/'ci/app29-gate-b.request.json',admission['authorized_request_sha256'])
 check(A/transport['checkpoint_path'],admission['deployed_checkpoint_sha256'])
 for relative,h in transport['deployed_tooling'].items(): check(A/relative,h)
 base=A/'docs/remediation/app29-lease-dispatch-pg-03'
 for p,h in transport['authority_pins'].items(): check(base/'authority'/p,h)
 check(A/transport['source_bundle']['path'],transport['source_bundle']['sha256'])
 old_requests=json.loads((E.parent/'other-requests-before.json').read_text())
 for p,h in old_requests.items():
  if p!='ci/app29-gate-b.request.json': check(A/p,h)
 scopes=['.github/workflows/app29-gate-b.yml','ci/app29-gate-b.py','ci/app29-gate-b.request.json','review/working/app-29-lease-dispatch-pg03-bound-01/profile','docs/remediation/app29-lease-dispatch-pg-03']
 raw=git('status','--porcelain=v1','-z','-uall')
 entries=[e for e in raw.split(b'\0') if e]
 assert all(e[:2] in (b' M',b'??') and e[2:3]==b' ' for e in entries),'unexpected staged/index/rename state'
 paths=[e[3:].decode() for e in entries]
 assert len(paths)==len(set(paths)) and paths
 assert all(any(p==s or p.startswith(s+'/') for s in scopes) for p in paths),'unexpected changed path'
 record('precommit.json',{'at_utc':now(),'parent':before,'paths':paths,'authority_files_checked':len(transport['authority_pins']),'private_push_confirmed':True,'active_runs':[],'status_parser':'raw NUL-delimited bytes; status columns preserved','source_preflight':'genuine fresh481-source local-v3 preflight adopted; no rerun','request_sha256':digest(A/'ci/app29-gate-b.request.json')})
 git('diff','--check')
 git('add','--',*scopes)
 staged=[x.decode() for x in git('diff','--cached','--name-only','-z').split(b'\0') if x]
 assert set(staged)==set(paths)
 git('diff','--cached','--check','--',*scopes[:4])
 commit=git('commit','-m','Validate two lease dispatch cases after compile repair [skip both]')
 (E/'commit.log').write_bytes(commit)
 sha=git('rev-parse','HEAD').decode().strip()
 record('commit.json',{'at_utc':now(),'head':sha,'parent':before,'tree':git('rev-parse','HEAD^{tree}').decode().strip(),'paths':staged,'product_integration':False})
 (E/'push.log').write_bytes(git('push','origin','HEAD:refs/heads/remediation/app-29-backend-complaints'))
 remote=git('ls-remote','--heads','origin','remediation/app-29-backend-complaints').decode().split()[0]
 assert remote==sha
 record('remote.json',{'at_utc':now(),'sha':sha,'remote':remote,'private':True})
 print('PUSHED',sha,flush=True)
 deadline=time.monotonic()+180
 while run is None:
  rows=json.loads(gh('run','list','--repo','kira-manga/kira-admin','--workflow','app29-gate-b.yml','--commit',sha,'--limit','5','--json','databaseId,status,conclusion,headSha,url,workflowName,event'))
  assert len(rows)<=1,'multiple lease-dispatch-failed2 runs'
  if rows: run=rows[0]; break
  assert time.monotonic()<deadline,'push run not observed; do not dispatch duplicate'
  time.sleep(10)
 record('run-initial.json',run)
 print('RUN',run['url'],flush=True)
 deadline=time.monotonic()+2100; last=None
 while True:
  rawrun=gh('api',f'repos/kira-manga/kira-admin/actions/runs/{run["databaseId"]}')
  state=json.loads(rawrun)
  assert state['head_sha']==sha and state['run_attempt']==1
  if state['status']!=last: print('STATUS',state['status'],state['conclusion'],flush=True);last=state['status']
  if state['status']=='completed':complete=True;break
  assert time.monotonic()<deadline,'observer deadline; remote status must be reconciled before next batch'
  time.sleep(45)
 (E/'run-final.json').write_bytes(rawrun)
 rawart=gh('api',f'repos/kira-manga/kira-admin/actions/runs/{run["databaseId"]}/artifacts')
 (E/'artifacts-metadata.json').write_bytes(rawart)
 artifacts=json.loads(rawart)['artifacts']
 expected=f'app29-lease-dispatch-pg-03-{run["databaseId"]}-1'
 owned=[x for x in artifacts if x['name']==expected]
 assert len(owned)==1 and not owned[0]['expired'],'raw expected artifact missing'
 assert owned[0]['size_in_bytes']<512*1024**2 and shutil.disk_usage(W).free>8*1024**3+owned[0]['size_in_bytes']*3
 gh('run','download',str(run['databaseId']),'--repo','kira-manga/kira-admin','--name',expected,'--dir',str(E/'artifacts'))
 log=cmd(['gh','run','view',str(run['databaseId']),'--repo','kira-manga/kira-admin','--log'],timeout=180)
 (E/'workflow.log').write_bytes(log)
 files={str(p.relative_to(E/'artifacts')):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted((E/'artifacts').rglob('*')) if p.is_file()}
 assert not any(p.is_symlink() for p in (E/'artifacts').rglob('*'))
 record('collection.json',{'at_utc':now(),'run_url':run['url'],'carrier_sha':sha,'attempt':1,'conclusion':state['conclusion'],'files':files,'artifact':owned[0]['name'],'disposition':'RAW_RESULT_REVIEW_REQUIRED','local_builds':0,'disk_free_bytes':shutil.disk_usage(W).free})
 collected=True
 print('COLLECTED',state['conclusion'],len(files),'files; independent review required',flush=True)
except BaseException as e:
 record('observer-error.json',{'at_utc':now(),'type':type(e).__name__,'error':str(e),'run':run,'completed_observed':complete,'collected':collected,'no_retry_dispatched':True})
 raise
finally:
 record('lane-release.json',{'at_utc':now(),'pid':os.getpid(),'remote_completed_observed':complete,'raw_collected':collected,'run':run,'next_batch_requires_reconcile':bool(run and not complete),'local_builds_or_services_started':False})
 fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
