#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FPSLocker配置下载器

这个脚本用于GitHub Actions，自动探测FPSLocker-Warehouse页面中的ZIP文件下载链接，
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
from urllib.parse import urljoin, urlparse, unquote

# GitHub仓库URL
GITHUB_REPO_URL = "https://github.com/masagrator/FPSLocker-Warehouse"
# 临时目录
TEMP_DIR = None
# 上次下载的文件哈希值存储文件路径
HASH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpslocker_last_hash.txt")

# ZIP链接筛选关键词（提升匹配准确性）
ZIP_KEYWORDS = ["config", "fpslocker", "saltysd"]
# ========== 新增：模拟浏览器请求头 ==========
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://github.com/",
    "Connection": "keep-alive"
}


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
    """计算文件的哈希值"""
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"计算文件哈希值时发生错误: {e}")
        return None


def save_hash(hash_value):
    """保存文件哈希值到本地文件"""
    try:
        with open(HASH_FILE, 'w') as f:
            f.write(hash_value)
        print(f"哈希值已保存到 {HASH_FILE}")
    except Exception as e:
        print(f"保存哈希值时发生错误: {e}")


def get_saved_hash():
    """从本地文件获取上次保存的哈希值"""
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
    优化版：搜索页面内所有ZIP文件下载链接
    - 模拟浏览器请求头
    - 扩大筛选范围（包含.zip的链接，而非仅结尾）
    - 增加调试日志
    - 补充Release页面查找
    返回: 下载链接URL或None
    """
    try:
        # ========== 1. 模拟浏览器访问页面 ==========
        print(f"正在访问GitHub仓库（模拟浏览器）: {GITHUB_REPO_URL}")
        response = requests.get(
            GITHUB_REPO_URL,
            headers=REQUEST_HEADERS,  # 新增请求头
            timeout=30,
            allow_redirects=True  # 允许重定向
        )
        response.raise_for_status()
        
        print(f"成功获取页面内容，状态码: {response.status_code}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ========== 2. 调试：打印页面中所有<a>标签的href（前20个） ==========
        all_a_hrefs = [a.get('href', '').strip() for a in soup.find_all('a', href=True)[:20]]
        print(f"\n【调试】页面前20个<a>标签的href:")
        for idx, href in enumerate(all_a_hrefs, 1):
            print(f"  {idx}. {href}")
        
        # ========== 3. 扩大范围筛选ZIP链接 ==========
        zip_links = []
        print("\n开始搜索页面中所有ZIP文件下载链接...")
        
        # 遍历所有<a>标签，筛选包含.zip的href（处理带参数的情况）
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href').strip()
            decoded_href = unquote(href)  # 解码URL编码（比如%20→空格）
            
            # 筛选规则：href中包含.zip（忽略大小写），且不是锚点链接
            if '.zip' in decoded_href.lower() and not decoded_href.startswith('#'):
                # 拼接完整URL
                full_url = urljoin(GITHUB_REPO_URL, href)
                # 解析URL路径，用于关键词匹配
                url_path = urlparse(full_url).path.lower()
                
                # 标记是否为优先匹配的链接
                is_priority = any(keyword in url_path for keyword in ZIP_KEYWORDS)
                zip_links.append({
                    'url': full_url,
                    'priority': is_priority,
                    'path': url_path
                })
        
        # ========== 4. 补充：查找Release页面的ZIP链接 ==========
        if not zip_links:
            print("\n主页面未找到ZIP链接，尝试访问Release页面...")
            release_url = f"{GITHUB_REPO_URL}/releases/latest"
            try:
                release_resp = requests.get(release_url, headers=REQUEST_HEADERS, timeout=30, allow_redirects=True)
                release_resp.raise_for_status()
                release_soup = BeautifulSoup(release_resp.text, 'html.parser')
                
                # 筛选Release页面的ZIP资产链接
                for a_tag in release_soup.find_all('a', href=True):
                    href = a_tag.get('href').strip()
                    decoded_href = unquote(href)
                    if '.zip' in decoded_href.lower() and 'assets' in decoded_href.lower():
                        full_url = urljoin("https://github.com", href)
                        url_path = urlparse(full_url).path.lower()
                        is_priority = any(keyword in url_path for keyword in ZIP_KEYWORDS)
                        zip_links.append({
                            'url': full_url,
                            'priority': is_priority,
                            'path': url_path
                        })
            except Exception as e:
                print(f"访问Release页面失败: {e}")
        
        # ========== 5. 处理找到的ZIP链接 ==========
        if not zip_links:
            print("\n❌ 未找到任何ZIP文件下载链接")
            return None
        
        # 打印所有找到的zip链接
        print(f"\n✅ 共找到 {len(zip_links)} 个ZIP链接:")
        for idx, link in enumerate(zip_links, 1):
            priority_note = "[优先匹配]" if link['priority'] else ""
            print(f"  {idx}. {link['url']} {priority_note}")
        
        # 优先选择包含特征关键词的链接
        for link in zip_links:
            if link['priority']:
                print(f"\n选择优先匹配的ZIP链接: {link['url']}")
                return link['url']
        
        # 无优先链接时，选择第一个
        first_link = zip_links[0]['url']
        print(f"\n无优先匹配链接，选择第一个ZIP链接: {first_link}")
        return first_link
        
    except Exception as e:
        print(f"获取ZIP下载链接时发生错误: {e}")
        return None


def download_file(url, save_path):
    """下载文件（新增请求头）"""
    try:
        print(f"开始下载文件: {url}")
        print(f"保存到: {save_path}")
        
        with requests.get(
            url,
            stream=True,
            headers=REQUEST_HEADERS,  # 新增请求头
            timeout=60,
            allow_redirects=True
        ) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"下载进度: {progress:.1f}%", end='\r')
        
        print(f"\n文件下载完成，大小: {downloaded_size} 字节")
        return True
    except Exception as e:
        print(f"下载文件时发生错误: {e}")
        return False


def extract_zip(zip_path, extract_dir):
    """解压ZIP文件"""
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
    """查找SaltySD目录"""
    try:
        print("查找SaltySD目录...")
        
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
    """创建SaltySD.zip文件"""
    try:
        print(f"开始创建SaltySD.zip...")
        print(f"源目录: {saltysd_dir}")
        print(f"输出文件: {output_zip_path}")
        
        parent_dir = os.path.dirname(saltysd_dir)
        
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, dirs, files in os.walk(saltysd_dir):
                for file in files:
                    file_path = os.path.join(root, file)
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
        temp_dir = setup_temp_directory()
        zip_file_path = os.path.join(temp_dir, "fpslocker_configs.zip")
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        output_zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SaltySD.zip")
        
        # 1. 获取ZIP下载链接
        download_url = get_download_link()
        if not download_url:
            print("无法获取ZIP下载链接，程序退出")
            return 1
        
        # 2. 下载文件
        if not download_file(download_url, zip_file_path):
            print("文件下载失败，程序退出")
            return 1
        
        # 3. 哈希校验
        current_hash = calculate_file_hash(zip_file_path)
        if current_hash:
            saved_hash = get_saved_hash()
            if saved_hash and current_hash == saved_hash:
                print(f"文件未发生变化（哈希值: {current_hash}），跳过后续处理")
                return 0
            save_hash(current_hash)
        
        # 4. 解压+查找SaltySD+打包
        if not extract_zip(zip_file_path, extract_dir):
            return 1
        saltysd_dir = find_saltysd_directory(extract_dir)
        if not saltysd_dir:
            return 1
        if not create_saltysd_zip(saltysd_dir, output_zip_path):
            return 1
        
        print("\n✅ 任务完成！SaltySD.zip已创建成功")
        return 0
    except Exception as e:
        print(f"程序执行过程中发生未处理的错误: {e}")
        return 1
    finally:
        cleanup_temp_directory()


if __name__ == "__main__":
    sys.exit(main())
