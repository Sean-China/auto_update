#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FPSLocker配置下载器
"""

import os
import sys
import shutil
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


def setup_temp_directory():
    global TEMP_DIR
    TEMP_DIR = tempfile.mkdtemp(prefix="fpslocker_")
    print(f"创建临时目录: {TEMP_DIR}")
    return TEMP_DIR


def cleanup_temp_directory():
    global TEMP_DIR
    if TEMP_DIR and os.path.exists(TEMP_DIR):
        print(f"清理临时目录: {TEMP_DIR}")
        shutil.rmtree(TEMP_DIR)


def calculate_file_hash(file_path, algorithm='sha256'):
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
    try:
        with open(HASH_FILE, 'w') as f:
            f.write(hash_value)
    except Exception as e:
        print(f"保存哈希值时发生错误: {e}")


def get_saved_hash():
    try:
        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, 'r') as f:
                return f.read().strip()
        return None
    except Exception as e:
        print(f"读取哈希值时发生错误: {e}")
        return None


# ===================== 这是修复后的核心函数 =====================
def get_download_link():
    """
    精准匹配：
    1. 找父文本包含 download all configs 且链接文字是 here 的a标签
    2. 找不到直接返回该仓库固定下载链接（100%可用）
    """
    try:
        print(f"正在访问: {GITHUB_REPO_URL}")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(GITHUB_REPO_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 【精准匹配】你说的：链接文本是 here，父级有 download all configs
        for a in soup.find_all("a"):
            a_text = a.get_text(strip=True).lower()
            parent_text = a.parent.get_text(strip=True).lower() if a.parent else ""
            
            # 匹配：链接是 here，旁边文字包含下载配置
            if a_text == "here" and "download all configs" in parent_text:
                href = a.get("href")
                if href:
                    full_url = urljoin(GITHUB_REPO_URL, href)
                    print(f"✅ 精准找到下载链接: {full_url}")
                    return full_url

        # ===================== 兜底：直接返回固定真实链接 =====================
        print("⚠️ 页面匹配失败，使用仓库固定下载链接")
        fixed_url = "https://github.com/masagrator/FPSLocker-Warehouse/archive/refs/heads/main.zip"
        print(f"✅ 使用固定链接: {fixed_url}")
        return fixed_url

    except Exception as e:
        print(f"获取链接出错: {e}")
        # 出错也返回固定链接
        return "https://github.com/masagrator/FPSLocker-Warehouse/archive/refs/heads/main.zip"
# ==================================================================


def download_file(url, save_path):
    try:
        print(f"开始下载: {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        with requests.get(url, stream=True, headers=headers, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            now = 0
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        now += len(chunk)
                        if total > 0:
                            print(f"下载进度: {now/total*100:.1f}%", end='\r')
        print(f"\n下载完成")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False


def extract_zip(zip_path, extract_dir):
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)
        print(f"解压完成")
        return True
    except Exception as e:
        print(f"解压失败: {e}")
        return False


def find_saltysd_directory(extract_dir):
    for root, dirs, files in os.walk(extract_dir):
        if 'SaltySD' in dirs:
            path = os.path.join(root, 'SaltySD')
            print(f"找到SaltySD: {path}")
            return path
    print("未找到SaltySD")
    return None


def create_saltysd_zip(saltysd_dir, output_zip_path):
    try:
        parent = os.path.dirname(saltysd_dir)
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for rt, dirs, files in os.walk(saltysd_dir):
                for f in files:
                    full = os.path.join(rt, f)
                    arc = os.path.relpath(full, parent)
                    z.write(full, arc)
        print(f"✅ SaltySD.zip 创建成功")
        return True
    except Exception as e:
        print(f"打包失败: {e}")
        return False


def main():
    try:
        temp_dir = setup_temp_directory()
        zip_file = os.path.join(temp_dir, "fpslocker.zip")
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        out_zip = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SaltySD.zip")

        # 1. 获取链接
        dl_url = get_download_link()
        if not dl_url:
            return 1

        # 2. 下载
        if not download_file(dl_url, zip_file):
            return 1

        # 3. 哈希校验
        current_hash = calculate_file_hash(zip_file)
        saved_hash = get_saved_hash()
        if current_hash and saved_hash and current_hash == saved_hash:
            print("文件无更新，退出")
            return 0
        if current_hash:
            save_hash(current_hash)

        # 4. 解压
        if not extract_zip(zip_file, extract_dir):
            return 1

        # 5. 找目录
        saltysd = find_saltysd_directory(extract_dir)
        if not saltysd:
            return 1

        # 6. 打包
        if not create_saltysd_zip(saltysd, out_zip):
            return 1

        print("\n🎉 全部完成！SaltySD.zip 已在脚本同目录")
        return 0

    except Exception as e:
        print(f"错误: {e}")
        return 1
    finally:
        cleanup_temp_directory()


if __name__ == "__main__":
    sys.exit(main())
