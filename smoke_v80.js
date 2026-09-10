// v80 专项冒烟：①租客登记必填校验 ②账单图片内嵌二维码+备注入图 ③水电抄表记录可编辑
const fs=require('fs'),vm=require('vm');
const APP='/Coze/Drive/明灯/所有对话/主对话/tools_build/repo/app.html';
const I18N='/Coze/Drive/明灯/所有对话/主对话/tools_build/repo/i18n.js';
const html=fs.readFileSync(APP,'utf8');
const blocks=[];const re=/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;let m;
while((m=re.exec(html))){blocks.push(m[1]);}

function makeEl(){
  const el=function(){};
  el.style={};el.children=[];el.classList={_s:{},add(c){this._s[c]=1},remove(c){delete this._s[c]},toggle(c,f){if(f===undefined)this._s[c]=!this._s[c];else if(f)this._s[c]=1;else delete this._s[c]},contains(c){return !!this._s[c]}};
  el.dataset={};el.value='';el._text='';el._html='';el.checked=false;
  el.appendChild=function(c){el.children.push(c);return c};
  el.remove=function(){};el.removeChild=function(){};el.replaceWith=function(){};
  el.querySelector=function(){return makeEl()};el.querySelectorAll=function(){return []};
  el.setAttribute=function(){};el.getAttribute=function(){return null};
  el.addEventListener=function(){};el.removeEventListener=function(){};
  el.focus=function(){};el.click=function(){};el.scrollIntoView=function(){};
  el.getBoundingClientRect=function(){return{top:0,left:0,width:100,height:10}};
  el.insertAdjacentHTML=function(){};el.closest=function(){return null};
  el.cloneNode=function(){return makeEl()};
  el.parentElement=null;el.parentNode=null;el.firstChild=null;
  Object.defineProperty(el,'textContent',{configurable:true,get(){return el._text},set(v){el._text=v}});
  Object.defineProperty(el,'innerHTML',{configurable:true,get(){return el._html},set(h){el._html=h}});
  return el;
}
const __ctxs=[];
function makeCtx(){const texts=[],draws=[];
  const ctx=new Proxy({},{
    get(t,p){ if(p==='__texts')return texts; if(p==='__draws')return draws;
      return function(...a){ if(p==='fillText')texts.push(String(a[0])); if(p==='drawImage')draws.push(a[0]); }; },
    set(){return true}
  });return ctx;
}
function makeCanvasEl(){const el=makeEl();el.width=0;el.height=0;const ctx=makeCtx();el.getContext=function(){return ctx};el.toDataURL=function(){return'data:image/png;base64,FAKEQR'};el.__ctx=ctx;__ctxs.push(ctx);return el}
function makeDivEl(){const e=makeEl();e.querySelector=function(s){return s==='canvas'?makeCanvasEl():makeEl()};return e}
function anyObj(name){
  return new Proxy(function(){},{
    get(t,prop){
      if(prop===Symbol.toPrimitive)return ()=>'';
      if(prop==='length')return 0;
      if(prop==='then')return undefined;
      if(prop in t)return t[prop];
      t[prop]=anyObj(name+'.'+String(prop));return t[prop];
    },
    set(t,prop,v){t[prop]=v;return true},
    apply(){return anyObj(name+'()')},
    construct(){return makeEl()}
  });
}
globalThis.elRegistry={};
const elRegistry=globalThis.elRegistry;
function getEl(id){
  if(elRegistry[id])return elRegistry[id];
  elRegistry[id]=makeEl();return elRegistry[id];
}
const documentMock={
  getElementById:getEl,
  querySelector:function(){return makeEl()},
  querySelectorAll:function(){return []},
  createElement:function(tag){ if(tag==='canvas')return makeCanvasEl(); if(tag==='div')return makeDivEl();
    if(tag==='script'){const sc=makeEl();sc._src='';Object.defineProperty(sc,'src',{set(v){sc._src=v;setTimeout(function(){sc.onerror&&sc.onerror();},0)},get(){return sc._src}});return sc;}
    return makeEl(); },
  createTextNode:function(){return makeEl()},
  body:makeEl(),documentElement:makeEl(),head:makeEl(),
  addEventListener:function(){},removeEventListener:function(){},
  cookie:'',title:'',hidden:false,
  location:{href:'https://ruilifangfong.site/app.html',pathname:'/app.html',search:'',reload(){}},
  localStorage:{_d:{},getItem(k){return this._d[k]||null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}},
};
const windowMock=anyObj('window');
windowMock.location=documentMock.location;windowMock.localStorage=documentMock.localStorage;
windowMock.navigator={userAgent:'node-smoke',language:'zh-CN',clipboard:{writeText(){}}};
windowMock.document=documentMock;
windowMock.addEventListener=function(){};windowMock.scrollTo=function(){};windowMock.innerWidth=390;
windowMock.confirm=function(){return true};windowMock.alert=function(){};

const sandbox2={
  window:windowMock,document:documentMock,console,localStorage:documentMock.localStorage,
  location:documentMock.location,navigator:windowMock.navigator,
  setTimeout,clearTimeout,setInterval,clearInterval,
  fetch:async()=>({ok:false,json:async()=>({})}),
  URL:anyObj('URL'),Blob:function(){},FileReader:anyObj('FileReader'),
  File:function(){},FormData:function(){return{append(){}}},
  Math,JSON,Date,Object,Array,String,Number,Boolean,RegExp,parseInt,parseFloat,isNaN,encodeURIComponent,decodeURIComponent,
  Promise,Proxy,Reflect,Symbol,Map,Set,
  btoa:s=>Buffer.from(s,'binary').toString('base64'),
  atob:s=>Buffer.from(s,'base64').toString('binary'),
};
sandbox2.globalThis=sandbox2;sandbox2.self=sandbox2;sandbox2.window=sandbox2;
sandbox2.alert=function(){};sandbox2.confirm=function(){return true};
sandbox2.addEventListener=function(){};sandbox2.removeEventListener=function(){};
sandbox2.innerWidth=390;sandbox2.scrollTo=function(){};sandbox2.open=function(){return null};
sandbox2.navigator={userAgent:'node-smoke',language:'zh-CN',clipboard:{writeText(){}}};
// Image mock：设置 src 后异步触发 onload
sandbox2.Image=function(){const im={};im._src='';Object.defineProperty(im,'src',{set(v){im._src=v;setTimeout(function(){im.onload&&im.onload()},0)},get(){return im._src}});return im};
// 跳过 app 自带的网络超时看门狗等长定时器(>=1s)，业务回调均为短延迟
sandbox2.setTimeout=function(fn,ms){if(typeof ms==='number'&&ms>=1000)return 0;return setTimeout(fn,ms);};
sandbox2.setInterval=function(){return 0};
vm.createContext(sandbox2);

// ===== mock 数据库 =====
const DB={bill_shares:[],meter_readings:[],meter_items:[],income_records:[],tenants:[],rooms:[],rents:[],buildings:[],workspace_settings:[]};
const writeLog=[];
function qb(table){
  const b={
    _ins:null,_upd:null,_f:null,_fv:null,_in:null,_del:false,_upsert:false,
    select(){return b},order(){return b},eq(col,v){b._f=col;b._fv=v;return b},
    insert(rows){b._ins=Array.isArray(rows)?rows:[rows];return b},
    update(patch){b._upd=patch;return b},
    upsert(patch,opts){b._ins=Array.isArray(patch)?patch:[patch];b._upsert=true;b._onConflict=opts&&opts.onConflict;return b},
    delete(){b._del=true;return b},
    single:async function(){var r=await b._exec();return{error:r.error,data:(Array.isArray(r.data)&&r.data.length)?r.data[0]:null}},
    then(res,rej){return b._exec().then(res,rej)},
    async _exec(){
      writeLog.push({table,ins:b._ins?b._ins.map(r=>({...r})):null,upd:b._upd,del:b._del,f:b._f,fv:b._fv});
      if(b._ins){
        b._ins.forEach((r,i)=>{if(!r.id)r.id=table+'_'+(DB[table].length+i+1);DB[table].push({...r})});
        return{error:null,data:b._ins.map(r=>({...r}))};
      }
      if(b._upd){
        let rows=DB[table];if(b._f)rows=rows.filter(r=>r[b._f]===b._fv);
        rows.forEach(r=>Object.assign(r,b._upd));
        return{error:null,data:[]};
      }
      if(b._del){
        if(b._f)DB[table]=DB[table].filter(r=>r[b._f]!==b._fv);
        return{error:null,data:[]};
      }
      let rows=(DB[table]||[]).map(r=>({...r}));
      if(b._f)rows=rows.filter(r=>r[b._f]===b._fv);
      return{error:null,data:rows};
    }
  };
  return b;
}
sandbox2.sb={auth:{getSession:async()=>({data:{session:{access_token:'t'}}}),signOut:async()=>({})},
  from:(t)=>qb(t),
  channel(){return {on(){return this},subscribe(){return this}}},removeChannel(){}};
sandbox2.FileAPI={upload:async function(b,p){return{path:p}},getUrl:function(){return 'https://x'},remove:async()=>({})};

try{vm.runInContext(fs.readFileSync(I18N,'utf8'),sandbox2,{filename:'i18n.js'});sandbox2.i18n=sandbox2.i18n||sandbox2.window.i18n;}catch(e){console.log('❌ i18n:',e.message);process.exit(1)}
if(sandbox2.i18n)sandbox2.window.i18n=sandbox2.i18n;
blocks.forEach((b,i)=>{try{vm.runInContext(b,sandbox2,{filename:'app_block'+i+'.js'});}catch(e){console.log('❌ 块'+i+'顶层错误:',e.stack.split('\n')[0]);process.exit(1)}});

// ===== VM 内重建 mock 数据库（app 顶层 var sb 覆盖）=====
vm.runInContext(`
var __DB={bill_shares:[],
  meter_readings:[
    {id:'m1',tenant_id:'t1',room_id:'r1',reading_date:'2026-09-05',paid:false,total_fee:50,notes:'旧备注',photo_url:null,owner_id:'o'},
    {id:'m2',tenant_id:'t1',room_id:'r1',reading_date:'2026-08-05',paid:true,paid_date:'2026-08-10',total_fee:50,notes:'',photo_url:null,owner_id:'o'}
  ],
  meter_items:[{id:'d1',reading_id:'m1',kind:'cold_water',label:'冷水',amount:100,owner_id:'o'}],
  income_records:[],
  tenants:[{id:'t1',name:'郭强',room_id:'r1',status:'active',rent_amount:500,move_in_date:'2026-01-01',contract_end:'2026-12-31',owner_id:'o'}],
  rooms:[{id:'r1',name:'404',building_id:'b1',owner_id:'o'}],
  rents:[{id:'x1',tenant_id:'t1',room_id:'r1',amount:500,status:'pending',period_start:'2026-09-01',due_date:'2026-09-30',owner_id:'o'}],
  buildings:[{id:'b1',name:'祥和',owner_id:'o'}],
  workspace_settings:[{owner_id:'o'}]
};
function __qb(table){
  var b={_ins:null,_upd:null,_f:null,_fv:null,_del:false,
    select(){return b},order(){return b},eq(col,v){b._f=col;b._fv=v;return b},
    insert(rows){b._ins=Array.isArray(rows)?rows:[rows];return b},
    update(p){b._upd=p;return b},
    delete(){b._del=true;return b},
    single:async function(){var r=await b._exec();return{error:r.error,data:(Array.isArray(r.data)&&r.data.length)?r.data[0]:null}},
    then(res,rej){return b._exec().then(res,rej)},
    async _exec(){
      if(!__DB[table])__DB[table]=[];
      if(b._ins){
        b._ins.forEach(function(r,i){if(!r.id)r.id=table+'_'+(__DB[table].length+i+1);__DB[table].push(Object.assign({},r))});
        return{error:null,data:b._ins.map(function(r){return Object.assign({},r)})};
      }
      if(b._upd){
        var rows=__DB[table];if(b._f)rows=rows.filter(function(r){return r[b._f]===b._fv});
        rows.forEach(function(r){Object.assign(r,b._upd)});
        return{error:null,data:[]};
      }
      if(b._del){
        if(b._f)__DB[table]=__DB[table].filter(function(r){return r[b._f]!==b._fv});
        return{error:null,data:[]};
      }
      var out=__DB[table].map(function(r){return Object.assign({},r)});
      if(b._f)out=out.filter(function(r){return r[b._f]===b._fv});
      return{error:null,data:out};
    }
  };
  return b;
}
sb={auth:{getSession:async function(){return{data:{session:{access_token:'t'}}}},signOut:async function(){return{}}},
  from:function(t){return __qb(t)},
  channel:function(){return{on:function(){return this},subscribe:function(){return this}}},removeChannel:function(){}};
`,sandbox2);

let pass=0,fail=0;
function ok(name,cond,extra){if(cond){pass++;console.log('✅',name)}else{fail++;console.log('❌',name,extra||'')}}

vm.runInContext(`
  currentUser={id:'owner-test-1',email:'332303155@qq.com'};
  cache={
    settings:{owner_id:'o',default_cold_water_price:5,default_hot_water_price:6,default_electricity_price:1.5},
    buildings:[{id:'b1',name:'祥和'}],
    rooms:[{id:'r1',name:'404',building_id:'b1',rent_amount:500,owner_id:'o'}],
    tenants:[{id:'t1',name:'郭强',room_id:'r1',status:'active',rent_amount:500,move_in_date:'2026-01-01',contract_end:'2026-12-31',owner_id:'o',phone:'13800000000'}],
    rents:[{id:'x1',tenant_id:'t1',room_id:'r1',amount:500,status:'pending',period_start:'2026-09-01',due_date:'2026-09-30',owner_id:'o'}],
    meters:[
      {id:'m1',tenant_id:'t1',room_id:'r1',reading_date:'2026-09-05',paid:false,total_fee:50,notes:'旧备注',photo_url:null,owner_id:'o',created_at:'2026-09-05T10:00:00Z'},
      {id:'m2',tenant_id:'t1',room_id:'r1',reading_date:'2026-08-05',paid:true,paid_date:'2026-08-10',total_fee:50,notes:'',photo_url:null,owner_id:'o',created_at:'2026-08-05T10:00:00Z'}
    ],
    meterItems:[
      {id:'mi1',reading_id:'m1',kind:'cold_water',label:'冷水',cur_reading:100,prev_reading:80,usage:20,price:5,amount:100,sort_order:0},
      {id:'mi2',reading_id:'m2',kind:'electricity',label:'电表',cur_reading:150,prev_reading:100,usage:50,price:1,amount:50,sort_order:0}
    ]
  };
  getOwnerId=function(){return 'o'};
  today=function(){return '2026-09-11'};
  isAdmin=function(){return true};canEdit=function(){return true};
  goPage=function(p){lastPage=p};
  loadAllData=async function(){return};
  showTenantDetail=function(){};renderPage=function(){};
  var __toasts=[];toast=function(m){__toasts.push(m)};window.__toasts=__toasts;
  var __modalHtml=null;openModal=function(h){__modalHtml=h;window.__modalHtml=h};closeModal=function(){__modalHtml=null;window.__modalHtml=null};
  var __confirm=null;confirmDialog=function(t,s,cb){__confirm={cb}};
  window.QRCode=function(el,opt){this.el=el;this.opt=opt;window.__lastQROpt=opt;__qrCalls.push(opt)};
  window.QRCode.CorrectLevel={M:0,H:1,L:2,Q:3};
  __qrCalls=[];window.__qrCalls=__qrCalls;
  window.crypto={randomUUID:function(){return 'test-token-v80-uuid'}};
  window._saving=false;
`,sandbox2);

function setField(id,value){elRegistry[id]={value:value};}
function lastToast(){const t=sandbox2.__toasts;return t.length?t[t.length-1]:'';}
function clearToasts(){sandbox2.__toasts.length=0;}

(async function(){
  // ========== 优化1：租客登记必填校验 ==========
  // 合法基础字段
  setField('fTN','郭强');setField('fTRm','r1');setField('fTPM','月付');
  // T1 缺月租金
  clearToasts();
  setField('fTRa','');setField('fTMI','2026-01-01');setField('fTCE','2026-12-31');
  await vm.runInContext(`(async()=>{try{await doAddTenant()}catch(e){window.__addErr=e&&e.message}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,10));
  ok('T1 月租金为空→拦截提示', /租金/.test(lastToast()), lastToast());

  // T2 缺入住日期
  clearToasts();
  setField('fTRa','500');setField('fTMI','');setField('fTCE','2026-12-31');
  await vm.runInContext(`(async()=>{try{await doAddTenant()}catch(e){window.__addErr=e&&e.message}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,10));
  ok('T2 入住日期为空→拦截提示', /入住日期/.test(lastToast()), lastToast());

  // T3 缺合同到期
  clearToasts();
  setField('fTRa','500');setField('fTMI','2026-01-01');setField('fTCE','');
  await vm.runInContext(`(async()=>{try{await doAddTenant()}catch(e){window.__addErr=e&&e.message}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,10));
  ok('T3 合同到期为空→拦截提示', /合同到期/.test(lastToast()), lastToast());

  // T4 合同到期早于入住
  clearToasts();
  setField('fTRa','500');setField('fTMI','2026-06-01');setField('fTCE','2026-01-01');
  await vm.runInContext(`(async()=>{try{await doAddTenant()}catch(e){window.__addErr=e&&e.message}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,10));
  ok('T4 合同到期≤入住→拦截提示', /晚于入住/.test(lastToast()), lastToast());

  // T5 新增表单红星：入住/合同到期/租金 label 含 req
  const addHasStar=vm.runInContext(`(function(){try{showAddTenant();var h=window.__modalHtml||'';closeModal();return h}catch(e){return 'ERR:'+e.message}})()`,sandbox2);
  function starFor(html,id){const i=html.indexOf('id="'+id+'"');if(i<0)return false;return html.slice(i-120,i).indexOf('req')>=0;}
  ok('T5 新增租客弹窗 入住/到期/租金均带必填红星',
    addHasStar.indexOf('id="fTMI"')>=0&&starFor(addHasStar,'fTMI')&&starFor(addHasStar,'fTCE')&&starFor(addHasStar,'fTRa'),
    addHasStar.slice(0,50));

  // T6 doEditTenant 缺日期也拦截
  clearToasts();
  setField('fTN','郭强');setField('fTRm','r1');setField('fTPM','月付');
  setField('fTRa','500');setField('fTMI','');setField('fTCE','2026-12-31');
  await vm.runInContext(`(async()=>{try{await doEditTenant('t1')}catch(e){window.__editErr=e&&e.message}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,10));
  ok('T6 编辑租客 入住日期为空同样拦截', /入住日期/.test(lastToast()), lastToast()+' | '+(sandbox2.__editErr||''));

  // T7 i18n 新键中英齐全
  const keys=['tenant.needRent','tenant.needMoveIn','tenant.needContractEnd','tenant.contractAfterMoveIn','meter.editTitle','meter.editHint','meter.photoKeep','bill.scanTip'];
  const zhOk=keys.every(k=>{const v=vm.runInContext(`i18n.t('${k}')`,sandbox2);return v&&v.length>2&&v.indexOf(k)<0;});
  ok('T7 v80 新增中文文案齐全', zhOk===true, String(zhOk));
  vm.runInContext(`localStorage.setItem('lang','en')`,sandbox2);
  const enOk=keys.every(k=>{const v=vm.runInContext(`i18n.t('${k}')`,sandbox2);return v&&/[a-zA-Z]/.test(v)&&v.indexOf(k)<0;});
  vm.runInContext(`localStorage.setItem('lang','zh-CN')`,sandbox2);
  ok('T8 v80 新增英文文案齐全', enOk===true, String(enOk));

  // ========== 优化3：水电抄表编辑 ==========
  // T9 renderMeterList 输出含编辑按钮
  const listHtml=vm.runInContext(`renderMeterList('t1')`,sandbox2);
  ok('T9 抄表列表渲染含编辑按钮(showMeterEditModal)', listHtml.indexOf('showMeterEditModal')>=0, listHtml.slice(0,40));

  // T10 打开编辑弹窗，预填 m1 子表数据
  const editOpen=vm.runInContext(`(function(){try{showMeterEditModal('m1');var ctx=window._meterCtx;closeModal();return JSON.stringify({err:null,editId:ctx.editId,n:ctx.items.length,first:ctx.items[0]})}catch(e){return JSON.stringify({err:e.message})}})()`,sandbox2);
  const eo=JSON.parse(editOpen);
  ok('T10 编辑弹窗打开且editId=m1、预填1条抄表项', !eo.err&&eo.editId==='m1'&&eo.n===1, editOpen);
  ok('T11 预填值正确(冷水 cur=100/price=5/amount=100)', eo.first&&eo.first.kind==='cold_water'&&Number(eo.first.cur)===100&&Number(eo.first.price)===5&&Number(eo.first.amount)===100, JSON.stringify(eo.first));

  // T12 提交编辑 m1（模拟用户改成 cur=120），验证 update + 子表删旧插新
  // 重新打开并取 items id，预置 DOM 输入
  vm.runInContext(`showMeterEditModal('m1')`,sandbox2);
  const items1=JSON.parse(vm.runInContext(`JSON.stringify(window._meterCtx.items.map(function(x){return{id:x.id,type:x.type}}))`,sandbox2));
  items1.forEach(function(it){
    setField('mi_label_'+it.id,'冷水');
    if(it.type==='meter'){setField('mi_cur_'+it.id,'120');setField('mi_prev_'+it.id,'100');setField('mi_price_'+it.id,'5');setField('mi_amt_'+it.id,'100');}
    else setField('mi_amt_'+it.id,'');
  });
  setField('mDate','2026-09-10');setField('mNotes','已核对水表');
  clearToasts();
  await vm.runInContext(`(async()=>{try{window._meterPhotoPath=null;await doMeterUpdate('m1')}catch(e){window.__updErr=e&&(e.stack||e.message)}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,20));
  const m1after=JSON.parse(vm.runInContext(`JSON.stringify(__DB.meter_readings.find(function(r){return r.id==='m1'}))`,sandbox2));
  const itemsAfter=JSON.parse(vm.runInContext(`JSON.stringify(__DB.meter_items.filter(function(r){return r.reading_id==='m1'}))`,sandbox2));
  ok('T12 编辑保存后主表更新(日期/备注/金额)', m1after&&m1after.reading_date==='2026-09-10'&&m1after.notes==='已核对水表'&&Number(m1after.total_fee)===100, JSON.stringify(m1after)+' '+(sandbox2.__updErr||''));
  ok('T13 子表删旧重插=1条且cur=120', itemsAfter.length===1&&Number(itemsAfter[0].cur_reading)===120&&Number(itemsAfter[0].amount)===100, JSON.stringify(itemsAfter));

  // T14 已收记录 m2 编辑后同步 income_records
  vm.runInContext(`showMeterEditModal('m2')`,sandbox2);
  const items2=JSON.parse(vm.runInContext(`JSON.stringify(window._meterCtx.items.map(function(x){return{id:x.id,type:x.type}}))`,sandbox2));
  items2.forEach(function(it){
    setField('mi_label_'+it.id,'电表');
    if(it.type==='meter'){setField('mi_cur_'+it.id,'200');setField('mi_prev_'+it.id,'100');setField('mi_price_'+it.id,'2');setField('mi_amt_'+it.id,'200');}
    else setField('mi_amt_'+it.id,'');
  });
  setField('mDate','2026-08-05');setField('mNotes','');
  await vm.runInContext(`(async()=>{try{window._meterPhotoPath=null;await doMeterUpdate('m2')}catch(e){window.__updErr2=e&&(e.stack||e.message)}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,20));
  const inc=JSON.parse(vm.runInContext(`JSON.stringify(__DB.income_records.filter(function(r){return r.source==='meter'&&r.ref_id==='m2'}))`,sandbox2));
  ok('T14 已收抄表编辑后自动同步水电收入(¥200)', inc.length===1&&Number(inc[0].amount)===200&&inc[0].category==='utility', JSON.stringify(inc)+' '+(sandbox2.__updErr2||''));

  // ========== 优化2：账单图片内嵌二维码 + 备注入图 ==========
  // 预置账单弹窗 DOM
  setField('b_rent','500.00');
  ['b_cw_f','b_hw_f','b_el_f'].forEach(function(id){setField(id,'')});
  setField('b_note','请于本周内缴清水电费，谢谢配合！');
  elRegistry['b_other_rows']=(function(){const e=makeEl();e.children=[];e.querySelectorAll=function(){return[]};return e})();
  elRegistry['b_total']=makeEl();
  vm.runInContext(`window._billCtx={type:'tenant',id:'t1',tenant:cache.tenants[0],room:cache.rooms[0],bills:cache.rents};`,sandbox2);
  __ctxs.length=0;sandbox2.__qrCalls.length=0;
  await vm.runInContext(`(async()=>{try{await _billGenImage()}catch(e){window.__imgErr=e&&(e.stack||e.message)}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,400));
  const imgErr=sandbox2.__imgErr;
  if(imgErr)console.log('   [_billGenImage threw]',String(imgErr).slice(0,400));
  // T15 生成图片成功并弹出预览（含 data:image）
  const modalHtml=sandbox2.__modalHtml||'';
  ok('T15 账单图片生成成功并弹出预览', !imgErr&&modalHtml.indexOf('data:image')>=0, (imgErr||'').slice(0,120));
  // T16 二维码被绘制到画布（drawImage 被调用）
  const lastCtx=__ctxs[__ctxs.length-1];
  ok('T16 二维码已 drawImage 到账单画布', lastCtx&&lastCtx.__draws.length>=1, 'draws='+(lastCtx?lastCtx.__draws.length:'no-ctx'));
  // T17 扫码提示文案入图
  ok('T17 扫码提示文案绘制入图', lastCtx&&lastCtx.__texts.some(function(t){return t.indexOf('扫码')>=0||/scan/i.test(t)}), JSON.stringify(lastCtx?lastCtx.__texts.slice(-4):[]));
  // T18 备注文字绘制入图
  ok('T18 备注文字绘制入图', lastCtx&&lastCtx.__texts.some(function(t){return t.indexOf('请于本周内')>=0}), JSON.stringify(lastCtx?lastCtx.__texts.filter(function(t){return t.indexOf('备注')>=0||t.indexOf('请于')>=0}):[]));
  // T19 生成图片时已建分享链接(bill_shares)
  const shares=JSON.parse(vm.runInContext(`JSON.stringify(__DB.bill_shares)`,sandbox2));
  ok('T19 生成图片时创建账单分享记录', shares.length>=1, 'shares='+shares.length);
  ok('T20 分享链接含token且二维码内容指向billshare', (function(){const opt=sandbox2.__qrCalls[sandbox2.__qrCalls.length-1];return !!opt&&/billshare\.html\?token=test-token-v80/.test(opt.text)})(), JSON.stringify(sandbox2.__qrCalls[sandbox2.__qrCalls.length-1]));

  // T21 无二维码时（QRCode缺失且脚本加载失败）也能正常出图（降级不阻断）
  const qrBackup=sandbox2.window.QRCode;
  vm.runInContext(`window.QRCode=undefined;`,sandbox2);
  __ctxs.length=0;
  await vm.runInContext(`(async()=>{try{await _billGenImage()}catch(e){window.__imgErr2=e&&(e.stack||e.message)}})()`,sandbox2);
  await new Promise(r=>setTimeout(r,300));
  const ok2=!sandbox2.__imgErr2&&(sandbox2.__modalHtml||'').indexOf('data:image')>=0;
  ok('T21 二维码库缺失时降级仍能生成图片', ok2, (sandbox2.__imgErr2||'').slice(0,120));
  sandbox2.window.QRCode=qrBackup;

  // ========== 静态/版本 ==========
  const swTxt=fs.readFileSync(APP.replace(/app\.html$/,'sw.js'),'utf8');
  ok('T22 sw 版本升级到 fangdong-v80', swTxt.indexOf('fangdong-v80')>=0, '');
  ok('T23 app.html 引用 i18n.js?v=80', html.indexOf('i18n.js?v=80')>=0, '');

  console.log('\n===== v80结果: '+pass+' 通过 / '+fail+' 失败 =====');
  process.exit(fail>0?1:0);
})().catch(e=>{console.log('❌ 测试异常:',e.stack);process.exit(1)});
