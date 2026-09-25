const fs=require('fs'),path=require('path'),vm=require('vm');
const REPO=path.join(__dirname,'tools_build','repo');
const app=fs.readFileSync(path.join(REPO,'app.html'),'utf8');
const i18nSrc=fs.readFileSync(path.join(REPO,'i18n.js'),'utf8');
let pass=0,fail=0;
function ok(c,m){ if(c){pass++}else{fail++;console.log('✗',m)} }

// 结构 / 版本
ok(/fangdong-v100/.test(fs.readFileSync(path.join(REPO,'sw.js'),'utf8')),'sw v100');
ok(/i18n\.js\?v=100/.test(app),'i18n ref v100');
ok(!app.includes('data-p="remind"'),'independent remind nav removed');
ok(!app.includes('remind:rRemind'),'remind dispatch removed');
ok(!/function rRemind\b/.test(app),'rRemind removed');
ok(/function _billSendWx\b/.test(app),'_billSendWx present');
ok(/function _billRenderPayQr\b/.test(app),'_billRenderPayQr present');
ok(/function _robustDecode\b/.test(app),'_robustDecode present');
ok(/function classifyPayQr\b/.test(app),'classifyPayQr kept');
ok(/function showPayQrModal\b/.test(app),'showPayQrModal kept');
ok(!app.includes('weixin://dl/search'),'fake search scheme removed');
ok(app.includes("window.location.href='weixin://'"),'reliable weixin:// open');
ok(fs.existsSync(path.join(REPO,'vendor/zxing.min.js')),'zxing vendor');
ok(fs.existsSync(path.join(REPO,'deploy_v100.sh')),'deploy script');
// i18n keys
ok(i18nSrc.includes('"bill.sendWx": "发给TA（打开微信）"'),'bill.sendWx zh');
ok(i18nSrc.includes('"bill.addQr": "上传我的收款码'),'bill.addQr zh');
ok(i18nSrc.includes('"bill.sendWx": "Send (open WeChat)"'),'bill.sendWx en');

function grab(name){
  const lines=app.split('\n');
  const start=lines.findIndex(l=>new RegExp('function\\s+'+name+'\\s*\\(').test(l));
  if(start<0)return null;
  let depth=0,began=false,out=[];
  for(let i=start;i<lines.length;i++){out.push(lines[i]);
    for(const ch of lines[i]){if(ch==='{'){depth++;began=true}if(ch==='}')depth--}
    if(began&&depth===0)break}
  return out.join('\n');
}

// 真实执行 _looksCollectPayload
{
  const startLine=app.split('\n').findIndex(l=>l.includes('var _COLLECT_PATTERNS'));
  const codeText=app.split('\n').slice(startLine,startLine+18).join('\n');
  const end=codeText.indexOf('return false;\n}');
  const code=codeText.slice(0,end+'return false;\n}'.length);
  const sb={};vm.createContext(sb);vm.runInContext(code,sb);
  ok(sb._looksCollectPayload('wxp://f2f0abc'),'wechat collect accepted');
  ok(sb._looksCollectPayload('https://qr.alipay.com/bax1'),'alipay accepted');
  ok(!sb._looksCollectPayload('https://x.com'),'random rejected');
  ok(!sb._looksCollectPayload('134567890123456789'),'digits rejected');
}

// 真实执行 _billBuildText 生成话术
{
  const sb={
    localStorage:{getItem:()=>'zh-CN'},
    _billFmt:n=>Number(n).toFixed(2),
    cache:{settings:{pay_qr_path:'u/1.jpg'}},
    window:{},
    i18n:{t:(k,v)=>{
      const m={'bill.rent':'房租','meter.coldWater':'冷水','meter.hotWater':'热水','meter.electricity':'电',
        'bill.total':'合计','bill.thanksEn':'Thanks','bill.qrInText':'收款码我一并发你，扫码即可'};
      let s=m[k]!==undefined?m[k]:k; if(v)s=s.replace(/\{(\w+)\}/g,(_,x)=>v[x]); return s;}}
  };
  vm.createContext(sb);
  vm.runInContext(grab('_billBuildText'),sb);
  sb.window._billCtx={tenant:{name:'金巧巧'},room:{name:'402'}};
  sb._billCollect=()=>({rent:800,cw:0,hw:0,el:0,others:[],note:'',total:800});
  const s=vm.runInContext('_billBuildText()',sb);
  ok(s.includes('金巧巧'),'text name');
  ok(s.includes('402'),'text room');
  ok(s.includes('¥800.00'),'text amount');
  ok(s.includes('收款码我一并发你'),'text qr tail');
}

// 校验 _robustDecode 的候选策略数量与缩放循环（静态结构：3 区域 × 4 尺寸 = 12 次尝试）
{
  const fn=grab('_robustDecode');
  ok(/targetSizes=\[1400,1000,700,500\]/.test(fn),'4 scale targets');
  ok((fn.match(/crops/g)||[]).length>=1,'crop regions defined');
  ok(/decodeFromImageElement/.test(fn),'uses decodeFromImageElement');
  ok(/TRY_HARDER/.test(fn),'uses TRY_HARDER hint');
}

console.log(`\n${pass} 通过, ${fail} 失败`);
process.exit(fail?1:0);
