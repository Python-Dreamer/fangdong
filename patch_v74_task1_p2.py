# -*- coding: utf-8 -*-
"""v74 任务1 phase2: app.html 前端改造
- 登记租户弹窗: 房间楼栋筛选+房号搜索; 新增 PDF/Word 文件上传区
- 编辑租户弹窗: 房间筛选; 已存文件可删除
- 详情页: 补文件区展示
- 修复 cap() 导致 UUID 开头字母时文件按钮/列表找不到的bug
- 3MB/10个 限制
所有业务数据流(insert/update/字段)不变。"""
import io, sys

def patch(path, repls):
    with io.open(path, 'r', encoding='utf-8') as f:
        s = f.read()
    for old, new, cnt in repls:
        actual = s.count(old)
        if actual != cnt:
            print('FAIL [%s]: expect %d got %d' % (path, cnt, actual))
            print('--- anchor head:', repr(old[:100]))
            sys.exit(1)
        s = s.replace(old, new)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('OK [%s]: %d hunks applied' % (path, len(repls)))

R = []

# 1) cap bug: triggerFileUpload 先找原id再找cap
R.append((
r"""function triggerFileUpload(tenantId){var input=document.getElementById('fileInput'+cap(tenantId));if(input)input.click()}""",
r"""function triggerFileUpload(tenantId){var input=document.getElementById('fileInput'+tenantId)||document.getElementById('fileInput'+cap(tenantId));if(input)input.click()}""",
1))

# 2) cap bug: renderFileList 同样兼容
R.append((
r"""function renderFileList(tenantId){var el=document.getElementById('fileList'+cap(tenantId));if(!el)return;""",
r"""function renderFileList(tenantId){var el=document.getElementById('fileList'+tenantId)||document.getElementById('fileList'+cap(tenantId));if(!el)return;""",
1))

# 3) 文件数量 1 -> 10
R.append((
r"""if(existing.length+files.length>1){toast(i18n.t('tenant.max1File'),'w');input.value='';return}""",
r"""if(existing.length+files.length>10){toast(i18n.t('tenant.maxFiles'),'w');input.value='';return}""",
1))

# 4) 文件大小 1MB -> 3MB
R.append((
r"""if(f.size>1*1024*1024){toast(''+i18n.t('common.file')+' '+f.name+' '+i18n.t('common.exceeding')+'1MB','e');continue}""",
r"""if(f.size>3*1024*1024){toast(''+i18n.t('common.file')+' '+f.name+' '+i18n.t('common.exceeding')+'3MB','e');continue}""",
1))

# 5) filterTenantRooms 全局函数(挂在 cap 后面)
R.append((
r"""function cap(s){return s.charAt(0).toUpperCase()+s.slice(1)}""",
r"""function cap(s){return s.charAt(0).toUpperCase()+s.slice(1)}
function filterTenantRooms(){var sel=document.getElementById('fTRm');if(!sel)return;var bEl=document.getElementById('fTRmB'),sEl=document.getElementById('fTRmS');var bid=bEl?bEl.value:'__all__';var kw=sEl?(sEl.value||'').trim().toLowerCase():'';var cur=sel.value;var ph=sel.options[0]&&!sel.options[0].value?sel.options[0].text:'';var html=(ph&&!cur)?'<option value="">'+ph+'</option>':'';var kept=false;for(var i=0;i<sel.options.length;i++){var o=sel.options[i];if(!o.value)continue;var ob=o.getAttribute('data-bid')||'';var txt=o.text.toLowerCase();var ok=(bid==='__all__'||ob===bid)&&(!kw||txt.indexOf(kw)>=0);if(ok){html+='<option value="'+o.value+'" data-bid="'+ob+'"'+(o.value===cur?' selected':'')+'>'+o.text+'</option>';if(o.value===cur)kept=true}}if(cur&&!kept){var co=sel.querySelector('option[value="'+cur+'"]');if(co)html='<option value="'+co.value+'" data-bid="'+(co.getAttribute('data-bid')||'')+'" selected>'+co.text+'</option>'+html}sel.innerHTML=html}""",
1))

# 6) renderFilesHtml 加 editable 参数+删除按钮; 新增 deleteContractFile
R.append((
r"""function renderFilesHtml(files,tenantId){if(!files||!files.length)return '<p style="font-size:12px;color:var(--ts);margin-top:8px">'+i18n.t('tenant.noContractFiles')+'</p>';
var html='<div class="file-section"><h4>'+i18n.t('tenant.contractFiles')+'</h4><div class="file-list">';
for(var i=0;i<files.length;i++){
var f=files[i];var name=typeof f==='string'?f:(f.name||f.path||'');
var ext=name.split('.').pop().toLowerCase();
var icon=ext==='pdf'?'📄':(ext==='doc'||ext==='docx')?'📝':'📎';
var path=typeof f==='string'?f:f.path;
html+='<div class="file-item"><span class="file-icon">'+icon+'</span><div class="file-info"><div class="file-name">'+esc(name)+'</div></div><div class="file-actions"><button class="file-btn" onclick="downloadFile(\''+esc(path)+'\',\''+esc(name)+'\',\''+tenantId+'\')">'+i18n.t('common.download')+'</button></div></div>'}
html+='</div></div>';return html}""",
r"""function renderFilesHtml(files,tenantId,editable){if(!files||!files.length)return '<p style="font-size:12px;color:var(--ts);margin-top:8px">'+i18n.t('tenant.noContractFiles')+'</p>';
var html='<div class="file-section"><h4>'+i18n.t('tenant.contractFiles')+'</h4><div class="file-list">';
for(var i=0;i<files.length;i++){
var f=files[i];var name=typeof f==='string'?f:(f.name||f.path||'');
var ext=name.split('.').pop().toLowerCase();
var icon=ext==='pdf'?'📄':(ext==='doc'||ext==='docx')?'📝':'📎';
var path=typeof f==='string'?f:f.path;
var dlBtn='<button class="file-btn" onclick="downloadFile(\''+esc(path)+'\',\''+esc(name)+'\',\''+tenantId+'\')">'+i18n.t('common.download')+'</button>';
var delBtn=editable?'<button class="file-btn" style="color:var(--d)" onclick="deleteContractFile(\''+esc(path)+'\',\''+tenantId+'\')">'+i18n.t('common.del')+'</button>':'';
html+='<div class="file-item"><span class="file-icon">'+icon+'</span><div class="file-info"><div class="file-name">'+esc(name)+'</div></div><div class="file-actions">'+dlBtn+delBtn+'</div></div>'}
html+='</div></div>';return html}
async function deleteContractFile(path,tenantId){confirmDialog(i18n.t('tenant.delFileConfirm'),'',async function(){try{try{await FileAPI.remove('contract-files',path)}catch(e){console.warn('File delete error:',e)}var _norm=function(x){return typeof x==='string'?x:x.path};if(tenantId==='new'){var fl=pendingFiles['new']||[];pendingFiles['new']=fl.filter(function(x){return _norm(x)!==path});renderFileList('new')}else{var tenant=cache.tenants.find(function(t){return t.id===tenantId});if(!tenant)return;var files=(tenant.contract_files||[]).filter(function(x){return _norm(x)!==path});var upd=await sb.from('tenants').update({contract_files:files}).eq('id',tenantId);if(upd.error){toast(i18n.t('common.deleteFailed'),'e');return}if(pendingFiles[tenantId]){pendingFiles[tenantId]=pendingFiles[tenantId].filter(function(x){return _norm(x)!==path})}await loadAllData();showEditTenant(tenantId)}}catch(e){console.error('Delete file error:',e);toast(i18n.t('common.deleteFailed'),'e')}})}""",
1))

# 7) showAddTenant: 开头重置 pendingFiles['new']
R.append((
r"""function showAddTenant(){if(!canEdit()){toast(i18n.t('common.readOnly'),'w');return}pendingPhotos['new']=[];window._occList=[];""",
r"""function showAddTenant(){if(!canEdit()){toast(i18n.t('common.readOnly'),'w');return}pendingPhotos['new']=[];pendingFiles['new']=[];window._occList=[];""",
1))

# 8) showAddTenant: roomOptions 加 data-bid + 楼栋名前缀
R.append((
r"""var roomOptions=allRooms.map(function(r){var cnt=getRoomTenantCount(r.id);var label=esc(r.name)+(cnt>0?' ('+cnt+''+i18n.t('tenant.peopleLiving')+')':'');return'<option value="'+r.id+'" data-rent="'+(r.rent_amount||'')+'">'+label+'</option>'}).join('');""",
r"""var _bMap={};(cache.buildings||[]).forEach(function(b){_bMap[b.id]=b.name});var roomOptions=allRooms.map(function(r){var cnt=getRoomTenantCount(r.id);var bn=(r.building_id&&_bMap[r.building_id])?_bMap[r.building_id]+' / ':'';var label=bn+esc(r.name)+(cnt>0?' ('+cnt+''+i18n.t('tenant.peopleLiving')+')':'');return'<option value="'+r.id+'" data-rent="'+(r.rent_amount||'')+'" data-bid="'+(r.building_id||'')+'">'+label+'</option>'}).join('');""",
1))

# 9) showAddTenant: 房间行后插入 楼栋筛选+房号搜索
R.append((
r"""'+roomOptions+'</select></div><div class="fg"><label>'+i18n.t('tenant.rentLabel')+'</label><input class="fc" id="fTRa" type="number" placeholder="'+i18n.t('rent.amount3')+'"></div></div>""",
r"""'+roomOptions+'</select></div><div class="fg"><label>'+i18n.t('tenant.rentLabel')+'</label><input class="fc" id="fTRa" type="number" placeholder="'+i18n.t('rent.amount3')+'"></div></div><div class="fr"><div class="fg"><label>'+i18n.t('building.selectBuilding')+'</label><select class="fc" id="fTRmB" onchange="filterTenantRooms()" autocomplete="off" data-lpignore="true"><option value="__all__">'+i18n.t('common.all')+'</option>'+(cache.buildings||[]).map(function(b){return'<option value="'+b.id+'">'+esc(b.name)+'</option>'}).join('')+'</select></div><div class="fg"><label>'+i18n.t('tenant.roomSearch')+'</label><input class="fc" id="fTRmS" placeholder="'+i18n.t('tenant.roomSearchPh')+'" oninput="filterTenantRooms()" oncompositionstart="_composing=true" oncompositionend="_composing=false;filterTenantRooms()"></div></div>""",
1))

# 10) showAddTenant: 照片区后插入合同文件上传区
R.append((
r"""onchange="handlePhotoUpload(this,\'new\')"></div></div><div class="m-ft">""",
r"""onchange="handlePhotoUpload(this,\'new\')"></div></div><div class="file-section"><h4>'+i18n.t('tenant.contractFiles')+'</h4><div class="file-list" id="fileListNew"></div><div class="file-upload-btn" onclick="triggerFileUpload(\'new\')"><span>+</span>'+i18n.t('tenant.uploadContractFile')+'</div><p class="file-hint">'+i18n.t('common.fileHint')+'</p><input type="file" id="fileInputNew" accept=".pdf,.doc,.docx" multiple style="display:none" onchange="handleFileUpload(this,\'new\')"></div><div class="m-ft">""",
1))

# 11) doAddTenant: 成功后清空 pendingFiles['new']
R.append((
r"""await sb.from('rooms').update({status:'occupied'}).eq('id',rmId);pendingPhotos['new']=[];""",
r"""await sb.from('rooms').update({status:'occupied'}).eq('id',rmId);pendingPhotos['new']=[];pendingFiles['new']=[];""",
1))

# 12) showEditTenant: filesHtml 传入 editable
R.append((
r"""var filesHtml=renderFilesHtml(t.contract_files||[],id);""",
r"""var filesHtml=renderFilesHtml(t.contract_files||[],id,canEdit()&&t.status==='active');""",
1))

# 13) showEditTenant: 房间 option 加 data-bid + 楼栋名前缀
R.append((
r"""+allRooms.map(function(r){var sel=(r.id===t.room_id?' selected':'');return'<option value="'+r.id+'"'+sel+'>'+esc(r.name)+'</option>'}).join('')+'</select>""",
r"""+(function(){var _bm={};(cache.buildings||[]).forEach(function(b){_bm[b.id]=b.name});return allRooms.map(function(r){var sel=(r.id===t.room_id?' selected':'');var bn=(r.building_id&&_bm[r.building_id])?_bm[r.building_id]+' / ':'';return'<option value="'+r.id+'" data-bid="'+(r.building_id||'')+'"'+sel+'>'+bn+esc(r.name)+'</option>'}).join('')})()+'</select>""",
1))

# 14) showEditTenant: 租金行后插入 楼栋筛选+房号搜索(只读时禁用)
R.append((
r"""<input class="fc" id="fTRa" type="number" value="'+(t.rent_amount||'')+'"'+(isEdit?'':' readonly')+'></div></div><div class="fr"><div class="fg"><label>'+i18n.t('tenant.moveInDate')+'</label>""",
r"""<input class="fc" id="fTRa" type="number" value="'+(t.rent_amount||'')+'"'+(isEdit?'':' readonly')+'></div></div><div class="fr"><div class="fg"><label>'+i18n.t('building.selectBuilding')+'</label><select class="fc" id="fTRmB" onchange="filterTenantRooms()" autocomplete="off" data-lpignore="true"'+(isEdit?'':' disabled')+'><option value="__all__">'+i18n.t('common.all')+'</option>'+(cache.buildings||[]).map(function(b){return'<option value="'+b.id+'">'+esc(b.name)+'</option>'}).join('')+'</select></div><div class="fg"><label>'+i18n.t('tenant.roomSearch')+'</label><input class="fc" id="fTRmS" placeholder="'+i18n.t('tenant.roomSearchPh')+'" oninput="filterTenantRooms()" oncompositionstart="_composing=true" oncompositionend="_composing=false;filterTenantRooms()"'+(isEdit?'':' disabled')+'></div></div><div class="fr"><div class="fg"><label>'+i18n.t('tenant.moveInDate')+'</label>""",
1))

# 15) showTenantDetail: 照片区后补合同文件区
R.append((
r"""'<h4 style="margin-top:14px;font-size:13px;font-weight:700">'+i18n.t('common.contractPhotos')+'</h4>'+photoHtml+'<div id="adjSection_'+id+'">""",
r"""'<h4 style="margin-top:14px;font-size:13px;font-weight:700">'+i18n.t('common.contractPhotos')+'</h4>'+photoHtml+'<h4 style="margin-top:14px;font-size:13px;font-weight:700">'+i18n.t('common.contractFiles')+'</h4>'+filesHtml+'<div id="adjSection_'+id+'">""",
1))

patch('app.html', R)
print('phase2 done')
