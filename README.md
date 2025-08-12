# WeChat Status Monitor

自动监控 WeChat 状态变化，当检测到 OPEN 状态时发送邮件通知。

## 功能特点

- ✅ 每5分钟自动检查状态（GitHub Actions限制）
- ✅ 只在状态变为OPEN时发送邮件通知（避免重复通知）
- ✅ 自动记录状态变化历史
- ✅ 支持手动触发监控

## 设置步骤

1. Fork 这个仓库
2. 在 Settings → Secrets 中添加邮箱配置
3. 启用 GitHub Actions
4. 监控将自动开始运行

## 手动运行

进入 Actions 页面，选择工作流并点击 "Run workflow"

## 监控日志

检查 Actions 页面查看运行日志和结果
