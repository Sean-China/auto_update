#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FPSLocker配置下载器

这个脚本用于GitHub Actions，自动探测FPSLocker-Warehouse页面中的下载链接，
下载所有配置文件，提取SaltySD目录，并重新打包为SaltySD.zip。

依赖项：requests, beautifulsoup4, zipfile（标准库）, hashlib（标准库）
"""

import os
import sys
import shutil
import requests
import zipfile
import tempfile
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# GitHub仓库URL
GITHUB_REPO_URL = "https://github.com/masagrator/FPSLocker-Warehouse"
# 临时目录
TEMP_DIR = None
# 上次下载的文件哈希值存储文件路径
HASH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpslocker_last_hash.txt")

# ========== 新增：ZIP链接筛选关键词（提升匹配准确性） ==========
ZIP_KEYWORDS = ["FPSLocker-Warehouse", "config", "fpslocker", "saltysd"]  # 匹配包含这些关键词的zip链接


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
    优先选择包含FPSLocker配置特征的ZIP链接
    返回: 下载链接URL或None
    """
    try:
        print(f"正在访问GitHub仓库: {GITHUB_REPO_URL}")
        response = requests.get(GITHUB_REPO_URL, timeout=30)
        response.raise_for_status()
        
        print(f"成功获取页面内容，状态码: {response.status_code}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 存储所有找到的zip链接（按匹配优先级排序）
        zip_links = []
        
        # 第一步：遍历所有<a>标签，筛选href以.zip结尾的链接
        print("开始搜索页面中所有ZIP文件下载链接...")
        for a_tag in soup.find_all('a', href=True):  # 只遍历有href属性的a标签
            href = a_tag.get('href').strip()
            # 筛选以.zip结尾的链接（忽略大小写）
            if href.lower().endswith('.zip'):
                # 拼接完整URL
                full_url = urljoin(GITHUB_REPO_URL, href)
                # 解析URL路径，用于关键词匹配
                url_path = urlparse(full_url).path.lower()
                
                # 标记是否为优先匹配的链接（包含配置相关关键词）
                is_priority = any(keyword in url_path for keyword in ZIP_KEYWORDS)
                zip_links.append({
                    'url': full_url,
                    'priority': is_priority,
                    'path': url_path
                })
        
        # 第二步：处理找到的zip链接
        if not zip_links:
            print("未找到任何ZIP文件下载链接")
            return None
        
        # 打印所有找到的zip链接，方便调试
        print(f"\n共找到 {len(zip_links)} 个ZIP链接:")
        for idx, link in enumerate(zip_links, 1):
            priority_note = "[优先匹配]" if link['priority'] else ""
            print(f"  {idx}. {link['url']} {priority_note}")
        
        # 优先选择包含特征关键词的链接，无则选第一个
        for link in zip_links:
            if link['priority']:
                print(f"\n选择优先匹配的ZIP链接: {link['url']}")
                return link['url']
        
        # 无优先链接时，选择第一个找到的zip链接
        first_link = zip_links[0]['url']
        print(f"\n无优先匹配链接，选择第一个ZIP链接: {first_link}")
        return first_link
        
    except Exception as e:
        print(f"获取ZIP下载链接时发生错误: {e}")
        return None


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
        
        # 使用stream模式下载大文件
        with requests.get(url, stream=True, timeout=60) as response:
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
        print(f"创建SaltySD.zip时发生错误: {e}")
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
        
        # 1. 获取下载链接
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
