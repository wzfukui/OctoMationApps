- [OctoMationApps](#octomationapps)
  - [OctoMation 介绍](#octomation-介绍)
  - [OctoMationApps](#octomationapps-1)
  - [应用列表](#应用列表)
    - [离线模拟 X 系列](#离线模拟-x-系列)
    - [其他应用](#其他应用)
  - [如何使用应用APP](#如何使用应用app)
    - [Releases](#releases)
    - [应用源码包](#应用源码包)
  - [如何参与社区贡献](#如何参与社区贡献)
  - [许可](#许可)

# OctoMationApps

OctoMationApps 是 [OctoMation编排自动化产品](https://github.com/flagify-com/OctoMation) （雾帜智能HoneyGuide SOAR产品的社区免费版）的应用能力（联动网络、安全、IT和SaaS等产品的能力扩展包）的集合。

## OctoMation 介绍

OctoMation编排自动化（Octopus Orchestration & Automation）是上海雾帜智能科技有限公司HoneyGuide SOAR产品的社区免费版，是中国企业市场领先的编排和自动化（Orchestration & Automation， O&A）产品。

OctoMation 的特点包括:

- 简单且直观的图形化界面以建立自动化流程
- 支持各种产品和服务的连接集成
- 强大的自定义功能,支持 Python 脚本进行扩展
- 社区驱动,用户可以共享工作流程和APP

## OctoMationApps 

OctoMationApps 提供了一系列为 OctoMation 建立的自动化应用程序和脚本。这些应用程序可以直接导入 OctoMation 中,实现各种自动化任务。

## 应用列表

当前仓库根目录包含 46 个可导入应用。下表根据各应用的 `config.json` 整理，方便用户快速了解应用名称、类型和能力范围，而不需要逐个打开目录确认。

其中 `X` 系列离线模拟应用不依赖外部安全产品、网络设备、IT 系统或 SaaS 服务，适合开箱体验内置剧本、演示编排流程和做本地验证。

### 离线模拟 X 系列

| 应用 | 分类 | 动作数 | 说明 |
| --- | --- | ---: | --- |
| [XAsset 资产管理](shakespeare-action-python-xasset/) | IT系统 | 10 | 离线模拟资产与负责人 CMDB，提供资产归属、标签和关联查询能力 |
| [XAV 防病毒软件](shakespeare-action-python-xav/) | 安全产品 | 7 | 离线模拟防病毒与 EDR 轻量处置能力，支持扫描、隔离文件和清除威胁 |
| [XCloud 云平台](shakespeare-action-python-xcloud/) | 云服务 | 7 | 离线模拟云资产和安全组处置能力，支持云资产、安全组、封禁和快照 |
| [XFirewall防火墙](shakespeare-action-python-xfirewall/) | 安全产品 | 6 | XFirewall 新一代网络防火墙 |
| [XHIDS 主机安全](shakespeare-action-python-xhids/) | 安全产品 | 8 | 离线模拟 HIDS 主机安全平台，提供主机、进程、端口、告警与隔离动作 |
| [XIAM 身份与访问管理](shakespeare-action-python-xiam/) | IT系统 | 7 | 离线模拟 AD/LDAP/IAM 身份系统，支持用户查询、登录记录、禁用、启用和重置密码 |
| [XJumpServer 堡垒机](shakespeare-action-python-xjumpserver/) | 安全产品 | 7 | 离线模拟堡垒机访问审计，返回员工通过堡垒机访问目标设备的方式、协议、会话和命令记录 |
| [XLDAP 目录服务](shakespeare-action-python-xldap/) | IT系统 | 10 | 离线模拟 LDAP/AD 目录服务，支持用户、组织、用户组和账号状态管理 |
| [XMail 邮件安全](shakespeare-action-python-xmail/) | 安全产品 | 7 | 离线模拟邮件安全网关，支持邮件解析、事件查询、隔离、释放和发件人阻断 |
| [XNotify 通知系统](shakespeare-action-python-xnotify/) | SaaS服务 | 7 | 离线模拟通知服务，支持企业微信、邮件、短信式通知与投递状态查询 |
| [XSandbox 文件沙箱](shakespeare-action-python-xsandbox/) | 安全产品 | 6 | 离线模拟沙箱分析平台，支持文件/URL 提交、分析报告和行为轨迹查询 |
| [XScanner 漏洞扫描器](shakespeare-action-python-xscanner/) | 安全产品 | 7 | 离线模拟漏洞扫描器，支持目标管理、扫描任务、漏洞结果和报告生成 |
| [XSIEM 日志与告警平台](shakespeare-action-python-xsiem/) | 安全产品 | 7 | 离线模拟 SIEM 日志搜索、告警详情、事件聚合和告警状态流转 |
| [XSwitch 交换机](shakespeare-action-python-xswitch/) | 网络设备 | 7 | 离线模拟交换机 MAC、ARP、接口状态和端口阻断/恢复能力 |
| [XTI 威胁情报](shakespeare-action-python-xti/) | 安全产品 | 7 | 离线模拟威胁情报平台，支持 IP、域名、URL、文件 Hash、CVE 查询 |
| [XTicket 工单系统](shakespeare-action-python-xticket/) | IT系统 | 7 | 离线模拟工单系统，支持创建、分派、评论、流转和历史查询 |
| [XVPN 远程接入](shakespeare-action-python-xvpn/) | 网络设备 | 8 | 离线模拟 VPN 远程接入系统，支持登录状态、账号创建、账号禁用和踢人下线 |
| [XWAF Web应用防火墙](shakespeare-action-python-xwaf/) | 安全产品 | 7 | 离线模拟 WAF 攻击检测、站点防护、IP 封禁和 URL 规则能力 |

### 其他应用

| 应用 | 分类 | 动作数 | 说明 |
| --- | --- | ---: | --- |
| [AWVS](shakespeare-action-python-AWVS/) | 未分类 | 7 | awvs |
| [Gemini](shakespeare-action-python-Gemini/) | 网络工具,大模型,AI | 2 | Google Gemini大模型 |
| [GitHub助手](shakespeare-action-python-GitHubAssistant/) | 网络工具,开发工具 | 3 | GitHub助手 |
| [通用HTTP客户端](shakespeare-action-python-HTTP_Client/) | 网络工具 | 1 | 通用HTTP客户端 |
| [IPinfo.io](shakespeare-action-python-IPinfo/) | 网络工具 | 1 | IP数据库IPinfo.io |
| [IP Address Fraud Check](shakespeare-action-python-Scamalytics/) | 未分类 | 3 | Scamalytics IP欺诈风险检测 |
| [活动列表管理器](shakespeare-action-python-activelist_manager/) | 数据统计 | 11 | 活动列表管理器 |
| [云Web应用防火墙](shakespeare-action-python-aliyun_waf/) | 未分类 | 8 | 阿里云云Web应用防火墙 |
| [demo](shakespeare-action-python-app_demo/) | 示例 | 2 | app样例 |
| [CSV CMDB](shakespeare-action-python-csv_cmdb/) | 工具 | 3 | CSV 台账查询 CMDB，支持按 IP 查询负责人和按 AD 账号查询资产 |
| [Red Hat Security Data](shakespeare-action-python-cve_search/) | 未分类 | 2 | cve搜索 |
| [DeepSeek LLM](shakespeare-action-python-deepseek_chat/) | LLM | 1 | 支持调用deepseek接口进行对话 |
| [email_tool](shakespeare-action-python-email_tool/) | 未分类 | 3 | 邮件工具 |
| [Generic_Collection_Manager](shakespeare-action-python-generic_collection_manager/) | 未分类 | 12 | 通用集合管理 |
| [greynoise](shakespeare-action-python-greynoise_IPLookup/) | 情报查询 | 1 | greynoise IP查询 |
| [山石云瞻威胁情报](shakespeare-action-python-hillstonenet_ti/) | 威胁情报 | 5 | 山石云瞻-威胁情报 |
| [Kafka](shakespeare-action-python-kafka_client/) | 消息队列,基础工具 | 15 | Kafka 客户端，支持消息收发、Topic 查询、Consumer Group 查询和受保护的管理动作 |
| [nvd_cve](shakespeare-action-python-nvd_cve/) | 未分类 | 2 | cve数据获取 |
| [防火墙](shakespeare-action-python-paloalto_ngfw/) | 安全产品 | 1 | Palo Alto NGFW |
| [Redis](shakespeare-action-python-redis/) | 数据库,基础工具 | 9 | Redis客户端 |
| [Splunk](shakespeare-action-python-splunk_query/) | 安全产品 | 3 | Splunk 查询客户端，支持按时间窗口轮询告警 |
| [ssh](shakespeare-action-python-ssh_req/) | ssh | 1 | SSH应用 |
| [企业微信](shakespeare-action-python-tencent_wecom/) | 发送消息 | 6 | 企业微信（企微应用管理） |
| [tfLink (tmpfile.link)](shakespeare-action-python-tmpfile/) | 文件工具 | 3 | tmpfile.link - 临时文件上传与分享服务 |
| [变量生成器](shakespeare-action-python-variable_generator/) | 工具 | 1 | 变量生成器（输出一个或者更多个变量供后续节点使用，配合函数使用） |
| [vika](shakespeare-action-python-vika/) | 工具 | 3 | 维格云 |
| [企业微信](shakespeare-action-python-wework_group_admin/) | IM,办公 | 4 | 企业微信群管理 |
| [XTools](shakespeare-action-python-xtools/) | 工具 | 50 | X工具箱 |

## 如何使用应用APP

### Releases

1. 通过项目[releases](https://github.com/flagify-com/OctoMationApps/releases)列表，下载应用包zip文件
2. 如果批量下载则需要进行解压
3. 登录OctoMation后台，访问【应用管理】界面，上传zip包完成导入

### 应用源码包
1. 下载项目源码

```bash
# 下载主版本
git clone --depth 1 https://github.com/flagify-com/OctoMationApps.git

# 下载特定分支（适合开发）
git clone --depth 1 --branch dev-ce https://github.com/flagify-com/OctoMationApps.git
```

2. 创建应用包

找到你需要的应用APP文件夹，使用zip压缩该目录，如：
   
```bash
# 除了命令行，也可以使用图形化工具
zip -r shakespeare-action-python-IPinfo.zip shakespeare-action-python-IPinfo
```

3. 上传zip包

录OctoMation后台，访问【应用管理】界面，上传zip包完成导入。


## 如何参与社区贡献
欢迎参与OctoMationApps项目，如果您愿意向APP仓库贡献，可以在GitHub上Fork本项目，并在修改后提交Pull Request：

1. Fork项目[https://github.com/flagify-com/OctoMationApps.git](https://github.com/flagify-com/OctoMationApps.git)，建议copy所有分支。
2. 按需修改应用APP的源码、配置文件和资源文件
3. 充分测试和验证您的APP代码
4. Pull Request到项目`dev-ce`分支

关于如何编写应用能力APP，请参考：
- [🐙我的第一个OctoMation 应用APP开发](https://github.com/flagify-com/OctoMation/wiki/%E6%88%91%E7%9A%84%E7%AC%AC%E4%B8%80%E4%B8%AAOctoMation-%E5%BA%94%E7%94%A8APP%E5%BC%80%E5%8F%91)
- [🚀️OctoMation应用开发手册](https://github.com/flagify-com/OctoMation/wiki/OctoMation%E5%BA%94%E7%94%A8%E5%BC%80%E5%8F%91%E6%89%8B%E5%86%8C)


## 许可

**本项目采用双重许可。对于非商业用途，我们使用MIT许可证。对于商业用途，请查看我们的商业许可证，或者联系我们获取更多信息。**

- [MIT许可协议](MIT_License.txt)
- [商用许可协议](Commercial_License.txt)
