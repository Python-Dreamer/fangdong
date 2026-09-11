# -*- coding: utf-8 -*-
# 需求1+2：记账本 图表分析 / 导出筛选数据 / 流水详情(编辑删除+关联账单)
# 全部为新增独立函数；rFinanceBook 只做两处"插入"，不改原逻辑
import io
s=io.open('app.html',encoding='utf-8').read()

# ---------- 1) 新增函数：注入到 rFinanceBook 之前 ----------
anchor='function rFinanceBook(){'
assert s.count(anchor)==1

new_funcs = r'''// ===== v75: 记账本图表分析 / 筛选导出 / 流水详情（增量，不改原逻辑）=====
function _finFiltered(){
  var entries=_ledgerEntries();
  if(finBldg!=='__all__')entries=entries.filter(function(e){return e.bid===finBldg});
  entries=entries.filter(function(e){return (e.date||'').slice(0,4)===finYear});
  if(finMonth!=='all')entries=entries.filter(function(e){return (e.date||'').slice(0,7)===finMonth});
  if(finFilter!=='all')entries=entries.filter(function(e){return e.type===finFilter});
  return entries;
}
function _finBarChart(entries){
  var months=[];
  for(var mi=1;mi<=12;mi++){
    var ym=finYear+'-'+(mi<10?'0'+mi:''+mi);
    var d={ym:ym,label:mi,in:0,out:0};
    entries.forEach(function(e){if((e.date||'').slice(0,7)===ym){if(e.type==='in')d.in+=e.amount;else d.out+=e.amount}});
    months.push(d);
  }
  if(finMonth!=='all')months=months.filter(function(d){return d.ym===finMonth});
  var has=months.some(function(d){return d.in>0||d.out>0});
  if(!has)return '<div class="card" style="padding:20px;text-align:center;color:var(--ts);font-size:13px">'+i18n.t('fin.chartNoData')+'</div>';
  var maxV=1;months.forEach(function(d){maxV=Math.max(maxV,d.in,d.out)});
  var W=320,H=170,pad=24,bw=11,gap=(W-pad*2-12*bw)/11;
  var bars='';
  months.forEach(function(d,i){
    var x=pad+i*(bw+gap);
    var hi=Math.round(d.in/maxV*(H-pad*2));var ho=Math.round(d.out/maxV*(H-pad*2));
    var ly=H-pad-hi;var oy=H-pad-ho;
    var lbl=i18n.getLang&&i18n.getLang()==='en'?(parseInt(d.label,10)):(d.label);
    bars+='<rect x="'+x+'" y="'+ly+'" width="'+bw+'" height="'+hi+'" rx="2" fill="#16a34a"><title>'+d.label+i18n.t('common.monthUnit')+' '+i18n.t('fin.shortIncome')+' ¥'+d.in.toLocaleString()+'</title></rect>';
    bars+='<rect x="'+(x+bw+1)+'" y="'+oy+'" width="'+bw+'" height="'+ho+'" rx="2" fill="#dc2626"><title>'+d.label+i18n.t('common.monthUnit')+' '+i18n.t('fin.shortExpense')+' ¥'+d.out.toLocaleString()+'</title></rect>';
    bars+='<text x="'+(x+bw)+'" y="'+(H-8)+'" font-size="9" fill="var(--ts)" text-anchor="middle">'+lbl+'</text>';
  });
  var tIn=entries.filter(function(e){return e.type==='in'}).reduce(function(a,e){return a+e.amount},0);
  var tOut=entries.filter(function(e){return e.type==='out'}).reduce(function(a,e){return a+e.amount},0);
  return '<div class="card" style="padding:12px 14px;margin-bottom:12px"><div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px">'+
    '<b style="font-size:14px">📊 '+i18n.t('fin.chartTitle')+'</b>'+
    '<span style="font-size:12px;color:var(--g,#16a34a)">■ '+i18n.t('fin.shortIncome')+' ¥'+tIn.toLocaleString()+'</span>'+
    '<span style="font-size:12px;color:var(--d,#dc2626)">■ '+i18n.t('fin.shortExpense')+' ¥'+tOut.toLocaleString()+'</span>'+
    '<span style="font-size:12px;font-weight:700;color:'+(tIn-tOut>=0?'#4F46E5':'var(--d,#dc2626)')+'">'+i18n.t('fin.shortBalance')+' ¥'+(tIn-tOut).toLocaleString()+'</span></div>'+
    '<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;max-width:560px;display:block;margin:0 auto">'+bars+'</svg></div>';
}
function exportLedgerFiltered(){
  var entries=_finFiltered();
  if(!entries.length){toast(i18n.t('fin.noLedgerData'),'w');return}
  var rows=entries.map(function(e){
    var _o={};
    _o[i18n.t('fin.expenseDate')]=e.date||'';
    _o[i18n.t('fin.filterType')]=e.type==='in'?i18n.t('fin.filterIncome'):i18n.t('fin.filterExpense');
    _o[i18n.t('fin.category')]=(e.title||'').replace(/^[^\u4e00-\u9fa5A-Za-z]+/,'');
    _o[i18n.t('fin.amount')]=(e.type==='in'?'':'-')+(e.amount||0);
    _o[i18n.t('fin.relatedTenant')]=e.sub||'';
    return _o;
  });
  var ws=XLSX.utils.json_to_sheet(rows);
  var wb=XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb,ws,i18n.t('fin.ledger'));
  var scope=finYear+(finMonth!=='all'?'-'+finMonth.slice(5):'')+(finBldg!=='__all__'?'_'+(function(){var b=cache.buildings.find(function(x){return x.id===finBldg});return b?b.name:''})():'');
  XLSX.writeFile(wb,i18n.t('fin.ledger')+'_'+scope+'.xlsx');
  toast(i18n.t('set.excelExported'));
}
function showLedgerDetail(idx){
  var e=_finFiltered()[idx];
  if(!e)return;
  var rows='';
  function row(k,v){return '<div style="display:flex;gap:10px;padding:7px 0;border-bottom:1px solid var(--bd);font-size:13px"><span style="color:var(--ts);flex:0 0 88px">'+k+'</span><span style="flex:1;word-break:break-all">'+(v||'-')+'</span></div>'}
  rows+=row(i18n.t('fin.expenseDate'),fmtDate(e.date));
  rows+=row(i18n.t('fin.filterType'),e.type==='in'?'<span style="color:var(--g,#16a34a)">'+i18n.t('fin.filterIncome')+'</span>':'<span style="color:var(--d,#dc2626)">'+i18n.t('fin.filterExpense')+'</span>');
  rows+=row(i18n.t('fin.amount'),'<b style="color:'+(e.type==='in'?'var(--g,#16a34a)':'var(--d,#dc2626)')+'">'+(e.type==='in'?'+':'-')+'¥'+(e.amount||0).toLocaleString()+'</b>');
  rows+=row(i18n.t('fin.category'),e.title||'');
  if(e.sub)rows+=row(i18n.t('fin.relatedTenant'),e.sub);
  var link='';
  if(e.kind==='rent'&&e.tid){
    link='<div style="margin-top:12px"><button class="btn btn-gh" style="width:100%" onclick="closeModal();goPage(\'rent\');setTimeout(function(){var t=cache.tenants.find(function(x){return x.id===\\''+e.tid+'\\'});toast((t?t.name:\'\')+\' · \'+i18n.t('fin.viewBillsHint'),\'i\')},150)">📋 '+i18n.t('fin.viewBills')+'</button></div>';
  }else if(e.kind==='water'||e.kind==='electric'||e.kind==='utility'){
    link='<div style="margin-top:12px"><button class="btn btn-gh" style="width:100%" onclick="closeModal();goPage(\'rent\');toast(i18n.t('fin.viewMeterHint'),\'i\')">⚡ '+i18n.t('fin.viewMeters')+'</button></div>';
  }
  var ops='';
  if(canEdit()&&e.editable&&e.id){
    var editFn=e.type==='in'?'showIncomeModal':'showExpenseModal';
    var delFn=e.type==='in'?'delIncome':'delExpense';
    ops='<div style="display:flex;gap:8px;margin-top:14px">'+
      '<button class="btn btn-gh" style="flex:1" onclick="closeModal();'+editFn+'(\\''+e.id+'\\')">'+i18n.t('common.edit')+'</button>'+
      '<button class="btn btn-o" style="flex:1;color:var(--d)" onclick="closeModal();'+delFn+'(\\''+e.id+'\\')">'+i18n.t('common.delete')+'</button></div>';
  }else if(canEdit()&&e.kind==='rent'){
    ops='<p class="hint" style="margin-top:12px">'+i18n.t('fin.rentSysTag')+'</p>';
  }
  openModal('<div class="m-hd"><h3>🧾 '+i18n.t('fin.detailTitle')+'</h3><button class="m-x" onclick="closeModal()">×</button></div>'+
    '<div class="m-bd">'+rows+link+ops+'</div>');
}
// ===== v75 增量结束 =====
'''
s=s.replace(anchor, new_funcs+anchor, 1)

# ---------- 2) rFinanceBook：工具栏加 [图表] [导出] 按钮 ----------
old_bar="""  html+='<select class="fc" style="width:auto;font-size:13px;padding:6px 10px" onchange="finFilter=this.value;rFinance()">';
  html+='<option value="all"'+(finFilter==='all'?' selected':'')+'>'+i18n.t('fin.filterAll')+'</option>';
  html+='<option value="in"'+(finFilter==='in'?' selected':'')+'>'+i18n.t('fin.filterIncome')+'</option>';
  html+='<option value="out"'+(finFilter==='out'?' selected':'')+'>'+i18n.t('fin.filterExpense')+'</option>';
  html+='</select></div>';"""
new_bar=old_bar+"""
  // v75: 图表分析 + 导出筛选数据 按钮
  html+='<button class="btn btn-gh" style="font-size:13px;padding:6px 12px" onclick="document.getElementById(\\'finChartCard\\').style.display=document.getElementById(\\'finChartCard\\').style.display===\\'none\\'?\\'block\\':\\'none\\'">📊 '+i18n.t('fin.chartBtn')+'</button>';
  html+='<button class="btn btn-p" style="font-size:13px;padding:6px 12px" onclick="exportLedgerFiltered()">📥 '+i18n.t('fin.exportFiltered')+'</button></div>';
  html+='<div id="finChartCard" style="display:block">'+_finBarChart(yearEntries)+'</div>';"""
assert s.count(old_bar)==1, 'toolbar anchor count=%d'%s.count(old_bar)
s=s.replace(old_bar,new_bar,1)

io.open('app.html','w',encoding='utf-8').write(s)
print('OK app.html: 图表/导出/详情函数 + 工具栏按钮 + 图表卡片')
