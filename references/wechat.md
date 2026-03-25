# 微信公众号 RSS 订阅

通过 [wechat2rss](https://wechat2rss.xlab.app) 桥接服务将微信公众号转为标准 RSS feed，与 holo-rss-reader 无缝集成。

## 快速开始

### 1. 查找公众号 account-id

访问 [wechat2rss 公众号列表](https://wechat2rss.xlab.app/list/all/)，搜索目标公众号名称，获取其 hash ID。

已验证的公众号示例：
- 新智元: `ede30346413ea70dbef5d485ea5cbb95cca446e7`
- 机器之心: `51e92aad2728acdd1fda7314be32b16639353001`
- 量子位: `7131b577c61365cb47e81000738c10d872685908`

### 2. 添加订阅

```bash
bash scripts/rss.sh wechat add <account-id> --title <名称>

# 示例
bash scripts/rss.sh wechat add ede30346413ea70dbef5d485ea5cbb95cca446e7 --title 新智元
```

添加时会自动验证 feed 可达性。

### 3. 抓取文章

```bash
bash scripts/rss.sh fetch
```

微信源与其他 RSS 源一起并发抓取，文章会出现在日报 `digest.md` 中。

### 4. 获取全文

```bash
bash scripts/rss.sh full <mp.weixin.qq.com-article-url>
```

微信文章 URL 有反爬机制，无法直接 HTTP 抓取。`full` 命令会自动从当天 feed 缓存的 `content:encoded` 中提取全文保存。

## 管理命令

```bash
# 列出所有微信源
bash scripts/rss.sh wechat list

# 移除微信源（按 account-id 或 feed URL）
bash scripts/rss.sh wechat remove <account-id>
```

## Feed URL 格式

```
https://wechat2rss.xlab.app/feed/{account-id}.xml
```

Feed 输出为标准 RSS 2.0，包含 `content:encoded` 全文 HTML。

## 常见问题

### Feed 超过 2MB 限制

部分活跃公众号的 feed 可能超过默认 `max_feed_bytes`（2MB）。修改 `$RSS_DATA_DIR/config.json`：

```json
{
  "network": {
    "max_feed_bytes": 8388608
  }
}
```

### 公众号不在 wechat2rss 列表中

wechat2rss 不包含所有公众号。若目标公众号未收录，暂无法通过此方式订阅。

### 全文获取失败

确保先运行 `fetch` 抓取当天文章，`full` 命令依赖 `digest.json` 中缓存的 `content:encoded`。若当天未抓取过该文章，全文回退将找不到内容。
