#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动漫番剧新闻RSS生成器 v2
- 中文标题 + 英文原标题
- 缩略图
- 摘要（中英混合）
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone
import ssl
import os

ssl._create_default_https_context = ssl._create_unverified_context

# -------------------------- 配置区 --------------------------
WHITE_LIST = ["新番", "动画", "动画化", "定档", "开播", "PV", "STAFF", "CAST", 
              "放送", "档期", "延期", "新作", "预告", "anime", "animation", 
              "新动画", "剧场版", "TV动画", "animated", "teaser", "trailer",
              "premiere", "adaptation", "season", "reveals", "unveils"]

BLACK_LIST = ["漫画", "小说", "手游", "游戏", "周边", "手办", "演唱会", "cos", 
              "真人", "广播", "manga", "novel", "game", "merchandise", "figure",
              "live-action", "hollywood", "film adaptation"]

CRUNCHYROLL_RSS = "https://www.crunchyroll.com/news/rss"

# 关键词翻译映射
TRANSLATIONS = {
    "unveils": "公开",
    "reveals": "公开",
    "announces": "宣布",
    "announcement": "公告",
    "additional": "追加",
    "staff": "制作阵容",
    "cast": "声优阵容",
    "promo": "宣传视频",
    "teaser": "预告",
    "trailer": "预告PV",
    "pv": "PV",
    "anime": "动画",
    "animation": "动画",
    "tv": "TV",
    "season": "季度",
    "premiere": "开播",
    "adaptation": "改编",
    "opening": "开播",
    "second": "第二",
    "third": "第三",
    "first": "第一",
    "new": "新作",
    "live-action": "真人",
    "the": "",
    "for": "",
    "to": "",
    "of": "",
    "in": "",
    "with": "",
    "and": "",
}

SOURCE_NAMES = {
    "ANN": " Anime News Network",
    "MAL": " MyAnimeList",
    "CR": " Crunchyroll",
}
# -----------------------------------------------------------------------

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def escape_xml(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text

def should_keep(title):
    if not title:
        return False
    title_lower = title.lower()
    for w in BLACK_LIST:
        if w.lower() in title_lower:
            return False
    for w in WHITE_LIST:
        if w.lower() in title_lower:
            return True
    return False

def translate_keywords(text):
    """简单关键词翻译"""
    result = text
    for en, cn in TRANSLATIONS.items():
        # 替换单词（区分大小写）
        pattern = r'\b' + en + r'\b'
        result = re.sub(pattern, cn, result, flags=re.IGNORECASE)
    return result

def format_title(title, source):
    """格式化标题：中文标签 + 原标题"""
    # 提取关键词
    keywords = []
    title_lower = title.lower()
    
    if 'anime' in title_lower or 'tv anime' in title_lower:
        keywords.append("动画")
    if 'movie' in title_lower or 'film' in title_lower or '剧场版' in title_lower:
        keywords.append("剧场版")
    if 'pv' in title_lower or 'promo' in title_lower or 'teaser' in title_lower or 'trailer' in title_lower:
        keywords.append("PV")
    if 'cast' in title_lower:
        keywords.append("CAST")
    if 'staff' in title_lower:
        keywords.append("STAFF")
    if 'premiere' in title_lower or 'opening' in title_lower:
        keywords.append("开播")
    if 'season' in title_lower:
        keywords.append("续作")
    if 'unveils' in title_lower or 'reveals' in title_lower:
        keywords.append("公开")
    if 'announces' in title_lower:
        keywords.append("发表")
    
    # 来源标签
    source_label = SOURCE_NAMES.get(source, "")
    
    # 构建中文标题
    if keywords:
        keyword_str = "[" + "][".join(keywords) + "]"
        # 简化原标题
        simple_title = title.replace("'s ", "的 ").replace("'", "")
        translated = translate_keywords(simple_title)
        return f"{keyword_str}{source_label} {translated}"
    else:
        return f"{source_label} {title}"

def truncate_text(text, max_len=150):
    """截断文本"""
    if not text:
        return ""
    text = clean_text(text)
    if len(text) > max_len:
        return text[:max_len].rsplit(' ', 1)[0] + "..."
    return text

def fetch_ann(soup):
    """抓取 Anime News Network"""
    items = []
    for item in soup.select(".herald.box.news")[:15]:
        h3_tag = item.find("h3")
        if not h3_tag:
            continue
        link_tag = h3_tag.find("a")
        if not link_tag:
            continue
        
        raw_title = clean_text(link_tag.get_text())
        href = link_tag.get("href", "")
        if not raw_title or not href:
            continue
        
        # 链接
        if href.startswith("http"):
            link = href
        else:
            link = "https://www.animenewsnetwork.com" + href
        
        # 摘要
        snippet_tag = item.select_one(".snippet")
        snippet = clean_text(snippet_tag.get_text()) if snippet_tag else ""
        if snippet:
            snippet = truncate_text(snippet, 200)
        
        # 图片
        thumb = item.select_one(".thumbnail")
        img_url = ""
        if thumb:
            data_src = thumb.get("data-src", "")
            if data_src:
                if data_src.startswith("/"):
                    img_url = "https://www.animenewsnetwork.com" + data_src
                else:
                    img_url = data_src
        
        if should_keep(raw_title):
            title = format_title(raw_title, "ANN")
            items.append({
                "title": title,
                "raw_title": raw_title,
                "link": link,
                "source": "ANN",
                "snippet": snippet,
                "image": img_url
            })
            print(f"  OK [ANN] {raw_title[:50]}...")
    return items

def fetch_mal(soup):
    """抓取 MyAnimeList"""
    items = []
    for item in soup.select(".news-unit.clearfix.rect")[:15]:
        title_tag = item.select_one(".news-unit-right p.title a")
        if not title_tag:
            continue
        
        raw_title = clean_text(title_tag.get_text())
        href = title_tag.get("href", "")
        if not raw_title or not href:
            continue
        
        # 链接
        if href.startswith("http"):
            link = href
        else:
            link = "https://myanimelist.net" + href
        
        # 摘要
        text_tag = item.select_one(".news-unit-right div.text")
        snippet = clean_text(text_tag.get_text()) if text_tag else ""
        if snippet:
            snippet = truncate_text(snippet, 200)
        
        # 图片
        img_tag = item.select_one("a.image-link img.image")
        img_url = img_tag.get("src", "") if img_tag else ""
        if img_url:
            # 获取高清图
            img_url = img_url.replace("/r/100x156/", "/r/300x450/")
        
        if should_keep(raw_title):
            title = format_title(raw_title, "MAL")
            items.append({
                "title": title,
                "raw_title": raw_title,
                "link": link,
                "source": "MAL",
                "snippet": snippet,
                "image": img_url
            })
            print(f"  OK [MAL] {raw_title[:50]}...")
    return items

def fetch_crunchyroll_rss():
    """通过RSS抓取Crunchyroll新闻"""
    items = []
    print(f"正在抓取: {CRUNCHYROLL_RSS}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(CRUNCHYROLL_RSS, headers=headers, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        for entry in soup.find_all("item")[:15]:
            title_tag = entry.find("title")
            link_tag = entry.find("link")
            desc_tag = entry.find("description")
            
            if not title_tag:
                continue
            
            raw_title = clean_text(title_tag.get_text())
            link = link_tag.get_text() if link_tag else ""
            snippet = clean_text(desc_tag.get_text()) if desc_tag else ""
            if snippet:
                snippet = truncate_text(snippet, 200)
            
            if not link or not should_keep(raw_title):
                continue
            
            title = format_title(raw_title, "CR")
            items.append({
                "title": title,
                "raw_title": raw_title,
                "link": link,
                "source": "CR",
                "snippet": snippet,
                "image": ""
            })
            print(f"  OK [CR] {raw_title[:50]}...")
    except Exception as e:
        print(f"  FAIL Crunchyroll RSS: {e}")
    return items

def fetch_news():
    """从各个新闻源抓取新闻"""
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # ANN
    ann_url = "https://www.animenewsnetwork.com/news/"
    print(f"正在抓取: {ann_url}")
    try:
        r = requests.get(ann_url, headers=headers, timeout=20)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")
        items.extend(fetch_ann(soup))
    except Exception as e:
        print(f"  FAIL ANN: {e}")
    
    # MAL
    mal_url = "https://myanimelist.net/news"
    print(f"正在抓取: {mal_url}")
    try:
        r = requests.get(mal_url, headers=headers, timeout=20)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")
        items.extend(fetch_mal(soup))
    except Exception as e:
        print(f"  FAIL MAL: {e}")
    
    # Crunchyroll RSS
    items.extend(fetch_crunchyroll_rss())
    
    return items

def build_rss(items):
    """生成RSS XML"""
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">',
        '  <channel>',
        '    <title>番剧每日新闻RSS</title>',
        '    <description>自动聚合：新番、定档、PV、STAFF、CAST、延期资讯 | Auto-updated anime news aggregator</description>',
        '    <link>https://github.com/pmliulei66/anime-news-rss</link>',
        '    <atom:link href="https://pmliulei66.github.io/anime-news-rss/rss.xml" rel="self" type="application/rss+xml"/>',
        '    <language>zh</language>',
        f'    <lastBuildDate>{now}</lastBuildDate>',
        f'    <generator>Anime News Bot v2</generator>',
    ]
    
    seen = set()
    count = 0
    
    for item in items:
        if item["link"] in seen:
            continue
        seen.add(item["link"])
        count += 1
        
        # 构建描述（包含摘要）
        description_parts = []
        if item.get("snippet"):
            description_parts.append(item["snippet"])
        description_parts.append(f"来源: {item['source']}")
        description_parts.append(f"原文: {item['raw_title']}")
        description = " | ".join(description_parts)
        
        xml_lines.append('    <item>')
        xml_lines.append(f'      <title>{escape_xml(item["title"])}</title>')
        xml_lines.append(f'      <link>{escape_xml(item["link"])}</link>')
        xml_lines.append(f'      <guid isPermaLink="true">{escape_xml(item["link"])}</guid>')
        xml_lines.append(f'      <pubDate>{now}</pubDate>')
        xml_lines.append(f'      <description><![CDATA[{description}]]></description>')
        
        # 添加图片（media:content）
        if item.get("image"):
            xml_lines.append(f'      <enclosure url="{escape_xml(item["image"])}" type="image/jpeg"/>')
            xml_lines.append(f'      <media:content url="{escape_xml(item["image"])}" medium="image"/>')
        
        xml_lines.append('    </item>')
    
    xml_lines.append('  </channel>')
    xml_lines.append('</rss>')
    
    xml_content = '\n'.join(xml_lines)
    
    with open("rss.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    
    print(f"\nRSS生成完成！共 {count} 条去重后的资讯")
    return count

def main():
    print("=" * 60)
    print("番剧新闻RSS生成器 v2")
    print("=" * 60)
    print(f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"新闻源: ANN + MAL + Crunchyroll RSS")
    print("-" * 60)
    
    news = fetch_news()
    print("-" * 60)
    
    count = build_rss(news)
    
    print("=" * 60)
    print(f"完成！已生成 {count} 条新闻")
    print(f"RSS文件: rss.xml")
    print("=" * 60)

if __name__ == "__main__":
    main()
