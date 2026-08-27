# -*- coding: utf-8 -*-
import io

# ============ 1. app.html modifications ============
with io.open('app.html','r',encoding='utf-8') as f:
    lines = f.readlines()

# Helper: find line index by exact startswith
def find_line(prefix, start=0):
    for i in range(start, len(lines)):
        if lines[i].startswith(prefix):
            return i
    return -1

# (A) Insert CSS before </style>
style_end = find_line('</style>')
assert style_end >= 0, 'no </style>'
css = (
'.bldg-bar{display:flex;gap:8px;overflow-x:auto;padding:4px 0 12px;-webkit-overflow-scrolling:touch;scrollbar-width:none}'
'.bldg-bar::-webkit-scrollbar{display:none}'
'.bldg-card{flex:0 0 auto;min-width:108px;padding:10px 12px;border-radius:10px;background:var(--card,#fff);border:1.5px solid var(--bd);cursor:pointer;transition:all .15s}'
'.bldg-card.on{border-color:var(--p);background:var(--p);color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.08)}'
'.bldg-card .bn{font-size:13px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
'.bldg-card .bs{font-size:11px;margin-top:4px;opacity:.9}'
'.bldg-card .bs b{font-size:14px}'
'.bldg-card .g{color:var(--g)}'
'.bldg-card.on .g{color:#c8f7d0}'
'.bldg-card .y{color:var(--w,#f59e0b)}'
'.bldg-card.on .y{color:#ffe7a3}'
'td.floor-hd{background:rgba(0,0,0,.03);font-weight:700;font-size:12px;color:var(--p);padding:6px 10px!important;letter-spacing:.3px}'
'td.floor-hd .fc{display:inline-block;padding:2px 8px;background:rgba(0,0,0,.05);border-radius:10px}'
'.bldg-select-wrap{display:flex;gap:6px;align-items:stretch}'
'.bldg-select-wrap .fc{flex:1}'
'.bldg-add-btn{flex:0 0 auto;width:36px;border:1.5px dashed var(--bd);background:transparent;border-radius:8px;font-size:20px;line-height:1;color:var(--p);cursor:pointer;padding:0}'
'.bldg-add-btn:active{background:var(--p);color:#fff;border-style:solid}'
'.bldg-overview{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}'
'.bldg-ov-card{padding:12px;border:1px solid var(--bd);border-radius:10px;background:var(--card,#fff)}'
'.bldg-ov-card .bn{font-weight:700;font-size:13px;margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
'.bldg-ov-bar{height:6px;background:var(--bd);border-radius:3px;overflow:hidden;margin:4px 0 6px}'
'.bldg-ov-bar i{display:block;height:100%;background:var(--g)}'
'.bldg-ov-meta{font-size:11px;color:var(--ts);display:flex;justify-content:space-between}'
)
lines.insert(style_end, css + '\n')

# (B) Add new building functions after selectBuilding line
for i,l in enumerate(lines):
    if l.startswith('function selectBuilding(id)'):
        sel_idx = i
        break
else:
    raise Exception('selectBuilding not found')

with io.open('_bldg_tmp/newfuncs.txt','r',encoding='utf-8') as f:
    newfuncs = f.read().rstrip('\n') + '\n'
lines.insert(sel_idx+1, newfuncs)

# (C) doEditRoom: insert building_id into update object
for i,l in enumerate(lines):
    if l.startswith('async function doEditRoom(id)'):
        edit_idx = i
        break
else:
    raise Exception('doEditRoom not found')
old = lines[edit_idx]
needle = "address:document.getElementById('fRA').value.trim(),"
# It exists once (doEditRoom also has address). We need the one in update. doEditRoom: update({name:name,address:...
# Actually both doAddRoom and doEditRoom have this exact string. We'll replace within edit_idx line.
assert old.count(needle) == 1, 'expected 1 needle in doEditRoom, got %d' % old.count(needle)
new = old.replace(needle, needle + "building_id:document.getElementById('fRB').value||null,", 1)
lines[edit_idx] = new

# (D) meterGetPrices rewrite: add building prices before room prices
for i,l in enumerate(lines):
    if l.startswith('function meterGetPrices('):
        m_idx = i
        break
else:
    raise Exception('meterGetPrices not found')
new_meter = (
"function meterGetPrices(tenantId,roomId){\n"
"  var s=cache.settings||{};\n"
"  var room=roomId?cache.rooms.find(function(r){return r.id===roomId}):null;\n"
"  if(!room&&tenantId){var t=cache.tenants.find(function(x){return x.id===tenantId});if(t)room=cache.rooms.find(function(r){return r.id===t.room_id})}\n"
"  var bldg=(room&&room.building_id)?(cache.buildings||[]).find(function(b){return b.id===room.building_id}):null;\n"
"  function pick(bv,rv,sv,dv){var v;if(bv!==undefined&&bv!==null){v=parseFloat(bv);if(!isNaN(v))return v}if(rv!==undefined&&rv!==null){v=parseFloat(rv);if(!isNaN(v))return v}if(sv!==undefined&&sv!==null){v=parseFloat(sv);if(!isNaN(v))return v}return dv}\n"
"  var cp=pick(bldg&&bldg.cold_water_price,room&&room.cold_water_price,s.default_cold_water_price,5);\n"
"  var hp=pick(bldg&&bldg.hot_water_price,room&&room.hot_water_price,s.default_hot_water_price,6);\n"
"  var ep=pick(bldg&&bldg.electricity_price,room&&room.electricity_price,s.default_electricity_price,1.5);\n"
"  if(isNaN(cp))cp=5;if(isNaN(hp))hp=6;if(isNaN(ep))ep=1.5;\n"
"  return{cold:cp,hot:hp,elec:ep};\n"
"}\n"
)
lines[m_idx] = new_meter

# (E) rDashboard: add bldg overview section before final '
for i,l in enumerate(lines):
    if l.startswith('function rDashboard()'):
        dash_idx = i
        break
else:
    raise Exception('rDashboard not found')
dash_line = lines[dash_idx]
# Find the last occurrence of paidTbl card close pattern: the ending is ...paidTbl+</div></div></div>'}
# Insert building overview block just before the final closing: replace last "</div></div>'}"
marker = "+paidTbl+'</div></div></div>'}"
assert marker in dash_line, 'dashboard end marker not found'
bldg_overview_code = (
"+paidTbl+'</div></div></div>'"
"+((cache.buildings&&cache.buildings.length)?('<div class=\\'card\\'><div class=\\'card-hd\\'><h3>'+i18n.t('building.overview')+'</h3></div><div class=\\'bldg-overview\\'>'"
"+cache.buildings.map(function(b){"
"var brs=cache.rooms.filter(function(r){return r.building_id===b.id});"
"var occ=brs.filter(function(r){return r.status==='occupied'}).length;"
"var rate=brs.length?Math.round(occ/brs.length*100):0;"
"var tids=brs.map(function(r){return r.id});"
"var activeTenants=cache.tenants.filter(function(t){return t.status==='active'&&tids.indexOf(t.room_id)>=0});"
"var m=thisMonth();"
"var due=activeTenants.reduce(function(a,t){return a+(t.rent_amount||0)},0);"
"var paid=cache.rents.filter(function(r){return r.status==='paid'&&r.due_date&&String(r.due_date).slice(0,7)===m&&activeTenants.some(function(t){return t.id===r.tenant_id})}).reduce(function(a,r){return a+r.amount},0);"
"return'<div class=\\'bldg-ov-card\\'>'+('<div class=\\'bn\\'>'+esc(b.name)+'</div>')+'<div class=\\'bldg-ov-bar\\'><i style=\\'width:'+rate+'%\\'></i></div>'+'<div class=\\'bldg-ov-meta\\'><span>'+occ+'/'+brs.length+' · '+rate+'%</span><span>¥'+due.toLocaleString()+'</span></div></div>'}).join('')+'</div></div>'):'')}"
)
new_dash = dash_line.replace(marker, bldg_overview_code, 1)
assert new_dash != dash_line
lines[dash_idx] = new_dash

with io.open('app.html','w',encoding='utf-8') as f:
    f.writelines(lines)

print('app.html patched')

# ============ 2. i18n.js: add building.floorN in en ============
with io.open('i18n.js','r',encoding='utf-8') as f:
    ilines = f.readlines()
# Find en section's building.occupancy line
en_idx = -1
for i,l in enumerate(ilines):
    if '"building.occupancy": "Occupancy",' in l:
        en_idx = i
        break
assert en_idx >= 0
# Check next line doesn't already contain floorN
if 'building.floorN' not in ilines[en_idx+1]:
    ilines.insert(en_idx+1, '    "building.floorN": "Floor {n}",\n')
with io.open('i18n.js','w',encoding='utf-8') as f:
    f.writelines(ilines)
print('i18n.js patched')
