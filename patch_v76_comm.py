#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v76 中介员工提成模块 —— 纯增量补丁。只新增、不改现有业务逻辑。"""
import io, sys

APP = "app.html"
src = io.open(APP, encoding="utf-8").read()
orig_len = len(src)

def rep(text, old, new, label):
    c = text.count(old)
    if c != 1:
        print("!! anchor[%s] count=%d (expect 1) -> ABORT" % (label, c)); sys.exit(1)
    print("  +", label)
    return text.replace(old, new, 1)

JS = r"""
// ===== v76: 中介员工提成模块（纯增量，不影响现有逻辑）=====
var commState={tab:'report',month:'',staff:'__all__',settled:'__all__'};
function _commOn(){return !!(cache&&cache.settings&&cache.settings.commission_enabled)}
async function _commLoadAll(){
  var oid=getOwnerId();var out={staff:[],cfg:[],rec:[]};
  try{var rs=await sb.from('staff').select('*').eq('owner_id',oid).order('created_at',{ascending:true});if(rs&&!rs.error)out.staff=rs.data||[]}catch(e){}
  try{var rc=await sb.from('tenant_commission').select('*').eq('owner_id',oid);if(rc&&!rc.error)out.cfg=rc.data||[]}catch(e){}
  try{var rr=await sb.from('commission_records').select('*').eq('owner_id',oid);if(rr&&!rr.error)out.rec=rr.data||[]}catch(e){}
  return out;
}
function _commMonthRange(t){
  var start=(t.move_in_date||'').slice(0,7);
  if(!start)return null;
  var end;
  if(t.status==='inactive'){end=(t.move_out_date||t.contract_end||'').slice(0,7)||null}
  else{end=(t.contract_end||'').slice(0,7)||null}
  var nowM=today().slice(0,7);
  if(!end||end>nowM)end=nowM;
  if(start>end)return null;
  var months=[];var y=parseInt(start.slice(0,4),10),m=parseInt(start.slice(5,7),10);
  var ey=parseInt(end.slice(0,4),10),em=parseInt(end.slice(5,7),10),guard=0;
  while((y<ey||(y===ey&&m<=em))&&guard<600){months.push(y+'-'+(m<10?'0'+m:''+m));m++;if(m>12){m=1;y++}guard++}
  return months;
}
function _commCalc(base,cfg){
  base=base||0;
  if(cfg.rate_type==='fixed')return Math.round((cfg.rate||0)*100)/100;
  return Math.round(base*(cfg.rate||0)/100*100)/100;
}
async function commGenerate(){
  if(!_commOn())return 0;
  var oid=getOwnerId();var d=await _commLoadAll();
  var staff=d.staff,cfg=d.cfg,rec=d.rec;
  var exist={};
  rec.forEach(function(r){exist[r.tenant_id+'|'+(r.month||'')+'|'+r.mode]=true});
  var toAdd=[];
  for(var i=0;i<cfg.length;i++){
    var c=cfg[i];
    if(!c.staff_id)continue;
    var t=cache.tenants.find(function(x){return x.id===c.tenant_id});
    if(!t)continue;
    var rent=t.rent_amount||0;
    if(c.mode==='onetime'){
      var om=(t.move_in_date||today()).slice(0,7);var key=t.id+'|'+om+'|onetime';
      if(!exist[key]){toAdd.push({owner_id:oid,staff_id:c.staff_id,tenant_id:t.id,month:om,amount:_commCalc(rent,c),base_amount:rent,mode:'onetime',basis:c.basis||'effective',settled:false,note:i18n.t('comm.oneTimeNote')});exist[key]=true}
    }else if(c.basis==='received'){
      cache.rents.filter(function(r){return r.tenant_id===t.id&&r.status==='paid'&&r.pay_date}).forEach(function(r){
        var pm=String(r.pay_date).slice(0,7);var key=t.id+'|'+pm+'|monthly';
        if(!exist[key]){toAdd.push({owner_id:oid,staff_id:c.staff_id,tenant_id:t.id,month:pm,amount:_commCalc(r.amount,c),base_amount:r.amount||0,mode:'monthly',basis:'received',settled:false,note:i18n.t('comm.recvNote')});exist[key]=true}
      });
    }else{
      var months=_commMonthRange(t);
      if(months)months.forEach(function(mo){var key=t.id+'|'+mo+'|monthly';
        if(!exist[key]){toAdd.push({owner_id:oid,staff_id:c.staff_id,tenant_id:t.id,month:mo,amount:_commCalc(rent,c),base_amount:rent,mode:'monthly',basis:'effective',settled:false,note:i18n.t('comm.effNote')});exist[key]=true}
      });
    }
  }
  if(toAdd.length){for(var k=0;k<toAdd.length;k+=100){try{await sb.from('commission_records').insert(toAdd.slice(k,k+100))}catch(e){}}}
  return toAdd.length;
}
async function rCommission(){
  var mc=document.getElementById('mainContent');
  if(mc)mc.innerHTML='<div class="page-hd"><h2>'+i18n.t('comm.title')+'</h2></div><div class="empty"><div class="ei">💼</div><p>'+i18n.t('common.loading')+'</p></div>';
  var d=await _commLoadAll();
  if(_commOn()){try{await commGenerate();d=await _commLoadAll()}catch(e){}}
  cache.staff=d.staff;cache.tcomm=d.cfg;cache.commissions=d.rec;
  var staff=d.staff,rec=d.rec;
  var months={};rec.forEach(function(r){if(r.month)months[r.month]=1});
  var mList=Object.keys(months).sort().reverse();
  var nowM=today().slice(0,7);
  if(!commState.month)commState.month=mList.indexOf(nowM)>=0?nowM:(mList[0]||nowM);
  var tabs='<div style="display:flex;gap:8px;margin-bottom:14px">'+
    '<button class="btn btn-sm '+(commState.tab==='report'?'btn-p':'btn-gh')+'" onclick="commTab(\'report\')">📊 '+i18n.t('comm.reportTab')+'</button>'+
    '<button class="btn btn-sm '+(commState.tab==='staff'?'btn-p':'btn-gh')+'" onclick="commTab(\'staff\')">👥 '+i18n.t('comm.staffTab')+'</button></div>';
  var body;
  if(commState.tab==='staff'){body=_commStaffHtml(staff)}
  else{
    var monthOpts=mList.map(function(m){return'<option value="'+m+'"'+(commState.month===m?' selected':'')+'>'+m+'</option>'}).join('');
    if(mList.indexOf(commState.month)<0)monthOpts='<option value="'+commState.month+'" selected>'+commState.month+'</option>'+monthOpts;
    var staffOpts='<option value="__all__"'+(commState.staff==='__all__'?' selected':'')+'>'+i18n.t('common.all')+'</option>'+staff.map(function(s){return'<option value="'+s.id+'"'+(commState.staff===s.id?' selected':'')+'>'+esc(s.name)+'</option>'}).join('');
    var setOpts='<option value="__all__"'+(commState.settled==='__all__'?' selected':'')+'>'+i18n.t('comm.allStatus')+'</option><option value="unsettled"'+(commState.settled==='unsettled'?' selected':'')+'>'+i18n.t('comm.unsettled')+'</option><option value="settled"'+(commState.settled==='settled'?' selected':'')+'>'+i18n.t('comm.settled')+'</option>';
    var cur=rec.filter(function(r){return r.month===commState.month});
    if(commState.staff!=='__all__')cur=cur.filter(function(r){return r.staff_id===commState.staff});
    if(commState.settled==='settled')cur=cur.filter(function(r){return r.settled});
    if(commState.settled==='unsettled')cur=cur.filter(function(r){return!r.settled});
    var tot=cur.reduce(function(a,r){return a+(r.amount||0)},0);
    var setTot=cur.filter(function(r){return r.settled}).reduce(function(a,r){return a+(r.amount||0)},0);
    var unsetTot=cur.filter(function(r){return!r.settled}).reduce(function(a,r){return a+(r.amount||0)},0);
    var smap={};
    cur.forEach(function(r){var sid=r.staff_id||'__none__';if(!smap[sid])smap[sid]={name:(r.staff_id?((staff.find(function(s){return s.id===r.staff_id})||{name:i18n.t('comm.staffGone')}).name):i18n.t('comm.noStaff')),total:0,settled:0,unsettled:0,cnt:0};smap[sid].total+=r.amount||0;smap[sid].cnt++;if(r.settled)smap[sid].settled+=r.amount||0;else smap[sid].unsettled+=r.amount||0});
    var sumRows=Object.keys(smap).map(function(sid){var s=smap[sid];return'<tr><td style="font-weight:600">'+esc(s.name)+'</td><td>'+s.cnt+'</td><td style="font-weight:700">¥'+s.total.toLocaleString()+'</td><td style="color:var(--g)">¥'+s.settled.toLocaleString()+'</td><td style="color:var(--w)">¥'+s.unsettled.toLocaleString()+'</td></tr>'}).join('');
    var sumTbl=Object.keys(smap).length?'<div class="tbl-wrap"><table><thead><tr><th>'+i18n.t('comm.staffName')+'</th><th>'+i18n.t('comm.recCount')+'</th><th>'+i18n.t('comm.monthTotal')+'</th><th>'+i18n.t('comm.settled')+'</th><th>'+i18n.t('comm.unsettled')+'</th></tr></thead><tbody>'+sumRows+'</tbody></table></div>':'<p style="font-size:12px;color:var(--ts);padding:8px 4px">'+i18n.t('comm.noDataMonth')+'</p>';
    var detRows=cur.slice().sort(function(a,b){var sa=a.staff_id||'',sb2=b.staff_id||'';if(sa!==sb2)return sa<sb2?-1:1;return (a.tenant_id||'')<(b.tenant_id||'')?-1:1;}).map(function(r){
      var s=r.staff_id?staff.find(function(x){return x.id===r.staff_id}):null;
      var t=cache.tenants.find(function(x){return x.id===r.tenant_id});
      return'<tr><td style="font-weight:600">'+esc(s?s.name:i18n.t('comm.staffGone'))+'</td><td>'+esc(t?t.name:'-')+'</td><td>'+_commModeText(r)+'</td><td>¥'+(r.base_amount||0).toLocaleString()+'</td><td style="font-weight:700">¥'+(r.amount||0).toLocaleString()+'</td><td>'+(r.settled?'<span class="tag t-green">'+i18n.t('comm.settled')+'</span>':'<span class="tag t-yellow">'+i18n.t('comm.unsettled')+'</span>')+'</td><td style="white-space:nowrap">'+(canEdit()?('<button class="btn btn-sm btn-gh" onclick="commToggleSettle(\''+r.id+'\')">'+(r.settled?i18n.t('comm.markUnsettled'):i18n.t('comm.markSettled'))+'</button> <button class="btn btn-sm btn-gh" style="color:var(--d)" onclick="commDelRec(\''+r.id+'\')">'+i18n.t('common.del')+'</button>'):'-')+'</td></tr>';
    }).join('');
    var detTbl=cur.length?'<div class="tbl-wrap"><table><thead><tr><th>'+i18n.t('comm.staffName')+'</th><th>'+i18n.t('set.tenants')+'</th><th>'+i18n.t('comm.rule')+'</th><th>'+i18n.t('comm.base')+'</th><th>'+i18n.t('comm.amount')+'</th><th>'+i18n.t('common.status')+'</th><th>'+i18n.t('common.operation')+'</th></tr></thead><tbody>'+detRows+'</tbody></table></div>':'<div class="empty"><div class="ei">💼</div><h3>'+i18n.t('comm.noDataMonth')+'</h3><p>'+i18n.t('comm.noDataHint')+'</p></div>';
    body='<div class="card"><div class="toolbar">'+
      '<select class="fsel" onchange="commState.month=this.value;rCommission()">'+monthOpts+'</select>'+
      '<select class="fsel" onchange="commState.staff=this.value;rCommission()">'+staffOpts+'</select>'+
      '<select class="fsel" onchange="commState.settled=this.value;rCommission()">'+setOpts+'</select>'+
      '<span style="flex:1"></span>'+
      (canEdit()?'<button class="btn btn-sm btn-g" onclick="commSettleAll(\''+commState.month+'\')">'+i18n.t('comm.settleAll')+'</button>':'')+
      '<button class="btn btn-sm btn-o" onclick="commExport()">'+i18n.t('comm.export')+'</button></div></div>'+
      '<div class="stats"><div class="sc"><div class="sc-i blue">📊</div><div><h3>'+cur.length+'</h3><p>'+i18n.t('comm.recCount')+'</p></div></div>'+
      '<div class="sc"><div class="sc-i yellow">💵</div><div><h3>¥'+tot.toLocaleString()+'</h3><p>'+i18n.t('comm.monthTotal')+'</p></div></div>'+
      '<div class="sc"><div class="sc-i green">✅</div><div><h3>¥'+setTot.toLocaleString()+'</h3><p>'+i18n.t('comm.settled')+'</p></div></div>'+
      '<div class="sc"><div class="sc-i red">⏳</div><div><h3>¥'+unsetTot.toLocaleString()+'</h3><p>'+i18n.t('comm.unsettled')+'</p></div></div></div>'+
      '<div class="card"><div class="card-hd"><h3>'+i18n.t('comm.staffSummary')+'</h3></div><div style="padding:12px 14px">'+sumTbl+'</div></div>'+
      '<div class="card"><div class="card-hd"><h3>'+i18n.t('comm.detail')+'</h3></div>'+detTbl+'</div>';
  }
  document.getElementById('mainContent').innerHTML='<div class="page-hd"><h2>'+i18n.t('comm.title')+'</h2></div><div class="card" style="padding:12px 16px;margin-bottom:16px"><span style="font-size:13px">💡 '+i18n.t('comm.hint')+'</span></div>'+tabs+body;
}
function _commModeText(r){
  var mt=r.mode==='onetime'?i18n.t('comm.modeOnetime'):i18n.t('comm.modeMonthly');
  var bt=r.basis==='received'?i18n.t('comm.basisReceived'):i18n.t('comm.basisEffective');
  if(r.mode==='onetime')return mt;
  return mt+'·'+bt;
}
function commTab(t){commState.tab=t;rCommission()}
function _commStaffHtml(staff){
  var rows=staff.map(function(s){
    return'<tr><td style="font-weight:600">'+esc(s.name)+'</td><td>'+esc(s.phone||'-')+'</td><td>'+(s.active?'<span class="tag t-green">'+i18n.t('comm.staffActive')+'</span>':'<span class="tag t-gray">'+i18n.t('comm.staffInactive')+'</span>')+'</td><td style="white-space:nowrap">'+(canEdit()?('<button class="btn btn-sm btn-gh" onclick="commStaffEdit(\''+s.id+'\')">'+i18n.t('common.edit')+'</button> '+(s.active?'<button class="btn btn-sm btn-gh" style="color:var(--w)" onclick="commStaffToggle(\''+s.id+'\',false)">'+i18n.t('comm.staffDeactivate')+'</button>':'<button class="btn btn-sm btn-gh" style="color:var(--g)" onclick="commStaffToggle(\''+s.id+'\',true)">'+i18n.t('comm.staffActivate')+'</button>')+' <button class="btn btn-sm btn-gh" style="color:var(--d)" onclick="commStaffDel(\''+s.id+'\')">'+i18n.t('common.del')+'</button>'):'-')+'</td></tr>';
  }).join('');
  var tbl=staff.length?'<div class="tbl-wrap"><table><thead><tr><th>'+i18n.t('comm.staffName')+'</th><th>'+i18n.t('common.phone')+'</th><th>'+i18n.t('common.status')+'</th><th>'+i18n.t('common.operation')+'</th></tr></thead><tbody>'+rows+'</tbody></table></div>':'<div class="empty"><div class="ei">👥</div><h3>'+i18n.t('comm.noStaff')+'</h3><p>'+i18n.t('comm.noStaffHint')+'</p></div>';
  return'<div class="card"><div class="card-hd"><h3>'+i18n.t('comm.staffList')+'</h3>'+(canEdit()?'<button class="btn btn-sm btn-p" onclick="commStaffEdit(null)">'+i18n.t('comm.addStaff')+'</button>':'')+'</div>'+tbl+'</div>';
}
function commStaffEdit(id){
  var s=id?(cache.staff||[]).find(function(x){return x.id===id}):null;
  window._commStaffEdit=id||null;
  openModal('<div class="m-hd"><h3>'+(s?i18n.t('comm.editStaff'):i18n.t('comm.addStaff'))+'</h3><button class="m-x" onclick="closeModal()">×</button></div>'+
    '<div class="m-bd"><div class="fg"><label>'+i18n.t('comm.staffName')+'<span class="req">*</span></label><input class="fc" id="fCSName" value="'+esc(s?s.name:'')+'" placeholder="'+i18n.t('comm.staffNamePh')+'"></div>'+
    '<div class="fg"><label>'+i18n.t('common.phone')+'</label><input class="fc" id="fCSPhone" value="'+esc(s?s.phone||'':'')+'" type="tel"></div>'+
    '<div class="fg"><label>'+i18n.t('common.notes')+'</label><textarea class="fc" id="fCSNote">'+esc(s?s.note||'':'')+'</textarea></div>'+
    (s?'<div class="s-item"><div><h4>'+i18n.t('comm.staffActive')+'</h4></div><button class="tgl'+(s.active?' on':'')+'" id="fCSActive" onclick="this.classList.toggle(\'on\')"></button></div>':'')+
    '</div><div class="m-ft"><button class="btn btn-gh" onclick="closeModal()">'+i18n.t('common.cancel')+'</button><button class="btn btn-p" onclick="commStaffSave()">'+i18n.t('common.save')+'</button></div>');
}
async function commStaffSave(){
  var nameEl=document.getElementById('fCSName');var name=nameEl?nameEl.value.trim():'';
  if(!name){toast(i18n.t('comm.enterStaffName'),'e');return}
  var id=window._commStaffEdit;
  var payload={name:name,phone:(document.getElementById('fCSPhone').value||'').trim()||null,note:(document.getElementById('fCSNote').value||'').trim()||null};
  var tgl=document.getElementById('fCSActive');
  if(tgl)payload.active=tgl.classList.contains('on');
  var r;
  if(id){r=await sb.from('staff').update(payload).eq('id',id)}
  else{payload.owner_id=getOwnerId();payload.active=true;r=await sb.from('staff').insert(payload)}
  if(r.error){toast(r.error.message,'e');return}
  closeModal();toast(i18n.t('common.updateSuccess'));rCommission();
}
function commStaffToggle(id,active){
  sb.from('staff').update({active:active}).eq('id',id).then(function(r){if(r&&r.error){toast(r.error.message,'e');return}toast(i18n.t('common.updateSuccess'));rCommission()});
}
function commStaffDel(id){
  confirmDialog(i18n.t('comm.delStaffConfirm'),i18n.t('comm.delStaffSub'),async function(){
    var r=await sb.from('staff').delete().eq('id',id);
    if(r.error){toast(r.error.message,'e');return}
    toast(i18n.t('common.deleted'));rCommission();
  });
}
function _commStaffOptions(sel){
  var list=(cache.staff||[]).filter(function(s){return s.active});
  return'<option value="">'+i18n.t('comm.selectStaff')+'</option>'+list.map(function(s){return'<option value="'+s.id+'"'+(s.id===sel?' selected':'')+'>'+esc(s.name)+(s.phone?' ('+esc(s.phone)+')':'')+'</option>'}).join('');
}
function _commSectionHtml(cfg){
  if(!_commOn())return'';
  cfg=cfg||{};
  return'<div class="file-section" style="border-top:1px dashed var(--bd);margin-top:12px;padding-top:12px"><h4>💼 '+i18n.t('comm.leaseTitle')+'</h4>'+
    '<div class="fr"><div class="fg"><label>'+i18n.t('comm.dealStaff')+'</label><select class="fc" id="fCStaff">'+_commStaffOptions(cfg.staff_id)+'</select></div>'+
    '<div class="fg"><label>'+i18n.t('comm.mode')+'</label><select class="fc" id="fCMode" onchange="_commFieldChg()"><option value="monthly"'+(cfg.mode!=='onetime'?' selected':'')+'>'+i18n.t('comm.modeMonthly')+'</option><option value="onetime"'+(cfg.mode==='onetime'?' selected':'')+'>'+i18n.t('comm.modeOnetime')+'</option></select></div></div>'+
    '<div class="fr"><div class="fg" id="fCBasisFg"><label>'+i18n.t('comm.basis')+'</label><select class="fc" id="fCBasis" onchange="_commFieldChg()"><option value="effective"'+(cfg.basis!=='received'?' selected':'')+'>'+i18n.t('comm.basisEffective')+'</option><option value="received"'+(cfg.basis==='received'?' selected':'')+'>'+i18n.t('comm.basisReceived')+'</option></select></div>'+
    '<div class="fg"><label>'+i18n.t('comm.rateType')+'</label><select class="fc" id="fCRateType" onchange="_commFieldChg()"><option value="percent"'+(cfg.rate_type!=='fixed'?' selected':'')+'>'+i18n.t('comm.ratePercent')+'</option><option value="fixed"'+(cfg.rate_type==='fixed'?' selected':'')+'>'+i18n.t('comm.rateFixed')+'</option></select></div></div>'+
    '<div class="fg"><label id="fCRateLabel">'+i18n.t('comm.ratePercentLabel')+'</label><input class="fc" id="fCRate" type="number" step="0.01" min="0" value="'+(cfg.rate!=null?cfg.rate:'')+'" placeholder="'+i18n.t('comm.ratePh')+'"></div>'+
    '<p class="file-hint" id="fCHint">'+i18n.t('comm.hintMonthlyEff')+'</p></div>';
}
function _commFieldChg(){
  var modeEl=document.getElementById('fCMode');if(!modeEl)return;
  var basisFg=document.getElementById('fCBasisFg');
  var rtEl=document.getElementById('fCRateType');
  var lab=document.getElementById('fCRateLabel');
  var hint=document.getElementById('fCHint');
  var isOne=modeEl.value==='onetime';
  if(basisFg)basisFg.style.display=isOne?'none':'';
  var isPct=rtEl&&rtEl.value==='percent';
  if(lab)lab.textContent=isPct?i18n.t('comm.ratePercentLabel'):i18n.t('comm.rateFixedLabel');
  if(hint){
    if(isOne)hint.textContent=i18n.t('comm.hintOnetime');
    else{var bEl=document.getElementById('fCBasis');hint.textContent=(bEl&&bEl.value==='received')?i18n.t('comm.hintMonthlyRecv'):i18n.t('comm.hintMonthlyEff')}
  }
}
function _commInitForm(tenantId){
  if(!_commOn())return;
  var sel=document.getElementById('fCStaff');if(!sel)return;
  var cfg=tenantId?(cache.tcomm||[]).find(function(c){return c.tenant_id===tenantId}):null;
  function fill(){
    if(cfg){
      if(document.getElementById('fCMode'))document.getElementById('fCMode').value=cfg.mode==='onetime'?'onetime':'monthly';
      if(document.getElementById('fCBasis'))document.getElementById('fCBasis').value=cfg.basis==='received'?'received':'effective';
      if(document.getElementById('fCRateType'))document.getElementById('fCRateType').value=cfg.rate_type==='fixed'?'fixed':'percent';
      if(document.getElementById('fCRate'))document.getElementById('fCRate').value=cfg.rate!=null?cfg.rate:'';
    }
    _commFieldChg();
  }
  if((cache.staff||[]).length){fill();return}
  _commLoadAll().then(function(d){
    cache.staff=d.staff;cache.tcomm=d.cfg;
    var se=document.getElementById('fCStaff');
    if(se){var cur=cfg?cfg.staff_id:'';se.innerHTML=_commStaffOptions(cur)}
    fill();
  });
}
async function _commSaveForTenant(tenantId){
  try{
    if(!_commOn()||!tenantId)return;
    var staffEl=document.getElementById('fCStaff');if(!staffEl)return;
    var staffId=staffEl.value||null;
    if(!staffId){try{await sb.from('tenant_commission').delete().eq('tenant_id',tenantId)}catch(e){}return}
    var modeEl=document.getElementById('fCMode'),basisEl=document.getElementById('fCBasis'),rtEl=document.getElementById('fCRateType'),rateEl=document.getElementById('fCRate');
    var mode=modeEl?modeEl.value:'monthly';
    var payload={owner_id:getOwnerId(),tenant_id:tenantId,staff_id:staffId,mode:mode,basis:mode==='onetime'?'effective':(basisEl?basisEl.value:'effective'),rate_type:rtEl?rtEl.value:'percent',rate:parseFloat(rateEl?rateEl.value:'0')||0,updated_at:new Date().toISOString()};
    var r=await sb.from('tenant_commission').upsert(payload,{onConflict:'tenant_id'}).select();
    if(r.error)console.warn('commission save:',r.error.message);
  }catch(e){console.warn('commission save failed:',e)}
}
async function commToggleSettle(id){
  var rec=(cache.commissions||[]).find(function(r){return r.id===id});
  if(!rec)return;
  var nv=!rec.settled;
  var r=await sb.from('commission_records').update({settled:nv,settled_at:nv?new Date().toISOString():null}).eq('id',id);
  if(r.error){toast(r.error.message,'e');return}
  toast(nv?i18n.t('comm.settledDone'):i18n.t('comm.unsettledDone'));
  rec.settled=nv;rCommission();
}
function commSettleAll(month){
  var ids=(cache.commissions||[]).filter(function(r){return r.month===month&&!r.settled}).map(function(r){return r.id});
  if(!ids.length){toast(i18n.t('comm.noUnsettled'),'w');return}
  confirmDialog(i18n.t('comm.settleAllConfirm',{n:ids.length,m:month}),i18n.t('comm.settleAllSub'),async function(){
    var r=await sb.from('commission_records').update({settled:true,settled_at:new Date().toISOString()}).in_('id',ids);
    if(r.error){toast(r.error.message,'e');return}
    toast(i18n.t('comm.settledDone'));rCommission();
  });
}
function commDelRec(id){
  confirmDialog(i18n.t('comm.delRecConfirm'),'',async function(){
    var r=await sb.from('commission_records').delete().eq('id',id);
    if(r.error){toast(r.error.message,'e');return}
    toast(i18n.t('common.deleted'));rCommission();
  });
}
function commExport(){
  var rec=(cache.commissions||[]).filter(function(r){return r.month===commState.month});
  if(commState.staff!=='__all__')rec=rec.filter(function(r){return r.staff_id===commState.staff});
  if(commState.settled==='settled')rec=rec.filter(function(r){return r.settled});
  if(commState.settled==='unsettled')rec=rec.filter(function(r){return!r.settled});
  if(!rec.length){toast(i18n.t('comm.noDataMonth'),'w');return}
  var staff=cache.staff||[];
  var rows=rec.map(function(r){
    var s=r.staff_id?staff.find(function(x){return x.id===r.staff_id}):null;
    var t=cache.tenants.find(function(x){return x.id===r.tenant_id});
    return{'提成月份':r.month,'员工姓名':s?s.name:i18n.t('comm.staffGone'),'员工电话':s?(s.phone||''):'','租户姓名':t?t.name:'-','提成方式':_commModeText(r),'计提基数':r.base_amount||0,'提成金额':r.amount||0,'结算状态':r.settled?i18n.t('comm.settled'):i18n.t('comm.unsettled'),'备注':r.note||''};
  });
  var ws=XLSX.utils.json_to_sheet(rows);
  var wb=XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb,ws,i18n.t('comm.detail'));
  XLSX.writeFile(wb,i18n.t('comm.exportFileName',{m:commState.month})+'.xlsx');
  toast(i18n.t('set.excelExported'));
}
async function tglCommission(){
  var cur=!!(cache.settings&&cache.settings.commission_enabled);
  var nv=!cur;
  var r=await sb.from('workspace_settings').upsert({owner_id:getOwnerId(),commission_enabled:nv},{onConflict:'owner_id'});
  if(r.error){toast(r.error.message,'e');return}
  cache.settings.commission_enabled=nv;
  var tg=document.getElementById('tglCommission');
  if(tg)tg.classList.toggle('on',nv);
  toast(nv?i18n.t('comm.enabled'):i18n.t('comm.disabled'));
  _commNavSync();
  if(nv)setTimeout(function(){goPage('commission')},300);
}
function _commNavSync(){
  var el=document.querySelector('.nav-item[data-p="commission"]');
  if(el)el.style.display=_commOn()?'flex':'none';
}
// ===== /v76 提成模块 =====
"""

# 1) JS 模块插在 rFeedback 前
src = rep(src, "function rFeedback(){", JS + "\nfunction rFeedback(){", "JS module before rFeedback")

# 2) 路由表
src = rep(src,
  "var fn={dashboard:rDashboard,rooms:rRooms,tenants:rTenants,rent:rRent,finance:rFinance,settings:rSettings,feedback:rFeedback};",
  "var fn={dashboard:rDashboard,rooms:rRooms,tenants:rTenants,rent:rRent,finance:rFinance,commission:rCommission,settings:rSettings,feedback:rFeedback};",
  "renderPage route map")

# 3) 侧边栏导航
old_nav = """<div class="nav-item" data-p="finance" onclick="goPage(\\'finance\\')"><span class="ico">🧾</span>'+i18n.t('common.financeMgmt')+'<span class="badge" id="bAdj" style="display:none">0</span></div>"""
new_nav = old_nav + """<div class="nav-item" data-p="commission" onclick="goPage(\\'commission\\')" style="display:none"><span class="ico">💼</span>'+i18n.t('comm.title')+'</div>"""
src = rep(src, old_nav, new_nav, "sidebar nav item")

# 4) renderApp 末尾导航同步
src = rep(src,
  'if(isAdmin()){document.getElementById("navFeedback").style.display=""}renderPage();updateBadges()}',
  'if(isAdmin()){document.getElementById("navFeedback").style.display=""}try{_commNavSync()}catch(e){}renderPage();updateBadges()}',
  "renderApp nav sync")

# 5) 新增租客弹窗：notes 后插提成区块
old_add_notes = """<div class="fg"><label>'+i18n.t('common.notes')+'</label><textarea class="fc" id="fTNo" placeholder="'+i18n.t('common.notesPh')+'"></textarea></div><div class="occ-section">"""
new_add_notes = """<div class="fg"><label>'+i18n.t('common.notes')+'</label><textarea class="fc" id="fTNo" placeholder="'+i18n.t('common.notesPh')+'"></textarea></div>'+_commSectionHtml(null)+'<div class="occ-section">"""
src = rep(src, old_add_notes, new_add_notes, "add-tenant section")

# 6) 新增租客弹窗初始化
src = rep(src,
  "');renderOccForm()}",
  "');renderOccForm();_commInitForm(null)}",
  "add-tenant init")

# 7) 编辑租客弹窗：notes 后插提成区块
old_ed_notes = """<div class="fg"><label>'+i18n.t('common.notes')+'</label><textarea class="fc" id="fTNo"'+(isEdit?'':' readonly')+'>'+esc(t.notes||'')+'</textarea></div><div class="occ-section">"""
new_ed_notes = """<div class="fg"><label>'+i18n.t('common.notes')+'</label><textarea class="fc" id="fTNo"'+(isEdit?'':' readonly')+'>'+esc(t.notes||'')+'</textarea></div>'+_commSectionHtml((cache.tcomm||[]).find(function(c){return c.tenant_id===id}))+'<div class="occ-section">"""
src = rep(src, old_ed_notes, new_ed_notes, "edit-tenant section")

# 8) 编辑租客弹窗初始化
src = rep(src,
  "renderOccForm();var _idEl=document.getElementById('fTID');",
  "renderOccForm();_commInitForm(id);var _idEl=document.getElementById('fTID');",
  "edit-tenant init")

# 9) doAddTenant 保存提成
src = rep(src,
  "closeModal();toast(billCount>0?''+i18n.t('tenant.registerSuccess')+'，'+i18n.t('wl.autoGenerated')+''+billCount+''+i18n.t('rent.rentBillCount')+'':''+i18n.t('tenant.registerSuccess')+'');await loadAllData();renderPage()",
  "try{var _ctid=(r.data&&r.data[0])?r.data[0].id:(typeof tid!=='undefined'?tid:null);if(_ctid)await _commSaveForTenant(_ctid)}catch(e){}closeModal();toast(billCount>0?''+i18n.t('tenant.registerSuccess')+'，'+i18n.t('wl.autoGenerated')+''+billCount+''+i18n.t('rent.rentBillCount')+'':''+i18n.t('tenant.registerSuccess')+'');await loadAllData();renderPage();try{_commNavSync()}catch(e){}",
  "doAddTenant commission save")

# 10) doEditTenant 保存提成
src = rep(src,
  "closeModal();toast(i18n.t('common.updateSuccess'));await loadAllData();renderPage()}catch(e){toast(''+i18n.t('common.opFail')",
  "try{await _commSaveForTenant(id)}catch(e){}closeModal();toast(i18n.t('common.updateSuccess'));await loadAllData();renderPage()}catch(e){toast(''+i18n.t('common.opFail')",
  "doEditTenant commission save")

# 11) 设置页开关卡片（插在 accountInfo 卡片前）
old_set = """<div class="card"><div class="card-hd"><h3>'+i18n.t('common.accountInfo')+'</h3></div>"""
new_set = """<div class="card"><div class="card-hd"><h3>💠 '+i18n.t('comm.title')+'</h3></div><div style="padding:14px"><div class="s-item"><div><h4>'+i18n.t('comm.enableModule')+'</h4><p>'+i18n.t('comm.settingDesc')+'</p></div><button class="tgl'+(s.commission_enabled?' on':'')+'" id="tglCommission" onclick="tglCommission()"></button></div></div></div><div class="card"><div class="card-hd"><h3>'+i18n.t('common.accountInfo')+'</h3></div>"""
src = rep(src, old_set, new_set, "settings toggle card")

io.open(APP, "w", encoding="utf-8").write(src)
print("OK app.html %d -> %d bytes" % (orig_len, len(src)))
