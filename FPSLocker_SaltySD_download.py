#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FPSLocker配置下载器

这个脚本用于GitHub Actions，自动探测FPSLocker-Warehouse页面中的下载链接，
下载所有配置文件，提取SaltySD目录，并重新打包为SaltySD.zip。

依赖项：requests, beautifulsoup4, zipfile（标准库）, hashlib（标准库）, re（标准库）
"""

import os
import sys
import shutil
import re
import requests
import zipfile
import tempfile
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# GitHub仓库URL
GITHUB_REPO_URL = "https://github.com/masagrator/FPSLocker-Warehouse"
# 临时目录
TEMP_DIR = None
# 上次下载的文件哈希值存储文件路径
HASH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpslocker_last_hash.txt")

TARGET_URL_PREFIX = "https://github.com/masagrator/FPSLocker-Warehouse/archive/refs/heads/"


def setup_temp_directory():
    """创建临时目录用于存储下载和解压的文件"""
    global TEMP_DIR
    TEMP_DIR = tempfile.mkdtemp(prefix="fpslocker_")
    print(f"创建临时目录: {TEMP_DIR}")
    return TEMP_DIR


def cleanup_temp_directory():
    """清理临时目录"""
    global TEMP_DIR
    if TEMP_DIR and os.path.exists(TEMP_DIR):
        print(f"清理临时目录: {TEMP_DIR}")
        shutil.rmtree(TEMP_DIR)


def calculate_file_hash(file_path, algorithm='sha256'):
    """
    计算文件的哈希值
    参数:
        file_path: 文件路径
        algorithm: 哈希算法，默认为'sha256'
    返回: 文件的哈希值字符串
    """
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # 分块读取文件以处理大文件
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"计算文件哈希值时发生错误: {e}")
        return None


def save_hash(hash_value):
    """
    保存文件哈希值到本地文件
    参数:
        hash_value: 哈希值字符串
    """
    try:
        with open(HASH_FILE, 'w') as f:
            f.write(hash_value)
        print(f"哈希值已保存到 {HASH_FILE}")
    except Exception as e:
        print(f"保存哈希值时发生错误: {e}")


def get_saved_hash():
    """
    从本地文件获取上次保存的哈希值
    返回: 哈希值字符串或None
    """
    try:
        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, 'r') as f:
                return f.read().strip()
        else:
            print(f"未找到哈希值文件 {HASH_FILE}")
            return None
    except Exception as e:
        print(f"读取哈希值时发生错误: {e}")
        return None


def get_download_link():
    """
    获取下载链接
    返回: 下载链接URL或None
    """
    try:
        print(f"正在访问GitHub仓库: {GITHUB_REPO_URL}")
        # 模拟浏览器请求头，避免被拦截
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(GITHUB_REPO_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"成功获取页面内容，状态码: {response.status_code}")
        page_source = response.text  # 获取完整页面源码
        
        # 正则规则：匹配以指定前缀开头、.zip结尾的URL（兼容URL带参数的情况）
        # 解释：
        # ^ 匹配开头 | {TARGET_URL_PREFIX} 你的指定前缀 | .*? 非贪婪匹配任意字符 | \.zip 匹配.zip（转义.） | (\?.*)? 兼容带参数的情况（如?raw=true）
        pattern = re.compile(
            rf'^{re.escape(TARGET_URL_PREFIX)}.*?\.zip(\?.*)?',  # re.escape避免前缀中的特殊字符影响
            re.IGNORECASE | re.MULTILINE  # 忽略大小写 + 多行匹配
        )
        # 从页面源码中提取所有匹配的URL
        matched_urls = pattern.findall(page_source)
        # 处理匹配结果（去掉参数部分的空值，去重）
        valid_urls = []
        for url_part in matched_urls:
            # 拼接完整URL（findall会把括号里的分组也返回，这里只取主URL）
            full_url = re.search(rf'{re.escape(TARGET_URL_PREFIX)}.*?\.zip', page_source).group()
            if full_url not in valid_urls:
                valid_urls.append(full_url)
        
        # ========== 处理匹配结果 ==========
        if valid_urls:
            print(f"\n✅ 匹配到 {len(valid_urls)} 个符合要求的ZIP链接:")
            for idx, url in enumerate(valid_urls, 1):
                print(f"  {idx}. {url}")
            # 返回第一个匹配的URL
            target_url = valid_urls[0]
            print(f"\n选择链接: {target_url}")
            return target_url
        else:
            print("\n⚠️ 未匹配到符合要求的URL，使用兜底固定链接")
            # 兜底的固定链接（符合你的前缀要求）
            fallback_url = f"{TARGET_URL_PREFIX}v4.zip"
            print(f"兜底链接: {fallback_url}")
            return fallback_url
        
    except Exception as e:
        print(f"获取下载链接时发生错误: {e}")
        # 出错时也返回兜底链接
        fallback_url = f"{TARGET_URL_PREFIX}v4.zip"
        print(f"使用兜底链接: {fallback_url}")
        return fallback_url


def download_file(url, save_path):
    """
    下载文件
    参数:
        url: 文件URL
        save_path: 保存路径
    返回: 是否下载成功
    """
    try:
        print(f"开始下载文件: {url}")
        print(f"保存到: {save_path}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # 使用stream模式下载大文件
        with requests.get(url, stream=True, headers=headers, timeout=60) as response:
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"下载进度: {progress:.1f}%", end='\r')
            
        print(f"\n文件下载完成，大小: {downloaded_size} 字节")
        return True
    except Exception as e:
        print(f"下载文件时发生错误: {e}")
        return False


def extract_zip(zip_path, extract_dir):
    """
    解压ZIP文件
    参数:
        zip_path: ZIP文件路径
        extract_dir: 解压目录
    返回: 是否解压成功
    """
    try:
        print(f"开始解压文件: {zip_path}")
        print(f"解压到: {extract_dir}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        print(f"解压完成，共解压 {len(zip_ref.namelist())} 个文件")
        return True
    except Exception as e:
        print(f"解压文件时发生错误: {e}")
        return False


def find_saltysd_directory(extract_dir):
    """
    查找SaltySD目录
    参数:
        extract_dir: 解压目录
    返回: SaltySD目录路径或None
    """
    try:
        print("查找SaltySD目录...")
        
        # 在解压目录中搜索SaltySD目录
        for root, dirs, files in os.walk(extract_dir):
            if 'SaltySD' in dirs:
                saltysd_path = os.path.join(root, 'SaltySD')
                print(f"找到SaltySD目录: {saltysd_path}")
                return saltysd_path
        
        print("未找到SaltySD目录")
        return None
    except Exception as e:
        print(f"查找SaltySD目录时发生错误: {e}")
        return None


def create_saltysd_zip(saltysd_dir, output_zip_path):
    """
    创建SaltySD.zip文件
    参数:
        saltysd_dir: SaltySD目录路径
        output_zip_path: 输出ZIP文件路径
    返回: 是否创建成功
    """
    try:
        print(f"开始创建SaltySD.zip...")
        print(f"源目录: {saltysd_dir}")
        print(f"输出文件: {output_zip_path}")
        
        # 获取SaltySD目录的父目录
        parent_dir = os.path.dirname(saltysd_dir)
        
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            # 遍历SaltySD目录中的所有文件
            for root, dirs, files in os.walk(saltysd_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径，确保ZIP中包含SaltySD目录结构
                    arcname = os.path.relpath(file_path, parent_dir)
                    zip_ref.write(file_path, arcname)
                    
        print(f"SaltySD.zip创建成功，大小: {os.path.getsize(output_zip_path)} 字节")
        return True
    except Exception as e:
        print(f"创建FPSLocker.zip时发生错误: {e}")
        return False


def main():
    """主函数"""
    try:
        # 设置临时目录
        temp_dir = setup_temp_directory()
        
        # 下载文件路径
        zip_file_path = os.path.join(temp_dir, "fpslocker_configs.zip")
        # 解压目录
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        # 输出ZIP文件路径
        output_zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SaltySD.zip")
        
        # 1. 获取下载链接（核心修改后的函数）
        download_url = get_download_link()
        if not download_url:
            print("无法获取下载链接，程序退出")
            return 1
        
        # 2. 下载文件
        if not download_file(download_url, zip_file_path):
            print("文件下载失败，程序退出")
            return 1
        
        # 3. 计算下载文件的哈希值并与上次保存的进行比较
        current_hash = calculate_file_hash(zip_file_path)
        if not current_hash:
            print("无法计算文件哈希值，继续执行后续步骤")
        else:
            saved_hash = get_saved_hash()
            
            if saved_hash and current_hash == saved_hash:
                print(f"文件未发生变化（哈希值: {current_hash}），跳过后续处理")
                return 0
            else:
                print(f"文件已更新（新哈希值: {current_hash}，旧哈希值: {saved_hash if saved_hash else '无'}")
                # 保存新的哈希值
                save_hash(current_hash)
        
        # 4. 解压文件
        if not extract_zip(zip_file_path, extract_dir):
            print("文件解压失败，程序退出")
            return 1
        
        # 5. 查找SaltySD目录
        saltysd_dir = find_saltysd_directory(extract_dir)
        if not saltysd_dir:
            print("未找到SaltySD目录，程序退出")
            return 1
        
        # 6. 创建SaltySD.zip
        if not create_saltysd_zip(saltysd_dir, output_zip_path):
            print("SaltySD.zip创建失败，程序退出")
            return 1
        
        print("\n任务完成！SaltySD.zip已创建成功")
        return 0
    except Exception as e:
        print(f"程序执行过程中发生未处理的错误: {e}")
        return 1
    finally:
        # 清理临时目录
        cleanup_temp_directory()


if __name__ == "__main__":
    sys.exit(main())
