# -*- coding: utf-8 -*-
import io,sys

ROOT='/Coze/Drive/明灯/所有对话/主对话/tools_build/repo/'

def patch(path,repls):
    s=io.open(path,encoding='utf-8').read()
    for i,(old,new) in enumerate(repls):
        c=s.count(old)
        if c!=1:
            print('  [STOP] %s 替换#%d 命中 %d 次（应为1）：'%(path.split('/')[-1],i,c))
            print('   锚点前80字: '+old[:80].replace('\n','\\n'))
            return False
        s=s.replace(old,new,1)
    io.open(path,'w',encoding='utf-8').write(s)
    print('  [OK] %s：%d 处替换完成'%(path.split('/')[-1],len(repls)))
    return True

# ============ app.html ============
app=ROOT+'app.html'
repls=[]

# --- 优化1：新增表单 红星 ---
# 月租金（add）
repls.append((
'<label>\'+i18n.t(\'tenant.rentLabel\')+\'</label><input class="fc" id="fTRa"',
'<label>\'+i18n.t(\'tenant.rentLabel\')+\'<span class="req">*</span></label><input class="fc" id="fTRa"'))
# 入住日期（add，带 value today）
repls.append((
"""<label>'+i18n.t('tenant.moveInDate')+'</label><input class="fc" id="fTMI" type="date" value="'+today()+'">""",
"""<label>'+i18n.t('tenant.moveInDate')+'<span class="req">*</span></label><input class="fc" id="fTMI" type="date" value="'+today()+'">"""))
# 合同到期（add）
repls.append((
"""<label>'+i18n.t('tenant.contractEndDate')+'</label><input class="fc" id="fTCE" type="date"></div></div><div class="fr"><div class="fg"><label>'+i18n.t('room.depositLabel')+'""",
"""<label>'+i18n.t('tenant.contractEndDate')+'<span class="req">*</span></label><input class="fc" id="fTCE" type="date"></div></div><div class="fr"><div class="fg"><label>'+i18n.t('room.depositLabel')+'"""))

# --- 优化1：编辑表单 红星（仅编辑态显示，避免影响历史只读数据） ---
# 月租金（edit）
repls.append((
'<label>\'+i18n.t(\'cg.monthlyRent\')+\'</label><input class="fc" id="fTRa"',
'<label>\'+i18n.t(\'cg.monthlyRent\')+(isEdit?\'<span class="req">*</span>\':\'\')+\'</label><input class="fc" id="fTRa"'))
repls.append((
"""<label>'+i18n.t('tenant.moveInDate')+'</label><input class="fc" id="fTMI" type="date" value="'+(t.move_in_date||'')+'"'+(isEdit?'':' readonly')+'>""",
"""<label>'+i18n.t('tenant.moveInDate')+(isEdit?'<span class="req">*</span>':'')+'</label><input class="fc" id="fTMI" type="date" value="'+(t.move_in_date||'')+'"'+(isEdit?'':' readonly')+'>"""))
repls.append((
"""<label>'+i18n.t('tenant.contractEndDate')+'</label><input class="fc" id="fTCE" type="date" value="'+(t.contract_end||'')+'"'+(isEdit?'':' readonly')+'>""",
"""<label>'+i18n.t('tenant.contractEndDate')+(isEdit?'<span class="req">*</span>':'')+'</label><input class="fc" id="fTCE" type="date" value="'+(t.contract_end||'')+'"'+(isEdit?'':' readonly')+'>"""))

# --- 优化1：doAddTenant 校验（在 payMethod 校验后插入 moveIn 取值前） ---
repls.append((
"""if(!payMethod){toast(''+i18n.t('rent.selectPayMethod')+'','e');return}var rent=parseFloat(document.getElementById('fTRa').value)||0;var newPhotos=pendingPhotos['new']||[];var moveIn=document.getElementById('fTMI').value||null;var contractEnd=document.getElementById('fTCE').value||null;""",
"""if(!payMethod){toast(''+i18n.t('rent.selectPayMethod')+'','e');return}var rent=parseFloat(document.getElementById('fTRa').value)||0;if(!(rent>0)){toast(i18n.t('tenant.needRent'),'e');return}var newPhotos=pendingPhotos['new']||[];var moveIn=document.getElementById('fTMI').value||null;var contractEnd=document.getElementById('fTCE').value||null;if(!moveIn){toast(i18n.t('tenant.needMoveIn'),'e');return}if(!contractEnd){toast(i18n.t('tenant.needContractEnd'),'e');return}if(contractEnd<=moveIn){toast(i18n.t('tenant.contractAfterMoveIn'),'e');return}"""))

# --- 优化1：doEditTenant 校验（函数开头，old/nrm 之后） ---
repls.append((
"""var old=cache.tenants.find(function(x){return x.id===id});var nrm=document.getElementById('fTRm').value;var r=await sb.from('tenants').update(""",
"""var old=cache.tenants.find(function(x){return x.id===id});var nrm=document.getElementById('fTRm').value;var _rentV=parseFloat(document.getElementById('fTRa').value)||0;if(!(_rentV>0)){toast(i18n.t('tenant.needRent'),'e');return}var _miV=document.getElementById('fTMI').value||null;if(!_miV){toast(i18n.t('tenant.needMoveIn'),'e');return}var _ceV=document.getElementById('fTCE').value||null;if(!_ceV){toast(i18n.t('tenant.needContractEnd'),'e');return}if(_ceV<=_miV){toast(i18n.t('tenant.contractAfterMoveIn'),'e');return}var r=await sb.from('tenants').update("""))

# --- 优化3：renderMeterList 加编辑按钮 ---
repls.append((
"""'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">'+toggleBtn+photoBtn+delBtn+'</div>'+""",
"""'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">'+toggleBtn+(canEdit()?'<button class="btn btn-sm btn-gh" onclick="showMeterEditModal('+Q+m.id+Q+')">✏️ '+i18n.t('common.edit')+'</button>':'')+photoBtn+delBtn+'</div>'+"""))

# --- 优化2：_billDrawCanvas 签名 ---
repls.append((
"function _billDrawCanvas(scale){\n  var d=_billCollect(),ctx0=window._billCtx;",
"function _billDrawCanvas(scale,qrImg,qrHint){\n  var d=_billCollect(),ctx0=window._billCtx;"))

# --- 优化2：H 高度公式（修正备注/合计重叠 + 二维码空间） ---
repls.append((
"""  var H=438+_rowH+noteLines.length*34;""",
"""  var H=446+_rowH+noteLines.length*30+(qrImg?340:0);"""))

# --- 优化2：备注+二维码 绘制段（替换原"备注/底部"之间的布局） ---
old_tail='''  // 备注
  y+=40;
  if(noteLines.length){
    c.fillStyle='#6b7280';c.font='17px sans-serif';c.textAlign='left';
    noteLines.forEach(function(ln){c.fillText(i18n.t('bill.note')+'：'+ln,44,y);y+=34});
    y+=10;
  }
  // 底部
  c.fillStyle='#9ca3af';c.font='15px sans-serif';c.textAlign='center';
  c.fillText(i18n.t('bill.imgFooter'),W/2,H-44);'''
new_tail='''  // 备注（v80:修正纵向位置，避免压在合计条上）
  y+=92;
  if(noteLines.length){
    c.fillStyle='#6b7280';c.font='17px sans-serif';c.textAlign='left';
    c.fillText(i18n.t('bill.note')+'：'+noteLines[0],44,y);
    for(var ni=1;ni<noteLines.length;ni++){y+=26;c.fillText(noteLines[ni],44,y)}
    y+=22;
  }
  // v80:账单内嵌扫码二维码
  if(qrImg){
    var qs=220;var qx=(W-qs)/2;
    c.fillStyle='#374151';c.font='16px sans-serif';c.textAlign='center';
    c.fillText(qrHint||i18n.t('bill.scanTip'),W/2,y+8);
    c.drawImage(qrImg,qx,y+22,qs,qs);
  }
  // 底部
  c.fillStyle='#9ca3af';c.font='15px sans-serif';c.textAlign='center';
  c.fillText(i18n.t('bill.imgFooter'),W/2,H-30);'''
repls.append((old_tail,new_tail))

# --- 优化2：_billGenImage 改 async + 嵌入二维码；新增3个辅助函数（插在函数前） ---
old_gen='''function _billGenImage(){
  var d=_billCollect();
  if(d.total<=0&&d.rent<=0){toast(i18n.t('bill.noAmount'),'w');return}
  try{
    var cv=_billDrawCanvas(2);'''
new_gen='''// ===== v80: 账单图片内嵌扫码二维码（纯增量，失败自动退回无二维码图片）=====
async function _billShareUrlForImage(){
  var ctx=window._billCtx;if(!ctx||!ctx.tenant)return null;
  var t=ctx.tenant,rm=ctx.room;var d=_billCollect();var photos=_billMeterPhotos(t.id);
  try{
    var token=_billNewToken();var exp=new Date(Date.now()+90*86400000).toISOString();
    var payload={owner_id:getOwnerId(),tenant_id:t.id,share_token:token,tenant_name:t.name||"",room_name:rm?rm.name:"",bill_summary:_billShareText(d),total_amount:d.total,photos:photos,expires_at:exp};
    var ins=await sb.from("bill_shares").insert(payload).select().single();
    if(ins.error||!ins.data)return null;
    return _billShareBase()+"/billshare.html?token="+token;
  }catch(e){console.warn('bill share url for image failed:',e);return null}
}
function _qrDataURL(text,size){
  return new Promise(function(res){
    try{
      var box=document.createElement('div');
      box.style.cssText='position:fixed;left:-9999px;top:-9999px;width:'+size+'px;height:'+size+'px;opacity:0;pointer-events:none';
      document.body.appendChild(box);
      new QRCode(box,{text:text,width:size,height:size,colorDark:'#1E293B',colorLight:'#ffffff',correctLevel:QRCode.CorrectLevel.M});
      setTimeout(function(){
        var cv=box.querySelector('canvas'),img=box.querySelector('img');
        if(cv){try{res(cv.toDataURL('image/png'))}catch(e){res(null)}}
        else if(img&&img.src&&img.complete&&img.naturalWidth>0){res(img.src)}
        else{var t0=Date.now();var iv=setInterval(function(){
          var c2=box.querySelector('canvas'),im2=box.querySelector('img');
          if(c2){clearInterval(iv);try{res(c2.toDataURL('image/png'))}catch(e){res(null)}}
          else if(im2&&im2.src&&im2.complete&&im2.naturalWidth>0){clearInterval(iv);res(im2.src)}
          else if(Date.now()-t0>4000){clearInterval(iv);res(null)}
        },80)}
        setTimeout(function(){try{document.body.removeChild(box)}catch(e){}},200);
      },180);
    }catch(e){console.warn('qr dataurl failed:',e);res(null)}
  });
}
function _loadImg(src){return new Promise(function(res){if(!src){res(null);return}var im=new Image();im.onload=function(){res(im)};im.onerror=function(){res(null)};im.src=src})}
// ===== v80 end =====
async function _billGenImage(){
  var d=_billCollect();
  if(d.total<=0&&d.rent<=0){toast(i18n.t('bill.noAmount'),'w');return}
  var qrImg=null,qrHint='';
  try{
    var url=await _billShareUrlForImage();
    if(url){
      var ok=await _qrReady();
      if(ok){var du=await _qrDataURL(url,240);if(du)qrImg=await _loadImg(du)}
      qrHint=i18n.t('bill.scanTip');
    }
  }catch(e){console.warn('bill qr image skipped:',e)}
  try{
    var cv=_billDrawCanvas(2,qrImg,qrHint);'''
repls.append((old_gen,new_gen))

# --- 优化3：新增 showMeterEditModal + doMeterUpdate（插在 delMeter 之后、_monthLabel 之前） ---
anchor_edit='''function _monthLabel(d){if(!d)return'';var p=String(d).split('-');return p[0]+'年'+parseInt(p[1],10)+'月'}'''
edit_fns='''// ===== v80: 水电抄表记录可编辑（纯增量，新增函数，不改原有新增逻辑）=====
async function showMeterEditModal(id){
  if(!canEdit()){toast(i18n.t('common.readOnly'),'w');return}
  var m=(cache.meters||[]).find(function(x){return x.id===id});if(!m)return;
  var t=cache.tenants.find(function(x){return x.id===m.tenant_id});if(!t)return;
  var p=meterGetPrices(m.tenant_id,m.room_id||t.room_id);
  window._meterCtx={tenantId:m.tenant_id,editId:id,prices:p,seq:0,items:[]};
  function n2(v){if(v===null||v===undefined||v==='')return '';var n=parseFloat(v);return isNaN(n)?'':n}
  var sub=(cache.meterItems||[]).filter(function(x){return x.reading_id===id}).sort(function(a,b){return(a.sort_order||0)-(b.sort_order||0)});
  var seq=0;
  function pushItem(o){seq++;o.id=seq;window._meterCtx.items.push(o)}
  if(sub.length){
    sub.forEach(function(it){
      if(it.kind==='other'){
        pushItem({type:'other',kind:'other',label:it.label||'',cur:null,prev:null,usage:null,price:null,amount:n2(it.amount)});
      }else{
        var def=_meterKindDef(it.kind);
        pushItem({type:'meter',kind:it.kind,label:it.label||def.label,
          cur:n2(it.cur_reading),prev:n2(it.prev_reading),usage:n2(it.usage),price:n2(it.price),amount:n2(it.amount)});
      }
    });
  }else{
    [['cold_water',m.cold_water,m.cold_water_price,m.cold_water_usage,m.cold_water_fee],
     ['hot_water',m.hot_water,m.hot_water_price,m.hot_water_usage,m.hot_water_fee],
     ['electricity',m.electricity,m.electricity_price,m.electricity_usage,m.electricity_fee]].forEach(function(a){
      if(a[1]!==null&&a[1]!==undefined&&a[1]!==''){
        var def=_meterKindDef(a[0]);
        pushItem({type:'meter',kind:a[0],label:def.label,cur:n2(a[1]),prev:'',usage:n2(a[3]),price:n2(a[2]),amount:n2(a[4])});
      }
    });
  }
  window._meterCtx.seq=seq;
  var kindBtns=_M_KINDS.map(function(k){
    return '<button class="btn btn-sm btn-gh" style="font-size:12px" onclick="meterAddRow('+Q+k.k+Q+')">➕ '+k.sym+' '+i18n.t('meter.addMeter',{name:k.label})+'</button>';
  }).join(' ');
  var photoHad=m.photo_url?('<div style="font-size:11px;color:var(--ts);margin-top:4px">📷 '+i18n.t('meter.photoKeep')+'</div>'):'';
  var html='<div class="m-hd"><h3>✏️ '+i18n.t('meter.editTitle')+'</h3><button class="m-x" onclick="closeModal()">×</button></div>'+
    '<div class="m-bd">'+
    '<div style="font-size:11px;color:var(--p);background:var(--bg);padding:8px;border-radius:6px;margin-bottom:10px">'+i18n.t('meter.editHint')+'</div>'+
    '<div class="dr"><div class="dl">'+i18n.t('meter.readingDate')+'</div><div class="dv"><input type="date" class="fc" id="mDate" value="'+(m.reading_date||today())+'"></div></div>'+
    '<div style="background:var(--bg);border-radius:8px;padding:10px;margin:8px 0">'+
      '<div style="font-size:12px;font-weight:700;margin-bottom:8px">📋 '+i18n.t('meter.meterList')+'</div>'+
      '<div style="display:flex;gap:6px;flex-wrap:wrap">'+kindBtns+'</div>'+
      '<div id="meterRows" style="margin-top:10px"></div>'+
    '</div>'+
    '<div style="background:var(--bg);border-radius:8px;padding:10px;margin:8px 0">'+
      '<div style="font-size:12px;font-weight:700;margin-bottom:8px">📦 '+i18n.t('meter.otherFees')+' <button class="btn btn-sm btn-gh" style="font-size:12px;float:right" onclick="meterAddOther()">➕ '+i18n.t('meter.addOther')+'</button></div>'+
      '<div id="meterOtherRows" style="clear:both"></div>'+
    '</div>'+
    '<div class="dr"><div class="dl">'+i18n.t('meter.photo')+'</div><div class="dv"><button class="btn btn-sm btn-gh" onclick="document.getElementById('+Q+'mPhotoInput'+Q+').click()">📷 '+i18n.t('meter.photo')+'</button><input type="file" id="mPhotoInput" accept="image/*" capture="environment" style="display:none" onchange="meterUploadPhoto(this)"><span id="mPhotoStatus" style="margin-left:8px;font-size:11px;color:var(--ts)"></span>'+photoHad+'</div></div>'+
    '<div class="dr"><div class="dl">'+i18n.t('meter.notes')+'</div><div class="dv"><input type="text" class="fc" id="mNotes" placeholder="'+i18n.t('common.notesPh')+'" value="'+esc(m.notes||'')+'"></div></div>'+
    '<div id="meterPreview" style="background:var(--bg);border-radius:8px;padding:10px 12px;margin-top:6px;font-size:12px"></div>'+
    '</div><div class="m-ft"><button class="btn btn-p" id="mSaveBtn" onclick="doMeterUpdate('+Q+id+Q+')">'+i18n.t('common.save')+'</button><button class="btn btn-gh" onclick="closeModal()">'+i18n.t('common.cancel')+'</button></div>';
  openModal(html);
  window._meterPhotoPath=null;
  meterRenderRows();
  meterPreview();
}
async function doMeterUpdate(id){
  if(!canEdit()){toast(i18n.t('common.readOnly'),'w');return}
  var m=(cache.meters||[]).find(function(x){return x.id===id});if(!m)return;
  var ctx=window._meterCtx;if(!ctx){toast(i18n.t('common.opFail'),'e');return}
  var items=(ctx.items||[]).map(function(it){
    if(it.type==='meter'){
      return {type:'meter',kind:it.kind,label:(document.getElementById('mi_label_'+it.id).value||'').trim(),
        cur:_meterNum(document.getElementById('mi_cur_'+it.id).value),
        prev:_meterNum(document.getElementById('mi_prev_'+it.id).value),
        price:_meterNum(document.getElementById('mi_price_'+it.id).value),
        amount:_meterNum(document.getElementById('mi_amt_'+it.id).value)};
    }
    return {type:'other',kind:'other',label:(document.getElementById('mi_label_'+it.id).value||'').trim(),
      amount:_meterNum(document.getElementById('mi_amt_'+it.id).value)};
  });
  var meters=items.filter(function(x){return x.type==='meter'&&x.cur!==null});
  var others=items.filter(function(x){return x.type==='other'&&x.amount!==null&&x.amount>0&&x.label});
  if(!meters.length&&!others.length){toast(i18n.t('meter.needReading'),'e');return}
  var date=document.getElementById('mDate').value||m.reading_date||today();
  var notes=document.getElementById('mNotes').value.trim();
  var btn=document.getElementById('mSaveBtn');btn.disabled=true;btn.textContent=i18n.t('common.saving');
  try{
    var t=cache.tenants.find(function(x){return x.id===m.tenant_id});
    function firstMeter(kind){return meters.find(function(x){return x.kind===kind})||null}
    var cm=firstMeter('cold_water'),hm=firstMeter('hot_water'),em=firstMeter('electricity');
    function usageOf(x){return (x&&x.cur!==null&&x.prev!==null)?Math.max(0,x.cur-x.prev):null}
    var total=0;
    items.forEach(function(x){if(x.amount!==null&&!isNaN(x.amount))total+=x.amount});
    var row={
      tenant_id:m.tenant_id,room_id:m.room_id||(t?t.room_id:null),
      reading_date:date,
      cold_water:cm?cm.cur:null,hot_water:hm?hm.cur:null,electricity:em?em.cur:null,
      cold_water_price:cm?cm.price:null,hot_water_price:hm?hm.price:null,electricity_price:em?em.price:null,
      cold_water_usage:usageOf(cm),hot_water_usage:usageOf(hm),electricity_usage:usageOf(em),
      cold_water_fee:cm?cm.amount:0,hot_water_fee:hm?hm.amount:0,electricity_fee:em?em.amount:0,
      total_fee:total,notes:notes
    };
    if(window._meterPhotoPath)row.photo_url=window._meterPhotoPath;
    var r=await sb.from('meter_readings').update(row).eq('id',id);
    if(r.error){var errMsg=r.error.message||r.error.details||r.error.hint||i18n.t('common.saveFailed');toast(errMsg,'e');btn.disabled=false;btn.textContent=i18n.t('common.save');return}
    await sb.from('meter_items').delete().eq('reading_id',id);
    var subRows=[];var order=0;
    items.forEach(function(x){
      if(x.type==='meter'&&x.cur===null)return;
      subRows.push({owner_id:getOwnerId(),reading_id:id,tenant_id:m.tenant_id,
        kind:x.kind,label:x.label||null,
        cur_reading:x.type==='meter'?x.cur:null,prev_reading:x.type==='meter'?x.prev:null,
        usage:x.type==='meter'?usageOf(x):null,price:x.type==='meter'?x.price:null,
        amount:(x.amount===null||isNaN(x.amount))?0:x.amount,sort_order:order++});
    });
    if(subRows.length){
      var r2=await sb.from('meter_items').insert(subRows).select();
      if(r2.error)toast(i18n.t('meter.detailSaveFailed')+' '+(r2.error.message||''),'e');
    }
    // 已收记录：同步自动入账的水电收入金额
    try{
      if(m.paid&&total>0){
        var ex=await sb.from('income_records').delete().eq('ref_id',id).eq('source','meter');
        await sb.from('income_records').insert({owner_id:getOwnerId(),tenant_id:m.tenant_id||null,room_id:m.room_id||(t?t.room_id:null),amount:total,category:'utility',source:'meter',occur_date:m.paid_date||today(),note:i18n.t('meter.incomeNote',{date:fmtDate(date)}),ref_id:id});
      }
    }catch(e){console.warn('income sync failed:',e)}
    toast(i18n.t('common.updateSuccess'));
    closeModal();
    await loadAllData();
    showTenantDetail(m.tenant_id);
  }catch(e){toast(e.message||i18n.t('common.saveFailed'),'e');btn.disabled=false;btn.textContent=i18n.t('common.save')}
}
// ===== v80 end =====
'''+anchor_edit
repls.append((anchor_edit,edit_fns))

ok=patch(app,repls)
if not ok:
    print('app.html 补丁失败，已中止（文件未写入）')
    sys.exit(1)

# ============ sw.js ============
ok=patch(ROOT+'sw.js',[
 ("var CACHE_NAME='fangdong-v79';","var CACHE_NAME='fangdong-v80';"),
])
if not ok: sys.exit(1)

# ============ app.html 版本号（单独，确保 sw 之后处理） ============
ok=patch(ROOT+'app.html',[
 ('<script src="i18n.js?v=79"></script>','<script src="i18n.js?v=80"></script>'),
])
if not ok: sys.exit(1)

# ============ i18n.js ============
zh_anchor='    "bqr.copyLink": "复制链接",'
zh_new='''    "bqr.copyLink": "复制链接",
    "tenant.needRent": "请填写月租金（大于0），否则无法自动生成账单",
    "tenant.needMoveIn": "请选择入住日期，否则无法自动生成账单",
    "tenant.needContractEnd": "请选择合同到期日期，否则无法自动生成账单",
    "tenant.contractAfterMoveIn": "合同到期日期需晚于入住日期",
    "meter.editTitle": "修改抄表记录",
    "meter.editHint": "可修改读数、单价、金额、日期、备注和照片，保存后自动更新",
    "meter.photoKeep": "已有照片，不重新上传则保留原照片",
    "bill.scanTip": "微信扫码查看本期账单明细与抄表照片",'''
en_anchor='    "bqr.copyLink": "Copy link",'
en_new='''    "bqr.copyLink": "Copy link",
    "tenant.needRent": "Please enter monthly rent (>0), otherwise bills cannot be auto-created",
    "tenant.needMoveIn": "Please select move-in date, otherwise bills cannot be auto-created",
    "tenant.needContractEnd": "Please select contract end date, otherwise bills cannot be auto-created",
    "tenant.contractAfterMoveIn": "Contract end date must be later than move-in date",
    "meter.editTitle": "Edit Meter Reading",
    "meter.editHint": "You can edit readings, price, amount, date, notes and photo. Changes save automatically.",
    "meter.photoKeep": "Photo exists. It is kept unless you upload a new one.",
    "bill.scanTip": "Scan with WeChat to view bill details & meter photos",'''
ok=patch(ROOT+'i18n.js',[
 (zh_anchor,zh_new),
 (en_anchor,en_new),
])
if not ok: sys.exit(1)

print('\n=== v80 补丁全部应用成功 ===')
