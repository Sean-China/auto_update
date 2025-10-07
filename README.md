# FPSLocker SaltySD 下载器

## 简介
这是一个自动化下载和处理FPSLocker配置文件的Python脚本。它主要用于GitHub Actions环境，能够自动检测FPSLocker-Warehouse页面中的下载链接，下载所有配置文件，提取SaltySD目录，并重新打包为SaltySD.zip。

## 功能特性
- 自动从GitHub仓库获取最新的FPSLocker配置下载链接
- 下载配置文件并验证文件完整性（通过SHA256哈希值）
- 解压下载的ZIP文件
- 提取SaltySD目录内容
- 重新打包SaltySD目录为SaltySD.zip
- 清理临时文件

## 依赖项
- Python 3（标准库）
- requests
- beautifulsoup4
- zipfile（标准库）
- hashlib（标准库）

## 使用方法
1. 确保已安装所有依赖项
2. 运行脚本：`python FPSLocker_SaltySD_download.py`
3. 脚本执行完成后，会在当前目录下生成SaltySD.zip文件

## 工作流程
1. 创建临时目录用于存储下载和解压的文件
2. 从GitHub仓库页面获取最新的下载链接
3. 下载ZIP文件并计算哈希值进行验证
4. 解压下载的ZIP文件
5. 查找SaltySD目录
6. 重新打包SaltySD目录
7. 清理临时目录

## 返回值
- 0: 成功执行
- 1: 执行过程中发生错误

## 注意事项
- 脚本使用临时目录进行操作，执行结束后会自动清理
- 会保存上次下载文件的哈希值，用于检测文件是否更新
- 支持显示下载进度
- 包含详细的错误处理和日志输出

## 许可证
请查看项目中的LICENSE文件了解详细许可信息。