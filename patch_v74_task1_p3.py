# -*- coding: utf-8 -*-
# v74 任务1 phase3: 修复 filterTenantRooms —— 每次从 cache.rooms 全量重建选项，
# 不再过滤当前 DOM（旧实现连续筛选时选项永久丢失）
import io,sys
p='app.html'
s=io.open(p,encoding='utf-8').read()

old = """function filterTenantRooms(){var sel=document.getElementById('fTRm');if(!sel)return;var bEl=document.getElementById('fTRmB'),sEl=document.getElementById('fTRmS');var bid=bEl?bEl.value:'__all__';var kw=sEl?(sEl.value||'').trim().toLowerCase():'';var cur=sel.value;var ph=sel.options[0]&&!sel.options[0].value?sel.options[0].text:'';var html=(ph&&!cur)?'<option value="">'+ph+'</option>':'';var kept=false;for(var i=0;i<sel.options.length;i++){var o=sel.options[i];if(!o.value)continue;var ob=o.getAttribute('data-bid')||'';var txt=o.text.toLowerCase();var ok=(bid==='__all__'||ob===bid)&&(!kw||txt.indexOf(kw)>=0);if(ok){html+='<option value="'+o.value+'" data-bid="'+ob+'"'+(o.value===cur?' selected':'')+'>'+o.text+'</option>';if(o.value===cur)kept=true}}if(cur&&!kept){var co=sel.querySelector('option[value="'+cur+'"]');if(co)html='<option value="'+co.value+'" data-bid="'+(co.getAttribute('data-bid')||'')+'" selected>'+co.text+'</option>'+html}sel.innerHTML=html}"""

new = """function filterTenantRooms(){var sel=document.getElementById('fTRm');if(!sel)return;var bEl=document.getElementById('fTRmB'),sEl=document.getElementById('fTRmS');var bid=bEl?bEl.value:'__all__';var kw=sEl?(sEl.value||'').trim().toLowerCase():'';var cur=sel.value;var ph=sel.options[0]&&!sel.options[0].value?sel.options[0].text:'';var bm={};(cache.buildings||[]).forEach(function(b){bm[b.id]=b.name});function lbl(r){var cnt=getRoomTenantCount(r.id);var pfx=(r.building_id&&bm[r.building_id])?bm[r.building_id]+' / ':'';return pfx+esc(r.name)+(cnt>0?' ('+cnt+i18n.t('tenant.peopleLiving')+')':'')}var html=(ph&&!cur)?'<option value="">'+ph+'</option>':'';var curMatched=false;(cache.rooms||[]).forEach(function(r){var label=lbl(r);var ok=(bid==='__all__'||r.building_id===bid)&&(!kw||label.toLowerCase().indexOf(kw)>=0);if(ok){html+='<option value="'+r.id+'" data-bid="'+(r.building_id||'')+'"'+(r.id===cur?' selected':'')+'>'+label+'</option>';if(r.id===cur)curMatched=true}});if(cur&&!curMatched){var cr=(cache.rooms||[]).find(function(r){return r.id===cur});if(cr){html='<option value="'+cr.id+'" data-bid="'+(cr.building_id||'')+'" selected>'+lbl(cr)+'</option>'+html}}sel.innerHTML=html}"""

assert s.count(old)==1, 'old filterTenantRooms count=%d' % s.count(old)
s=s.replace(old,new)
io.open(p,'w',encoding='utf-8').write(s)
print('OK: filterTenantRooms replaced (full rebuild from cache.rooms)')
