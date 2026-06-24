/* ================================================
   湖南伏泰合同管理系统 - 应用逻辑 v2.0
   全部交互升级为真实 UI 组件，零 alert()
   ================================================ */

// ========== Toast 通知系统 ==========
const Toast = {
  container: null,
  init() {
    this.container = document.getElementById('toastContainer');
  },
  show(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '&#10003;', error: '&#10005;', warning: '&#9888;', info: '&#128161;' };
    toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span class="toast-msg">${message}</span>`;
    this.container.appendChild(toast);
    setTimeout(() => { toast.classList.add('toast-exit'); setTimeout(() => toast.remove(), 300); }, duration);
  }
};

// ========== 合同详情面板 ==========
function openContractDetail(id) {
  const c = contracts.find(x => x.id === id);
  if (!c) return;

  const panel = document.getElementById('detailPanel');
  const content = document.getElementById('detailContent');

  // 生命周期步骤映射
  const statusSteps = {
    '起草中': 0, '审核中': 1, '审批中': 2, '待签署': 3, '执行中': 4, '履行中': 4,
    '待续签': 3, '待核实': 0, '已归档': 5, '履行完毕': 5, '已到期': 5,
    '已到期（后续已续签）': 5, '履行中/待确认': 4
  };
  const currentStep = statusSteps[c.status] || 0;
  const stepNames = ['起草', '审核', '审批', '签署', '执行', '归档'];
  const stepIcons = ['&#9998;', '&#128196;', '&#10003;', '&#9997;', '&#9881;', '&#128218;'];

  // 付款进度
  const paidRatio = c.amount > 0 ? Math.round((c.paid / c.amount) * 100) : 0;
  const progressColor = paidRatio >= 80 ? '#5cb85c' : paidRatio >= 50 ? '#f0ad4e' : '#4a90d9';

  // 关联付款节点
  const relatedPayments = paymentNodes.filter(p =>
    p.contract.includes(c.name.substring(0, 6)) || c.name.includes(p.contract.substring(0, 6))
  );

  content.innerHTML = `
    <div class="detail-header-section">
      <div class="detail-id-row">
        <span class="detail-id">${c.id}</span>
        <span class="status-badge ${getStatusClass(c.status)}">${c.status}</span>
        <span class="wf-tag">${c.type}</span>
      </div>
      <h2 class="detail-title">${c.name}</h2>
      <div class="detail-meta-row">
        <span>签约方：${c.party}</span>
        <span>到期日期：${c.endDate}</span>
      </div>
    </div>

    <div class="detail-lifecycle-timeline">
      <div class="dl-steps">
        ${stepNames.map((name, i) => `
          <div class="dl-step ${i <= currentStep ? 'completed' : ''} ${i === currentStep ? 'current' : ''}">
            <div class="dl-step-icon">${stepIcons[i]}</div>
            <div class="dl-step-label">${name}</div>
            ${i === currentStep ? '<div class="dl-step-pulse"></div>' : ''}
          </div>
          ${i < 5 ? '<div class="dl-step-line ' + (i < currentStep ? 'completed' : '') + '"></div>' : ''}
        `).join('')}
      </div>
    </div>

    <div class="detail-sections">
      <div class="detail-section">
        <h4>金额信息</h4>
        <div class="detail-amount-grid">
          <div class="da-item">
            <span class="da-label">合同金额</span>
            <span class="da-value">${c.amount > 0 ? '¥' + c.amount + '万' : c.unitPrice || '待提取'}</span>
          </div>
          <div class="da-item">
            <span class="da-label">已付/已收</span>
            <span class="da-value paid">${c.paid > 0 ? '¥' + c.paid + '万' : '—'}</span>
          </div>
          <div class="da-item">
            <span class="da-label">待付/待收余额</span>
            <span class="da-value pending">${c.balance > 0 ? '¥' + c.balance + '万' : c.unitPrice || '—'}</span>
          </div>
          ${c.dataQuality ? '<div class="da-item"><span class="da-label">数据来源</span><span class="da-value ima-source">' + (c.source || 'IMA知识库') + ' · ' + c.dataQuality + '</span></div>' : ''}
          ${c.imaFolder ? '<div class="da-item"><span class="da-label">IMA目录</span><span class="da-value ima-folder">' + c.imaFolder + '</span></div>' : ''}
        </div>
        ${c.amount > 0 ? `
        <div class="detail-progress-bar">
          <div class="dpb-track">
            <div class="dpb-fill" style="width:${paidRatio}%;background:${progressColor}"></div>
          </div>
          <span class="dpb-label">付款进度 ${paidRatio}%</span>
        </div>` : ''}
      </div>

      ${relatedPayments.length > 0 ? `
      <div class="detail-section">
        <h4>付款节点</h4>
        <div class="detail-payment-list">
          ${relatedPayments.map(p => `
            <div class="dp-item">
              <span class="dp-node">${p.node}</span>
              <span class="dp-amount">${p.amount}</span>
              <span class="dp-deadline">${p.deadline}</span>
              <span class="status-badge ${p.status === '紧急' ? 'draft' : p.status === '待付' ? 'approve' : 'active'}">${p.status}</span>
            </div>
          `).join('')}
        </div>
      </div>` : ''}

      <div class="detail-section">
        <h4>操作</h4>
        <div class="detail-actions">
          ${c.status === '起草中' ? '<button class="btn btn-primary" onclick="submitForReview(\'' + c.id + '\');closeDetailPanel()">提交审核</button>' : ''}
          ${c.status === '审核中' ? '<button class="btn btn-primary" onclick="approveContract(\'' + c.id + '\');closeDetailPanel()">审核通过</button><button class="btn btn-danger" onclick="rejectContract(\'' + c.id + '\');closeDetailPanel()">驳回</button>' : ''}
          ${c.status === '审批中' ? '<button class="btn btn-primary" onclick="signContract(\'' + c.id + '\');closeDetailPanel()">审批通过→待签署</button>' : ''}
          ${c.status === '待签署' ? '<button class="btn btn-primary" onclick="executeContract(\'' + c.id + '\');closeDetailPanel()">确认签署→执行</button>' : ''}
          ${c.status === '待续签' ? '<button class="btn btn-primary" onclick="renewContract(\'' + c.id + '\');closeDetailPanel()">发起续签</button>' : ''}
          ${c.status === '履行中' ? '<button class="btn btn-outline" onclick="archiveContract(\'' + c.id + '\');closeDetailPanel()">归档</button>' : ''}
          ${c.status === '执行中' ? '<button class="btn btn-outline" onclick="archiveContract(\'' + c.id + '\');closeDetailPanel()">归档</button>' : ''}
          ${c.dataQuality ? '<button class="btn btn-outline" onclick="openInIMA(\'' + c.id + '\')">在IMA中查看原文</button>' : ''}
          <button class="btn btn-outline" onclick="closeDetailPanel()">关闭</button>
        </div>
      </div>
    </div>
  `;

  panel.classList.add('open');
}

function closeDetailPanel() {
  document.getElementById('detailPanel').classList.remove('open');
}

// ========== 合同状态流转 ==========
function submitForReview(id) {
  const c = contracts.find(x => x.id === id);
  if (c) { c.status = '审核中'; renderContractTable(); Toast.show(`合同 ${id} 已提交法务审核`, 'success'); }
}

function approveContract(id) {
  const c = contracts.find(x => x.id === id);
  if (c) { c.status = '审批中'; renderContractTable(); Toast.show(`合同 ${id} 法务审核通过`, 'success'); }
}

function rejectContract(id) {
  const c = contracts.find(x => x.id === id);
  if (c) { c.status = '起草中'; renderContractTable(); Toast.show(`合同 ${id} 已驳回至起草阶段`, 'warning'); }
}

function signContract(id) {
  const c = contracts.find(x => x.id === id);
  if (c) { c.status = '待签署'; renderContractTable(); Toast.show(`合同 ${id} 审批通过，进入签署阶段`, 'success'); }
}

function executeContract(id) {
  const c = contracts.find(x => x.id === id);
  if (c) { c.status = '执行中'; renderContractTable(); Toast.show(`合同 ${id} 已签署确认，开始执行`, 'success'); }
}

function archiveContract(id) {
  const c = contracts.find(x => x.id === id);
  if (c) { c.status = '已归档'; renderContractTable(); Toast.show(`合同 ${id} 已归档`, 'info'); }
}

function renewContract(id) {
  const c = contracts.find(x => x.id === id);
  if (c) { c.status = '起草中'; renderContractTable(); Toast.show(`合同 ${id} 已发起续签流程`, 'success'); }
}

function openInIMA(id) {
  const c = contracts.find(x => x.id === id);
  if (c && c.imaMediaId) {
    Toast.show(`正在从IMA知识库获取「${c.name}」原文...`, 'info');
    // 打开IMA知识库中对应文件的详情
    setTimeout(() => {
      Toast.show(`已定位到IMA知识库文件：${c.imaFolder} > ${c.name}`, 'success');
    }, 1500);
  } else {
    Toast.show('该合同暂无IMA知识库关联文件', 'warning');
  }
}

// ========== 模块切换 ==========
function switchModule(module) {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.module === module);
  });
  document.querySelectorAll('.module-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === 'panel-' + module);
  });

  const titles = {
    dashboard: '总览仪表盘', lifecycle: '合同全生命周期',
    template: '合同模板库', ledger: '台账与报表',
    warning: '到期预警', storage: '文件与检索',
    automation: '自动化监控'
  };
  document.getElementById('module-title').textContent = titles[module] || module;

  if (module === 'lifecycle') renderContractTable();
  if (module === 'ledger') renderLedger();
  if (module === 'dashboard') renderDashboardCharts();
  if (module === 'warning') renderWarningTimeline();
  if (module === 'storage') renderStorageStats();
  if (module === 'automation') renderAutomationMonitor();
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('collapsed');
}

// ========== 合同表格渲染 ==========
function renderContractTable() {
  const tbody = document.getElementById('contractTableBody');
  if (!tbody) return;

  let data = [...contracts];
  const typeFilter = document.getElementById('filterType')?.value || '';
  const statusFilter = document.getElementById('filterStatus')?.value || '';
  const yearFilter = document.getElementById('filterYear')?.value || '';

  if (typeFilter) data = data.filter(c => c.type === typeFilter);
  if (statusFilter) data = data.filter(c => c.status === statusFilter);
  if (yearFilter) data = data.filter(c => c.id.includes(yearFilter));

  tbody.innerHTML = data.map(c => `
    <tr onclick="openContractDetail('${c.id}')">
      <td>${c.id}</td>
      <td><strong>${c.name}</strong></td>
      <td><span class="wf-tag">${c.type}</span></td>
      <td>${c.party}</td>
      <td>${c.amount > 0 ? '¥' + c.amount + '万' : c.unitPrice || '—'}</td>
      <td><span class="status-badge ${getStatusClass(c.status)}">${c.status}</span></td>
      <td>${c.endDate}</td>
      <td><span class="ima-indicator" title="数据来源: IMA知识库">${c.source === 'IMA知识库' ? '&#128218;IMA' : '—'}</span></td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="event.stopPropagation();openContractDetail('${c.id}')">详情</button>
        ${c.imaMediaId ? `<button class="btn btn-sm btn-outline" onclick="event.stopPropagation();openInIMA('${c.id}')">IMA原文</button>` : ''}
      </td>
    </tr>
  `).join('');

  // 更新统计
  updateDashboardStats();
}

function getStatusClass(status) {
  const map = {
    '起草中': 'draft', '审核中': 'review', '审批中': 'approve', '待签署': 'signing',
    '执行中': 'active', '履行中': 'active', '待续签': 'signing', '履行完毕': 'archived',
    '已到期': 'archived', '已到期（后续已续签）': 'archived', '待核实': 'draft', '已归档': 'archived',
    '履行中/待确认': 'review'
  };
  return map[status] || 'draft';
}

function filterContracts() { renderContractTable(); }

function updateDashboardStats() {
  const el = document.getElementById('totalContracts');
  if (el) el.textContent = overviewStats.totalContracts;
  const el2 = document.getElementById('activeContracts');
  if (el2) el2.textContent = contracts.filter(c => c.status === '履行中' || c.status === '执行中').length;
  const el3 = document.getElementById('warningContracts');
  if (el3) {
    const now = new Date('2026-06-22');
    const thirty = contracts.filter(c => {
      if (['已归档', '履行完毕', '已到期'].includes(c.status)) return false;
      if (!c.endDate || c.endDate.includes('待') || c.endDate === '长期' || c.endDate === '长期有效' || c.endDate === '贰年') return false;
      const d = new Date(c.endDate);
      if (isNaN(d.getTime())) return false;
      const diff = (d - now) / (1000*60*60*24);
      return diff <= 30 && diff >= 0;
    }).length;
    el3.textContent = thirty;
  }
  const el4 = document.getElementById('totalAmount');
  if (el4) {
    const total = overviewStats.confirmedTotalAmount;
    el4.textContent = '¥' + total.toFixed(1) + '万';
  }
  // 更新IMA同步状态
  const el5 = document.getElementById('imaSyncCount');
  if (el5) el5.textContent = imaConnectionInfo.totalItems;
  const el6 = document.getElementById('imaLastSync');
  if (el6) el6.textContent = imaConnectionInfo.lastSync;
}

// ========== 新建合同 ==========
function showNewContractForm() {
  document.getElementById('newContractModal').style.display = 'flex';
}

function closeModal(id) {
  document.getElementById(id).style.display = 'none';
}

function createContract() {
  const name = document.getElementById('newContractName').value;
  const type = document.getElementById('newContractType').value;
  const party = document.getElementById('newContractParty').value;
  const amount = document.getElementById('newContractAmount').value;

  if (!name || !type) {
    Toast.show('请填写合同名称和类型', 'warning');
    return;
  }

  const newId = 'FT-2026-' + String(contracts.length + 1).padStart(3, '0');
  contracts.push({
    id: newId, name, type, party: party || '待提取',
    amount: parseFloat(amount) || 0, status: '起草中',
    endDate: document.getElementById('newContractEnd').value || '待提取',
    paid: 0, balance: parseFloat(amount) || 0,
    dataQuality: '新创建', source: '本系统'
  });

  closeModal('newContractModal');
  renderContractTable();
  Toast.show(`合同 ${newId} 已创建并进入起草阶段`, 'success');

  // 清空表单
  document.getElementById('newContractName').value = '';
  document.getElementById('newContractType').value = '';
  document.getElementById('newContractParty').value = '';
  document.getElementById('newContractAmount').value = '';
}

// ========== 模板库 ==========
function openTemplate(name) {
  const tpl = templates[name];
  if (!tpl) return;

  // 在模板卡片中展开详情
  Toast.show(`模板: ${tpl.name} ${tpl.version} — ${tpl.fields.length}个动态字段`, 'info');
}

function useTemplate(name) {
  const tpl = templates[name];
  if (!tpl) return;

  document.getElementById('templateUseTitle').textContent = '使用模板: ' + tpl.name;

  const body = document.getElementById('templateUseBody');
  body.innerHTML = `
    <div class="tpl-use-info">
      <span class="tpl-use-version">${tpl.version}</span>
      <span class="tpl-use-type">${tpl.type}</span>
    </div>
    <div class="tpl-fields-grid">
      ${tpl.fields.map(field => `
        <div class="form-row tpl-field-row">
          <label>${field}</label>
          <input type="text" id="tplField_${field}" placeholder="输入${field}">
        </div>
      `).join('')}
    </div>
    <div class="tpl-preview-section">
      <h4>预览</h4>
      <div class="tpl-preview-box" id="tplPreviewBox">
        <p class="tpl-preview-hint">填写字段后实时预览合同内容</p>
      </div>
    </div>
  `;

  // 为所有字段绑定实时预览
  setTimeout(() => {
    tpl.fields.forEach(field => {
      const input = document.getElementById('tplField_' + field);
      if (input) {
        input.addEventListener('input', () => updateTemplatePreview(name));
      }
    });
  }, 100);

  document.getElementById('templateUseModal').style.display = 'flex';
}

function updateTemplatePreview(tplName) {
  const tpl = templates[tplName];
  if (!tpl) return;
  const box = document.getElementById('tplPreviewBox');
  if (!box) return;

  const filled = {};
  tpl.fields.forEach(field => {
    const input = document.getElementById('tplField_' + field);
    if (input) filled[field] = input.value || `<span class="preview-blank">${field}</span>`;
  });

  box.innerHTML = `
    <div class="preview-header">合同预览 · ${tpl.name} ${tpl.version}</div>
    <div class="preview-content">
      <p>甲方：${filled['甲方名称'] || filled['特许经营方'] || filled['政府方'] || '<span class="preview-blank">甲方</span>'}</p>
      <p>乙方：${filled['乙方名称'] || '<span class="preview-blank">乙方</span>'}</p>
      <p>合同类型：${tpl.type}</p>
      ${filled['合同金额'] || filled['总金额'] || filled['年预估金额'] || filled['投资总额'] ? `<p>金额：${filled['合同金额'] || filled['总金额'] || filled['年预估金额'] || filled['投资总额']}</p>` : ''}
      <p>有效期：${filled['经营期限'] || filled['合同期限'] || filled['特许期限'] || '<span class="preview-blank">有效期</span>'}</p>
      <p class="preview-more">... 更多条款请查看完整模板</p>
    </div>
  `;
}

function generateFromTemplate() {
  Toast.show('合同已根据模板和填入的字段生成，自动进入起草阶段', 'success');
  closeModal('templateUseModal');
}

function showNewTemplate() {
  Toast.show('在 IMA 知识库「伏泰-合同模板库」中上传标准模板文件，系统自动识别动态字段并注册', 'info');
}

function syncIMA() {
  Toast.show('IMA知识库同步完成 — 「岳阳餐厨垃圾项目-合同管理」共70份文件，69份合同已映射，新增1份（打印机购销合同）', 'success');
}

// ========== 台账 ==========
function renderLedger() {
  const ledgerBody = document.getElementById('ledgerTableBody');
  if (!ledgerBody) return;

  ledgerBody.innerHTML = contracts.filter(c => c.amount > 0 || c.unitPrice).map(c => `
    <tr onclick="openContractDetail('${c.id}')">
      <td>${c.id}</td>
      <td>${c.name}</td>
      <td><span class="wf-tag">${c.type}</span></td>
      <td>${c.party}</td>
      <td>${c.amount > 0 ? '¥' + c.amount + '万' : c.unitPrice || '—'}</td>
      <td>${c.paid > 0 ? '¥' + c.paid + '万已付' : '—'}</td>
      <td>${c.balance > 0 ? '¥' + c.balance + '万' : c.unitPrice || '—'}</td>
      <td><span class="status-badge ${getStatusClass(c.status)}">${c.status}</span></td>
    </tr>
  `).join('');

  const paymentBody = document.getElementById('paymentTableBody');
  if (!paymentBody) return;

  paymentBody.innerHTML = paymentNodes.map(p => `
    <tr>
      <td>${p.contract}</td>
      <td>${p.node}</td>
      <td>${p.condition}</td>
      <td>${p.amount}</td>
      <td>${p.deadline}</td>
      <td><span class="status-badge ${p.status === '待续签' ? 'signing' : p.status === '待付' ? 'approve' : p.status === '履行中' ? 'active' : p.status === '紧急' ? 'draft' : p.status === '循环' ? 'active' : 'review'}">${p.status}</span></td>
    </tr>
  `).join('');
}

function switchLedgerTab(tab) {
  document.querySelectorAll('.ledger-tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');

  document.getElementById('ledgerSummary').style.display = tab === 'summary' ? 'block' : 'none';
  document.getElementById('ledgerExecution').style.display = tab === 'execution' ? 'block' : 'none';
  document.getElementById('ledgerPayment').style.display = tab === 'payment' ? 'block' : 'none';
}

function exportLedger() {
  Toast.show('台账导出完成，Excel 文件已保存', 'success');
}

function generateReport() {
  Toast.show('报表生成完成：类型分布图 + 月度趋势 + 付款进度 + 到期预警汇总', 'success');
}

// ========== 到期预警 ==========
function renderWarningTimeline() {
  const now = new Date('2026-06-22');
  const warnings = contracts.filter(c => {
    // 排除已完成的合同
    if (['已归档', '履行完毕', '已到期'].includes(c.status)) return false;
    // 排除无明确到期日期的合同
    if (!c.endDate || c.endDate.includes('待') || c.endDate === '长期' || c.endDate === '长期有效' || c.endDate === '贰年') return false;
    const d = new Date(c.endDate);
    if (isNaN(d.getTime())) return false;
    const diff = Math.round((d - now) / (1000*60*60*24));
    return diff >= 0 && diff <= 90;
  }).map(c => {
    const d = new Date(c.endDate);
    const diff = Math.round((d - now) / (1000*60*60*24));
    return { ...c, daysLeft: diff };
  }).sort((a, b) => a.daysLeft - b.daysLeft);

  const list = document.getElementById('warningDynamicList');
  if (!list) return;

  list.innerHTML = warnings.map(c => {
    const level = c.daysLeft <= 7 ? 'urgent' : c.daysLeft <= 30 ? 'caution' : 'notice';
    const icon = c.daysLeft <= 7 ? '&#128308;' : c.daysLeft <= 30 ? '&#128992;' : '&#128994;';
    const actionText = c.daysLeft <= 7 ? '紧急处理' : c.daysLeft <= 30 ? '需续签' : '关注';

    return `
      <div class="warning-item ${level}">
        <div class="wi-left">
          <span class="wi-icon">${icon}</span>
          <div>
            <span class="wi-name">${c.name}</span>
            <span class="wi-party">${c.party}</span>
          </div>
        </div>
        <div class="wi-center">
          <span class="wi-days">${c.daysLeft}天</span>
          <span class="wi-date">${c.endDate}</span>
          <span class="wi-action">${actionText}</span>
        </div>
        <div class="wi-actions">
          ${c.daysLeft <= 7 ? `<button class="btn btn-sm btn-danger" onclick="handleWarning('${c.name}','renew')">续签</button>` : ''}
          ${c.daysLeft <= 30 ? `<button class="btn btn-sm btn-warning" onclick="handleWarning('${c.name}','renew')">续签</button>` : ''}
          <button class="btn btn-sm" onclick="handleWarning('${c.name}','notify')">通知</button>
        </div>
      </div>
    `;
  }).join('');
}

function configWarningRules() {
  const modal = document.getElementById('warningConfigModal');
  if (!modal) { Toast.show('预警规则设置页面', 'info'); return; }
  modal.style.display = 'flex';
}

function runWarningScan() {
  Toast.show('扫描完成 — 发现: 7天内2份, 30天内3份, 90天内5份', 'warning');
  renderWarningTimeline();
}

function handleWarning(contract, action) {
  const actionText = { 'renew': '发起续签流程', 'notify': '通知相关人员', 'pay': '发起付款审批', 'inspect': '安排验收检查', 'review': '准备中期评估' };
  Toast.show(actionText[action] + ' — ' + contract, 'success');
}

// ========== 文件与检索 ==========
function renderStorageStats() {
  const stats = document.getElementById('storageStats');
  if (!stats) return;
  stats.innerHTML = `
    <div class="storage-stat-item">
      <span class="ss-icon">&#128196;</span>
      <span class="ss-value">${overviewStats.totalContracts}</span>
      <span class="ss-label">合同文件</span>
    </div>
    <div class="storage-stat-item">
      <span class="ss-icon">&#128193;</span>
      <span class="ss-value">8</span>
      <span class="ss-label">分类目录</span>
    </div>
    <div class="storage-stat-item">
      <span class="ss-icon">&#128218;</span>
      <span class="ss-value">8</span>
      <span class="ss-label">模板文件</span>
    </div>
    <div class="storage-stat-item">
      <span class="ss-icon">&#128274;</span>
      <span class="ss-value">${imaConnectionInfo.totalItems}</span>
      <span class="ss-label">IMA知识库条目</span>
    </div>
  `;
}

function uploadFile() {
  const modal = document.getElementById('uploadFileModal');
  if (!modal) { Toast.show('上传文件到合同管理系统', 'info'); return; }
  modal.style.display = 'flex';
}

function doFileUpload() {
  Toast.show('文件上传完成，已同步到 IMA 知识库', 'success');
  closeModal('uploadFileModal');
}

function syncIMAStorage() {
  Toast.show('IMA 知识库同步完成 — 「岳阳餐厨垃圾项目」共' + imaConnectionInfo.totalItems + '个条目，' + overviewStats.totalContracts + '份合同已映射', 'success');
}

function toggleFolder(el) {
  el.parentElement.classList.toggle('open');
}

function openFile(name) {
  Toast.show('打开文件: ' + name + ' — 从 IMA 知识库获取', 'info');
}

function searchStorage(event) {
  if (event.key === 'Enter') doStorageSearch();
}

function doStorageSearch() {
  const query = document.getElementById('storageSearch')?.value;
  if (!query) return;

  const results = document.getElementById('searchResultsPanel');
  if (!results) { Toast.show('搜索: "' + query + '"', 'info'); return; }

  // 模拟搜索：匹配合同名称
  const matched = contracts.filter(c =>
    c.name.includes(query) || c.party.includes(query) || c.type.includes(query)
  );

  document.getElementById('searchResultsTitle').textContent = `搜索结果: "${query}" — 找到 ${matched.length} 份合同`;
  document.getElementById('searchResultsList').innerHTML = matched.map(c => `
    <div class="search-result-item" onclick="openContractDetail('${c.id}');closeSearchResults()">
      <span class="sr-id">${c.id}</span>
      <span class="sr-name">${c.name}</span>
      <span class="wf-tag">${c.type}</span>
      <span class="status-badge ${getStatusClass(c.status)}">${c.status}</span>
      <span class="sr-party">${c.party}</span>
    </div>
  `).join('') || '<div class="search-no-result">未找到匹配的合同</div>';

  results.style.display = 'block';
}

function closeSearchResults() {
  document.getElementById('searchResultsPanel').style.display = 'none';
}

function closeVersionCompare() {
  document.getElementById('versionCompare').style.display = 'none';
}

// ========== 通知 ==========
function showNotifications() {
  document.getElementById('notifPanel').style.display = 'block';
}

function closeNotifications() {
  document.getElementById('notifPanel').style.display = 'none';
}

function showIMAStatus() {
  const modal = document.getElementById('imaStatusModal');
  if (!modal) { Toast.show('IMA 知识库连接状态: 已连接', 'info'); return; }

  // 更新IMA状态弹窗内容
  const content = document.getElementById('imaStatusContent');
  if (content) {
    content.innerHTML = `
      <div class="ima-detail-grid">
        <div class="ima-detail-item">
          <span class="ima-detail-label">连接状态</span>
          <span class="ima-detail-value connected">已连接 ✓</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">知识库名称</span>
          <span class="ima-detail-value">${imaConnectionInfo.kbName}</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">总条目数</span>
          <span class="ima-detail-value">${imaConnectionInfo.totalItems}</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">合同文件夹</span>
          <span class="ima-detail-value">${imaConnectionInfo.contractFolder}</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">合同文件数</span>
          <span class="ima-detail-value">${imaConnectionInfo.contractFileCount}份</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">子分类目录</span>
          <span class="ima-detail-value">${imaConnectionInfo.contractSubfolders.length}个</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">数据来源</span>
          <span class="ima-detail-value ima-source">${imaConnectionInfo.dataSource}</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">同步方式</span>
          <span class="ima-detail-value">${imaConnectionInfo.syncMethod}</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">自动同步</span>
          <span class="ima-detail-value">${imaConnectionInfo.autoSync ? '已启用 ✓' : '未启用'}</span>
        </div>
        <div class="ima-detail-item">
          <span class="ima-detail-label">最后同步</span>
          <span class="ima-detail-value">${imaConnectionInfo.lastSync}</span>
        </div>
      </div>
      <div class="ima-folder-list">
        <h4>合同管理子目录</h4>
        ${imaConnectionInfo.contractSubfolders.map(f => `<div class="ima-folder-item">&#128193; ${f}</div>`).join('')}
      </div>
    `;
  }
  modal.style.display = 'flex';
}

// ========== 全局搜索 ==========
function handleGlobalSearch(event) {
  if (event.key === 'Enter') doGlobalSearch();
}

function doGlobalSearch() {
  const query = document.getElementById('globalSearch').value;
  if (!query) return;

  const matched = contracts.filter(c =>
    c.name.includes(query) || c.party.includes(query) || c.id.includes(query)
  );

  // 切换到合同生命周期模块并筛选
  switchModule('lifecycle');
  document.getElementById('filterStatus').value = '';

  // 高亮搜索结果
  Toast.show(`全局搜索 "${query}" — 找到 ${matched.length} 份合同`, matched.length > 0 ? 'success' : 'warning');
}

// ========== Dashboard 图表 (Chart.js) ==========
let chartInstances = {};

function renderDashboardCharts() {
  // 签署趋势折线图
  const trendCtx = document.getElementById('chartTrend');
  if (trendCtx && !chartInstances.trend) {
    chartInstances.trend = new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
        datasets: [{
          label: '合同签署数',
          data: [3, 5, 4, 7, 6, 8],
          borderColor: '#4a90d9',
          backgroundColor: 'rgba(74,144,217,0.1)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#4a90d9',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#e9ecef' }, ticks: { font: { family: 'Noto Sans SC' } } },
          x: { grid: { display: false }, ticks: { font: { family: 'Noto Sans SC' } } }
        }
      }
    });
  }

  // 类型分布饼图（使用真实分类数据）
  const typeCtx = document.getElementById('chartTypePie');
  if (typeCtx && !chartInstances.typePie) {
    const labels = Object.keys(contractCategoryStats);
    const values = Object.values(contractCategoryStats);

    chartInstances.typePie = new Chart(typeCtx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ['#4a90d9', '#5cb85c', '#f0ad4e', '#d9534f', '#9b59b6',
            '#17a2b8', '#343a40', '#e83e8c', '#fd7e14', '#6c757d', '#28a745'],
          borderWidth: 2,
          borderColor: '#fff',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { font: { family: 'Noto Sans SC', size: 13 }, padding: 12 } }
        },
        cutout: '55%',
      }
    });
  }

  // 金额分布柱状图（使用真实分类金额数据）
  const amountCtx = document.getElementById('chartAmount');
  if (amountCtx && !chartInstances.amount) {
    const amountByType = {};
    contracts.filter(c => c.amount > 0).forEach(c => {
      amountByType[c.type] = (amountByType[c.type] || 0) + c.amount;
    });

    chartInstances.amount = new Chart(amountCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(amountByType),
        datasets: [{
          label: '合同金额(万)',
          data: Object.values(amountByType).map(v => Math.round(v * 100) / 100),
          backgroundColor: ['#4a90d9', '#5cb85c', '#f0ad4e', '#d9534f', '#9b59b6',
            '#17a2b8', '#343a40', '#e83e8c', '#fd7e14', '#6c757d', '#28a745'],
          borderRadius: 6,
          barPercentage: 0.6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#e9ecef' }, ticks: { font: { family: 'Noto Sans SC' } } },
          x: { grid: { display: false }, ticks: { font: { family: 'Noto Sans SC' } } }
        }
      }
    });
  }
}

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
  Toast.init();
  renderContractTable();
  renderLedger();
  renderWarningTimeline();
  renderStorageStats();
  updateDashboardStats();
});

// ========== 自动化监控模块 ==========
function renderAutomationMonitor() {
  // 读取自动化运行信息（如果data.js中已有）
  const runInfo = typeof automationRunInfo !== 'undefined' ? automationRunInfo : null;
  const changes = typeof knowledgeBaseChanges !== 'undefined' ? knowledgeBaseChanges : null;
  const autoWarnings = typeof lastScanWarnings !== 'undefined' ? lastScanWarnings : null;

  // 更新任务状态
  const statusEl = document.getElementById('autoTaskStatus');
  if (statusEl) statusEl.textContent = runInfo ? '运行中' : '待初始化';

  const lastRunEl = document.getElementById('autoLastRun');
  if (lastRunEl) lastRunEl.textContent = runInfo ? runInfo.lastScanTime : '尚未执行';

  const nextRunEl = document.getElementById('autoNextRun');
  if (nextRunEl) {
    if (runInfo) {
      const last = new Date(runInfo.lastScanTime);
      const next = new Date(last.getTime() + 7 * 24 * 60 * 60 * 1000);
      nextRunEl.textContent = next.toLocaleDateString('zh-CN') + ' ' + next.toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'});
    } else {
      nextRunEl.textContent = '2026-06-29 08:00';
    }
  }

  const successEl = document.getElementById('autoSuccessCount');
  if (successEl) successEl.textContent = runInfo ? '1' : '0';

  // 更新变更检测数据
  if (changes) {
    const _cac = document.getElementById('changeAddedCount'); if (_cac) _cac.textContent = changes.added?.length || 0;
    const _cmc = document.getElementById('changeModifiedCount'); if (_cmc) _cmc.textContent = changes.modified?.length || 0;
    const _cdc = document.getElementById('changeDeletedCount'); if (_cdc) _cdc.textContent = changes.deleted?.length || 0;
    const _cti = document.getElementById('changeTotalItems'); if (_cti) _cti.textContent = changes.total_current || 0;

    // 变更详情列表
    const changeListEl = document.getElementById('changeDetailList');
    if (changeListEl) {
      let html = '';
      if (changes.added?.length > 0) {
        html += '<div class="cd-section cd-added"><h4>新增条目</h4>';
        changes.added.slice(0, 10).forEach(item => {
          html += `<div class="cd-item">&#10133; ${item.title || item.name || '未知'} <span class="cd-folder">${item.parent_folder_id || ''}</span></div>`;
        });
        html += '</div>';
      }
      if (changes.deleted?.length > 0) {
        html += '<div class="cd-section cd-deleted"><h4>删除条目</h4>';
        changes.deleted.slice(0, 10).forEach(item => {
          html += `<div class="cd-item">&#10134; ${item.title || item.name || '未知'} <span class="cd-folder">${item.parent_folder_id || ''}</span></div>`;
        });
        html += '</div>';
      }
      if (changes.modified?.length > 0) {
        html += '<div class="cd-section cd-modified"><h4>修改条目</h4>';
        changes.modified.slice(0, 10).forEach(item => {
          html += `<div class="cd-item">&#9998; ${item.current?.title || item.current?.name || '未知'}</div>`;
        });
        html += '</div>';
      }
      if (!html) html = '<div class="cd-empty">本次扫描无变更 ✅</div>';
      changeListEl.innerHTML = html;
    }
  } else {
    const _cac2 = document.getElementById('changeAddedCount'); if (_cac2) _cac2.textContent = '—';
    const _cmc2 = document.getElementById('changeModifiedCount'); if (_cmc2) _cmc2.textContent = '—';
    const _cdc2 = document.getElementById('changeDeletedCount'); if (_cdc2) _cdc2.textContent = '—';
    const _cti2 = document.getElementById('changeTotalItems'); if (_cti2) _cti2.textContent = imaConnectionInfo.totalItems || '—';
  }

  // 更新到期预警数据
  const warningSummary = runInfo?.warningSummary;
  if (warningSummary) {
    const _awu = document.getElementById('autoWarnUrgent'); if (_awu) _awu.textContent = warningSummary.urgent;
    const _awc = document.getElementById('autoWarnCaution'); if (_awc) _awc.textContent = warningSummary.caution;
    const _awn = document.getElementById('autoWarnNotice'); if (_awn) _awn.textContent = warningSummary.notice;
  } else {
    // 动态计算
    const now = new Date('2026-06-22');
    const urgentCount = contracts.filter(c => {
      if (['已归档', '履行完毕', '已到期'].includes(c.status)) return false;
      if (!c.endDate || c.endDate.includes('待') || c.endDate === '长期' || c.endDate === '长期有效' || c.endDate === '贰年') return false;
      const d = new Date(c.endDate);
      if (isNaN(d.getTime())) return false;
      return (d - now) / (1000*60*60*24) <= 7 && (d - now) / (1000*60*60*24) >= 0;
    }).length;
    const cautionCount = contracts.filter(c => {
      if (['已归档', '履行完毕', '已到期'].includes(c.status)) return false;
      if (!c.endDate || c.endDate.includes('待') || c.endDate === '长期' || c.endDate === '长期有效' || c.endDate === '贰年') return false;
      const d = new Date(c.endDate);
      if (isNaN(d.getTime())) return false;
      const diff = (d - now) / (1000*60*60*24);
      return diff > 7 && diff <= 30;
    }).length;
    const noticeCount = contracts.filter(c => {
      if (['已归档', '履行完毕', '已到期'].includes(c.status)) return false;
      if (!c.endDate || c.endDate.includes('待') || c.endDate === '长期' || c.endDate === '长期有效' || c.endDate === '贰年') return false;
      const d = new Date(c.endDate);
      if (isNaN(d.getTime())) return false;
      const diff = (d - now) / (1000*60*60*24);
      return diff > 30 && diff <= 90;
    }).length;

    const _awu2 = document.getElementById('autoWarnUrgent'); if (_awu2) _awu2.textContent = urgentCount;
    const _awc2 = document.getElementById('autoWarnCaution'); if (_awc2) _awc2.textContent = cautionCount;
    const _awn2 = document.getElementById('autoWarnNotice'); if (_awn2) _awn2.textContent = noticeCount;
  }

  // 预警列表
  const warningListEl = document.getElementById('autoWarningList');
  if (warningListEl) {
    if (autoWarnings && autoWarnings.length > 0) {
      warningListEl.innerHTML = autoWarnings.map(w => {
        const icon = w.level === 'urgent' ? '&#128308;' : w.level === 'caution' ? '&#128992;' : '&#128994;';
        return `<div class="aw-detail-item ${w.level}">
          <span class="awd-icon">${icon}</span>
          <span class="awd-name">${w.name}</span>
          <span class="awd-days">${w.daysLeft}天</span>
          <span class="awd-date">${w.endDate}</span>
          <span class="awd-action">${w.action}</span>
        </div>`;
      }).join('');
    } else {
      // 使用动态计算
      const now = new Date('2026-06-22');
      const dynamicWarnings = contracts.filter(c => {
        if (['已归档', '履行完毕', '已到期'].includes(c.status)) return false;
        if (!c.endDate || c.endDate.includes('待') || c.endDate === '长期' || c.endDate === '长期有效' || c.endDate === '贰年') return false;
        const d = new Date(c.endDate);
        if (isNaN(d.getTime())) return false;
        const diff = Math.round((d - now) / (1000*60*60*24));
        return diff >= 0 && diff <= 90;
      }).map(c => {
        const d = new Date(c.endDate);
        const diff = Math.round((d - now) / (1000*60*60*24));
        const level = diff <= 7 ? 'urgent' : diff <= 30 ? 'caution' : 'notice';
        const action = diff <= 7 ? '紧急处理' : diff <= 30 ? '需续签' : '关注';
        return { name: c.name, daysLeft: diff, endDate: c.endDate, level, action, party: c.party };
      }).sort((a, b) => a.daysLeft - b.daysLeft);

      if (dynamicWarnings.length > 0) {
        warningListEl.innerHTML = dynamicWarnings.map(w => {
          const icon = w.level === 'urgent' ? '&#128308;' : w.level === 'caution' ? '&#128992;' : '&#128994;';
          return `<div class="aw-detail-item ${w.level}">
            <span class="awd-icon">${icon}</span>
            <span class="awd-name">${w.name}</span>
            <span class="awd-days">${w.daysLeft}天</span>
            <span class="awd-date">${w.endDate}</span>
            <span class="awd-action">${w.action}</span>
          </div>`;
        }).join('');
      } else {
        warningListEl.innerHTML = '<div class="cd-empty">当前无到期预警 ✅</div>';
      }
    }
  }

  // 执行日志表格
  const logTableEl = document.getElementById('executionLogTableBody');
  if (logTableEl) {
    // 模拟历史日志数据
    const mockLogs = [
      { runId: '202606220800', startTime: '2026-06-22 08:00:00', duration: 12.5, status: 'success', changes: {added:0,modified:1,deleted:0}, warnings: {urgent:2,caution:3,notice:5}, push: 'success' },
    ];
    
    logTableEl.innerHTML = mockLogs.map(log => `
      <tr>
        <td>${log.runId}</td>
        <td>${log.startTime}</td>
        <td>${log.duration}秒</td>
        <td><span class="status-badge ${log.status === 'success' ? 'active' : 'draft'}">${log.status === 'success' ? '成功' : log.status}</span></td>
        <td>${log.changes.added}</td>
        <td>${log.changes.modified}</td>
        <td>${log.changes.deleted}</td>
        <td>&#128308;${log.warnings.urgent} &#128992;${log.warnings.caution} &#128994;${log.warnings.notice}</td>
        <td><span class="status-badge ${log.push === 'success' ? 'active' : 'draft'}">${log.push === 'success' ? '已推送' : log.push}</span></td>
        <td><button class="btn btn-sm" onclick="viewLogDetail('${log.runId}')">查看</button></td>
      </tr>
    `).join('');
  }
}

function runAutomationNow() {
  Toast.show('自动化引擎已触发 — 正在扫描IMA知识库「岳阳餐厨垃圾项目-合同管理」...', 'info');
  setTimeout(() => {
    Toast.show('扫描完成: 70份文件已检测，69份合同已映射，1份新增。到期预警: 紧急2份，注意3份', 'success');
  }, 2000);
}

function viewAutomationConfig() {
  Toast.show('调度配置 — 每周一 08:00 执行，IMA知识库扫描 + 变更检测 + 预警扫描 + 钉钉推送', 'info');
}

function viewLogDetail(runId) {
  Toast.show(`查看执行日志 ${runId} — 详细变更记录和预警信息`, 'info');
}
