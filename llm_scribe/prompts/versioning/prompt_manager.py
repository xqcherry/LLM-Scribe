from typing import Dict, Optional
import json
from pathlib import Path


class PromptManager:
    """提示词版本管理器"""
    
    def __init__(self, version_file: str = "prompt_versions.json"):
        self.version_file = Path(version_file)
        self.versions: Dict[str, Dict] = self._load_versions()
    
    def _load_versions(self) -> Dict:
        """加载版本信息"""
        if self.version_file.exists():
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_versions(self):
        """保存版本信息"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.versions, f, ensure_ascii=False, indent=2)
    
    def register_version(
        self,
        prompt_name: str,
        version: str,
        content: str,
        description: str = ""
    ):
        """注册提示词版本"""
        if prompt_name not in self.versions:
            self.versions[prompt_name] = {}
        
        self.versions[prompt_name][version] = {
            "content": content,
            "description": description,
            "created_at": str(Path().cwd())
        }
        
        self._save_versions()
    
    def get_version(
        self,
        prompt_name: str,
        version: Optional[str] = None
    ) -> Optional[str]:
        """获取指定版本的提示词"""
        if prompt_name not in self.versions:
            return None
        
        versions = self.versions[prompt_name]
        
        if version:
            return versions.get(version, {}).get("content")
        
        # 返回最新版本（按版本号排序）
        if versions:
            latest = sorted(versions.keys(), reverse=True)[0]
            return versions[latest].get("content")
        
        return None
    
    def list_versions(self, prompt_name: str) -> Dict:
        """列出所有版本"""
        return self.versions.get(prompt_name, {})
