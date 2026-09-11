# -*- coding: utf-8 -*-
# 需求3：合同文件 10个→2个，且拦截重复文件（同名+同大小），防止恶意重复上传
import io
# ---- app.html ----
p='app.html'; s=io.open(p,encoding='utf-8').read()

old1="if(existing.length+files.length>10){toast(i18n.t('tenant.maxFiles'),'w');input.value='';return}"
new1="if(existing.length+files.length>2){toast(i18n.t('tenant.maxFiles'),'w');input.value='';return}"
assert s.count(old1)==1; s=s.replace(old1,new1,1)

# 循环内、扩展名校验通过后，加重复文件拦截（对比 已存在列表 + 本次已选文件）
old2="if(['pdf','doc','docx'].indexOf(ext)===-1){toast(i18n.t('tenant.unsupportedFormat'),'w');continue}\nvar ext2=f.name.split('.').pop();"
new2=("if(['pdf','doc','docx'].indexOf(ext)===-1){toast(i18n.t('tenant.unsupportedFormat'),'w');continue}\n"
"var _dup=existing.some(function(x){return (x.name||'')===f.name && (x.size||0)===(f.size||0)})||\n"
"  files.slice(0,i).some(function(g){return g.name===f.name && (g.size||0)===(f.size||0)});\n"
"if(_dup){toast(i18n.t('tenant.dupFile',{name:f.name}),'w');continue}\n"
"var ext2=f.name.split('.').pop();")
assert s.count(old2)==1, 'dup anchor count=%d'%s.count(old2); s=s.replace(old2,new2,1)
io.open(p,'w',encoding='utf-8').write(s)
print('OK app.html: 2个上限+重复拦截')

# ---- i18n.js ----
p='i18n.js'; s=io.open(p,encoding='utf-8').read()
reps=[
 ('"tenant.maxFiles": "最多上传10个文件"','"tenant.maxFiles": "最多上传2个文件"'),
 ('"tenant.maxFiles": "Up to 10 files"','"tenant.maxFiles": "Up to 2 files"'),
 ('"common.fileHint": "支持 PDF、Word 格式，单个文件不超过 3MB，最多 10 个"','"common.fileHint": "支持 PDF、Word 格式，单个文件不超过 3MB，最多 2 个，重复文件无法上传"'),
 ('"common.fileHint": "Supports PDF, Word; each file up to 3MB; up to 10 files"','"common.fileHint": "Supports PDF, Word; each file up to 3MB; up to 2 files; duplicates are rejected"'),
]
for a,b in reps:
    assert s.count(a)==1, a
    s=s.replace(a,b,1)
# 新增 dupFile 键（中英各一），插在 maxFiles 后面
zh_anchor='"tenant.maxFiles": "最多上传2个文件",'
zh_add=zh_anchor+'\n    "tenant.dupFile": "文件 {name} 已上传过，请勿重复上传",'
assert s.count(zh_anchor)==1; s=s.replace(zh_anchor,zh_add,1)
en_anchor='"tenant.maxFiles": "Up to 2 files",'
en_add=en_anchor+'\n    "tenant.dupFile": "File {name} already uploaded; duplicates are not allowed",'
assert s.count(en_anchor)==1; s=s.replace(en_anchor,en_add,1)
io.open(p,'w',encoding='utf-8').write(s)
print('OK i18n.js: 文案2个/重复提示')
