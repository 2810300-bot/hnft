/* ================================================
   湖南伏泰 HR 人事管理系统 - 应用逻辑 v1.0
   ================================================ */

// ========== 全局状态 ==========
const MODULE_TITLES = {
  'dashboard': '总览仪表盘',
  'roster': '员工花名册',
  'hr-events': '入离职管理',
  'attendance': '考勤管理',
  'salary': '薪酬管理'
};

let currentModule = 'dashboard';
let salaryUnlocked = false;
let chartInstances = {};

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('syncTime').textContent = hrMeta.lastSyncTime;
  document.getElementById('dbSyncTime').textContent = hrMeta.lastSyncTime;
  renderDashboard();
  populateFilters();
});

// ========== 模块切换 ==========
function switchModule(moduleId) {
  currentModule = moduleId;

  // 更新导航
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  document.querySelector(`[data-module="${moduleId}"]`).classList.add('active');

  // 更新标题
  document.getElementById('module-title').textContent = MODULE_TITLES[moduleId] || moduleId;

  // 切换面板
  document.querySelectorAll('.module-panel').forEach(el => el.classList.remove('active'));
  const panel = document.getElementById('panel-' + moduleId);
  if (panel) panel.classList.add('active');

  // 渲染各模块
  switch (moduleId) {
    case 'dashboard': renderDashboard(); break;
    case 'roster': renderRoster(); break;
    case 'hr-events': renderEvents(); break;
    case 'attendance': renderAttendanceModule(); break;
    case 'salary':
      if (salaryUnlocked) renderSalary();
      break;
  }
}

// ========== 侧边栏切换 ==========
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('collapsed');
}

// ========== Toast 通知 ==========
const Toast = {
  show(msg, type) {
    const c = document.getElementById('toastContainer');
    const el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.innerHTML = '<span>' + msg + '</span>';
    c.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 3000);
  }
};

// ========== 填充筛选下拉 ==========
function populateFilters() {
  const depts = [...new Set(employees.map(e => e.department))];
  const deptSelect = document.getElementById('filterDept');
  depts.forEach(d => { const o = document.createElement('option'); o.value = d; o.textContent = d; deptSelect.appendChild(o); });

  const empSelect = document.getElementById('attDailyEmployee');
  employees.forEach(e => { const o = document.createElement('option'); o.value = e.id; o.textContent = e.name; empSelect.appendChild(o); });
}

// ================================================================
//  模块1: 总览仪表盘
// ================================================================
function renderDashboard() {
  renderDashboardStats();
  renderDashboardAlerts();
  renderDeptPieChart();
  renderAttendanceBar();
  renderSalaryTrend();
}

function renderDashboardStats() {
  const active = employees.filter(e => e.status !== '离职').length;
  const probation = employees.filter(e => e.status === '试用期').length;
  const departed = employees.filter(e => e.status === '离职').length;

  // 本月入职/离职
  const now = new Date(); const m = now.getMonth() + 1; const y = now.getFullYear();
  const monthOnboard = hrEvents.filter(e => {
    const d = new Date(e.date);
    return e.type === '入职' && d.getMonth() + 1 === m && d.getFullYear() === y;
  }).length;
  const monthOffboard = hrEvents.filter(e => {
    const d = new Date(e.date);
    return e.type === '离职' && d.getMonth() + 1 === m && d.getFullYear() === y;
  }).length;

  // 合同即将到期（30天内）
  const expiring = employees.filter(e => {
    if (e.status === '离职') return false;
    const end = new Date(e.contractEnd);
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    return diff <= 30 && diff >= 0;
  }).length;

  document.getElementById('dashboardStats').innerHTML = `
    <div class="stat-card"><div class="stat-icon stat-blue">&#128101;</div><div class="stat-info"><span class="stat-value">${active}</span><span class="stat-label">在职人数</span></div></div>
    <div class="stat-card"><div class="stat-icon stat-green">&#10133;</div><div class="stat-info"><span class="stat-value">${monthOnboard}</span><span class="stat-label">本月入职</span></div></div>
    <div class="stat-card"><div class="stat-icon stat-red">&#10134;</div><div class="stat-info"><span class="stat-value">${monthOffboard}</span><span class="stat-label">本月离职</span></div></div>
    <div class="stat-card"><div class="stat-icon stat-orange">&#9888;</div><div class="stat-info"><span class="stat-value">${expiring}</span><span class="stat-label">合同即将到期</span></div></div>
  `;
}

function renderDashboardAlerts() {
  const container = document.getElementById('dashboardAlerts');
  const now = new Date();

  const alerts = [];

  // 合同到期预警
  employees.filter(e => e.status !== '离职').forEach(e => {
    const end = new Date(e.contractEnd);
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    if (diff <= 90 && diff >= 0) {
      alerts.push({
        type: '合同到期', name: e.name, days: diff,
        msg: `劳动合同将于 ${e.contractEnd} 到期`,
        urgent: diff <= 30
      });
    }
  });

  // 试用期到期提醒
  employees.filter(e => e.status === '试用期' && e.probationEnd).forEach(e => {
    const end = new Date(e.probationEnd);
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    if (diff <= 30 && diff >= 0) {
      alerts.push({
        type: '试用期', name: e.name, days: diff,
        msg: `试用期将于 ${e.probationEnd} 结束`,
        urgent: diff <= 7
      });
    }
  });

  if (alerts.length === 0) {
    container.innerHTML = '<div style="text-align:center;padding:24px;color:var(--gray-400)">暂无待办提醒 &#10003;</div>';
    return;
  }

  container.innerHTML = alerts.map(a => `
    <div class="alert-item ${a.urgent ? 'urgent' : ''}">
      <div class="alert-icon">${a.type === '合同到期' ? '&#128196;' : '&#127891;'}</div>
      <div class="alert-info">
        <div class="alert-name">${a.name} - ${a.type}</div>
        <div class="alert-msg">${a.msg}</div>
      </div>
      <div class="alert-days">${a.days}<small> 天</small></div>
    </div>
  `).join('');
}

// ========== 图表: 部门分布饼图 ==========
function renderDeptPieChart() {
  destroyChart('chartDeptPie');
  const deptCount = {};
  employees.filter(e => e.status !== '离职').forEach(e => {
    deptCount[e.department] = (deptCount[e.department] || 0) + 1;
  });

  const labels = Object.keys(deptCount);
  const data = Object.values(deptCount);
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

  const ctx = document.getElementById('chartDeptPie').getContext('2d');
  chartInstances['chartDeptPie'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels, datasets: [{ data, backgroundColor: colors.slice(0, labels.length), borderWidth: 0 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, font: { size: 13 } } }
      }
    }
  });
}

// ========== 图表: 考勤概览柱状图 ==========
function renderAttendanceBar() {
  destroyChart('chartAttendanceBar');
  const labels = attendanceSummary.records.map(r => r.employeeName);
  const normalData = attendanceSummary.records.map(r => r.actualDays - r.leaveCount);
  const lateData = attendanceSummary.records.map(r => r.lateCount);
  const leaveData = attendanceSummary.records.map(r => r.leaveCount);

  const ctx = document.getElementById('chartAttendanceBar').getContext('2d');
  chartInstances['chartAttendanceBar'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: '正常出勤', data: normalData, backgroundColor: '#10b981' },
        { label: '迟到', data: lateData, backgroundColor: '#f59e0b' },
        { label: '请假', data: leaveData, backgroundColor: '#94a3b8' }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { x: { stacked: true }, y: { stacked: true, max: 25 } },
      plugins: { legend: { position: 'bottom' } }
    }
  });
}

// ========== 图表: 薪酬趋势（模拟） ==========
function renderSalaryTrend() {
  destroyChart('chartSalaryTrend');
  const months = ['1月', '2月', '3月', '4月', '5月', '6月'];
  // 模拟月度数据
  const totalGross = [95000, 92000, 98000, 96000, 99000, salaryData.summary.totalGross];
  const totalNet = [83000, 81000, 86000, 84000, 87000, salaryData.summary.totalNet];

  const ctx = document.getElementById('chartSalaryTrend').getContext('2d');
  chartInstances['chartSalaryTrend'] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        { label: '应发总额', data: totalGross, borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.1)', fill: true, tension: 0.3 },
        { label: '实发总额', data: totalNet, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', fill: true, tension: 0.3 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } },
      scales: { y: { ticks: { callback: v => '¥' + (v / 10000).toFixed(1) + '万' } } }
    }
  });
}

// ================================================================
//  模块2: 员工花名册
// ================================================================
function renderRoster() {
  const dept = document.getElementById('filterDept').value;
  const status = document.getElementById('filterStatus').value;
  const search = document.getElementById('searchEmployee').value.toLowerCase();

  let filtered = employees;
  if (dept) filtered = filtered.filter(e => e.department === dept);
  if (status) filtered = filtered.filter(e => e.status === status);
  if (search) filtered = filtered.filter(e =>
    e.name.includes(search) || e.position.includes(search) || e.phone.includes(search) || e.department.includes(search)
  );

  document.getElementById('rosterTableBody').innerHTML = filtered.map(e => `
    <tr onclick="showEmployeeDetail('${e.id}')">
      <td style="font-weight:600;color:var(--dark)">${e.name}</td>
      <td>${e.department}</td>
      <td>${e.position}</td>
      <td>${e.phone}</td>
      <td>${e.hireDate}</td>
      <td>${e.contractEnd || '--'}</td>
      <td><span class="status-badge ${e.status === '在职' ? 'active' : e.status === '试用期' ? 'probation' : 'departed'}">${e.status}</span></td>
      <td><button class="btn btn-sm btn-outline" onclick="event.stopPropagation();showEmployeeDetail('${e.id}')">详情</button></td>
    </tr>
  `).join('');

  if (filtered.length === 0) {
    document.getElementById('rosterTableBody').innerHTML = '<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--gray-400)">无匹配员工</td></tr>';
  }
}

function showEmployeeDetail(id) {
  const e = employees.find(emp => emp.id === id);
  if (!e) return;

  const statusLabel = e.status === '在职' ? 'active' : e.status === '试用期' ? 'probation' : 'departed';
  const syncTag = e.dingtalkUserId ? '<span style="font-size:11px;background:rgba(6,182,212,0.1);color:#06b6d4;padding:2px 6px;border-radius:4px">钉钉已同步</span>' : '';

  document.getElementById('detailContent').innerHTML = `
    <div class="detail-avatar">${e.name[0]}</div>
    <div class="detail-name">${e.name} ${syncTag}</div>
    <div class="detail-dept">${e.department} · ${e.position} · <span class="status-badge ${statusLabel}">${e.status}</span></div>

    <div class="detail-section">
      <h4>基本信息</h4>
      <div class="detail-grid">
        <div class="detail-item"><span class="dl">性别</span><span class="dv">${e.gender}</span></div>
        <div class="detail-item"><span class="dl">出生日期</span><span class="dv">${e.birthDate}</span></div>
        <div class="detail-item"><span class="dl">学历</span><span class="dv">${e.education}</span></div>
        <div class="detail-item"><span class="dl">毕业院校</span><span class="dv">${e.school || '--'}</span></div>
        <div class="detail-item"><span class="dl">专业</span><span class="dv">${e.major || '--'}</span></div>
        <div class="detail-item"><span class="dl">身份证号</span><span class="dv">${e.idNumber}</span></div>
      </div>
    </div>

    <div class="detail-section">
      <h4>工作信息</h4>
      <div class="detail-grid">
        <div class="detail-item"><span class="dl">部门</span><span class="dv">${e.department}</span></div>
        <div class="detail-item"><span class="dl">职位</span><span class="dv">${e.position}</span></div>
        <div class="detail-item"><span class="dl">入职日期</span><span class="dv">${e.hireDate}</span></div>
        <div class="detail-item"><span class="dl">转正日期</span><span class="dv">${e.probationEnd || '--'}</span></div>
        <div class="detail-item"><span class="dl">合同起</span><span class="dv">${e.contractStart || '--'}</span></div>
        <div class="detail-item"><span class="dl">合同止</span><span class="dv">${e.contractEnd || '--'}</span></div>
      </div>
    </div>

    <div class="detail-section">
      <h4>联系方式</h4>
      <div class="detail-grid">
        <div class="detail-item"><span class="dl">手机</span><span class="dv">${e.phone}</span></div>
        <div class="detail-item"><span class="dl">邮箱</span><span class="dv">${e.email || '--'}</span></div>
        <div class="detail-item" style="grid-column:1/-1"><span class="dl">紧急联系人</span><span class="dv">${e.emergencyContact || '--'}</span></div>
      </div>
    </div>

    <div class="detail-section">
      <h4>薪酬信息</h4>
      <div class="detail-grid">
        <div class="detail-item"><span class="dl">社保基数</span><span class="dv">¥${(e.socialSecurityBase || 0).toLocaleString()}</span></div>
        <div class="detail-item"><span class="dl">工资卡</span><span class="dv">${e.bankAccount || '--'}</span></div>
      </div>
    </div>

    ${e.notes ? `<div class="detail-section"><h4>备注</h4><p style="font-size:14px;color:var(--gray-500)">${e.notes}</p></div>` : ''}
  `;

  document.getElementById('detailPanel').classList.add('open');
}

function closeDetailPanel() {
  document.getElementById('detailPanel').classList.remove('open');
}

function exportContacts() {
  const lines = ['姓名,部门,职位,手机号,邮箱'];
  employees.filter(e => e.status !== '离职').forEach(e => {
    lines.push(`${e.name},${e.department},${e.position},${e.phone},${e.email || ''}`);
  });
  const text = lines.join('\n');
  navigator.clipboard.writeText(text).then(() => {
    Toast.show('通讯录已复制到剪贴板', 'success');
  }).catch(() => {
    Toast.show('复制失败，请手动操作', 'error');
  });
}

// ================================================================
//  模块3: 入离职管理
// ================================================================
function renderEvents() {
  const type = document.getElementById('filterEventType').value;
  let events = [...hrEvents].sort((a, b) => new Date(b.date) - new Date(a.date));
  if (type) events = events.filter(e => e.type === type);

  // 更新本月统计
  const now = new Date(); const m = now.getMonth() + 1; const y = now.getFullYear();
  document.getElementById('monthOnboard').textContent = hrEvents.filter(e => {
    const d = new Date(e.date);
    return e.type === '入职' && d.getMonth() + 1 === m && d.getFullYear() === y;
  }).length;
  document.getElementById('monthOffboard').textContent = hrEvents.filter(e => {
    const d = new Date(e.date);
    return e.type === '离职' && d.getMonth() + 1 === m && d.getFullYear() === y;
  }).length;

  const typeClass = {
    '入职': '入职',
    '转正': '转正',
    '离职': '离职',
    '调岗': '调岗'
  };

  document.getElementById('eventsTimeline').innerHTML = events.map(ev => {
    const emp = employees.find(e => e.id === ev.employeeId);
    return `
    <div class="timeline-item type-${ev.type}">
      <div class="tl-header">
        <span class="tl-date">${ev.date}</span>
        <span class="tl-type ${typeClass[ev.type] || ''}">${ev.type}</span>
      </div>
      <div class="tl-name">${emp ? emp.name : '--'}</div>
      <div class="tl-desc">${ev.description}</div>
    </div>
  `}).join('');

  if (events.length === 0) {
    document.getElementById('eventsTimeline').innerHTML = '<div style="text-align:center;padding:32px;color:var(--gray-400)">无入离职记录</div>';
  }
}

// ================================================================
//  模块4: 考勤管理
// ================================================================
function renderAttendanceModule() {
  renderMonthlyAttendance();
}

function switchAttTab(tab) {
  document.querySelectorAll('.att-tab').forEach(el => el.classList.remove('active'));
  event.target.classList.add('active');

  document.getElementById('attMonthlyPanel').style.display = tab === 'monthly' ? 'block' : 'none';
  document.getElementById('attDailyPanel').style.display = tab === 'daily' ? 'block' : 'none';

  if (tab === 'daily') renderDailyAttendance();
}

function renderMonthlyAttendance() {
  const records = attendanceSummary.records;

  // 统计卡片
  const avgRate = (records.reduce((s, r) => s + r.attendanceRate, 0) / records.length).toFixed(1);
  document.getElementById('attAvgRate').textContent = avgRate + '%';
  document.getElementById('attTotalLate').textContent = records.reduce((s, r) => s + r.lateCount, 0);
  document.getElementById('attTotalAbsent').textContent = records.reduce((s, r) => s + r.absentCount, 0);
  document.getElementById('attTotalOT').textContent = records.reduce((s, r) => s + r.overtimeHours, 0) + 'h';

  document.getElementById('attMonthlyBody').innerHTML = records.map(r => {
    const rateClass = r.attendanceRate >= 100 ? 'attendance-rate' :
      r.attendanceRate >= 90 ? 'attendance-rate warn' : 'attendance-rate danger';

    return `
    <tr>
      <td style="font-weight:600;color:var(--dark)">${r.employeeName}</td>
      <td>${r.department}</td>
      <td>${r.workDays}</td>
      <td>${r.actualDays}</td>
      <td>${r.lateCount > 0 ? '<span class="badge warn">' + r.lateCount + '</span>' : '0'}</td>
      <td>${r.earlyCount > 0 ? '<span class="badge warn">' + r.earlyCount + '</span>' : '0'}</td>
      <td>${r.absentCount > 0 ? '<span class="badge danger">' + r.absentCount + '</span>' : '0'}</td>
      <td>${r.leaveCount > 0 ? '<span class="badge warn">' + r.leaveCount + '</span>' : '0'}</td>
      <td>${r.overtimeHours}</td>
      <td>${r.businessTravelDays}</td>
      <td class="${rateClass}">${r.attendanceRate}%</td>
    </tr>
  `}).join('');
}

function renderDailyAttendance() {
  const empId = document.getElementById('attDailyEmployee').value;
  const status = document.getElementById('attDailyStatus').value;

  let records = [...attendanceDaily].sort((a, b) => new Date(b.date) - new Date(a.date));
  if (empId) records = records.filter(r => r.employeeId === empId);
  if (status) records = records.filter(r => r.status === status);

  document.getElementById('attDailyBody').innerHTML = records.map(r => {
    const emp = employees.find(e => e.id === r.employeeId);
    const statusBadge = r.status === '正常' ? 'ok' : r.status === '迟到' || r.status === '早退' ? 'warn' : 'danger';
    return `
    <tr>
      <td>${r.date}</td>
      <td>${emp ? emp.name : r.employeeId}</td>
      <td>${r.checkIn}</td>
      <td>${r.checkOut}</td>
      <td><span class="badge ${statusBadge}">${r.status}</span></td>
      <td>${r.location}</td>
      <td style="color:var(--gray-500);font-size:13px">${r.notes || '--'}</td>
    </tr>
  `}).join('');

  if (records.length === 0) {
    document.getElementById('attDailyBody').innerHTML = '<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--gray-400)">无考勤记录</td></tr>';
  }
}

// ================================================================
//  模块5: 薪酬管理
// ================================================================
function unlockSalary() {
  const pwd = document.getElementById('salaryPwd').value;
  // 默认密码: hr2026
  if (pwd === 'hr2026') {
    salaryUnlocked = true;
    document.getElementById('salaryLock').style.display = 'none';
    document.getElementById('salaryContent').style.display = 'block';
    document.getElementById('salaryPwd').value = '';
    renderSalary();
    Toast.show('薪酬数据已解锁', 'success');
  } else {
    Toast.show('密码错误', 'error');
  }
}

function renderSalary() {
  if (!salaryUnlocked) return;

  // 统计摘要
  const s = salaryData.summary;
  document.getElementById('salarySummary').innerHTML = `
    <div class="salary-stat"><div class="ss-value">¥${(s.totalGross / 10000).toFixed(2)}万</div><div class="ss-label">应发总额</div></div>
    <div class="salary-stat"><div class="ss-value">¥${(s.totalNet / 10000).toFixed(2)}万</div><div class="ss-label">实发总额</div></div>
    <div class="salary-stat"><div class="ss-value">¥${s.avgNet.toLocaleString()}</div><div class="ss-label">人均实发</div></div>
    <div class="salary-stat"><div class="ss-value">¥${(s.totalDeduction / 10000).toFixed(2)}万</div><div class="ss-label">扣款总额</div></div>
  `;

  // 薪酬明细表
  document.getElementById('salaryTableBody').innerHTML = salaryData.records.map(r => `
    <tr>
      <td style="font-weight:600;color:var(--dark)">${r.employeeName}</td>
      <td>${r.department}</td>
      <td>${r.baseSalary.toLocaleString()}</td>
      <td>${r.positionAllowance.toLocaleString()}</td>
      <td>${r.performanceBonus.toLocaleString()}</td>
      <td>${r.overtimePay.toLocaleString()}</td>
      <td>${r.mealAllowance}</td>
      <td>${r.transportAllowance}</td>
      <td>${r.otherAllowance}</td>
      <td style="font-weight:600;color:var(--primary)">${r.grossPay.toLocaleString()}</td>
      <td>${r.socialSecurity.toLocaleString()}</td>
      <td>${r.housingFund.toLocaleString()}</td>
      <td>${r.incomeTax.toLocaleString()}</td>
      <td>${r.otherDeduction}</td>
      <td style="color:var(--danger)">-${r.totalDeduction.toLocaleString()}</td>
      <td style="font-weight:700;color:var(--success)">${r.netPay.toLocaleString()}</td>
    </tr>
  `).join('');

  // 图表
  renderSalaryDeptBar();
  renderSalaryCompositionPie();
}

function renderSalaryDeptBar() {
  destroyChart('chartSalaryDept');
  const deptSalary = {};
  salaryData.records.forEach(r => {
    deptSalary[r.department] = (deptSalary[r.department] || 0) + r.netPay;
  });

  const ctx = document.getElementById('chartSalaryDept').getContext('2d');
  chartInstances['chartSalaryDept'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Object.keys(deptSalary),
      datasets: [{ label: '实发工资合计', data: Object.values(deptSalary), backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444'] }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { ticks: { callback: v => '¥' + (v / 10000).toFixed(1) + '万' } } }
    }
  });
}

function renderSalaryCompositionPie() {
  destroyChart('chartSalaryComposition');
  const totalBase = salaryData.records.reduce((s, r) => s + r.baseSalary, 0);
  const totalAllowance = salaryData.records.reduce((s, r) => s + r.positionAllowance, 0);
  const totalBonus = salaryData.records.reduce((s, r) => s + r.performanceBonus, 0);
  const totalOT = salaryData.records.reduce((s, r) => s + r.overtimePay, 0);
  const totalSubsidy = salaryData.records.reduce((s, r) => s + r.mealAllowance + r.transportAllowance + r.otherAllowance, 0);

  const ctx = document.getElementById('chartSalaryComposition').getContext('2d');
  chartInstances['chartSalaryComposition'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['基本工资', '岗位津贴', '绩效奖金', '加班费', '各类补贴'],
      datasets: [{ data: [totalBase, totalAllowance, totalBonus, totalOT, totalSubsidy], backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'], borderWidth: 0 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, font: { size: 13 } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ¥${ctx.raw.toLocaleString()} (${((ctx.raw / salaryData.summary.totalGross) * 100).toFixed(1)}%)` } }
      }
    }
  });
}

// ========== 辅助: 销毁图表 ==========
function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}
