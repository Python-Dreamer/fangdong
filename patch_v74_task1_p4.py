# -*- coding: utf-8 -*-
# v74 任务1 phase4: 房间区控件顺序调整为 搜索房间→所属楼栋→房间(月租金跟房间)
# 仅重排弹窗HTML中两个 .fr 行，不改任何 id/事件/数据流
import io
s=io.open('app.html',encoding='utf-8').read()

def extract_rows(fn_start_marker):
    i=s.find(fn_start_marker)
    assert i>=0, fn_start_marker
    j=s.find('function ',i+10)
    body=s[i:j]
    # 行A：含 id="fTRm" 的 fr；行B：含 id="fTRmB" 的 fr（两者相邻，A 在前 B 在后）
    def fr_row(fid):
        k=body.find('id="'+fid)
        st=body.rfind('<div class="fr">',0,k)
        nxt=body.find('<div class="fr">',k)
        return body[st:nxt], st, nxt
    rowA,_,_=fr_row('fTRm"')
    rowB,_,_=fr_row('fTRmB"')
    return rowA,rowB

def swap_b(rowB):
    # rowB = <div class="fr"> fgB(楼栋) fgS(搜索) </div>  →  fgS fgB
    open_tag='<div class="fr">'
    assert rowB.startswith(open_tag)
    inner=rowB[len(open_tag):rowB.rfind('</div>')]
    fg_start=inner.find('<div class="fg">')
    fg_end=inner.find('</div>',fg_start)+len('</div>')
    fgB=inner[fg_start:fg_end]          # 楼栋 fg
    fgS=inner[fg_end:].strip()           # 搜索 fg（剩余）
    assert 'fTRmB' in fgB and 'fTRmS' in fgS, 'fg split failed'
    return open_tag+fgS+fgB+'</div>'

# ---- showAddTenant ----
aA,aB=extract_rows('function showAddTenant')
aB_new=swap_b(aB)
old_add=aA+aB
new_add=aB_new+aA
assert s.count(old_add)==1, 'add rows count=%d'%s.count(old_add)
s=s.replace(old_add,new_add,1)

# ---- showEditTenant ----
eA,eB=extract_rows('async function showEditTenant')
eB_new=swap_b(eB)
old_edit=eA+eB
new_edit=eB_new+eA
assert s.count(old_edit)==1, 'edit rows count=%d'%s.count(old_edit)
s=s.replace(old_edit,new_edit,1)

io.open('app.html','w',encoding='utf-8').write(s)
print('OK: 房间区顺序已调整（搜索房间→所属楼栋→房间/月租金），登记+编辑弹窗')
