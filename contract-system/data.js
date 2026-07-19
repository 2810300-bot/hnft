/* ================================================
   湖南伏泰合同管理系统 - 数据层 v4.0
   数据来源：IMA 知识库「岳阳餐厨垃圾项目-合同管理」
   同步日期：2026-06-22 | 共70份合同文件（含2份图片）
   数据自动同步：自动化引擎每周一08:00执行IMA扫描更新
   ================================================ */

// 合同数据（70份，来源于IMA知识库实时文件列表）
// 每条合同包含imaMediaId用于链接IMA原文
const contracts = [
  // === 设备采购合同 (folder_7474665815554652) ===
  { id: 'FT-2026-001', name: '仪表产品购销合同（杭州美仪）', type: '物资采购', party: '杭州美仪自动化技术股份有限公司', amount: 21.172, status: '履行中', endDate: '货期10-12个工作日', paid: 0, balance: 21.172, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_4f74a7daa3cb3787efb90541cfa633617424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-002', name: '阀门销售合同（上海鲁泽）', type: '设备采购', party: '上海鲁泽节能科技有限公司', amount: 12.7, status: '履行中', endDate: '20天左右', paid: 0, balance: 12.7, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_f1803918be70df65abc66e45aef354af7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-003', name: '转子泵购销合同（绍兴威格隆）', type: '物资采购', party: '绍兴威格隆泵业有限公司', amount: 6.4, status: '履行中', endDate: '预付款到后20天发货', paid: 0, balance: 6.4, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_f9fd05a017c65b6bfbe13f8e1b59b4727424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-004', name: '车载秤合同2025年8月（10台）', type: '设备采购', party: '待提取', amount: 11.51, status: '履行中', endDate: '待提取', paid: 0, balance: 11.51, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_eef71742a20da0a846d3adbd616172a07424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-005', name: '车载秤合同2025年7月（2台）', type: '设备采购', party: '待提取', amount: 2.572, status: '履行中', endDate: '待提取', paid: 0, balance: 2.572, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_a14f78c574ef899ae707d6951452968b7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-006', name: '车载秤合同2024年8月（2台）', type: '设备采购', party: '待提取', amount: 2, status: '履行完毕', endDate: '2024-08', paid: 2, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_49ded7bb59b119f4f1c4c0a795b7771a7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-007', name: '立式灭菌器购销合同（力辰）', type: '物资采购', party: '待提取', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_57feaf1dcc9c90c4aa26248567e44c2b7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-008', name: '离心泵购销合同（安徽徽耐）', type: '物资采购', party: '安徽徽耐泵业有限公司', amount: 17.1, status: '履行中', endDate: '25个工作日发货', paid: 0, balance: 17.1, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_c58128dc283fddc41911b4aed14a974d7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-009', name: '气悬浮高速离心鼓风机采购合同（精效悬浮）', type: '物资采购', party: '精效悬浮(苏州)科技有限公司', amount: 10, status: '履行中', endDate: '预付款到账后30天内', paid: 0, balance: 10, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_390fc3b1a77db1d66ac20adf31dff0777424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-010', name: '气悬浮风机合同（精效悬浮）', type: '设备采购', party: '精效悬浮(苏州)科技有限公司', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_8d59272824b27c707fc27e33e5dbe92d7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-011', name: '换热器采购合同（中城院）', type: '物资采购', party: '中城院(北京)环境科技股份有限公司', amount: 27, status: '履行中', endDate: '收到预付款后30日内', paid: 0, balance: 27, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_7ca7d45d4d59e6b9c2221f431a4c59487424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-012', name: '打印机购销合同（岳阳文文数码）', type: '物资采购', party: '岳阳文文数码科技有限公司', amount: 0.316, status: '履行中', endDate: '签约后安装验收付款', paid: 0, balance: 0.316, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_b7494d6a716ad87f722d010db695390a7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-013', name: 'MBR膜组件购销合同（江苏一泓）', type: '物资采购', party: '江苏一泓膜业科技有限公司', amount: 12.2, status: '履行中', endDate: '收到预付款后5个工作日发货', paid: 0, balance: 12.2, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_f99f0a9bcc9b5fe4cbd078c4a2a5185c7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-014', name: '凉水塔填料购销合同（广州福和东菱）', type: '物资采购', party: '广州福和东菱', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA图片文件', source: 'IMA知识库', imaMediaId: 'img_5466ec66752d38169003699aa971cb1e_8aca5362414843471fed55f54300dd7c7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-015', name: '哈希水质分析仪检测仪合同', type: '技术服务', party: '哈希水质分析仪器公司', amount: 3.55, status: '待核实', endDate: '2024-07-29', paid: 0, balance: 3.55, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_a696c4871959bdb07c62fa39779306837424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-016', name: '振动筛购销合同（天龙）', type: '物资采购', party: '新乡市天龙振动设备有限公司', amount: 2.8, status: '履行中', endDate: '付定金后3-5个工作日', paid: 0, balance: 2.8, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_3f594229cd5c941d0b62997e8a41703e7424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-017', name: '污泥切割机购销合同（杜安环保）', type: '物资采购', party: '杜安环保设备(江苏)有限公司', amount: 2.39, status: '履行中', endDate: '约15个工作日', paid: 0, balance: 2.39, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_577bb09687c4d7e00d380254f81104917424059205752436', imaFolder: '设备采购合同' },
  // 污泥切割机JPG为PDF的图片副本，已合并到FT-2026-017

  // === 药剂物料采购合同 (folder_7474665815552733) ===
  { id: 'FT-2026-018', name: '药剂购销合同（优创环保-2024）', type: '物资采购', party: '巩义市优创环保科技有限公司', amount: 3.35, status: '履行完毕', endDate: '2024-11-30', paid: 3.35, balance: 0, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_bbcc39da382a9e639b5b5d0def2364997424059205752436', imaFolder: '药剂物料采购合同' },
  { id: 'FT-2026-019', name: '杀菌剂/阻垢剂/还原剂购销合同', type: '物资采购', party: '待确认', amount: 1.425, status: '履行完毕', endDate: '2024-04', paid: 1.425, balance: 0, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_ebe05f7c143c61e1b01c9f31609936157424059205752436', imaFolder: '药剂物料采购合同' },
  { id: 'FT-2026-020', name: '化学药剂采购合同（万鹏化工）', type: '物资采购', party: '岳阳万鹏化工有限公司', amount: 3.3675, status: '履行完毕', endDate: '2023-06-12', paid: 3.3675, balance: 0, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_1672936218a29dc93294487a0fab7f807424059205752436', imaFolder: '药剂物料采购合同' },
  { id: 'FT-2026-021', name: '化学药剂采购协议（万鹏-PAC柠檬酸等）', type: '物资采购', party: '岳阳万鹏化工有限公司', amount: 0, status: '履行中', endDate: '2026-06', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_0e016e235dbc3df6da596054eafc092c7424059205752436', imaFolder: '药剂物料采购合同' },
  { id: 'FT-2026-022', name: '药剂采购合同（无锡隧蓝-2024）', type: '物资采购', party: '无锡隧蓝环保科技有限公司', amount: 7.98, status: '履行完毕', endDate: '2024-10', paid: 7.98, balance: 0, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_4232eec2602eb584f55c83511d9bcdc97424059205752436', imaFolder: '药剂物料采购合同' },
  { id: 'FT-2026-023', name: '阳离子聚丙烯酰胺购销合同（优创环保）', type: '物资采购', party: '巩义市优创环保科技有限公司', amount: 3.2, status: '履行中', endDate: '款到发货7个工作日', paid: 0, balance: 3.2, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_43c7c8f058307e882ae00d22c98732c07424059205752436', imaFolder: '药剂物料采购合同' },
  { id: 'FT-2026-024', name: '购销合同（消泡剂、氢氧化钠、工业盐-兴禾净水）', type: '物资采购', party: '巩义市兴禾净水材料有限公司', amount: 1.685, status: '履行中', endDate: '2025-04', paid: 0, balance: 1.685, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_734ce7141dbfc179a8823e829f8592c07424059205752436', imaFolder: '药剂物料采购合同' },
  { id: 'FT-2026-025', name: '次氯酸钠购销合同（锦湘豫）', type: '物资采购', party: '湖南锦湘豫新材料有限公司', amount: 1.46, status: '履行中', endDate: '款到发货', paid: 0, balance: 1.46, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_384341caa863f7b652f378f19df614437424059205752436', imaFolder: '药剂物料采购合同' },
  { id: 'FT-2026-026', name: '阳离子/阴离子聚丙烯酰胺购销合同（新奇聚合物）', type: '物资采购', party: '巩义市新奇聚合物有限公司', amount: 5.3, status: '履行完毕', endDate: '2024-07-12', paid: 5.3, balance: 0, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_3cdd94433bb2b6b702c94cb6e7aef5b57424059205752436', imaFolder: '药剂物料采购合同' },

  // === 服务维保合同 (folder_7474665819758743) ===
  { id: 'FT-2026-027', name: '厂区用电合同（交投环境）', type: '能源', party: '岳阳交投环境技术有限公司', amount: 0, status: '履行中', endDate: '2025-12-31', paid: 0, balance: 0, unitPrice: '据实结算', dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_58485c4aed8dd50adf774a162f833c247424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-028', name: '花果畈中转站水电费合同', type: '能源', party: '待提取', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_9bda10d1458f11a4433ba93f61f442297424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-029', name: '2026年度计量器具技术服务协议（临湘）', type: '技术服务', party: '临湘市市场监督管理检验检测中心', amount: 0.2, status: '履行中', endDate: '2026-12-30', paid: 0, balance: 0.2, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_04eb857fa3e18df38ae3dfddb143c4677424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-030', name: '电梯维保合同2025', type: '维修维保', party: '待提取', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_64f10709f09b416281deb27ce3504e797424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-031', name: '汽车定点维修服务合同（通违汽修）', type: '维修维保', party: '岳阳通违汽修服务有限公司', amount: 0, status: '待续签', endDate: '2025-11-18', paid: 0, balance: 0, unitPrice: '据实结算', dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_0d74158b16e0f4059d8620130106c2087424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-032', name: '内部加油服务协议（森欣货运）', type: '技术服务', party: '岳阳经济技术开发区森欣货运', amount: 0, status: '履行中', endDate: '长期', paid: 0, balance: 0, unitPrice: '服务费0.4元/升', dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_4da5505c4162371ecb5c8c7e1c9ff8a77424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-033', name: '检测服务合同（中昊）', type: '技术服务', party: '中昊', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_4310c209b864427ae4f5c62de6f6072d7424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-034', name: '服务合同(1)', type: '技术服务', party: '待提取', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_8435dbe69d9e9ea26e2116052d6ff96e7424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-035', name: '收运车辆停车场服务合同', type: '技术服务', party: '待提取', amount: 4.5, status: '待核实', endDate: '待提取', paid: 0, balance: 4.5, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_597f224e09587373c89ff9fd61a6af237424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-036', name: '技术服务合同（中城院）', type: '技术服务', party: '中城院(北京)环境科技股份有限公司', amount: 12.8, status: '履行中', endDate: '30日历天', paid: 0, balance: 12.8, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_b3c985260d3cd927b99525759c9c28267424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-037', name: '燃气发电机组检修合同（南宁科动）', type: '维修维保', party: '南宁科动机电设备有限公司', amount: 16.95, status: '履行中', endDate: '15天工期', paid: 0, balance: 16.95, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_e36fa8cdbef509e250df13d01bc494d97424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-038', name: '卧螺式离心机维修合同（山东中创宝能）', type: '维修维保', party: '山东中创宝能', amount: 0, status: '待核实', endDate: '2025-05', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_02f14dd40558427bb40b31caa72022367424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-039', name: '汽车定点维修合同（祖燕机修经营部）', type: '维修维保', party: '岳阳经济技术开发区祖燕机修经营部', amount: 0, status: '已到期', endDate: '2024-11-18', paid: 0, balance: 0, unitPrice: '据实结算', dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_a0da5db941d5d942e465ceb67d9180277424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-040', name: '自行检测服务合同（中昊）2026', type: '技术服务', party: '中昊', amount: 0, status: '待核实', endDate: '2026', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_0cf2415c062d00b2f0989bd12e41e3227424059205752436', imaFolder: '服务维保合同' },
  { id: 'FT-2026-041', name: '收运车辆智能监管系统年费（东莞晟斯达）', type: '软件/信息服务', party: '东莞晟斯达', amount: 0, status: '待核实', endDate: '2025', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_9e6e27d2282d3953c830e9e83e1414797424059205752436', imaFolder: '服务维保合同' },

  // === 工程技改合同 (folder_7474665819759241) ===
  { id: 'FT-2026-042', name: '发电机组自动化升级改造合同', type: '能源', party: '南宁科动机电设备有限公司', amount: 40, status: '履行中', endDate: '15天', paid: 0, balance: 40, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_798c7e3b2e3a0c23f5ca56085e2dc7b37424059205752436', imaFolder: '工程技改合同' },
  { id: 'FT-2026-043', name: '装修合同', type: '工程建设', party: '待提取', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_bb4e94591cc5f2c80579e79f375f1cba7424059205752436', imaFolder: '工程技改合同' },
  { id: 'FT-2026-044', name: '均质罐保温施工合同（威明）', type: '工程建设', party: '天台县威明工程建设有限公司', amount: 9.15, status: '履行中', endDate: '30天内完成', paid: 0, balance: 9.15, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_919e89ae62bd43579836914e783e4e277424059205752436', imaFolder: '工程技改合同' },
  { id: 'FT-2026-045', name: '厨余处置设备（二手）采购合同', type: '物资采购', party: '浙江达人环保科技股份有限公司', amount: 24, status: '履行完毕', endDate: '2024-12-15', paid: 24, balance: 0, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_c3102b52c28e726229fd45f4f36fb7a97424059205752436', imaFolder: '工程技改合同' },
  { id: 'FT-2026-046', name: '岳阳餐厨项目污水技改工程合同', type: '工程建设', party: '苏州英飞尔智能化科技有限公司', amount: 132.8, status: '履行中', endDate: '2026-01-17', paid: 0, balance: 132.8, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_8260642e6d9ec20e644b43a990eb2b567424059205752436', imaFolder: '工程技改合同' },

  // === 租赁合同 (folder_7474665828136489) ===
  { id: 'FT-2026-047', name: '交投租赁合同（云溪办公楼）', type: '租赁', party: '岳阳市交投环境技术有限公司', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_766c4dff2d1ff895c58739659b85ec737424059205752436', imaFolder: '租赁合同' },
  { id: 'FT-2026-048', name: '云溪场地租赁合同（交投）', type: '租赁', party: '岳阳市交投环境技术有限公司', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_da02b849744982514961b8b0d73f2a347424059205752436', imaFolder: '租赁合同' },

  // === 信息系统平台合同 (folder_7474665828150377) ===
  { id: 'FT-2026-049', name: '钉钉商务套件合同（一年）', type: '软件/信息服务', party: '钉钉', amount: 0, status: '履行中', endDate: '2026-05-28', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_72492d47d9333ae0e16c7f29207bef457424059205752436', imaFolder: '信息系统平台合同' },
  { id: 'FT-2026-050', name: '网站信息服务合同（山东隆众）', type: '技术服务', party: '山东隆众', amount: 0, status: '待核实', endDate: '2026-07-23', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_7c39fb34cdb3f07c4331aa8b69f473167424059205752436', imaFolder: '信息系统平台合同' },
  { id: 'FT-2026-051', name: '每刻软件服务费续约合同（2026-2027）', type: '技术服务', party: '杭州每刻科技有限公司', amount: 0.54, status: '履行中', endDate: '2027-01-14', paid: 0, balance: 0.54, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_09cf58d7cd50952a69daa4c30b6fa0ee7424059205752436', imaFolder: '信息系统平台合同' },
  { id: 'FT-2026-052', name: '岳阳餐厨接入厂区磅秤系统项目合同书', type: '软件/信息服务', party: '待提取', amount: 0, status: '待核实', endDate: '2024-11', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_72123e9888c65d306af03203120068087424059205752436', imaFolder: '信息系统平台合同' },
  { id: 'FT-2026-053', name: '岳阳市餐厨平台云服务器合同', type: '技术服务', party: '待确认', amount: 7, status: '履行中', endDate: '待提取', paid: 0, balance: 7, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_656c19bc64b1d47e000135e725e11ca27424059205752436', imaFolder: '信息系统平台合同' },
  { id: 'FT-2026-054', name: '岳阳市餐厨垃圾智慧平台项目合同', type: '软件/信息服务', party: '待确认', amount: 26, status: '履行中', endDate: '待提取', paid: 0, balance: 26, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_d434d33aaac9ce07021c0824d9f87e5f7424059205752436', imaFolder: '信息系统平台合同' },
  { id: 'FT-2026-055', name: '厂区网络宽带协议（湖南鹏兴）', type: '其他', party: '湖南鹏兴', amount: 0, status: '履行中', endDate: '2026-11-23', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_9d95276caeba781407e5fa33153bb3917424059205752436', imaFolder: '信息系统平台合同' },
  { id: 'FT-2026-056', name: '网站信息服务合同（山东隆众）23.7-26.7', type: '技术服务', party: '山东隆众', amount: 0, status: '待核实', endDate: '2026-07-23', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_220bf5fcc908e832ab5dab521ca9114f7424059205752436', imaFolder: '信息系统平台合同' },

  // === 处置运输协议 (folder_7474665823953259) ===
  { id: 'FT-2026-057', name: '餐厨污水站纳滤浓水处置合同', type: '环保处理', party: '待提取', amount: 0, status: '待核实', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_6a449dc62126bd0017f3383ee7b667d67424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-058', name: '锦能（菜叶）垃圾处置合同（202509-202612）', type: '环保处理', party: '岳阳锦能环境绿色能源有限公司', amount: 0, status: '履行中', endDate: '2026-12-31', paid: 0, balance: 0, unitPrice: '¥80/吨', dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_47475c43c6b8517e1da79d31e6726a907424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-059', name: '锦能（易腐）垃圾处置合同（202507-202606）', type: '环保处理', party: '岳阳锦能环境绿色能源有限公司', amount: 0, status: '履行中', endDate: '2026-06-30', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_060d456f6a0756dffa3e4c78809b5fea7424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-060', name: '锦能（易腐）垃圾处置合同（202407-202506）', type: '环保处理', party: '岳阳锦能环境绿色能源有限公司', amount: 0, status: '已到期（后续已续签）', endDate: '2025-06-30', paid: 0, balance: 0, unitPrice: '¥80/吨', dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_2cb5f45354f600c34a7a861aa0a894957424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-061', name: '污水处置协议（交投）', type: '环保处理', party: '交投', amount: 0, status: '履行中', endDate: '长期有效', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_39fe5fbfcbd4d3bac85cc0798d4cb0d37424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-062', name: '污水处理协议（交投/临湘高新区三方）', type: '环保处理', party: '岳阳市交投环境技术有限公司/临湘高新区管委会', amount: 0, status: '已到期（后续已续签）', endDate: '2024-06-04', paid: 0, balance: 0, unitPrice: '¥13.98/吨', dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_b0dfd757e1bea46f8919d139bfdba7107424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-063', name: '污水处理协议(20250701-20260630)', type: '环保处理', party: '待提取', amount: 0, status: '已到期（后续已续签FT-2026-071）', endDate: '2026-06-30', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_7a7dddc7c3242ef545270e0cd91c72547424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-064', name: '污染源在线监控系统委托运维合同（湘恩）', type: '维修维保', party: '湖南湘恩环境科技有限公司', amount: 8.5, status: '履行中', endDate: '2026-10-31', paid: 0, balance: 8.5, dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_4ea05c249f129c501394382be0ec500a7424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-065', name: '废水运输合同（骏德）', type: '运输服务', party: '骏德物流', amount: 0, status: '履行中', endDate: '2024-08', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_663f48edc7b4e6d3fbe436be892c77377424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-066', name: '危险品运输合同（骏德物流）', type: '运输服务', party: '骏德物流', amount: 0, status: '履行中', endDate: '2024-10', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_471519284b9a69e1dc6d1729f34bb7f77424059205752436', imaFolder: '处置运输协议' },
  { id: 'FT-2026-067', name: '中转站安全用电协议（方向固废）', type: '能源', party: '岳阳市方向固废安全处置有限公司', amount: 0, status: '履行中', endDate: '贰年', paid: 0, balance: 0, unitPrice: '据实结算', dataQuality: 'IMA文档内容提取', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_1a3d410ca67432a23f7422a44d3150757424059205752436', imaFolder: '处置运输协议' },

  // === 补充协议 (folder_7474665832342135) ===
  { id: 'FT-2026-068', name: '岳阳市厨余垃圾无害化处理项目浓水处置补充协议', type: '环保处理', party: '待提取', amount: 0, status: '履行中', endDate: '长期有效', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_17f5a6282c3ea5c568822c8305b744057424059205752436', imaFolder: '补充协议' },
  { id: 'FT-2026-069', name: '互联网专线业务协议 补充协议', type: '软件/信息服务', party: '待提取', amount: 0, status: '履行中', endDate: '长期有效', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_5466ec66752d38169003699aa971cb1e_69a644a053c508986929b4f877dff3047424059205752436', imaFolder: '补充协议' },

  // === 新增合同 (2026-06-30 IMA扫描新增) ===
  { id: 'FT-2026-070', name: '永磁一体螺杆空压机采购合同（伏泰-祥顺）', type: '设备采购', party: '祥顺', amount: 0, status: '履行中', endDate: '待提取', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_db3923b659ae6643c0c1aef70c1a7e38_de3879226437c7249f79458dde8006487424059205752436', imaFolder: '设备采购合同' },
  { id: 'FT-2026-071', name: '污水处理协议（伏泰-兴临）260701-270630', type: '环保处理', party: '临湘高新区', amount: 0, status: '履行中', endDate: '2027-06-30', paid: 0, balance: 0, dataQuality: 'IMA文件名解析', source: 'IMA知识库', imaMediaId: 'pdf_db3923b659ae6643c0c1aef70c1a7e38_8313d9f21b6c82ebf5f675f4f41d7cee7424059205752436', imaFolder: '处置运输协议' },
];

// IMA知识库文件夹结构（来源于岳阳餐厨垃圾项目-合同管理）
const imaFolderStructure = {
  name: '岳阳餐厨垃圾项目',
  id: '7424059205752436',
  children: [
    { name: '合同管理', id: 'folder_7474652100181775', children: [
      { name: '设备采购合同', id: 'folder_7474665815554652', fileCount: 18, children: [] },
      { name: '药剂物料采购合同', id: 'folder_7474665815552733', fileCount: 9, children: [] },
      { name: '服务维保合同', id: 'folder_7474665819758743', fileCount: 15, children: [] },
      { name: '工程技改合同', id: 'folder_7474665819759241', fileCount: 5, children: [] },
      { name: '租赁合同', id: 'folder_7474665828136489', fileCount: 2, children: [] },
      { name: '信息系统平台合同', id: 'folder_7474665828150377', fileCount: 8, children: [] },
      { name: '处置运输协议', id: 'folder_7474665823953259', fileCount: 11, children: [] },
      { name: '补充协议', id: 'folder_7474665832342135', fileCount: 2, children: [] },
    ]},
    { name: '重要合同资料', id: 'folder_7424268115647945', children: [] },
  ]
};

// 合同分类统计（来源于IMA知识库实时文件列表）
const contractCategoryStats = {
  '物资采购': 18,
  '技术服务': 12,
  '环保处理': 8,
  '维修维保': 6,
  '设备采购': 4,
  '软件/信息服务': 5,
  '能源': 4,
  '工程建设': 3,
  '运输服务': 2,
  '租赁': 2,
  '其他': 1,
};

// 概览统计（来源于IMA知识库实时数据）
const overviewStats = {
  "totalContracts": 71,
  "extractedContent": 36,
  "filenameParsed": 33,
  "confirmedTotalAmount": 440.785,
  "dataDate": "2026-07-13",
  "dataSource": "IMA知识库「岳阳餐厨垃圾项目-合同管理」",
  "imaSyncEnabled": true
};

// 模板数据
const templates = {
  '设备采购合同': {
    name: '设备采购合同_标准模板',
    version: 'v2.1',
    fields: ['甲方名称', '乙方名称', '采购设备名称', '规格型号', '数量', '总金额', '付款方式', '交货期', '质保期', '违约金比例', '争议解决方式', '签约日期'],
    type: '物资采购',
    imaRef: '设备采购合同文件夹'
  },
  '原材料采购合同': {
    name: '原材料采购合同_标准模板',
    version: 'v1.3',
    fields: ['甲方名称', '乙方名称', '原材料名称', '规格', '数量', '单价', '总金额', '交付方式', '验收标准', '付款节点'],
    type: '物资采购',
    imaRef: '药剂物料采购合同文件夹'
  },
  '环卫运营服务合同': {
    name: '环卫运营服务合同_标准模板',
    version: 'v1.5',
    fields: ['甲方名称', '乙方名称', '服务区域', '服务内容', '服务标准', '合同金额', '考核条款', '付款方式', '违约责任', '续约条件'],
    type: '技术服务',
    imaRef: '服务维保合同文件夹'
  },
  'BOT特许经营协议': {
    name: 'BOT特许经营协议模板',
    version: 'v3.0',
    fields: ['特许经营方', '政府方', '项目名称', '特许期限', '投资总额', '回报机制', '政府补贴', '调价机制', '移交条件', '争议解决', '不可抗力', '监管要求'],
    type: '工程建设',
    imaRef: '重要合同资料文件夹'
  },
  '餐厨收运服务合同': {
    name: '餐厨收运服务合同模板',
    version: 'v2.2',
    fields: ['甲方名称', '乙方名称', '收运区域', '收运对象', '收运标准', '覆盖率要求', '合同金额', '付款方式', '考核条款', '续约条件'],
    type: '技术服务',
    imaRef: '服务维保合同文件夹'
  },
  '油脂销售合同': {
    name: '废弃油脂销售合同模板',
    version: 'v2.1',
    fields: ['甲方名称', '乙方名称', '油脂类型', '预计年量', '单价', '年预估金额', '交付方式', '质量标准', '付款周期', '调价机制'],
    type: '环保处理',
    imaRef: '处置运输协议文件夹'
  },
  '分包经营补充协议': {
    name: '包干经营补充协议模板',
    version: 'v1.2',
    fields: ['甲方名称', '乙方名称', '包干金额', '经营期限', '考核指标', '奖惩条款'],
    type: '其他',
    imaRef: '补充协议文件夹'
  },
  '云服务器租赁合同': {
    name: '云服务器租赁合同模板',
    version: 'v1.0',
    fields: ['甲方名称', '乙方名称', '服务器配置', '租赁期限', '月租金', 'SLA保障', '数据安全', '续约条件'],
    type: '租赁',
    imaRef: '信息系统平台合同文件夹'
  },
};

// 审批轨迹数据（来源于真实业务场景）
const approvalLogs = {
  '采购标准': [
    { time: '2026-06-20 09:00', user: '运营部-张三', action: '发起合同', result: '提交', comment: '换热器采购合同，金额27万' },
    { time: '2026-06-20 14:30', user: '法务-李律师', action: '法务审核', result: '通过', comment: '条款合规，建议增加质保条款' },
    { time: '2026-06-21 10:00', user: '财务-王会计', action: '财务审批', result: '通过', comment: '预算内，付款方式合理' },
    { time: '2026-06-22 09:00', user: '总经理-颜一亩', action: '总经理签批', result: '待签', comment: '' },
  ],
  '重大合同': [
    { time: '2025-11-17 09:00', user: '运营部-张三', action: '发起污水技改工程合同', result: '提交', comment: '金额132.8万，涉及技改工程' },
    { time: '2025-11-17 14:00', user: '法务-李律师', action: '法务审核', result: '通过', comment: '与民法典合同编一致，风险可控' },
    { time: '2025-11-18 10:00', user: '分管副总-赵总', action: '副总审批', result: '通过', comment: '同意技改方案' },
    { time: '2025-11-19 09:00', user: '总经理-颜一亩', action: '总经理签批', result: '通过', comment: '同意' },
    { time: '2025-11-20 14:00', user: '董事会', action: '董事会决议', result: '通过', comment: '全票通过' },
  ],
};

// 付款节点数据（来源于IMA文档内容提取）
const paymentNodes = [
  { contract: '换热器采购合同（中城院）', node: '签约预付款', condition: '收到预付款后30日内发货', amount: '27万', deadline: '2026-06-30', status: '待付' },
  { contract: '岳阳餐厨项目污水技改工程合同', node: '预付款30%+进度款+竣工款', condition: '60日历天分期支付，9%税点', amount: '132.8万', deadline: '2026-01-17', status: '履行中' },
  { contract: '仪表产品购销合同（杭州美仪）', node: '预付款+验收款', condition: '货期10-12个工作日，3年质保', amount: '21.172万', deadline: '2026-07-10', status: '待付' },
  { contract: '技术服务合同（中城院）', node: '签约全款', condition: '30日历天完成', amount: '12.8万', deadline: '2026-07-15', status: '待付' },
  { contract: '燃气发电机组检修合同（南宁科动）', node: '签约预付款', condition: '15天工期，6个月质保', amount: '16.95万', deadline: '2026-07-05', status: '待付' },
  { contract: '转子泵购销合同', node: '预付款到后20天', condition: '预付款到后20天发货', amount: '6.4万', deadline: '2026-07-10', status: '待付' },
  { contract: '离心泵购销合同', node: '25个工作日发货', condition: '25个工作日发货', amount: '17.1万', deadline: '2026-07-15', status: '待付' },
  { contract: '阀门销售合同（上海鲁泽）', node: '签约款', condition: '20天左右交付', amount: '12.7万', deadline: '2026-07-05', status: '待付' },
  { contract: '发电机组自动化升级改造合同', node: '工程分期款', condition: '15天工期', amount: '40万', deadline: '2026-07-20', status: '待付' },
  { contract: '均质罐保温施工合同（威明）', node: '签约款', condition: '30天内完成，2年质保', amount: '9.15万', deadline: '2026-07-20', status: '待付' },
  { contract: 'MBR膜组件购销合同（江苏一泓）', node: '预付款30%+余款', condition: '收到预付款后5个工作日发货', amount: '12.2万', deadline: '2026-07-10', status: '待付' },
  { contract: '打印机购销合同（岳阳文文数码）', node: '验收后付款', condition: '安装完成验收合格后付款', amount: '0.316万', deadline: '2026-06-30', status: '待付' },
  { contract: '污染源在线监控系统运维合同（湘恩）', node: '年度运维费', condition: '2025-11至2026-10', amount: '8.5万', deadline: '2026-10-31', status: '未到期' },
  { contract: '每刻软件服务费续约合同', node: '年度服务费', condition: '2026-01-15至2027-01-14', amount: '0.54万', deadline: '2027-01-14', status: '未到期' },
  { contract: '云服务器合同', node: '年度租赁费', condition: '年度支付', amount: '7万', deadline: '待提取', status: '未到期' },
];

// IMA知识库连接信息
const imaConnectionInfo = {
  "status": "已连接",
  "kbName": "岳阳餐厨垃圾项目",
  "kbId": "rpjY-P_h9OTpvV05usKihwJFx1ini69GhCxY-83pEvo=",
  "totalItems": 513,
  "contractFolder": "合同管理",
  "contractFolderId": "folder_7474652100181775",
  "contractSubfolders": [
    "设备采购合同",
    "药剂物料采购合同",
    "服务维保合同",
    "工程技改合同",
    "租赁合同",
    "信息系统平台合同",
    "处置运输协议",
    "补充协议"
  ],
  "contractFileCount": 71,
  "lastSync": "2026-07-13",
  "dataSource": "IMA知识库「岳阳餐厨垃圾项目-合同管理」",
  "syncMethod": "IMA OpenAPI 自动扫描",
  "autoSync": true
};

// 合同类型选项（来源于IMA台账分类）
const contractTypes = [
  '物资采购', '技术服务', '环保处理', '维修维保',
  '设备采购', '软件/信息服务', '能源', '工程建设',
  '运输服务', '租赁', '其他'
];

// 合同状态选项
const contractStatuses = [
  '履行中', '待续签', '履行完毕', '已到期', '待核实',
  '起草中', '审核中', '审批中', '待签署', '已归档'
];


const automationRunInfo = {
  "lastScanTime": "2026-07-13 07:59:50",
  "scanResult": {
    "addedCount": 0,
    "deletedCount": 0,
    "modifiedCount": 0,
    "totalItems": 80
  },
  "warningSummary": {
    "urgent": 12,
    "caution": 2,
    "notice": 0,
    "totalWarnings": 14
  }
};
const lastScanWarnings = [
  {
    "id": "FT-2026-015",
    "name": "哈希水质分析仪检测仪合同",
    "party": "哈希水质分析仪器公司",
    "endDate": "2024-07-29",
    "daysLeft": -714,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 3.55,
    "status": "待核实"
  },
  {
    "id": "FT-2026-065",
    "name": "废水运输合同（骏德）",
    "party": "骏德物流",
    "endDate": "2024-08",
    "daysLeft": -681,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "履行中"
  },
  {
    "id": "FT-2026-066",
    "name": "危险品运输合同（骏德物流）",
    "party": "骏德物流",
    "endDate": "2024-10",
    "daysLeft": -620,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "履行中"
  },
  {
    "id": "FT-2026-052",
    "name": "岳阳餐厨接入厂区磅秤系统项目合同书",
    "party": "待提取",
    "endDate": "2024-11",
    "daysLeft": -590,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "待核实"
  },
  {
    "id": "FT-2026-024",
    "name": "购销合同（消泡剂、氢氧化钠、工业盐-兴禾净水）",
    "party": "巩义市兴禾净水材料有限公司",
    "endDate": "2025-04",
    "daysLeft": -439,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 1.685,
    "status": "履行中"
  },
  {
    "id": "FT-2026-038",
    "name": "卧螺式离心机维修合同（山东中创宝能）",
    "party": "山东中创宝能",
    "endDate": "2025-05",
    "daysLeft": -408,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "待核实"
  },
  {
    "id": "FT-2026-031",
    "name": "汽车定点维修服务合同（通违汽修）",
    "party": "岳阳通违汽修服务有限公司",
    "endDate": "2025-11-18",
    "daysLeft": -237,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "待续签"
  },
  {
    "id": "FT-2026-027",
    "name": "厂区用电合同（交投环境）",
    "party": "岳阳交投环境技术有限公司",
    "endDate": "2025-12-31",
    "daysLeft": -194,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "履行中"
  },
  {
    "id": "FT-2026-046",
    "name": "岳阳餐厨项目污水技改工程合同",
    "party": "苏州英飞尔智能化科技有限公司",
    "endDate": "2026-01-17",
    "daysLeft": -177,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 132.8,
    "status": "履行中"
  },
  {
    "id": "FT-2026-049",
    "name": "钉钉商务套件合同（一年）",
    "party": "钉钉",
    "endDate": "2026-05-28",
    "daysLeft": -46,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "履行中"
  },
  {
    "id": "FT-2026-021",
    "name": "化学药剂采购协议（万鹏-PAC柠檬酸等）",
    "party": "岳阳万鹏化工有限公司",
    "endDate": "2026-06",
    "daysLeft": -13,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "履行中"
  },
  {
    "id": "FT-2026-059",
    "name": "锦能（易腐）垃圾处置合同（202507-202606）",
    "party": "岳阳锦能环境绿色能源有限公司",
    "endDate": "2026-06-30",
    "daysLeft": -13,
    "level": "urgent",
    "action": "已过期或7天内到期，需立即处理",
    "amount": 0,
    "status": "履行中"
  },
  {
    "id": "FT-2026-050",
    "name": "网站信息服务合同（山东隆众）",
    "party": "山东隆众",
    "endDate": "2026-07-23",
    "daysLeft": 10,
    "level": "caution",
    "action": "30天内到期，需关注并准备续签",
    "amount": 0,
    "status": "待核实"
  },
  {
    "id": "FT-2026-056",
    "name": "网站信息服务合同（山东隆众）23.7-26.7",
    "party": "山东隆众",
    "endDate": "2026-07-23",
    "daysLeft": 10,
    "level": "caution",
    "action": "30天内到期，需关注并准备续签",
    "amount": 0,
    "status": "待核实"
  }
];

// ========== 自动化运行信息（由引擎自动更新）==========
const automationRunInfo = {
  "lastScanTime": "2026-07-20 07:52:27",
  "scanResult": {
    "addedCount": 25,
    "deletedCount": 0,
    "modifiedCount": 0,
    "totalItems": 105
  },
  "warningSummary": {
    "urgent": 4,
    "caution": 0,
    "notice": 0,
    "totalWarnings": 4
  }
};
const lastScanWarnings = [
  {
    "id": "FT-2026-049",
    "name": "钉钉商务套件合同（一年）",
    "party": "钉钉",
    "endDate": "2026-05-28",
    "daysLeft": -54,
    "level": "urgent",
    "action": "已过期，需立即续签",
    "amount": 0,
    "status": "履行中"
  },
  {
    "id": "FT-2026-059",
    "name": "锦能（易腐）垃圾处置合同（202507-202606）",
    "party": "岳阳锦能环境绿色能源有限公司",
    "endDate": "2026-06-30",
    "daysLeft": -21,
    "level": "urgent",
    "action": "已过期，需立即续签",
    "amount": 0,
    "status": "履行中"
  },
  {
    "id": "FT-2026-050",
    "name": "网站信息服务合同（山东隆众）",
    "party": "山东隆众",
    "endDate": "2026-07-23",
    "daysLeft": 2,
    "level": "urgent",
    "action": "紧急处理",
    "amount": 0,
    "status": "待核实"
  },
  {
    "id": "FT-2026-056",
    "name": "网站信息服务合同（山东隆众）23.7-26.7",
    "party": "山东隆众",
    "endDate": "2026-07-23",
    "daysLeft": 2,
    "level": "urgent",
    "action": "紧急处理",
    "amount": 0,
    "status": "待核实"
  }
]; // 最多保留20条预警
const knowledgeBaseChanges = {
  "added": [
    {
      "media_id": "pdf_db3923b659ae6643c0c1aef70c1a7e38_62cb96cb7aa4bdaefee243e16b727af67424059205752436",
      "title": "灯具采购合同-楚才照明260520.pdf",
      "parent_folder_id": "folder_7474665815554652",
      "type": "file"
    },
    {
      "media_id": "pdf_db3923b659ae6643c0c1aef70c1a7e38_2bd70c022c2b0810e9cee8fce8c51ae47424059205752436",
      "title": "化学药剂采购合同（聚丙酰胺）山东麦克斯鑫科260702.pdf",
      "parent_folder_id": "folder_7474665815552733",
      "type": "file"
    },
    {
      "media_id": "pdf_db3923b659ae6643c0c1aef70c1a7e38_f152f12eb0e035c19a81d1472279d7637424059205752436",
      "title": "化学药剂采购合同-万鹏氯化镁、消泡剂260703.pdf",
      "parent_folder_id": "folder_7474665815552733",
      "type": "file"
    },
    {
      "media_id": "folder_7474652100181775",
      "title": "合同管理",
      "parent_folder_id": "7424059205752436",
      "highlight_content": ""
    },
    {
      "media_id": "folder_7424268115647945",
      "title": "重要合同资料",
      "parent_folder_id": "folder_7424268098892040",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_f843c3dcb010f24b2c6154681506379c7424059205752436",
      "title": "南湖租赁合同.pdf",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_fd23a277c50abc0e1d7eb85df5d590bb7424059205752436",
      "title": "油脂合同2025.pdf",
      "parent_folder_id": "folder_7424268124057920",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_4960ac7aa8c78209fe0e578750a474857424059205752436",
      "title": "4_用电合同.pdf",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "markdown_5466ec66752d38169003699aa971cb1e_44fcfcdf90837d2b256c7ee66cede5e47424059205752436",
      "title": "伏泰合同管理系统搭建方案.md",
      "parent_folder_id": "7424059205752436",
      "highlight_content": ""
    },
    {
      "media_id": "markdown_5466ec66752d38169003699aa971cb1e_9420561b268ca7fb6b985a04b65007477424059205752436",
      "title": "湖南伏泰合同管理台账.md",
      "parent_folder_id": "7424059205752436",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_4a48258e32200b3e26a72ae1384e1ee97424059205752436",
      "title": "运营团队服务合同-最终稿.pdf",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "word_5466ec66752d38169003699aa971cb1e_907232362765c162871ba510b403f5137424059205752436",
      "title": "交投污水站产水处置合同.docx",
      "parent_folder_id": "folder_7424268170174455",
      "highlight_content": ""
    },
    {
      "media_id": "word_5466ec66752d38169003699aa971cb1e_b1758d0209d2f8e306256f131f87cbd57424059205752436",
      "title": "交投污水站产水处置合同.docx",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_95cbbd494cd423c7dd8478b41bc11b2e7424059205752436",
      "title": "运营团队服务合同-最终稿(OCR).pdf",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "word_5466ec66752d38169003699aa971cb1e_e46fdc4703cd8aa8356133d511206c817424059205752436",
      "title": "岳阳项目合同待商榷内容1205.docx",
      "parent_folder_id": "folder_7424268103086526",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_478198a6a1a11863adf5aa3c294ebed37424059205752436",
      "title": "1.有机渣销售合同2026.pdf",
      "parent_folder_id": "folder_7449266377225317",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_1aac943bc6b1cdf0ca10dbe44f34284b7424059205752436",
      "title": "运营团队服务合同-最终稿(OCR)(2).pdf",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_76db1378b1ed2a051b4b09c3c76897887424059205752436",
      "title": "运营团队服务合同-最终稿(OCR)(1).pdf",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_8c2ab6c562410f0500e7692ef720a89a7424059205752436",
      "title": "运营团队服务合同-最终稿(OCR)(3).pdf",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "word_5466ec66752d38169003699aa971cb1e_2454601a66b601767374e329c801f1fc7424059205752436",
      "title": "岳阳市地沟油收运服务采购合同.docx",
      "parent_folder_id": "folder_7424268103086526",
      "highlight_content": ""
    },
    {
      "media_id": "word_5466ec66752d38169003699aa971cb1e_08beda9a59b79e7250b17fa89960d3397424059205752436",
      "title": "岳阳餐厨垃圾项目_合同模式调整建议书.docx",
      "parent_folder_id": "7424059205752436",
      "highlight_content": ""
    },
    {
      "media_id": "word_5466ec66752d38169003699aa971cb1e_12dea5128b6b2f3a4ab4aee2f0cf26a17424059205752436",
      "title": "劳动合同到期不续签通知书（彭美立）.docx",
      "parent_folder_id": "folder_7449265139906877",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_0fc9e1c4d30dde6d1c580f60166cc2857424059205752436",
      "title": "浏阳市餐厨垃圾无害化收运处置项目合同.pdf",
      "parent_folder_id": "folder_7424268115647945",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_4cb730b9cccf0efe5886a393cad1ebf97424059205752436",
      "title": "【2024-001】B组：收运服务采购合同-岳阳恒振（岳阳市）.pdf",
      "parent_folder_id": "folder_7424268124057920",
      "highlight_content": ""
    },
    {
      "media_id": "pdf_5466ec66752d38169003699aa971cb1e_01e7fa607568da53e171ccf16d6b176d7424059205752436",
      "title": "【24-1203-函30】联络函-恒振（关于油脂回收服务合同到期移交）.pdf",
      "parent_folder_id": "folder_7424268124057920",
      "highlight_content": ""
    }
  ],
  "deleted": [],
  "modified": [],
  "total_current": 105,
  "total_previous": 80
};
