const fs=require('fs'),path=require('path'),vm=require('vm');
const REPO=path.join(__dirname,'tools_build','repo');
const app=fs.readFileSync(path.join(REPO,'app.html'),'utf8');
const i18nSrc=fs.readFileSync(path.join(REPO,'i18n.js'),'utf8');
let pass=0,fail=0;
function ok(c,m){ if(c){pass++}else{fail++;console.log('✗',m)} }

// ---- 静态结构 ----
ok(/fangdong-v98/.test(fs.readFileSync(path.join(REPO,'sw.js'),'utf8')),'sw v98');
ok(/i18n\.js\?v=98/.test(app),'i18n ref v98');
ok(/remind:rRemind/.test(app),"renderPage dispatch remind");
ok(app.includes('data-p="remind"'),'nav entry');
ok(app.includes('vendor/zxing.min.js'),'zxing loader path');
ok(app.includes('function classifyPayQr'),'classifyPayQr present');
ok(app.includes('function loadZXing'),'loadZXing present');
ok(app.includes('groups.history')||/history:\[\]/.test(app),'history bucket');
ok(fs.existsSync(path.join(REPO,'supabase/migrations/20260924000000_pay_qr_path.sql')),'migration file');
ok(fs.existsSync(path.join(REPO,'vendor/zxing.min.js')),'zxing vendor file');

// ---- 搭运行环境 ----
const win={};
vm.runInNewContext(i18nSrc,{window:win});
const i18nApi=win.i18n;
ok(!!i18nApi,'window.i18n exposed');
ok(typeof i18nApi.t==='function','i18n.t function');
// 直接校验新 key 在中文文案中存在（i18n.t 默认语言可能未设置，故用源串）
ok(i18nSrc.includes('"remind.rejectPaycode": "这是【付款码】'),'rejectPaycode zh i18n');
ok(i18nSrc.includes('"remind.groupHistory": "历史欠款（已退租）"'),'groupHistory zh i18n');
ok(i18nSrc.includes('"remind.rejectPaycode": "That is a PAYMENT code'),'rejectPaycode en i18n');

// ---- 抽取被测函数 ----
function grab(name){
  const lines=app.split('\n');
  const start=lines.findIndex(l=>l.includes('function '+name+'(')||new RegExp('function\\s+'+name+'\\s*\\(').test(l));
  if(start<0)return null;
  let depth=0,began=false,out=[];
  for(let i=start;i<lines.length;i++){
    out.push(lines[i]);
    for(const ch of lines[i]){if(ch==='{'){depth++;began=true}if(ch==='}')depth--}
    if(began&&depth===0)break;
  }
  return out.join('\n');
}
function ctxFor(extra){
  return Object.assign({
    today:()=>'2026-09-24',
    daysDiff:(a,b)=>Math.round((new Date(b)-new Date(a))/864e5),
    _billNum:n=>Number(n)||0,
    cache:{tenants:[],rents:[],rooms:[],settings:{}},
    console
  },extra||{});
}

// _billEff
vm.runInNewContext(grab('_billEff')+'\nthis._billEff=_billEff;',ctxFor(global.__c=global.__c||{}));

// _remindCollect
{
  const sandbox=ctxFor();
  vm.createContext(sandbox);
  vm.runInContext('var REMIND_AHEAD_DAYS=3;'+grab('_billEff')+'\n'+grab('_remindCollect'),sandbox);
  sandbox.cache.rooms=[{id:'r1',name:'201'},{id:'r2',name:'402'},{id:'r3',name:'403'}];
  sandbox.cache.tenants=[
    {id:'t1',name:'段卿',status:'active',room_id:'r1',pay_method:'month'},
    {id:'t2',name:'金巧巧',status:'active',room_id:'r2',pay_method:'month'},
    {id:'t3',name:'旺也',status:'active',room_id:'r3',pay_method:'month'},
    {id:'t4',name:'何木成',status:'inactive',room_id:'r9',pay_method:'month'},
    {id:'t5',name:'远未到期',status:'active',room_id:'r5',pay_method:'month'}
  ];
  sandbox.cache.rents=[
    {id:'a1',tenant_id:'t1',period_start:'2026-09-06',due_date:'2026-10-06',amount:1000,status:'overdue'},
    {id:'a2',tenant_id:'t2',period_start:'2026-09-20',due_date:'2026-10-20',amount:800,status:'overdue'},
    {id:'a3',tenant_id:'t3',period_start:'2026-09-20',due_date:'2026-10-20',amount:800,status:'overdue'},
    {id:'h1',tenant_id:'t4',period_start:'2026-07-25',due_date:'2026-08-25',amount:1000,status:'overdue'},
    {id:'h2',tenant_id:'t4',period_start:'2026-08-25',due_date:'2026-09-25',amount:1200,status:'overdue'},
    {id:'f1',tenant_id:'t5',period_start:'2026-10-20',due_date:'2026-11-20',amount:900,status:'pending'}
  ];
  const g=vm.runInContext('_remindCollect()',sandbox);
  ok(g.overdue.length===3,'overdue bucket has 3 active (got '+g.overdue.length+')');
  ok(g.history.length===1,'history bucket has 1 tenant (got '+g.history.length+')');
  ok(g.soon.length===0&&g.today.length===0,'soon/today empty');
  const dq=g.overdue.find(x=>x.tenant.id==='t1');
  ok(dq.total===1000,'段卿 total ¥1000 (got '+dq.total+')');
  ok(dq.days===-18,'段卿 days=-18 (got '+dq.days+')');
  const he=g.history[0];
  ok(he.total===2200,'何木成历史欠款 ¥2200 (got '+he.total+')');
  ok(he.kind==='history','history kind flag');
}

// 收款码 payload 判定
{
  const lines=app.split('\n');
  const start=lines.findIndex(l=>l.includes('var _COLLECT_PATTERNS'));
  let chunk=[];
  for(let i=start;i<lines.length;i++){chunk.push(lines[i]);if(lines[i].includes('function _looksCollectPayload')){
    // 继续到该函数结束
  }}
  // 简单取从 _COLLECT_PATTERNS 到 _looksCollectPayload 函数结束
  const srcText=lines.slice(start,start+20).join('\n');
  const endIdx=srcText.indexOf('return false;\n}');
  const code=srcText.slice(0,endIdx+'return false;\n}'.length);
  const sb={};vm.createContext(sb);vm.runInContext(code,sb);
  ok(sb._looksCollectPayload('wxp://f2f0abc')===true,'wechat collect accepted');
  ok(sb._looksCollectPayload('https://qr.alipay.com/bax1')===true,'alipay collect accepted');
  ok(sb._looksCollectPayload('https://example.com/foo')===false,'random url rejected');
  ok(sb._looksCollectPayload('134567890123456789')===false,'plain digits rejected');
}

console.log(`\n${pass} 通过, ${fail} 失败`);
process.exit(fail?1:0);
