import argparse, csv, hashlib, json, re, subprocess, threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from pool_a_fixtures import BLOCKED_IDS, REPLAY_PASSWORDS, accounts_for

ROOT=Path(__file__).resolve().parents[1]
CSV_PATH=ROOT/'test-cases'/'a-forgot-password.csv'; OUT_PATH=ROOT/'postman'/'pool-a-forgot-password.postman_collection.json'
REPORT_PATH=ROOT/'postman'/'pool-a-conversion-report.md'; STATE_PATH=ROOT/'postman'/'pool-a-validation-results.json'
SCHEMA_PATH=ROOT/'postman'/'postman-v2.1.0-schema.json'; GMT7=timezone(timedelta(hours=7))
REQUIRED={'Test ID','Endpoint','Category','Test Objective','Preconditions','Request Input','Expected Result','Specification Basis','Assumptions / Notes'}
FLOWS={'API-076':['Request A - registered email','Request B - non-existing email'],'API-077':['Request A - concurrent participant','Request B - concurrent participant'],'API-078':['Step 1 - text/plain','Step 2 - JSON retry'],'API-079':['Step 1 - empty body','Step 2 - valid retry'],'API-080':['Step 1 - object password','Step 2 - string retry'],'API-081':['Step 1 - Account A injection string','Step 2 - Account B integrity check']}
EXPIRY={'API-025','API-065','API-072'}
PARTIAL={'API-025','API-030','API-046','API-047','API-050','API-052','API-055','API-057','API-063','API-065','API-067','API-068','API-069','API-070','API-071','API-072','API-073','API-074','API-076','API-077','API-078','API-081'}
NONMATCHING_TOKEN_IDS={'API-007','API-008','API-010','API-011','API-012','API-014','API-038','API-039','API-040','API-041','API-042','API-043','API-045','API-074','API-076'}
STUDENT_ID_LOG=["const studentId = pm.variables.replaceIn('{{studentId}}');","","pm.request.headers.upsert({","    key: 'X-Student-Id',","    value: studentId","});","","console.log(","    '[Pool A evidence] X-Student-Id:',","    studentId,","    'request=' + pm.info.requestName",");"]

def now(): return datetime.now(GMT7).strftime('%Y-%m-%d %H:%M:%S GMT+7')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def rows():
    with CSV_PATH.open(encoding='utf-8-sig',newline='') as f: data=list(csv.DictReader(f))
    ids=[r['Test ID'] for r in data]
    if not data or not REQUIRED.issubset(data[0]) or len(ids)!=82 or len(set(ids))!=82: raise RuntimeError('Reviewed CSV must contain 82 unique complete rows')
    return data
def var_name(label):
    words=re.findall(r'[A-Za-z0-9]+',label); return words[0].lower()+''.join(w[:1].upper()+w[1:] for w in words[1:]) if words else 'fixtureValue'
def placeholders(text): return re.sub(r'<([^>]+)>',lambda m:'{{'+var_name(m.group(1))+'}}',text)
def fragments(text):
    out=[]; stack=[]; start=None; quoted=False; escaped=False; pairs={'}':'{',']':'['}
    for i,ch in enumerate(text):
        if start is None:
            if ch in '{[': start=i; stack=[ch]
            continue
        if escaped: escaped=False
        elif ch=='\\' and quoted: escaped=True
        elif ch=='"': quoted=not quoted
        elif not quoted:
            if ch in '{[': stack.append(ch)
            elif ch in '}]':
                if not stack or stack[-1]!=pairs[ch]: start=None; stack=[]; continue
                stack.pop()
                if not stack: out.append(text[start:i+1]); start=None
    return out
def structured(text):
    try: value=json.loads(text)
    except json.JSONDecodeError: return None
    if not isinstance(value,dict) or not ({'Headers','Body','Raw Body'}&set(value)): return None
    headers=[{'key':str(k),'value':str(v),'type':'text'} for k,v in value.get('Headers',{}).items()]
    if 'Raw Body' in value: raw,kind=value['Raw Body'],'raw'
    elif 'Body' in value: raw,kind=json.dumps(value['Body'],ensure_ascii=False,separators=(',',':')),'json'
    else: raw,kind='','empty'
    return {'headers':headers,'raw':placeholders(raw),'kind':kind}
def specs(row):
    parsed=structured(row['Request Input'])
    if parsed: return [parsed]
    if row['Test ID']=='API-002': return [{'headers':[{'key':'Content-Type','value':'application/json','type':'text'}],'raw':'{"email":"test@domain.com","resetToken":"123456","newPassword":"NewPassword123!"','kind':'raw'}]
    bits=fragments(row['Request Input']); labels=FLOWS.get(row['Test ID']); result=[]
    for step in range(len(labels) if labels else 1):
        if row['Test ID']=='API-079' and step==0: raw,kind='','empty'
        else:
            if step>=len(bits): raise RuntimeError(f"{row['Test ID']} step {step+1}: cannot resolve reviewed body")
            raw,kind=placeholders(bits[step]),'json'
        ctype='text/plain' if row['Test ID']=='API-078' and step==0 else 'application/json'
        headers=[{'key':'Content-Type','value':ctype,'type':'text'}]
        if row['Test ID']=='API-082': headers.append({'key':'Authorization','value':'Bearer definitely-not-a-valid-jwt','type':'text'})
        result.append({'headers':headers,'raw':raw,'kind':kind})
    return result
def expected(row,step=0):
    special={'API-076':[400,400],'API-077':[None,None],'API-078':[None,200],'API-079':[400,200],'API-080':[400,200],'API-081':[200,200]}
    if row['Test ID'] in special: return special[row['Test ID']][step]
    if row['Test ID'] in {'API-030','API-075'}: return None
    m=re.search(r'\b(200|201|204|400|401|403|404|409|415|422|429|500)\b',row['Expected Result']); return int(m.group(1)) if m else None
def flags(tid):
    out=[]
    if accounts_for(tid): out.append('DETERMINISTIC DIRECT-SQLITE FIXTURE')
    if tid in EXPIRY: out+=['OBSERVABLE EXPIRY POINT REQUIRED','BLOCKED / NOT EXECUTABLE: SUT HAS NO EXPIRY STATE OR CHECK']
    if tid=='API-075': out+=['BLOCKED / NOT EXECUTABLE: SUT HAS NO RATE LIMIT OR AUTHORITATIVE THRESHOLD','MANUAL / DATA-DRIVEN EXECUTION REQUIRED']
    if tid=='API-077': out+=['BLOCKED / NOT EXECUTABLE IN SEQUENTIAL POSTMAN / NEWMAN','TRUE CONCURRENT HARNESS REQUIRED']
    if tid=='API-068': out.append('WHITE-BOX STORAGE ORACLE REQUIRED')
    if tid in REPLAY_PASSWORDS: out.append('AUTOMATED FIRST-USE RESET BEFORE REPLAY')
    if tid=='API-030': out.append('EXPLORATORY / MANUAL ORACLE REQUIRED')
    elif tid in PARTIAL: out.append('PARTIALLY AUTOMATED / MANUAL ORACLE REQUIRED')
    return out
def pre_script(tid):
    reasons={'API-025':'SUT has no OTP expiry state or check','API-065':'SUT has no OTP expiry state or check','API-072':'SUT has no OTP expiry state or check','API-075':'SUT has no rate limiter or authoritative threshold','API-077':'sequential Newman cannot establish a concurrent barrier'}
    if tid in BLOCKED_IDS: return [f"console.warn('[{tid} BLOCKED / NOT EXECUTABLE] {reasons[tid]}');","pm.execution.skipRequest();"]
    if tid not in REPLAY_PASSWORDS: return None
    acct=accounts_for(tid)[0]; password=REPLAY_PASSWORDS[tid]
    return ["pm.sendRequest({","  url: pm.variables.replaceIn('{{baseUrl}}/api/reset-password'),","  method: 'POST',","  header: [{ key: 'Content-Type', value: 'application/json' }, { key: 'X-Student-Id', value: pm.variables.replaceIn('{{studentId}}') }],",f"  body: {{ mode: 'raw', raw: JSON.stringify({{ email: '{acct.email}', resetToken: '{acct.reset_token}', newPassword: '{password}' }}) }}","}, function (error, response) {","  if (error || response.code !== 200) { console.error('[Pool A replay fixture failed]', error || ('HTTP ' + response.code)); pm.execution.skipRequest(); return; }","});"]
def api076(store):
    base=["function snap(){ var t=(pm.response.headers.get('Content-Type')||'').split(';')[0].trim().toLowerCase(); var r=pm.response.text(),b=r,j=t.indexOf('json')!==-1; if(j){try{b=JSON.parse(r);}catch(e){j=false;b=r;}} return {status:pm.response.code,type:t,isJson:j,body:b}; }"]
    return base+(["pm.collectionVariables.set('__api076A',JSON.stringify(snap()));"] if store else ["var a=JSON.parse(pm.collectionVariables.get('__api076A')||'null'); pm.test('API-076 - comparable failure representation',function(){pm.expect(snap()).to.eql(a);}); pm.collectionVariables.unset('__api076A');"])
def description(row,label=None):
    tid=row['Test ID']; p=[f"Test ID: {tid}",f"Category: {row['Category']}",f"Objective: {row['Test Objective']}"]
    if label: p.append(f"Flow step: {label}")
    p+=['','Preconditions / Setup:',row['Preconditions'],'','Reviewed request input:',row['Request Input'],'','Reviewed expected result:',row['Expected Result'],'','Specification basis:',row['Specification Basis'],'','Assumptions / Notes:',row['Assumptions / Notes']]
    accts=accounts_for(tid)
    if accts: p+=['','Deterministic SQLite fixture (seed after SUT startup):']+[f"- {a.email}: reset_token TEXT {a.reset_token}" for a in accts]
    if flags(tid): p+=['','Execution classification:']+[f'- {x}' for x in flags(tid)]
    return '\n'.join(p)
def item(row,spec,step=0,label=None):
    tid=row['Test ID']; status=expected(row,step); tests=[f"console.log('[Pool A evidence] {tid}','status='+pm.response.code);"]
    if tid=='API-078' and step==0: tests.append("pm.test('API-078 - text/plain response is 4xx',function(){pm.expect(pm.response.code).to.be.within(400,499);});")
    elif status is not None: tests.append(f"pm.test('{tid} - reviewed status is {status}',function(){{pm.response.to.have.status({status});}});")
    else: tests.append(f"console.warn('[Pool A manual oracle] {tid}: no automatic status oracle');")
    if tid=='API-076': tests+=api076(step==0)
    if tid in PARTIAL: tests.append(f"console.warn('[Pool A partial automation] {tid}: see description');")
    events=[]; pre=pre_script(tid)
    if pre: events.append({'listen':'prerequest','script':{'type':'text/javascript','exec':pre}})
    events.append({'listen':'test','script':{'type':'text/javascript','exec':tests}})
    name=f"{tid} - {row['Test Objective']}"+(f' [{label}]' if label else '')
    result={'name':name,'event':events,'request':{'method':'POST','header':spec['headers'],'body':{'mode':'raw','raw':spec['raw'],'options':{'raw':{'language':'json' if spec['kind']=='json' else 'text'}}},'url':{'raw':'{{baseUrl}}/api/reset-password','host':['{{baseUrl}}'],'path':['api','reset-password']},'description':description(row,label)}}
    if tid=='API-076': result['protocolProfileBehavior']={'followRedirects':False}
    return result
def build(data):
    cats={x:[] for x in ('CONTRACT','DOMAIN','STATE','SECURITY')}; report=[]; vars=set()
    for row in data:
        ss=specs(row); labels=FLOWS.get(row['Test ID']); items=[item(row,s,n,labels[n] if labels else None) for n,s in enumerate(ss)]
        for s in ss: vars.update(re.findall(r'{{\s*([A-Za-z0-9_.-]+)\s*}}',s['raw']))
        cats[row['Category']].append({'name':f"{row['Test ID']} - reviewed multi-request flow",'description':description(row),'item':items} if labels else items[0])
        report.append({'row':row,'items':items,'statuses':[expected(row,n) for n in range(len(ss))]})
    values={'baseUrl':'http://localhost:3000','studentId':'23127261',**{v:'' for v in vars}}
    collection={'info':{'_postman_id':'b4a0b818-b6cd-4ed4-9fa3-23127261000a','name':'Pool A - Reset Password Reviewed Tests','description':'Start/init the SUT, then seed deterministic SQLite fixtures. No baseline request calls /api/forgot-password.','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},'event':[{'listen':'prerequest','script':{'type':'text/javascript','exec':STUDENT_ID_LOG}}],'variable':[{'key':k,'value':v,'type':'string'} for k,v in sorted(values.items())],'item':[{'name':k,'item':v} for k,v in cats.items()]}
    return collection,report
def load_state(want=None):
    state=json.loads(STATE_PATH.read_text(encoding='utf-8')) if STATE_PATH.exists() else {}; return state if not want or state.get('collectionSha256')==want else {}
def save(state): STATE_PATH.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def generate():
    data=(json.dumps(build(rows())[0],ensure_ascii=False,indent=2)+'\n').encode(); OUT_PATH.write_bytes(data); h=hashlib.sha256(data).hexdigest().upper(); old=load_state(); save(old if old.get('collectionSha256')==h else {'collectionSha256':h,'generatedAt':now()}); print(f'GENERATED: 82 logical IDs; SHA-256 {h}')
def walk(items):
    for x in items:
        if 'request' in x: yield x
        yield from walk(x.get('item',[]))
def independent_structured(row):
    try: wrapper=json.loads(row['Request Input'])
    except json.JSONDecodeError: return None
    if not isinstance(wrapper,dict) or not ({'Headers','Body','Raw Body'}&set(wrapper)): return None
    headers=[{'key':str(key),'value':str(value),'type':'text'} for key,value in wrapper.get('Headers',{}).items()]
    if 'Raw Body' in wrapper: raw=wrapper['Raw Body']
    elif 'Body' in wrapper: raw=json.dumps(wrapper['Body'],ensure_ascii=False,separators=(',',':'))
    else: raw=''
    if '<' in raw: raise RuntimeError(f"{row['Test ID']}: unresolved placeholder in structured reviewed input")
    return {'headers':headers,'raw':raw}
def static_validate():
    data=rows(); collection=json.loads(OUT_PATH.read_text(encoding='utf-8')); requests=list(walk(collection['item'])); by={}
    executable=json.dumps([{'url':x['request']['url'],'event':x.get('event',[])} for x in requests],ensure_ascii=False)
    if '/api/forgot-password' in executable or 'fixtureReady' in executable or re.search(r'otpApi\d',executable): raise RuntimeError('Obsolete forgot-password fixture dependency remains')
    for x in requests: by.setdefault(re.match(r'API-\d{3}',x['name']).group(),[]).append(x)
    if set(by)!={r['Test ID'] for r in data}: raise RuntimeError('Logical ID mismatch')
    for row in data:
        wanted=specs(row); actual=by[row['Test ID']]
        if len(wanted)!=len(actual): raise RuntimeError(f"{row['Test ID']}: request count mismatch")
        for n,(w,a) in enumerate(zip(wanted,actual),1):
            if a['request']['body']['raw']!=w['raw'] or a['request']['header']!=w['headers']: raise RuntimeError(f"{row['Test ID']} step {n}: CSV mapping mismatch")
    structured_checked=0
    for row in data:
        independent=independent_structured(row)
        if independent is None: continue
        structured_checked+=1; request=by[row['Test ID']][0]['request']
        if request['body']['raw']!=independent['raw'] or request['header']!=independent['headers']: raise RuntimeError(f"{row['Test ID']}: independent structured CSV mapping mismatch")
    fixture_rows=0
    for row in data:
        fixtures=accounts_for(row['Test ID'])
        if not fixtures: continue
        fixture_rows+=1
        for fixture in fixtures:
            if fixture.email not in row['Preconditions'] or fixture.reset_token not in row['Preconditions']: raise RuntimeError(f"{row['Test ID']}: CSV precondition does not match fixture {fixture.email}/{fixture.reset_token}")
        if row['Test ID'] not in NONMATCHING_TOKEN_IDS and fixtures[0].reset_token not in row['Request Input']: raise RuntimeError(f"{row['Test ID']}: reviewed request data does not use seeded primary token {fixtures[0].reset_token}")
        if row['Test ID']=='API-081' and fixtures[1].reset_token not in row['Request Input']: raise RuntimeError('API-081: reviewed request data does not use seeded secondary token')
    seeder_source=(ROOT/'postman'/'seed_pool_a_fixtures.py').read_text(encoding='utf-8')
    for marker in ('from pool_a_fixtures import all_accounts','accounts = all_accounts()','account.email','account.reset_token'):
        if marker not in seeder_source: raise RuntimeError(f'Fixture seeder no longer consumes the shared account/token manifest: missing {marker!r}')
    for tid in BLOCKED_IDS:
        scripts=json.dumps(by[tid])
        if 'BLOCKED / NOT EXECUTABLE' not in scripts or 'pm.execution.skipRequest()' not in scripts or 'throw new Error' in scripts: raise RuntimeError(f'{tid}: blocked case must use pm.execution.skipRequest() without throwing')
    collection_pre=json.dumps(collection.get('event',[])); variables={item['key']:item.get('value') for item in collection.get('variable',[])}
    if not all(marker in collection_pre for marker in ('X-Student-Id','studentId','headers.upsert')) or not variables.get('studentId'): raise RuntimeError('Collection-level X-Student-Id injection is missing or unconfigured')
    for tid in REPLAY_PASSWORDS:
        if json.dumps(by[tid]).count('/api/reset-password')<2 or 'skipRequest' not in json.dumps(by[tid]): raise RuntimeError(f'{tid}: replay setup missing')
    if not isinstance(json.loads(by['API-009'][0]['request']['body']['raw'])['resetToken'],int): raise RuntimeError('API-009 token is not numeric')
    if json.loads(by['API-013'][0]['request']['body']['raw'])['resetToken']!='012345': raise RuntimeError('API-013 leading zero lost')
    h=digest(OUT_PATH); state=load_state(h); state.update({'collectionSha256':h,'static':{'status':'PASS','validatedAt':now(),'logicalTestIds':82,'generatedRequests':len(requests),'forgotPasswordReferences':0,'fixtureRowsChecked':fixture_rows,'structuredMappingsIndependentlyChecked':structured_checked,'studentIdInjectionChecked':True,'blockedSkipRequestIds':sorted(BLOCKED_IDS)}}); save(state); print(f'STATIC PASS: 82 IDs; {len(requests)} requests; {fixture_rows} fixture rows; {structured_checked} independent structured mappings; blocked skipRequest and X-Student-Id verified')
def schema_validate(path):
    import jsonschema
    collection=json.loads(OUT_PATH.read_text(encoding='utf-8')); schema=json.loads(path.read_text(encoding='utf-8')); errors=list(jsonschema.validators.validator_for(schema)(schema).iter_errors(collection))
    if errors: raise RuntimeError('\n'.join(f'{list(e.absolute_path)}: {e.message}' for e in errors))
    h=digest(OUT_PATH); state=load_state(h); state.update({'collectionSha256':h,'schema':{'status':'PASS','validatedAt':now(),'schemaPath':str(path.relative_to(ROOT)).replace('\\','/')}}); save(state); print('SCHEMA PASS: full Postman v2.1 schema')
class Mock(BaseHTTPRequestHandler):
    captured=[]; statuses=[]
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get('Content-Length','0'))).decode(); type(self).captured.append({'path':self.path,'body':body,'studentId':self.headers.get('X-Student-Id')}); status=type(self).statuses.pop(0) if type(self).statuses else 200; self.send_response(status); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b'{}')
    def log_message(self,*_): pass
def named(collection,tid): return next(x for x in walk(collection['item']) if x['name'].startswith(tid))
def newman_validate(command):
    collection=json.loads(OUT_PATH.read_text(encoding='utf-8')); server=ThreadingHTTPServer(('127.0.0.1',0),Mock); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start(); port=server.server_address[1]; checks={}
    runs=[('API-001',[200]),('API-009',[400]),('API-013',[200]),('API-025',[]),('API-026',[200,400]),('API-078',[400,200]),('API-079',[400,200]),('API-080',[400,200]),('API-081',[200,200])]
    try:
        for tid,statuses in runs:
            Mock.captured=[]; Mock.statuses=list(statuses); folder=f'{tid} - reviewed multi-request flow' if tid in FLOWS else named(collection,tid)['name']; result=subprocess.run(command+['run',str(OUT_PATH),'--folder',folder,'--env-var',f'baseUrl=http://127.0.0.1:{port}','--reporters','cli'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
            if result.returncode: raise RuntimeError(f'Newman {tid} failed:\n{result.stdout}\n{result.stderr}')
            if any(x['path']!='/api/reset-password' for x in Mock.captured): raise RuntimeError(f'{tid}: non-reset request emitted')
            if any(x['studentId']!='23127261' for x in Mock.captured): raise RuntimeError(f'{tid}: X-Student-Id injection failed in Newman')
            checks[tid]=list(Mock.captured)
        if checks['API-025']: raise RuntimeError('API-025: blocked request was transmitted instead of skipped')
        if json.loads(checks['API-009'][0]['body'])['resetToken']!=123456: raise RuntimeError('numeric serialization failed')
        if json.loads(checks['API-013'][0]['body'])['resetToken']!='012345': raise RuntimeError('leading-zero serialization failed')
        replay=[json.loads(x['body']) for x in checks['API-026']]
        if len(replay)!=2 or replay[0]['resetToken']!=replay[1]['resetToken']: raise RuntimeError('replay setup failed')
        cross=[json.loads(x['body']) for x in checks['API-081']]
        if cross[0]['email']==cross[1]['email'] or cross[0]['resetToken']==cross[1]['resetToken']: raise RuntimeError('cross-account fixtures are not distinct')
    finally: server.shutdown(); server.server_close(); thread.join(timeout=5)
    vr=subprocess.run(command+['--version'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60); version=vr.stdout.strip() if vr.returncode==0 else 'unknown'; h=digest(OUT_PATH); state=load_state(h); state.update({'collectionSha256':h,'newman':{'status':'PASS','validatedAt':now(),'version':version,'scope':'Local-mock deterministic/numeric/leading-zero/replay/flow/blocked-skip compatibility with X-Student-Id capture','newmanRuns':len(runs),'mockHttpRequestsCaptured':sum(map(len,checks.values())),'blockedRequestsSkipped':1,'studentIdHeaderChecked':True,'forgotPasswordRequestsCaptured':0,'sutExecuted':False}}); save(state); print(f'NEWMAN PASS: {version}; {len(runs)} runs; zero forgot-password requests')
def report():
    data=rows(); _,entries=build(data); h=digest(OUT_PATH); state=load_state(h); missing=[x for x in ('static','schema','newman') if state.get(x,{}).get('status')!='PASS']
    if missing: raise RuntimeError(f'Missing passing validation: {missing}')
    lines=['# Pool A Postman Conversion Report','','## Fixture strategy','','- Start/init the SUT first because its `database.js` drops and recreates `users` on every start.','- Then run `postman/seed_pool_a_fixtures.py`. It opens `backend/database.sqlite` directly, validates the live `users` schema, replaces only owned `poola-api-%@example.test` rows, and verifies every OTP is SQLite TEXT.','- Each independent executable case has a dedicated account. Cross-account cases have distinct A/B accounts and OTPs. The collection never calls `/api/forgot-password`.','- API-013 stores TEXT `012345`; API-009/API-044 store TEXT `123456` but send JSON number `123456`; replay cases seed fresh OTPs and consume them once before retry.','','## Traceability and execution classification','','| Test ID | Category | Requests | Status oracle(s) | Fixture / execution classification |','|---|---|---:|---|---|']
    for e in entries:
        row=e['row']; statuses=', '.join('any 4xx' if row['Test ID']=='API-078' and n==0 else (str(v) if v is not None else 'manual') for n,v in enumerate(e['statuses'])); lines.append(f"| {row['Test ID']} | {row['Category']} | {len(e['items'])} | {statuses} | {'; '.join(flags(row['Test ID'])) or 'No database fixture required'} |")
    lines+=['','## Unsupported/manual cases','','- API-025, API-065, API-072: blocked because the actual SUT has no OTP expiry column/state/check.','- API-075: blocked because the actual SUT has no rate limiter or authoritative threshold.','- API-077: blocked in sequential Postman/Newman; a concurrent harness with a synchronization barrier is required.','- Every blocked request uses `pm.execution.skipRequest()` without throwing a runtime error.','- API-068 HTTP execution is automated, but its plaintext-storage oracle requires authorized SQLite inspection. Other partial/manual labels preserve reviewed external side-effect or persistence oracles.','','## Exact SUT → seed → Newman commands','','```powershell','Set-Location D:\\GitHub\\eshop-sut\\backend','npm install','node server.js','# In a second PowerShell after the server reports it is running:','Set-Location D:\\GitHub\\SoftwareTesting-HW06','C:\\Users\\xing0\\AppData\\Local\\Python\\bin\\python.exe postman\\seed_pool_a_fixtures.py --sut-dir D:\\GitHub\\eshop-sut','newman run postman\\pool-a-forgot-password.postman_collection.json --env-var baseUrl=http://127.0.0.1:3000','```','','## Validation results','',f'- Collection SHA-256: `{h}`',f"- Static: **PASS** ({state['static']['validatedAt']}); 82 IDs, {state['static']['generatedRequests']} requests, {state['static']['fixtureRowsChecked']} fixture rows matched to the seeder manifest, {state['static']['structuredMappingsIndependentlyChecked']} structured mappings independently checked, all blocked cases use skipRequest, X-Student-Id injection present, and zero forgot-password references.",f"- Full Postman v2.1 schema: **PASS** ({state['schema']['validatedAt']}) using `{state['schema']['schemaPath']}`.",f"- Newman {state['newman']['version']}: **PASS** ({state['newman']['validatedAt']}); {state['newman']['newmanRuns']} local-mock runs, blocked request skipped, X-Student-Id captured, and zero forgot-password requests.",'- Full-suite SUT conformance execution was outside this conversion-validation step. The later real-SUT evidence is preserved in `reports/pool-a/pool-a.json` and `reports/pool-a/pool-a.html`, and analyzed in `Main_Report.md` Section A.8.']
    REPORT_PATH.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('REPORT FINALIZED')
def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True); sub.add_parser('generate'); sub.add_parser('validate-static'); sub.add_parser('report'); s=sub.add_parser('validate-schema'); s.add_argument('--schema',type=Path,default=SCHEMA_PATH); n=sub.add_parser('validate-newman'); n.add_argument('--newman-command',nargs='+',required=True); a=p.parse_args()
    {'generate':generate,'validate-static':static_validate,'validate-schema':lambda:schema_validate(a.schema.resolve()),'validate-newman':lambda:newman_validate(a.newman_command),'report':report}[a.cmd]()
if __name__=='__main__': main()
