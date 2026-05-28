import base64
import ctypes
from ctypes import wintypes


class SecretStorageError(RuntimeError):
    """本地密钥保护失败。"""


class _DataBlob(ctypes.Structure):
    """Windows DPAPI 所需的数据结构。"""

    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def protect_secret(secret: str) -> str:
    """使用 Windows DPAPI 加密密钥后再写入配置文件。"""

    if not secret:
        return ""
    raw = secret.encode("utf-8")
    encrypted = _crypt_protect(raw)
    return "dpapi:" + base64.b64encode(encrypted).decode("ascii")


def unprotect_secret(protected: str) -> str:
    """读取配置文件里的 DPAPI 密文并还原为 API Key。"""

    if not protected:
        return ""
    if not protected.startswith("dpapi:"):
        raise SecretStorageError("不支持的密钥存储格式。")
    encrypted = base64.b64decode(protected.removeprefix("dpapi:"))
    return _crypt_unprotect(encrypted).decode("utf-8")


def _crypt_protect(data: bytes) -> bytes:
    """调用 Windows CryptProtectData，密文只允许当前用户解密。"""

    in_blob = _blob_from_bytes(data)
    out_blob = _DataBlob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise SecretStorageError("Windows DPAPI 加密失败。")
    return _bytes_from_blob(out_blob)


def _crypt_unprotect(data: bytes) -> bytes:
    """调用 Windows CryptUnprotectData 解密当前用户的密文。"""

    in_blob = _blob_from_bytes(data)
    out_blob = _DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise SecretStorageError("Windows DPAPI 解密失败。")
    return _bytes_from_blob(out_blob)


def _blob_from_bytes(data: bytes) -> _DataBlob:
    """把 Python bytes 转成 DPAPI DATA_BLOB。"""

    buffer = ctypes.create_string_buffer(data)
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))


def _bytes_from_blob(blob: _DataBlob) -> bytes:
    """读取 DPAPI 返回的 DATA_BLOB 并释放系统内存。"""

    try:
        return ctypes.string_at(blob.pbData, blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob.pbData)
