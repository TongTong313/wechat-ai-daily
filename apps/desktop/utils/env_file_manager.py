# -*- coding: utf-8 -*-
"""
.env 文件管理器

负责读取、更新、创建 .env 文件，保留注释和格式。
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class EnvFileManager:
    """
    .env 文件管理器
    
    提供读取、更新、创建 .env 文件的功能，保留文件中的注释和格式。
    """
    
    def __init__(self, project_root: Path):
        """初始化 .env 文件管理器
        
        Args:
            project_root: 项目根目录
        """
        self.env_file = project_root / ".env"
        self.project_root = project_root
    
    def exists(self) -> bool:
        """检查 .env 文件是否存在
        
        Returns:
            bool: 是否存在
        """
        return self.env_file.exists()
    
    def read_all(self) -> Dict[str, str]:
        """读取所有环境变量
        
        Returns:
            Dict[str, str]: 环境变量字典 {KEY: VALUE}
        """
        if not self.exists():
            return {}
        
        env_vars = {}
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue
                    # 解析 KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")  # 移除引号
                        env_vars[key] = value
        except Exception as e:
            logging.error(f"读取 .env 文件失败: {e}")
        
        return env_vars
    
    def get(self, key: str) -> Optional[str]:
        """获取单个环境变量
        
        Args:
            key: 环境变量名
            
        Returns:
            Optional[str]: 环境变量值，不存在返回 None
        """
        env_vars = self.read_all()
        return env_vars.get(key)
    
    def update(self, key: str, value: str) -> bool:
        """更新单个环境变量（保留注释和格式）
        
        Args:
            key: 环境变量名
            value: 环境变量值
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.exists():
                # 文件不存在，创建新文件
                return self.create({key: value})
            
            # 读取所有行（保留注释和格式）
            lines = []
            key_found = False
            
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    # 检查是否是要更新的键
                    if stripped and not stripped.startswith('#') and '=' in stripped:
                        existing_key = stripped.split('=', 1)[0].strip()
                        if existing_key == key:
                            # 更新这一行
                            lines.append(f'{key}="{value}"\n')
                            key_found = True
                            continue
                    # 保留原行
                    lines.append(line)
            
            # 如果键不存在，追加到文件末尾
            if not key_found:
                # 确保文件末尾有换行
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] += '\n'
                lines.append(f'{key}="{value}"\n')
            
            # 写回文件
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logging.info(f"✅ 已更新 .env 文件: {key}")
            return True
            
        except Exception as e:
            logging.error(f"更新 .env 文件失败: {e}")
            return False
    
    def update_multiple(self, variables: Dict[str, str]) -> bool:
        """批量更新环境变量
        
        Args:
            variables: 环境变量字典 {KEY: VALUE}
            
        Returns:
            bool: 是否全部成功
        """
        success = True
        for key, value in variables.items():
            if not self.update(key, value):
                success = False
        return success
    
    def create(self, variables: Dict[str, str], with_header: bool = True) -> bool:
        """创建 .env 文件
        
        Args:
            variables: 初始环境变量字典 {KEY: VALUE}
            with_header: 是否添加文件头注释
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                if with_header:
                    f.write("# 环境变量配置文件\n")
                    f.write("# 此文件包含敏感信息，请勿提交到版本控制系统\n")
                    f.write("#\n")
                    f.write("# 配置优先级（从高到低）：\n")
                    f.write("# 1. config.yaml 文件\n")
                    f.write("# 2. .env 文件（本文件）\n")
                    f.write("# 3. 系统环境变量\n")
                    f.write("\n")
                
                for key, value in variables.items():
                    f.write(f'{key}="{value}"\n')
            
            logging.info(f"✅ 已创建 .env 文件: {self.env_file}")
            return True
            
        except Exception as e:
            logging.error(f"创建 .env 文件失败: {e}")
            return False
    
    def remove(self, key: str) -> bool:
        """移除单个环境变量
        
        Args:
            key: 环境变量名
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.exists():
                return True  # 文件不存在，视为成功
            
            # 读取所有行
            lines = []
            key_found = False
            
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    # 检查是否是要删除的键
                    if stripped and not stripped.startswith('#') and '=' in stripped:
                        existing_key = stripped.split('=', 1)[0].strip()
                        if existing_key == key:
                            key_found = True
                            continue  # 跳过这一行
                    # 保留原行
                    lines.append(line)
            
            if not key_found:
                logging.warning(f".env 文件中不存在键: {key}")
                return True
            
            # 写回文件
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logging.info(f"✅ 已从 .env 文件中移除: {key}")
            return True
            
        except Exception as e:
            logging.error(f"从 .env 文件中移除键失败: {e}")
            return False
    
    def get_file_path(self) -> Path:
        """获取 .env 文件路径
        
        Returns:
            Path: .env 文件路径
        """
        return self.env_file
    
    def detect_source(self, key: str) -> Tuple[Optional[str], str]:
        """检测环境变量的来源
        
        Args:
            key: 环境变量名
            
        Returns:
            Tuple[Optional[str], str]: (值, 来源)
            来源可能为: 'env_file' | 'system' | 'not_set'
        """
        # 1. 检查 .env 文件
        env_file_value = self.get(key)
        if env_file_value:
            return env_file_value, 'env_file'
        
        # 2. 检查系统环境变量
        system_value = os.getenv(key)
        if system_value:
            return system_value, 'system'
        
        return None, 'not_set'
