"""文件哈希计算工具"""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_file_hash(file_path: Path | str, algorithm: str = "sha256") -> str:
    """计算文件的哈希值。

    Args:
        file_path: 文件路径
        algorithm: 哈希算法（默认 sha256）

    Returns:
        哈希值的十六进制字符串
    """
    file_path = Path(file_path)
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.hexdigest()
