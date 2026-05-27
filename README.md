# 金十 WebSocket 宏观新闻过滤与 QQ 推送工具

这个项目用于连接金十 WebSocket 实时消息流，筛选对加密资产、宏观市场、地缘风险和系统性风险有影响的快讯，并把符合规则的消息写入推送队列，再由独立 QQ 推送进程发送到群聊。

## 项目结构

- `probe.py`：连接金十 WebSocket，记录原始消息，执行过滤规则，并把待推送消息写入队列。
- `news_filter.py`：关键词、评分规则、`score_news()`、`should_push()` 和文本提取逻辑。
- `impact_analyzer.py`：判断新闻对 BTC、原油、黄金、美股等资产的影响方向。
- `push_queue.py`：JSONL 推送队列写入器，以及基于 offset 的增量消费工具。
- `qq_pusher.py`：独立 QQ 群推送进程。
- `config.py`：路径、队列、日志和 QQ HTTP API 配置，敏感配置从 `.env` 读取。
- `scripts/`：过滤规则回归测试、影响判断测试和历史消息回测脚本。
- `deploy/`：systemd 服务模板。
- `logs/`：运行日志目录，不提交到 GitHub。

## 数据流程

金十 WebSocket -> `probe.py` -> `news_filter.py` -> `logs/push_queue.jsonl` -> `qq_pusher.py` -> QQ 群。

`pushed_news.log` 表示过滤器命中了消息，不代表 QQ 已发送成功。QQ 发送结果记录在 `qq_sent.log` 和 `qq_failed.log`。

## 运行新闻接收器

复制 `.env.example` 为 `.env`，配置 `JIN10_WS_URL`，然后运行：

```bash
python3 probe.py
```

## 运行 QQ 推送器

只预览队列消息，不实际发送 QQ：

```bash
python3 qq_pusher.py --dry-run --once
```

持续运行：

```bash
python3 qq_pusher.py --loop --interval 3
```

dry-run 默认使用 `logs/push_queue.dry_run.offset`，不会推进真实的 `logs/push_queue.offset`。如需刻意测试真实 offset：

```bash
python3 qq_pusher.py --dry-run --once --advance-offset
```

## 开启真实 QQ 推送

在 `.env` 中配置部署参数：

```bash
QQ_PUSH_ENABLED=true
QQ_BOT_API_URL=http://127.0.0.1:3000/send_group_msg
QQ_GROUP_ID=your_group_id
QQ_ACCESS_TOKEN=
QQ_ACCESS_TOKEN_MODE=none
```

不要提交真实 access token、QQ 群号、WebSocket URL、代理订阅或节点信息。

## 修改新闻过滤规则

优化关键词、评分和跳过规则时，主要修改 `news_filter.py`。`probe.py` 应保持专注于接收消息和写入队列，`qq_pusher.py` 不应导入或调用新闻过滤逻辑。

## 队列 Offset 排查

`qq_pusher.py` 会从 `push_queue.offset` 记录的字节位置开始读取 `push_queue.jsonl`。如果队列文件被截断或轮转，且 offset 大于文件大小，消费者会自动把 offset 重置为 `0`。

如需从头重放，停止 `qq_pusher.py` 后执行：

```bash
printf '0\n' > logs/push_queue.offset
```

dry-run offset 是独立的：

```bash
printf '0\n' > logs/push_queue.dry_run.offset
```

## 网络与代理注意事项

服务器已有全局代理。不要为本项目额外安装或重配代理客户端。如果依赖下载失败，先查看命令错误输出和基础网络连通性。不要把代理订阅链接、访问令牌或节点信息写入代码、日志或 README。
