const $ = id => document.getElementById(id);
const titles = {shielded:'Shielded receipt',leaky:'Planted log leak',transparent:'Transparent payment',request:'Request only'};
const labels = {recipient_preflight:'Recipient preflight',recipient_observation:'Recipient observation',canary_leak:'Canary leak scan'};
let activeReport, scanReport, generation = 0;
const node = (tag, text, className) => {const el=document.createElement(tag); if(text!==undefined) el.textContent=text; if(className) el.className=className; return el;};
function validate(report) {
  if(!report || ![1,2].includes(report.schema_version) || !Array.isArray(report.checks) || !report.checks.length || report.checks.length>100) throw Error('Choose a CLI JSON report with schema version 1 or 2 and a nonempty checks array.');
  for(const check of report.checks) if(!check || typeof check.check!=='string' || !['pass','fail','unverified'].includes(check.status) || (check.evidence!==undefined && (!check.evidence || typeof check.evidence!=='object' || Array.isArray(check.evidence)))) throw Error('Report contains an invalid check, status, or evidence object.');
  if(report.limits!==undefined && (!Array.isArray(report.limits) || !report.limits.every(x=>typeof x==='string'))) throw Error('Report limits must be a list of text entries.');
  return report;
}
function action(check) {
  if(check.status==='unverified') return 'Next: collect the missing wallet or scan evidence with the CLI before treating this check as verified.';
  if(check.status==='fail' && check.check==='canary_leak') return 'Next: remove the sensitive logging path and rerun the same canary control.';
  if(check.status==='fail') return 'Next: use a shielded receiver and verify a matching confirmed note in the recipient wallet.';
  return 'Next: preserve this evidence and rerun after changes to the payment flow.';
}
function drawCheck(check, target) {
  const section=node('article',undefined,'check'), top=node('div',undefined,'check-top');
  top.append(node('h3',labels[check.check] || check.check),node('span',check.status.toUpperCase(),'badge '+check.status));section.append(top);
  section.append(node('p',check.reason || 'This report does not include a reason.'),node('p',action(check),'action'));
  const details=node('details');details.append(node('summary','Inspect evidence & reproduction'),node('pre',JSON.stringify(check.evidence || {},null,2)));
  for(const [key,label] of [['evidence_source','Source'],['reproduce','Reproduce'],['privacy_boundary','Boundary']]) details.append(node('p',label+': '+(check[key] || 'Not recorded in this report version.')));
  section.append(details);target.append(section);
}
function render(report,title,origin) {
  activeReport=report;$('report-title').textContent=title;$('report-origin').textContent=origin;$('report-message').textContent=report.network_scope || 'Network scope not recorded';$('report-message').className='';
  $('summary').replaceChildren(); for(const status of ['pass','fail','unverified']) {const count=report.checks.filter(x=>x.status===status).length; $('summary').append(node('span',`${count} ${status.toUpperCase()}`));}
  $('checks').replaceChildren();for(const check of report.checks) drawCheck(check,$('checks'));
  $('boundaries').replaceChildren(node('h3','WHAT THIS REPORT DOES NOT PROVE'));for(const limit of report.limits || ['No privacy limits were recorded in this report.']) $('boundaries').append(node('p',limit));$('download').disabled=false;
}
async function loadCase(key) {
  const token=++generation;$('report-message').textContent='Loading recorded CLI evidence…';
  try {const response=await fetch(key+'.json');if(!response.ok)throw Error('The sample report could not be loaded. Serve this folder over HTTP.');const report=validate(await response.json());if(token!==generation)return;render(report,titles[key],key==='request'?'RECORDED CLI EVIDENCE / REQUEST ONLY':'RECORDED CLI EVIDENCE / LOCAL REGTEST'); document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===key)));}
  catch(error) {if(token!==generation)return;$('report-message').textContent=error.message;$('report-message').className='error';}
}
document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>loadCase(b.dataset.case)));
for(const mode of ['report','scan']) $(mode+'-tab').addEventListener('click',()=>{for(const other of ['report','scan']){$(other+'-panel').hidden=other!==mode;$(other+'-tab').setAttribute('aria-pressed',String(other===mode));}});
$('report-file').addEventListener('change',async event=>{const file=event.target.files[0];if(!file)return;const token=++generation;try {if(file.size>2_000_000)throw Error('Choose a report smaller than 2 MB.');const report=validate(JSON.parse(await file.text()));if(token!==generation)return;render(report,'Your CLI report','UPLOADED REPORT / SUPPLIED EVIDENCE');document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed','false'));}catch(error){$('report-message').textContent=error instanceof SyntaxError?'This file is not valid JSON. Choose an exported CLI report.':error.message;$('report-message').className='error';}event.target.value='';});
function download(report,name) {const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json'}));const a=node('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('download').addEventListener('click',()=>{if(activeReport)download(activeReport,'privacy-report.json');});
function resetScan(){scanReport=null;$('scan-result').replaceChildren();$('scan-download').hidden=true;$('scan-message').textContent='';}
for(const id of ['markers','log']) $(id).addEventListener('input',resetScan);
for(const type of ['plant','clean']) $(type).addEventListener('click',()=>{resetScan();$('markers').value='DEMO-CANARY-7F3A';$('log').value=type==='plant'?'payment received\ndebug: DEMO-CANARY-7F3A\nreceipt stored':'payment received\nreceipt stored';});
$('log-file').addEventListener('change',async event=>{const file=event.target.files[0];if(!file)return;resetScan();if(file.size>2_000_000){$('scan-message').textContent='Choose a UTF-8 log smaller than 2 MB.';$('scan-message').className='error';return;}try{$('log').value=await file.text();}catch{$('scan-message').textContent='Could not read this log file.';}event.target.value='';});
async function digest(text){const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));return [...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('');}
$('scan-form').addEventListener('submit',async event=>{event.preventDefault();resetScan();$('scan-message').className='';try {const markers=[...new Set($('markers').value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean))];const log=$('log').value;if(!markers.length||!log.trim())throw Error('Supply at least one marker and a nonempty log.');if(markers.length>100||log.length>2_000_000)throw Error('Use up to 100 markers and a log smaller than 2 MB.');const findings=[];const hashes=await Promise.all(markers.map(digest));log.split(/\r\n|\n|\r/).forEach((line,index)=>markers.forEach((marker,i)=>{if(line.includes(marker))findings.push({file_index:1,line:index+1,canary_sha256:hashes[i]});}));const check={check:'canary_leak',status:findings.length?'fail':'pass',reason:findings.length?'Synthetic marker found in supplied log':'No supplied canary found',evidence:{files_scanned:1,findings},evidence_source:'Browser-local supplied text and synthetic markers',reproduce:'Rerun with the same supplied log and markers.',privacy_boundary:'Literal matching covers only supplied text and markers.'};scanReport={schema_version:2,network_scope:'No wallet or chain observed (browser-local scan)',checks:[check],limits:['Only the supplied text and literal canaries were scanned.','No wallet receipt, network privacy, or external logs were tested.']};drawCheck(check,$('scan-result'));$('scan-message').textContent=`Scan complete. ${findings.length} marker location${findings.length===1?'':'s'} found.`;$('scan-download').hidden=false;}catch(error){$('scan-message').textContent=error.message;$('scan-message').className='error';}});
$('scan-download').addEventListener('click',()=>{if(scanReport)download(scanReport,'local-canary-scan.json');});
loadCase('shielded');
