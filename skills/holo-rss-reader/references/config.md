# 配置参考

配置文件路径：`$RSS_DATA_DIR/config.json`（默认 `~/data/rss/config.json`），也可通过 `RSS_CONFIG` 环境变量或 `--config` 参数指定。

缺失或损坏时自动使用默认值。

## 完整 Schema

```json
{
  "network": {
    "connect_timeout_sec": 5,
    "read_timeout_sec": 10,
    "max_feed_bytes": 2097152,
    "max_article_bytes": 8388608,
    "retries": 1
  },
  "fetch": {
    "workers": 8
  },
  "security": {
    "mode": "loose",
    "allowlist": []
  }
}
```

## 字段取值范围

| 字段 | 默认值 | 最小值 | 最大值 |
|------|--------|--------|--------|
| `network.connect_timeout_sec` | 5 | 1 | 60 |
| `network.read_timeout_sec` | 10 | 1 | 300 |
| `network.max_feed_bytes` | 2MB | 64KB | 32MB |
| `network.max_article_bytes` | 8MB | 256KB | 64MB |
| `network.retries` | 1 | 0 | 10 |
| `fetch.workers` | 8 | 1 | 64 |

超出范围的值会被自动 clamp 到最近边界。非法值回退到默认值。

## 安全模式

| 模式 | 行为 |
|------|------|
| `loose`（默认） | 仅要求 URL scheme 为 http/https |
| `restricted` | 额外阻止 localhost、内网 IP、link-local、multicast、保留地址 |
| `allowlist` | 仅允许 `allowlist` 中列出的主机名 |

`security.mode` 值不合法时回退到 `loose`。
