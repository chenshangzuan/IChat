"""
快速诊断企业微信签名验证失败原因

用法：把最新一次 GET 请求的参数填入下方，然后运行：
  uv run python test/debug_wechat_verify.py
"""
import hashlib
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ========== 把请求参数粘贴到这里 ==========
MSG_SIGNATURE = "9643962b0f3185ec92a72399afe03b1517caafe4"
TIMESTAMP     = "1776923580"
NONCE         = "1777036186"
ECHOSTR       = "glP54GLsceVcPo7CDE6aP4xGJlQHlgv/BtDqJimXi00b2uECj3prnJoogF6ymbt6kgh0pKylr5noaspK3Bt6Ug=="
# ==========================================

TOKEN = os.getenv("WECHAT_WORK_TOKEN", "")
AES_KEY = os.getenv("WECHAT_WORK_ENCODING_AES_KEY", "")
CORP_ID = os.getenv("WECHAT_WORK_CORP_ID", "")

print("=" * 60)
print(f"TOKEN (完整): {repr(TOKEN) if TOKEN else '[❌ 未设置]'}")
print(f"AES_KEY    : {'[已设置] 长度=' + str(len(AES_KEY)) if AES_KEY else '[❌ 未设置]'}")
print(f"CORP_ID    : {CORP_ID if CORP_ID else '[❌ 未设置]'}")
print("=" * 60)
print("⚠️  请将 TOKEN 与企业微信后台「接收消息」→「Token」字段核对是否完全一致（区分大小写，无多余空格）")

# 计算签名（4 参数）
parts = sorted([TOKEN, TIMESTAMP, NONCE, ECHOSTR])
computed = hashlib.sha1("".join(parts).encode()).hexdigest()

print(f"\n参与签名的 4 个参数（排序后）:")
for p in parts:
    display = p if len(p) < 40 else p[:40] + "..."
    print(f"  {display!r}")

print(f"\n计算结果  : {computed}")
print(f"期望签名  : {MSG_SIGNATURE}")
print(f"\n验证结果  : {'✅ 匹配' if computed == MSG_SIGNATURE else '❌ 不匹配'}")

if computed != MSG_SIGNATURE:
    # 试试 3 参数（没有 echostr）
    parts3 = sorted([TOKEN, TIMESTAMP, NONCE])
    computed3 = hashlib.sha1("".join(parts3).encode()).hexdigest()
    print(f"\n[对照] 3 参数签名: {computed3}")
    if computed3 == MSG_SIGNATURE:
        print("  → 企业微信用的是 3 参数签名（兼容模式/明文模式？）")
