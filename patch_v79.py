# -*- coding: utf-8 -*-
"""v79 patch: 催租账单生成二维码 -> 租户扫码看抄表照片。纯增量,不改动现有账单逻辑。"""
import io,sys,re

APP='app.html'
s=io.open(APP,encoding='utf-8').read()
orig=s

JS = r'''
// ===== v79: 账单抄表照片扫码分享（纯增量，不改动现有账单逻辑）=====
function _qrReady(){return new Promise(function(res){
  if(typeof QRCode!=="undefined"){res(true);return}
  var srcs=["vendor/qrcode.min.js","https://cdn.jsdelivr.net/gh/davidshimjs/qrcodejs/qrcode.min.js","https://cdn.bootcdn.net/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"];var i=0;
  (function tryL(){if(i>=srcs.length){res(false);return}
    var sc=document.createElement("script");sc.src=srcs[i];
    sc.onload=function(){if(typeof QRCode!=="undefined")res(true);else{i++;tryL()}};
    sc.onerror=function(){i++;tryL()};document.head.appendChild(sc);})();
})}
function _billShareBase(){var b=(location.origin||FILE_BASE||"");return String(b).replace(/\/+$/,"")}
function _billMeterPhotos(tenantId){
  var arr=(cache.meters||[]).filter(function(m){return m.tenant_id===tenantId&&m.photo_url}).slice();
  arr.sort(function(a,b){return String(b.reading_date||"").localeCompare(String(a.reading_date||""))||String(b.created_at||"").localeCompare(String(a.created_at||""))});
  var photos=[];
  if(arr.length){var p=arr[0].photo_url;if(p.indexOf("contract-photos/")===0)p=p.substring("contract-photos/".length);photos.push({path:p,date:arr[0].reading_date||""})}
  return photos;
}
function _billShareText(d){
  var lang=localStorage.getItem("lang")||"zh-CN";var lines=[];
  if(d.rent>0)lines.push((lang==="en"?"Rent":"房租")+" ¥"+_billFmt(d.rent));
  if(d.cw>0)lines.push(i18n.t("meter.coldWater")+" ¥"+_billFmt(d.cw));
  if(d.hw>0)lines.push(i18n.t("meter.hotWater")+" ¥"+_billFmt(d.hw));
  if(d.el>0)lines.push(i18n.t("meter.electricity")+" ¥"+_billFmt(d.el));
  (d.others||[]).forEach(function(o){lines.push(o.name+" ¥"+_billFmt(o.amount))});
  var head="";
  if(lang==="en"){head="Payment notice";}
  else{var ps=(window._billCtx&&window._billCtx.bills)?window._billCtx.bills.map(function(b){return _monthLabel(b.period_start||b.due_date)}).filter(function(v,i,ar){return ar.indexOf(v)===i}):[];head="缴费期间："+(ps.join("、")||"-");}
  return head+"\n"+lines.join("\n");
}
function _billNewToken(){
  try{if(crypto&&crypto.randomUUID)return crypto.randomUUID()}catch(e){}
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,function(c){var r=Math.random()*16|0,v=c==="x"?r:(r&0x3|0x8);return v.toString(16)});
}
async function _genBillShareQR(){
  var ctx=window._billCtx;if(!ctx||!ctx.tenant){toast(i18n.t("common.opFail"),"e");return}
  var t=ctx.tenant,rm=ctx.room;var d=_billCollect();var photos=_billMeterPhotos(t.id);
  try{
    var token=_billNewToken();var exp=new Date(Date.now()+90*86400000).toISOString();
    var payload={owner_id:getOwnerId(),tenant_id:t.id,share_token:token,tenant_name:t.name||"",room_name:rm?rm.name:"",bill_summary:_billShareText(d),total_amount:d.total,photos:photos,expires_at:exp};
    var ins=await sb.from("bill_shares").insert(payload).select().single();
    if(ins.error||!ins.data){toast((ins.error&&ins.error.message)||i18n.t("common.opFail"),"e");return}
    var url=_billShareBase()+"/billshare.html?token="+token;
    var ok=await _qrReady();
    var qrHtml=ok?'<div id="bqrBox" style="display:flex;justify-content:center;padding:8px 0"></div>':'<div style="color:var(--d);font-size:13px;margin:10px 0">'+i18n.t("bqr.qrFail")+'</div>';
    openModal('<div class="m-hd"><h3>📷 '+i18n.t("bqr.title")+'</h3><button class="m-x" onclick="closeModal()">&times;</button></div>'
      +'<div class="m-bd" style="text-align:center">'
      +'<p style="font-size:13px;color:var(--ts);margin-bottom:6px">'+i18n.t("bqr.hint")+'</p>'
      +qrHtml
      +'<div id="bqrUrl" style="background:var(--bg);border-radius:8px;padding:10px;margin:10px 0;word-break:break-all;font-size:12px;line-height:1.6;user-select:all;text-align:left">'+esc(url)+'</div>'
      +'<p style="font-size:11px;color:var(--ts)">'+i18n.t("bqr.privacy")+'</p>'
      +'</div>'
      +'<div class="m-ft"><button class="btn btn-gh" onclick="_copyBillShareUrl()">🔗 '+i18n.t("bqr.copyLink")+'</button><button class="btn btn-p" onclick="closeModal()">'+i18n.t("common.close")+'</button></div>');
    if(ok){new QRCode(document.getElementById("bqrBox"),{text:url,width:220,height:220,colorDark:"#1E293B",colorLight:"#ffffff",correctLevel:QRCode.CorrectLevel.M})}
  }catch(e){console.error("bill share",e);toast(i18n.t("common.opFail"),"e")}
}
function _copyBillShareUrl(){var el=document.getElementById("bqrUrl");if(el&&el.textContent.trim())_copyText(el.textContent.trim())}
// ===== v79 end =====
function showBillModal(targetType,targetId){'''

anchor='function showBillModal(targetType,targetId){'
assert s.count(anchor)>=1, "showBillModal anchor not found"
# 只在第一处（定义处）前插入；定义处是行首 function
s=s.replace(anchor, JS, 1)

# 弹窗 footer 加二维码按钮（在“保存图片”按钮前）
foot_anchor='+\'<button class="btn btn-p" onclick="_billGenImage()">'
assert s.count(foot_anchor)==1, "footer anchor count=%d"%s.count(foot_anchor)
foot_new=('+\'<button class="btn btn-gh" onclick="_genBillShareQR()">📷 \'+i18n.t("bqr.btn")+\'</button>\'\n    '
          +foot_anchor)
s=s.replace(foot_anchor, foot_new, 1)

io.open(APP,'w',encoding='utf-8').write(s)
print("app.html patched: JS injected=%s, footer btn=%s"%(JS in s, "_genBillShareQR()" in s))

# ---- sw.js ----
SW='sw.js'
w=io.open(SW,encoding='utf-8').read()
w=w.replace("var CACHE_NAME='fangdong-v78'","var CACHE_NAME='fangdong-v79'")
add_assets="  './billshare.html',\n  './vendor/qrcode.min.js',"
if './billshare.html' not in w:
    w=w.replace("  './sign.html',\n","  './sign.html',\n"+add_assets+"\n",1)
io.open(SW,'w',encoding='utf-8').write(w)
print("sw.js: v79=%s, billshare=%s, qrcode=%s"%("fangdong-v79" in w, "./billshare.html" in w, "./vendor/qrcode.min.js" in w))

# ---- app.html i18n 版本号 ----
s2=io.open(APP,encoding='utf-8').read()
s2=s2.replace("i18n.js?v=78","i18n.js?v=79")
io.open(APP,'w',encoding='utf-8').write(s2)
print("app.html i18n ?v=79:", "i18n.js?v=79" in s2)
