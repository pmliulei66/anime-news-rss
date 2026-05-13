# 🎌 番剧新闻RSS

> 自动聚合：新番、定档、PV、STAFF、CAST、延期资讯

## 📡 RSS链接

```
https://pomliulei66.github.io/anime-news-rss/rss.xml
```

## ✨ 功能特点

- 🔄 **自动更新**: 每6小时自动抓取最新番剧新闻
- 🎯 **智能过滤**: 只保留新番、动画、动画化、定档、PV、STAFF、CAST等关键资讯
- 🚫 **自动屏蔽**: 过滤掉漫画、小说、游戏、周边、手办等不相关内容
- 📦 **自动去重**: 相同新闻只出现一次

## 📰 新闻来源

- [Anime News Network](https://www.animenewsnetwork.com/news/)
- [Crunchyroll News](https://www.crunchyroll.com/news/anime)
- [MyAnimeList News](https://myanimelist.net/news)

## 📖 使用方法

### RSS阅读器订阅

1. 复制上方RSS链接
2. 粘贴到任意RSS阅读器：
   - [Inoreader](https://www.inoreader.com/)
   - [Feedly](https://feedly.com/)
   - [Reeder](https://reederapp.com/)
   - [NetNewsWire](https://netnewswire.com/)

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python main.py
```

## ⚙️ 部署说明

本项目使用 GitHub Actions 自动运行脚本并更新RSS。

### 启用自动更新

1. 仓库 Settings → Pages
2. Source 选择 "Deploy from a branch"
3. Branch 选择 "main"，Folder 选择 "/ (root)"
4. 保存

### 启用Actions权限

1. 仓库 Settings → Actions → General
2. Workflow permissions 选择 "Read and write permissions"
3. 保存

## 🔧 自定义配置

编辑 `main.py` 中的配置区域：

```python
# 白名单关键词
WHITE_LIST = ["新番", "动画", "动画化", "定档", "开播", "PV", "STAFF", "CAST", ...]

# 黑名单关键词
BLACK_LIST = ["漫画", "小说", "手游", "游戏", "周边", "手办", ...]
```

## 📝 License

MIT License
