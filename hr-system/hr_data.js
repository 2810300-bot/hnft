/* ================================================
   湖南伏泰 HR 人事管理系统 - 数据层 v1.0
   数据来源：IMA 知识库「伏泰HR人事管理」+ 钉钉考勤
   最后同步：自动更新 | 自动化引擎按调度频率刷新
   ================================================ */

// --- 1. 员工花名册 ---
const employees = [
  {
    id: "EMP001", dingtalkUserId: "manager001", name: "颜一亩", gender: "男",
    birthDate: "1985-03-15", phone: "138****1111", email: "yanyimu@hnft.com",
    department: "管理层", position: "总经理", hireDate: "2022-01-01",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "本科", school: "湖南大学", major: "环境工程",
    emergencyContact: "张XX 138****1112", bankAccount: "6217***************",
    contractStart: "2025-01-01", contractEnd: "2027-12-31",
    socialSecurityBase: 15000, notes: ""
  },
  {
    id: "EMP002", dingtalkUserId: "user002", name: "施洪彬", gender: "男",
    birthDate: "1988-07-22", phone: "139****2222", email: "shihongbin@hnft.com",
    department: "运营部", position: "运营经理", hireDate: "2022-03-15",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "大专", school: "岳阳职业技术学院", major: "环境工程",
    emergencyContact: "李XX 139****2223", bankAccount: "6217***************",
    contractStart: "2025-03-15", contractEnd: "2027-03-14",
    socialSecurityBase: 8000, notes: ""
  },
  {
    id: "EMP003", dingtalkUserId: "user003", name: "苏铮铮", gender: "男",
    birthDate: "1990-11-08", phone: "137****3333", email: "suzhengzheng@hnft.com",
    department: "技术部", position: "技术主管", hireDate: "2023-06-01",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "本科", school: "长沙理工大学", major: "机械工程",
    emergencyContact: "王XX 137****3334", bankAccount: "6217***************",
    contractStart: "2025-06-01", contractEnd: "2028-05-31",
    socialSecurityBase: 9000, notes: ""
  },
  {
    id: "EMP004", dingtalkUserId: "user004", name: "吴胡兵", gender: "男",
    birthDate: "1992-04-15", phone: "136****4444", email: "wuhubing@hnft.com",
    department: "运营部", position: "运行班长", hireDate: "2023-01-10",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "中专", school: "岳阳市第一职业中专", major: "机电",
    emergencyContact: "赵XX 136****4445", bankAccount: "6217***************",
    contractStart: "2025-01-10", contractEnd: "2027-01-09",
    socialSecurityBase: 6000, notes: ""
  },
  {
    id: "EMP005", dingtalkUserId: "user005", name: "李慧", gender: "女",
    birthDate: "1995-08-20", phone: "135****5555", email: "lihui@hnft.com",
    department: "财务部", position: "会计", hireDate: "2023-09-01",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "本科", school: "湖南商学院", major: "会计学",
    emergencyContact: "刘XX 135****5556", bankAccount: "6217***************",
    contractStart: "2025-09-01", contractEnd: "2028-08-31",
    socialSecurityBase: 7000, notes: ""
  },
  {
    id: "EMP006", dingtalkUserId: "user006", name: "龙冠学", gender: "男",
    birthDate: "1993-12-03", phone: "134****6666", email: "longguanxue@hnft.com",
    department: "运营部", position: "收运调度", hireDate: "2024-02-15",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "大专", school: "湖南环境生物职院", major: "环境监测",
    emergencyContact: "陈XX 134****6667", bankAccount: "6217***************",
    contractStart: "2026-02-15", contractEnd: "2028-02-14",
    socialSecurityBase: 6000, notes: ""
  },
  {
    id: "EMP007", dingtalkUserId: "user007", name: "李莉", gender: "女",
    birthDate: "1997-05-18", phone: "133****7777", email: "lili@hnft.com",
    department: "综合部", position: "行政专员", hireDate: "2024-06-01",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "本科", school: "湖南理工学院", major: "行政管理",
    emergencyContact: "周XX 133****7778", bankAccount: "6217***************",
    contractStart: "2025-06-01", contractEnd: "2027-05-31",
    socialSecurityBase: 5500, notes: ""
  },
  {
    id: "EMP008", dingtalkUserId: "user008", name: "鲁文辉", gender: "男",
    birthDate: "1989-09-25", phone: "132****8888", email: "luwenhui@hnft.com",
    department: "技术部", position: "设备维修", hireDate: "2024-03-01",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "中专", school: "岳阳工业技校", major: "机电一体化",
    emergencyContact: "黄XX 132****8889", bankAccount: "6217***************",
    contractStart: "2025-03-01", contractEnd: "2027-02-28",
    socialSecurityBase: 5500, notes: ""
  },
  {
    id: "EMP009", dingtalkUserId: "user009", name: "卢梁", gender: "男",
    birthDate: "1991-02-14", phone: "131****9999", email: "luliang@hnft.com",
    department: "运营部", position: "收运员", hireDate: "2024-08-01",
    status: "在职", probationEnd: null, departureDate: null,
    idNumber: "430***************", education: "高中", school: "岳阳市一中", major: "",
    emergencyContact: "曹XX 131****9990", bankAccount: "6217***************",
    contractStart: "2025-08-01", contractEnd: "2027-07-31",
    socialSecurityBase: 4500, notes: ""
  },
  {
    id: "EMP010", dingtalkUserId: "user010", name: "张伟", gender: "男",
    birthDate: "1994-06-30", phone: "130****0000", email: "zhangwei@hnft.com",
    department: "运营部", position: "运行工", hireDate: "2025-03-15",
    status: "试用期", probationEnd: "2025-09-14", departureDate: null,
    idNumber: "430***************", education: "高中", school: "岳阳市十五中", major: "",
    emergencyContact: "杨XX 130****0001", bankAccount: "6217***************",
    contractStart: "2025-03-15", contractEnd: "2027-03-14",
    socialSecurityBase: 4000, notes: "试用期6个月"
  }
];

// --- 2. 入离职记录 ---
const hrEvents = [
  { id: "EVT001", employeeId: "EMP010", type: "入职", date: "2025-03-15", description: "张伟入职运营部运行工岗位，试用期6个月", relatedFiles: [] },
  { id: "EVT002", employeeId: "EMP006", type: "入职", date: "2024-02-15", description: "龙冠学入职运营部收运调度岗位", relatedFiles: [] },
  { id: "EVT003", employeeId: "EMP008", type: "入职", date: "2024-03-01", description: "鲁文辉入职技术部设备维修岗位", relatedFiles: [] },
  { id: "EVT004", employeeId: "EMP007", type: "入职", date: "2024-06-01", description: "李莉入职综合部行政专员岗位", relatedFiles: [] },
  { id: "EVT005", employeeId: "EMP009", type: "入职", date: "2024-08-01", description: "卢梁入职运营部收运员岗位", relatedFiles: [] },
  { id: "EVT006", employeeId: "EMP004", type: "入职", date: "2023-01-10", description: "吴胡兵入职运营部运行班长岗位", relatedFiles: [] },
  { id: "EVT007", employeeId: "EMP003", type: "入职", date: "2023-06-01", description: "苏铮铮入职技术部技术主管岗位", relatedFiles: [] },
  { id: "EVT008", employeeId: "EMP005", type: "入职", date: "2023-09-01", description: "李慧入职财务部会计岗位", relatedFiles: [] },
  { id: "EVT009", employeeId: "EMP002", type: "入职", date: "2022-03-15", description: "施洪彬入职运营部运营经理岗位", relatedFiles: [] },
  { id: "EVT010", employeeId: "EMP001", type: "入职", date: "2022-01-01", description: "颜一亩正式入职，担任总经理", relatedFiles: [] },
  { id: "EVT011", employeeId: "EMP004", type: "转正", date: "2023-04-10", description: "吴胡兵试用期满，正式转正", relatedFiles: [] },
  { id: "EVT012", employeeId: "EMP003", type: "转正", date: "2023-09-01", description: "苏铮铮试用期满，正式转正", relatedFiles: [] },
  { id: "EVT013", employeeId: "EMP005", type: "转正", date: "2023-12-01", description: "李慧试用期满，正式转正", relatedFiles: [] }
];

// --- 3. 考勤汇总（当前月） ---
const attendanceSummary = {
  year: 2026, month: 6, totalEmployees: 10,
  records: [
    { employeeId: "EMP001", employeeName: "颜一亩", department: "管理层", workDays: 22, actualDays: 22, lateCount: 0, earlyCount: 0, absentCount: 0, leaveCount: 0, overtimeHours: 8, businessTravelDays: 3, attendanceRate: 100 },
    { employeeId: "EMP002", employeeName: "施洪彬", department: "运营部", workDays: 22, actualDays: 21, lateCount: 1, earlyCount: 0, absentCount: 0, leaveCount: 1, overtimeHours: 12, businessTravelDays: 0, attendanceRate: 95.5 },
    { employeeId: "EMP003", employeeName: "苏铮铮", department: "技术部", workDays: 22, actualDays: 22, lateCount: 0, earlyCount: 0, absentCount: 0, leaveCount: 0, overtimeHours: 5, businessTravelDays: 0, attendanceRate: 100 },
    { employeeId: "EMP004", employeeName: "吴胡兵", department: "运营部", workDays: 22, actualDays: 20, lateCount: 2, earlyCount: 1, absentCount: 0, leaveCount: 2, overtimeHours: 15, businessTravelDays: 0, attendanceRate: 90.9 },
    { employeeId: "EMP005", employeeName: "李慧", department: "财务部", workDays: 22, actualDays: 22, lateCount: 0, earlyCount: 0, absentCount: 0, leaveCount: 0, overtimeHours: 3, businessTravelDays: 0, attendanceRate: 100 },
    { employeeId: "EMP006", employeeName: "龙冠学", department: "运营部", workDays: 22, actualDays: 21, lateCount: 0, earlyCount: 0, absentCount: 1, leaveCount: 0, overtimeHours: 10, businessTravelDays: 0, attendanceRate: 95.5 },
    { employeeId: "EMP007", employeeName: "李莉", department: "综合部", workDays: 22, actualDays: 22, lateCount: 0, earlyCount: 0, absentCount: 0, leaveCount: 0, overtimeHours: 2, businessTravelDays: 1, attendanceRate: 100 },
    { employeeId: "EMP008", employeeName: "鲁文辉", department: "技术部", workDays: 22, actualDays: 21, lateCount: 1, earlyCount: 0, absentCount: 0, leaveCount: 1, overtimeHours: 8, businessTravelDays: 0, attendanceRate: 95.5 },
    { employeeId: "EMP009", employeeName: "卢梁", department: "运营部", workDays: 22, actualDays: 22, lateCount: 0, earlyCount: 0, absentCount: 0, leaveCount: 0, overtimeHours: 6, businessTravelDays: 0, attendanceRate: 100 },
    { employeeId: "EMP010", employeeName: "张伟", department: "运营部", workDays: 22, actualDays: 20, lateCount: 3, earlyCount: 0, absentCount: 0, leaveCount: 2, overtimeHours: 4, businessTravelDays: 0, attendanceRate: 90.9 }
  ]
};

// --- 4. 考勤每日明细（最近30天样本数据） ---
const attendanceDaily = [
  // 最近几天的样本数据
  { date: "2026-06-30", employeeId: "EMP001", checkIn: "08:30", checkOut: "17:45", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-30", employeeId: "EMP002", checkIn: "08:55", checkOut: "18:00", status: "迟到", location: "公司", notes: "迟到5分钟" },
  { date: "2026-06-30", employeeId: "EMP003", checkIn: "08:15", checkOut: "17:30", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-30", employeeId: "EMP004", checkIn: "08:10", checkOut: "17:20", status: "正常", location: "厂区", notes: "" },
  { date: "2026-06-30", employeeId: "EMP005", checkIn: "08:25", checkOut: "17:35", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-30", employeeId: "EMP006", checkIn: "--", checkOut: "--", status: "旷工", location: "--", notes: "未打卡" },
  { date: "2026-06-30", employeeId: "EMP007", checkIn: "08:40", checkOut: "17:50", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-30", employeeId: "EMP008", checkIn: "09:30", checkOut: "17:00", status: "迟到", location: "公司", notes: "迟到30分钟" },
  { date: "2026-06-30", employeeId: "EMP009", checkIn: "08:00", checkOut: "18:00", status: "正常", location: "厂区", notes: "" },
  { date: "2026-06-30", employeeId: "EMP010", checkIn: "09:10", checkOut: "17:00", status: "迟到", location: "公司", notes: "迟到40分钟" },
  { date: "2026-06-29", employeeId: "EMP001", checkIn: "08:35", checkOut: "17:40", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-29", employeeId: "EMP002", checkIn: "08:20", checkOut: "17:30", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-29", employeeId: "EMP003", checkIn: "08:30", checkOut: "17:30", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-29", employeeId: "EMP004", checkIn: "08:15", checkOut: "17:25", status: "正常", location: "厂区", notes: "" },
  { date: "2026-06-29", employeeId: "EMP005", checkIn: "08:30", checkOut: "17:30", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-29", employeeId: "EMP006", checkIn: "08:05", checkOut: "18:30", status: "正常", location: "厂区", notes: "加班" },
  { date: "2026-06-29", employeeId: "EMP007", checkIn: "08:20", checkOut: "17:40", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-29", employeeId: "EMP008", checkIn: "08:25", checkOut: "17:30", status: "正常", location: "公司", notes: "" },
  { date: "2026-06-29", employeeId: "EMP009", checkIn: "07:50", checkOut: "18:00", status: "正常", location: "厂区", notes: "" },
  { date: "2026-06-29", employeeId: "EMP010", checkIn: "08:50", checkOut: "17:00", status: "迟到", location: "公司", notes: "迟到20分钟" }
];

// --- 5. 薪酬数据（2026年6月） ---
const salaryData = {
  year: 2026, month: 6,
  records: [
    { employeeId: "EMP001", employeeName: "颜一亩", department: "管理层", position: "总经理", baseSalary: 15000, positionAllowance: 3000, performanceBonus: 2000, overtimePay: 800, mealAllowance: 400, transportAllowance: 300, otherAllowance: 0, grossPay: 21500, socialSecurity: 1200, housingFund: 600, incomeTax: 900, otherDeduction: 0, totalDeduction: 2700, netPay: 18800 },
    { employeeId: "EMP002", employeeName: "施洪彬", department: "运营部", position: "运营经理", baseSalary: 8000, positionAllowance: 1500, performanceBonus: 1500, overtimePay: 1200, mealAllowance: 400, transportAllowance: 200, otherAllowance: 0, grossPay: 12800, socialSecurity: 800, housingFund: 400, incomeTax: 350, otherDeduction: 0, totalDeduction: 1550, netPay: 11250 },
    { employeeId: "EMP003", employeeName: "苏铮铮", department: "技术部", position: "技术主管", baseSalary: 9000, positionAllowance: 1000, performanceBonus: 1200, overtimePay: 500, mealAllowance: 400, transportAllowance: 200, otherAllowance: 0, grossPay: 12300, socialSecurity: 850, housingFund: 450, incomeTax: 300, otherDeduction: 0, totalDeduction: 1600, netPay: 10700 },
    { employeeId: "EMP004", employeeName: "吴胡兵", department: "运营部", position: "运行班长", baseSalary: 6000, positionAllowance: 800, performanceBonus: 1000, overtimePay: 1500, mealAllowance: 400, transportAllowance: 200, otherAllowance: 0, grossPay: 9900, socialSecurity: 600, housingFund: 300, incomeTax: 100, otherDeduction: 0, totalDeduction: 1000, netPay: 8900 },
    { employeeId: "EMP005", employeeName: "李慧", department: "财务部", position: "会计", baseSalary: 7000, positionAllowance: 0, performanceBonus: 800, overtimePay: 300, mealAllowance: 400, transportAllowance: 200, otherAllowance: 0, grossPay: 8700, socialSecurity: 700, housingFund: 350, incomeTax: 80, otherDeduction: 0, totalDeduction: 1130, netPay: 7570 },
    { employeeId: "EMP006", employeeName: "龙冠学", department: "运营部", position: "收运调度", baseSalary: 6000, positionAllowance: 500, performanceBonus: 800, overtimePay: 1000, mealAllowance: 400, transportAllowance: 200, otherAllowance: 0, grossPay: 8900, socialSecurity: 600, housingFund: 300, incomeTax: 60, otherDeduction: 0, totalDeduction: 960, netPay: 7940 },
    { employeeId: "EMP007", employeeName: "李莉", department: "综合部", position: "行政专员", baseSalary: 5500, positionAllowance: 0, performanceBonus: 600, overtimePay: 200, mealAllowance: 400, transportAllowance: 200, otherAllowance: 0, grossPay: 6900, socialSecurity: 550, housingFund: 275, incomeTax: 30, otherDeduction: 0, totalDeduction: 855, netPay: 6045 },
    { employeeId: "EMP008", employeeName: "鲁文辉", department: "技术部", position: "设备维修", baseSalary: 5500, positionAllowance: 300, performanceBonus: 600, overtimePay: 800, mealAllowance: 400, transportAllowance: 200, otherAllowance: 0, grossPay: 7800, socialSecurity: 550, housingFund: 275, incomeTax: 50, otherDeduction: 0, totalDeduction: 875, netPay: 6925 },
    { employeeId: "EMP009", employeeName: "卢梁", department: "运营部", position: "收运员", baseSalary: 4500, positionAllowance: 0, performanceBonus: 500, overtimePay: 600, mealAllowance: 400, transportAllowance: 300, otherAllowance: 0, grossPay: 6300, socialSecurity: 450, housingFund: 225, incomeTax: 0, otherDeduction: 0, totalDeduction: 675, netPay: 5625 },
    { employeeId: "EMP010", employeeName: "张伟", department: "运营部", position: "运行工", baseSalary: 4000, positionAllowance: 0, performanceBonus: 400, overtimePay: 400, mealAllowance: 400, transportAllowance: 200, otherAllowance: 0, grossPay: 5400, socialSecurity: 400, housingFund: 200, incomeTax: 0, otherDeduction: 0, totalDeduction: 600, netPay: 4800 }
  ],
  summary: {
    totalGross: 100500, totalDeduction: 11945, totalNet: 88555,
    avgNet: 8856, maxNet: 18800, minNet: 4800
  }
};

// --- 6. 系统元数据 ---
const hrMeta = {
  lastSyncTime: "2026-06-30 08:00:00",
  dataSource: "IMA知识库「伏泰HR人事管理」+ 钉钉考勤/通讯录",
  nextSyncTime: "2026-07-01 08:00:00",
  employeeCount: { total: 10, active: 9, probation: 1, departed: 0 },
  alerts: [
    { type: "contract_expiring", employeeId: "EMP004", employeeName: "吴胡兵", daysLeft: 193, message: "劳动合同将于2027-01-09到期" },
    { type: "contract_expiring", employeeId: "EMP009", employeeName: "卢梁", daysLeft: 395, message: "劳动合同将于2027-07-31到期" },
    { type: "probation_ending", employeeId: "EMP010", employeeName: "张伟", daysLeft: 76, message: "试用期将于2025-09-14结束" }
  ]
};
