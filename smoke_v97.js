// smoke_v97.js — 催租助手：三档分组 + 话术生成 + 收款码
const fs=require('fs'),vm=require('vm'),path=require('path');
const REPO=path.join(__dirname,'tools_build','repo');
let pass=0,fail=0;
function ok(c,m){ if(c){pass++;} else {fail++;console.log('  ✗',m);} }

const app=fs.readFileSync(path.join(REPO,'app.html'),'utf8');

// ---- 静态结构断言 ----
ok(app.includes('data-p="remind"'),'侧边栏有催租助手入口');
ok(app.includes('remind:rRemind'),'renderPage 分发 remind');
ok(app.includes("FileAPI.upload('pay-qrcodes'"),'收款码走 pay-qrcodes 桶');
ok(app.includes("FileAPI.getUrl('pay-qrcodes'"),'收款码读取用 pay-qrcodes 桶');
ok(app.includes('pay_qr_path: path'),'收款码路径存入 workspace_settings(不改表)');
ok(app.includes('weixin://dl/search'),'发给TA 跳转微信搜索');
ok(app.includes('doQuickPay(tenantId)'),'销账复用 doQuickPay 不重写');
ok(app.includes('i18n.js?v=97'),'app 引用 i18n v97');
// 旧功能关键标记仍在
ok(app.includes('function showBillModal'),'旧账单弹窗 showBillModal 保留');
ok(app.includes('function confirmQuickPay'),'旧快速收款 confirmQuickPay 保留');
ok(app.includes('function batchPay'),'旧批量收款 batchPay 保留');

const i18n=fs.readFileSync(path.join(REPO,'i18n.js'),'utf8');
for(const k of ['remind.title','remind.overdue"','remind.today"','remind.soon"','remind.sendBtn','remind.settleBtn']){
  ok(i18n.includes(k),'i18n 含 '+k);
}
ok(/remind\.title": "Rent Reminder"/.test(i18n),'i18n 英文 remind.title');

const sw=fs.readFileSync(path.join(REPO,'sw.js'),'utf8');
ok(sw.includes('fangdong-v97'),'sw 升 v97');

const wn=fs.readFileSync(path.join(REPO,'whatsnew.html'),'utf8');
ok(wn.includes('V97')&&wn.includes('催租助手'),'whatsnew 有 v97 卡片');
ok(/V96[\s\S]{0,40}version-tag/.test(wn)||wn.includes('>V96<'),'v96 标记退为 V96');

// ---- 抽取催租助手整段函数，在沙箱里真实执行 ----
const startMark='// ========== 催租助手（v97 纯增量） ==========';
const endMark='// ========== 租金管理 ==========';
const si=app.indexOf(startMark), ei=app.indexOf(endMark);
ok(si>=0&&ei>si,'成功定位催租助手代码块');
const block=app.slice(si,ei);

// 复刻真实工具函数
function daysDiff(a,b){return Math.ceil((new Date(b)-new Date(a))/86400000)}
function _billNum(v){var n=parseFloat(v);return isNaN(n)||!isFinite(v)?0:n}
function addMonths(dateStr,months){var parts=dateStr.split('-');var y=parseInt(parts[0]);var m=parseInt(parts[1])-1+months;var d=parseInt(parts[2]);y+=Math.floor(m/12);m=m%12;if(m<0)m+=12;var ld=new Date(y,m+1,0).getDate();if(d>ld)d=ld;return y+'-'+String(m+1).padStart(2,'0')+'-'+String(d).padStart(2,'0')}

const dict={
  'remind.hello':'{name}你好，',
  'remind.overdue':'你{room}房的房租¥{amount}（{period}）已逾期{n}天，按合同约定请尽快缴清。',
  'remind.today':'你{room}房的房租¥{amount}（{period}）今天该交啦。',
  'remind.soon':'你{room}房的房租¥{amount}（{period}）还有{n}天到期。',
  'remind.tail':'收到我会马上登记好。',
  'remind.qrTail':'收款码我一并发你，扫码就行。'
};
function t(key,vars){var s=dict[key]||key;if(vars)Object.keys(vars).forEach(function(k){s=s.replace('{'+k+'}',vars[k])});return s}

const TD='2026-09-23';
function makeTenant(id,name,room,due,amount,status){
  return {tenant:{id:id,name:name,status:'active',pay_method:'月付'},
    room:{id:'r_'+id,name:room},
    bill:{tenant_id:id,amount:amount,due_date:due,period_start:addMonths(due,-1),status:status}};
}
const t1=makeTenant('t1','张三','201','2026-09-18',1000,'overdue'); // 逾期5天
const t2=makeTenant('t2','李四','202',TD,800,'pending');          // 今天
const t3=makeTenant('t3','王五','203','2026-09-25',900,'pending'); // 2天后
const t4=makeTenant('t4','赵六','204','2026-10-10',1100,'pending');// 远，不应出现
const t5=makeTenant('t5','钱七','205','2026-09-20',700,'paid');    // 已缴，不应出现

const sandbox={
  console:console,
  cache:{
    tenants:[t1.tenant,t2.tenant,t3.tenant,t4.tenant,t5.tenant],
    rooms:[t1.room,t2.room,t3.room,t4.room,t5.room],
    rents:[t1.bill,t2.bill,t3.bill,t4.bill,t5.bill],
    settings:{}
  },
  daysDiff:daysDiff,_billNum:_billNum,addMonths:addMonths,
  _payInterval:function(){return 1},
  fmtShortPeriod:function(r){return r.period_start.slice(5).replace(/-/g,'/')+' ~ '+r.due_date.slice(5).replace(/-/g,'/')},
  i18n:{t:t},
  today:function(){return TD},
  navigator:{clipboard:null},
  window:{},
  FileAPI:{getUrl:function(b,p){return '/files/'+b+'/'+p}},
  toast:function(){},
  getOwnerId:function(){return 'o1'},
  sb:{from:function(){return {upsert:async()=>({})}}}
};
vm.createContext(sandbox);
vm.runInContext(block,sandbox);

const g=sandbox._remindCollect();
ok(g.overdue.length===1 && g.overdue[0].tenant.id==='t1','逾期分组命中张三');
ok(g.today.length===1 && g.today[0].tenant.id==='t2','今天分组命中李四');
ok(g.soon.length===1 && g.soon[0].tenant.id==='t3','3天内分组命中王五');
ok(!g.overdue.concat(g.today).concat(g.soon).some(function(x){return x.tenant.id==='t4'}),'远期账单赵六不出现');
ok(!g.overdue.concat(g.today).concat(g.soon).some(function(x){return x.tenant.id==='t5'}),'已缴账单钱七不出现');
ok(g.overdue[0].days===-5,'逾期天数=5');
ok(g.overdue[0].total===1000,'逾期金额合计=1000');

const msgOver=sandbox._remindMsg(g.overdue[0]);
ok(msgOver.indexOf('张三你好')===0,'逾期话术以称呼开头');
ok(msgOver.includes('¥1,000')&&msgOver.includes('逾期5天'),'逾期话术含金额和逾期天数');
ok(msgOver.endsWith('收到我会马上登记好。'),'无收款码时用普通结尾');

const msgSoon=sandbox._remindMsg(g.soon[0]);
ok(msgSoon.includes('还有2天到期'),'提前提醒话术含剩余天数');

// 配置收款码后话术结尾改变
sandbox.cache.settings.pay_qr_path='o1/abc.jpg';
const msgQr=sandbox._remindMsg(g.today[0]);
ok(msgQr.includes('收款码我一并发你'),'配收款码后话术带收款码提示');

// 复制函数真实调用 navigator.clipboard
let copied=null;
sandbox.navigator.clipboard={writeText:async function(txt){copied=txt}};
sandbox._copyText('TEST_TEXT','ok');
setTimeout(function(){
  ok(copied==='TEST_TEXT','_copyText 调用 clipboard.writeText');
  console.log(`\nsmoke_v97: ${pass} passed, ${fail} failed`);
  process.exit(fail?1:0);
},20);
