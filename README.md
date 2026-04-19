
# 智能 AGV 仓库管理系统 (WMS)

这是一个集成了现代 Web 技术与工业通讯协议的智能仓储解决方案。系统核心在于通过 FastAPI 驱动的后端，连接 Tortoise-ORM 数据库、数字孪生 Web 前端（Vue），以及基于 TCP 的 AGV 小车通讯模拟器。

## 系统架构

本系统采用高效的异步架构，实现了物理设备与管理界面的实时同步。



## 管理后台 (Dashboard)

系统的核心管理界面，提供可视化的库位矩阵管理、实时任务指派以及 AGV 状态监控。

### 1. 库位大屏数字孪生矩阵

基于 Vue 和响应式数据绑定的数字孪生大屏。矩阵实时展示几百个库位的当前状态：



* **变灰**：从 WS 获取到 `mission_completed` 信号，起点库位变为空闲（0）。
* **变蓝**：新任务开始，终点库位变为锁定/占用（2/1）。

### 2. 用户与权限管理

系统集成基础的权限管理功能，支持多用户登录与模块化权限指派：



### 3. 系统登录

系统提供安全的 OAuth2 登录接口，采用 JWT Token 进行状态管理，支持在 `.env` 中安全配置敏感秘钥：


## 工业协议与调试 (TCP Communication)

系统后端集成了原生的 TCP 监听服务（默认 13245 端口），专门用于对接真实的硬件，处理复杂的字节流通讯。

### 1. 硬件信号调试机制

通过 **网络调试助手 (NetAssist)** 模拟物理 AGV 的反馈信号。核心调试流程如下：



* **发送协议 (HEX)**：发送 `[4字节hardware_id][0x01]`。
* **示例报文**：发送 `32 39 37 38 01`，代表 `hardware_id='2978'` 的任务已完成。
* **后端反馈**：后端收到信号后完成数据库事务，并通过 WS 广播通知前端，最后向助手回传 `32 39 37 38 EE` 闭环确认包。
* <img width="802" height="696" alt="{6C09BCCF-50C6-4556-B056-D070FDC3A931}" src="https://github.com/user-attachments/assets/0200e4f6-855d-4d2a-9ee4-acaeb1939a6f" />
<img width="1591" height="891" alt="{83B1A474-A932-4C7E-B21F-2189FA3CBDEC}" src="https://github.com/user-attachments/assets/a5787fd5-19d6-4013-b312-1b8e19a913c6" />

<img width="1920" height="876" alt="{72733E9E-774F-41C8-B2AA-A4A96D58B874}" src="https://github.com/user-attachments/assets/1f799917-f065-4876-a42b-3a3cb2e2779d" />
<img width="802" height="696" alt="{6C09BCCF-50C6-4556-B056-D070FDC3A931}" src="https://github.com/user-attachments/assets/817e8331-40b3-4b0d-a91f-6e79f33d1eb7" />
<img width="1920" height="888" alt="{44D6D06B-81BC-430E-B802-B82BED73F1BE}" src="https://github.com/user-attachments/assets/5bd37217-26f1-4113-a500-f16922a8b03f" />




  
