#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
P="i18n.js"
s=io.open(P,encoding="utf-8").read()

ZH = {
"comm.title":"员工提成","comm.hint":"中介老板专用：给成交员工算提成。普通房东不用开，可在设置里关闭。",
"comm.reportTab":"提成报表","comm.staffTab":"员工管理","comm.staffName":"员工姓名","comm.recCount":"笔数",
"comm.monthTotal":"当月提成","comm.settled":"已结算","comm.unsettled":"未结算","comm.allStatus":"全部状态",
"comm.noDataMonth":"本月暂无提成流水","comm.noDataHint":"在「租客管理」给租约选成交员工并设置提成规则后，系统会自动按月生成流水。",
"comm.staffSummary":"员工提成汇总","comm.detail":"提成明细","comm.settleAll":"全部标记已结算","comm.export":"导出Excel",
"comm.rule":"提成规则","comm.base":"计提基数","comm.amount":"提成金额","comm.modeOnetime":"一次性提成",
"comm.modeMonthly":"按月计提","comm.basisReceived":"按实收租金","comm.basisEffective":"按租约生效",
"comm.staffGone":"员工已删除","comm.noStaff":"未指定员工","comm.staffList":"员工列表","comm.addStaff":"添加员工",
"comm.editStaff":"编辑员工","comm.staffNamePh":"如：小王","comm.staffActive":"在职","comm.staffInactive":"已停用",
"comm.staffDeactivate":"停用","comm.staffActivate":"启用","comm.enterStaffName":"请填写员工姓名",
"comm.delStaffConfirm":"确定删除该员工？","comm.delStaffSub":"该员工名下租约的提成配置会保留，可重新指定其他员工。",
"comm.selectStaff":"选择成交员工（无则不提成）","comm.leaseTitle":"成交员工与提成","comm.dealStaff":"成交员工",
"comm.mode":"提成方式","comm.basis":"计提规则","comm.rateType":"计算方式","comm.ratePercent":"按比例（%）",
"comm.rateFixed":"固定金额（元）","comm.ratePercentLabel":"提成比例（%）","comm.rateFixedLabel":"固定提成（元）",
"comm.ratePh":"如 50 表示 50%，100 表示 100 元","comm.hintMonthlyEff":"按月计提：按租约生效月起每月生成提成，退租自动停止。",
"comm.hintMonthlyRecv":"按月计提：租客实际收到租金的月份才生成提成。","comm.hintOnetime":"一次性提成：按入住月生成一笔，之后不再产生。",
"comm.markSettled":"标记已结算","comm.markUnsettled":"标记未结算","comm.settledDone":"已标记为已结算",
"comm.unsettledDone":"已改为未结算","comm.noUnsettled":"当前没有待结算的提成","comm.settleAllConfirm":"确定把本月 {n} 笔未结算提成全部标记为已结算？","comm.settleAllSub":"月份：{m}。标记后可在明细里单笔改回未结算。",
"comm.delRecConfirm":"确定删除这条提成流水？","comm.oneTimeNote":"一次性成交提成",
"comm.recvNote":"按实收租金计提","comm.effNote":"按月计提（租约生效期间）","comm.exportFileName":"员工提成报表_{m}",
"comm.enableModule":"启用员工提成模块","comm.settingDesc":"开启后，侧边栏显示「员工提成」，租客登记里可设置成交员工与提成规则。普通房东保持关闭即可。",
"comm.enabled":"已开启员工提成模块","comm.disabled":"已关闭员工提成模块","comm.noStaffHint":"先添加员工，再在租客资料里给租约指定成交员工。",
}
EN = {
"comm.title":"Staff Commission","comm.hint":"For agencies: pay commission to the staff who closed a lease. Regular landlords can leave it off in Settings.",
"comm.reportTab":"Report","comm.staffTab":"Staff","comm.staffName":"Staff","comm.recCount":"Records",
"comm.monthTotal":"This month","comm.settled":"Settled","comm.unsettled":"Unsettled","comm.allStatus":"All status",
"comm.noDataMonth":"No commission this month","comm.noDataHint":"Assign a deal staff and set commission rules in a tenant's profile; the system then generates monthly records automatically.",
"comm.staffSummary":"Staff summary","comm.detail":"Details","comm.settleAll":"Mark all settled","comm.export":"Export Excel",
"comm.rule":"Rule","comm.base":"Base","comm.amount":"Commission","comm.modeOnetime":"One-time",
"comm.modeMonthly":"Monthly","comm.basisReceived":"By rent received","comm.basisEffective":"By lease active",
"comm.staffGone":"Staff deleted","comm.noStaff":"No staff","comm.staffList":"Staff","comm.addStaff":"Add staff",
"comm.editStaff":"Edit staff","comm.staffNamePh":"e.g. Tom","comm.staffActive":"Active","comm.staffInactive":"Inactive",
"comm.staffDeactivate":"Disable","comm.staffActivate":"Enable","comm.enterStaffName":"Please enter staff name",
"comm.delStaffConfirm":"Delete this staff member?","comm.delStaffSub":"Their lease commission rules are kept and can be reassigned to another staff member.",
"comm.selectStaff":"Select deal staff (none = no commission)","comm.leaseTitle":"Deal staff & commission","comm.dealStaff":"Deal staff",
"comm.mode":"Commission type","comm.basis":"Basis","comm.rateType":"Calculation","comm.ratePercent":"Percentage (%)",
"comm.rateFixed":"Fixed amount","comm.ratePercentLabel":"Commission rate (%)","comm.rateFixedLabel":"Fixed commission",
"comm.ratePh":"50 = 50%, or 100 = 100 (fixed)","comm.hintMonthlyEff":"Monthly: a record is generated every month from lease start until move-out.",
"comm.hintMonthlyRecv":"Monthly: a record is generated only in months when rent is actually received.",
"comm.hintOnetime":"One-time: a single record on the move-in month, nothing after.",
"comm.markSettled":"Mark settled","comm.markUnsettled":"Mark unsettled","comm.settledDone":"Marked as settled",
"comm.unsettledDone":"Marked as unsettled","comm.noUnsettled":"No unsettled commission",
"comm.settleAllConfirm":"Mark all {n} unsettled records of this month as settled?","comm.settleAllSub":"Month: {m}. You can revert individual records later.",
"comm.delRecConfirm":"Delete this commission record?","comm.oneTimeNote":"One-time deal commission",
"comm.recvNote":"By rent received","comm.effNote":"Monthly (during active lease)","comm.exportFileName":"staff_commission_{m}",
"comm.enableModule":"Enable Staff Commission","comm.settingDesc":"When on, 'Staff Commission' appears in the sidebar and lease commission can be set in tenant profiles. Regular landlords can keep it off.",
"comm.enabled":"Staff commission enabled","comm.disabled":"Staff commission disabled","comm.noStaffHint":"Add staff first, then assign a deal staff in a tenant's profile.",
}

def block(lang, d):
    lines=["    // ===== v76 提成模块 ====="]
    for k,v in d.items():
        v=v.replace('\\','\\\\').replace('"','\\"')
        lines.append('    "%s": "%s",'%(k,v))
    return "\n".join(lines)+"\n"

zh_anchor='    "fin.viewMeterHint": "水电抄表记录在「房租管理」页上方",\n'
en_anchor='    "fin.viewMeterHint": "Meter readings are at the top of Rent page",\n'
assert s.count(zh_anchor)==1, "zh anchor %d"%s.count(zh_anchor)
assert s.count(en_anchor)==1, "en anchor %d"%s.count(en_anchor)
s=s.replace(zh_anchor, zh_anchor+block("zh",ZH),1)
s=s.replace(en_anchor, en_anchor+block("en",EN),1)
io.open(P,"w",encoding="utf-8").write(s)
print("i18n keys zh=%d en=%d inserted"%(len(ZH),len(EN)))
