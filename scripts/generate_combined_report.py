#!/usr/bin/env python3
"""
Generate combined report from YouTube and Telegram data
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import os

def load_latest_data():
    """Load latest data from both sources"""
    youtube_data = None
    telegram_data = None
    
    # Load YouTube data
    if os.path.exists('data/latest.json'):
        with open('data/latest.json', 'r', encoding='utf-8') as f:
            youtube_data = json.load(f)
    
    # Load Telegram data
    if os.path.exists('data/telegram_latest.json'):
        with open('data/telegram_latest.json', 'r', encoding='utf-8') as f:
            telegram_data = json.load(f)
    
    return youtube_data, telegram_data

def generate_report():
    """Generate markdown report for README"""
    youtube_data, telegram_data = load_latest_data()
    
    # Start report
    report = f"# 📊 AI Media Empire - Analytics Dashboard\n\n"
    report += f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*\n\n"
    
    # Combined summary
    report += f"## 🎯 Executive Summary\n\n"
    
    total_reach = 0
    platforms = []
    
    # YouTube metrics
    if youtube_data and 'channels' in youtube_data:
        youtube_channels = youtube_data['channels']
        youtube_subs = sum(ch['subscribers'] for ch in youtube_channels)
        youtube_views = sum(ch['views'] for ch in youtube_channels)
        total_reach += youtube_subs
        platforms.append(f"YouTube: {youtube_subs:,} subscribers")
        
        # Find Palych
        palych = next((ch for ch in youtube_channels if 'мотор' in ch['title'].lower()), None)
        if palych:
            report += f"- **Palych (YouTube)**: {palych['subscribers']:,} subs, {palych['views']:,} total views\n"
    
    # Telegram metrics
    if telegram_data and 'channels' in telegram_data:
        telegram_channels = [ch for ch in telegram_data['channels'] if 'error' not in ch]
        telegram_subs = sum(ch.get('subscribers', 0) for ch in telegram_channels if ch.get('subscribers'))
        total_reach += telegram_subs
        platforms.append(f"Telegram: {len(telegram_channels)} channels")
        
        report += f"- **Telegram Network**: {len(telegram_channels)} active channels\n"
    
    report += f"\n**Total Reach**: {total_reach:,} subscribers across {', '.join(platforms)}\n\n"
    
    # YouTube Section
    if youtube_data:
        report += f"## 📺 YouTube Analytics\n\n"
        report += "| Channel | Subscribers | Total Views | Videos | Avg Views |\n"
        report += "|---------|------------|-------------|--------|----------|\n"
        
        for channel in youtube_data.get('channels', []):
            avg_views = channel['views'] // channel['videos'] if channel['videos'] > 0 else 0
            report += f"| {channel['title']} | {channel['subscribers']:,} | {channel['views']:,} | {channel['videos']} | {avg_views:,} |\n"
        
        # Recent videos
        if 'recent_videos' in youtube_data:
            report += f"\n### 🎬 Top Recent Videos\n\n"
            videos = sorted(youtube_data['recent_videos'], key=lambda x: x['views'], reverse=True)[:5]
            
            for i, video in enumerate(videos, 1):
                report += f"{i}. **{video['title'][:60]}...**\n"
                report += f"   - Views: {video['views']:,} | Likes: {video['likes']:,}\n"
    
    # Telegram Section
    if telegram_data:
        report += f"\n## 💬 Telegram Analytics\n\n"
        
        # Limitations notice
        report += f"*Note: Using Bot API - limited metrics available*\n\n"
        
        report += "| Channel | Username | Bot Admin | Subscribers* |\n"
        report += "|---------|----------|-----------|-------------|\n"
        
        for channel in telegram_data.get('channels', []):
            if 'error' not in channel:
                subs = f"{channel.get('subscribers', 'N/A'):,}" if channel.get('subscribers') else 'N/A'
                admin = '✅' if channel.get('bot_is_admin') else '❌'
                report += f"| {channel['name']} | {channel['username']} | {admin} | {subs} |\n"
        
        report += f"\n*Subscriber counts only available where bot has admin rights\n"
    
    # Growth trends (if historical data exists)
    report += f"\n## 📈 Growth Trends\n\n"
    
    # Try to load historical data
    try:
        youtube_csv = pd.read_csv('data/youtube_stats.csv') if os.path.exists('data/youtube_stats.csv') else None
        telegram_csv = pd.read_csv('data/telegram_stats.csv') if os.path.exists('data/telegram_stats.csv') else None
        
        if youtube_csv is not None and not youtube_csv.empty:
            # Convert timestamp to datetime
            youtube_csv['timestamp'] = pd.to_datetime(youtube_csv['timestamp'])
            
            # Get data from 24 hours ago
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_data = youtube_csv[youtube_csv['timestamp'] <= yesterday]
            
            if not yesterday_data.empty:
                report += f"### YouTube Growth (24h)\n\n"
                
                for channel_id in youtube_csv['channel_id'].unique():
                    channel_data = youtube_csv[youtube_csv['channel_id'] == channel_id].sort_values('timestamp')
                    if len(channel_data) > 1:
                        latest = channel_data.iloc[-1]
                        previous = channel_data.iloc[-2]
                        growth = latest['subscribers'] - previous['subscribers']
                        if growth != 0:
                            report += f"- **{latest['title']}**: {growth:+,} subscribers\n"
    except:
        pass
    
    # Data access
    report += f"\n## 🔗 Data Access\n\n"
    report += f"### YouTube Data\n"
    report += f"- Latest: [data/latest.json](data/latest.json)\n"
    report += f"- History: [data/youtube_stats.csv](data/youtube_stats.csv)\n"
    report += f"- API: `https://raw.githubusercontent.com/Sigurd313/ai-media-empire-analytics/main/data/latest.json`\n\n"
    
    report += f"### Telegram Data\n"
    report += f"- Latest: [data/telegram_latest.json](data/telegram_latest.json)\n"
    report += f"- History: [data/telegram_stats.csv](data/telegram_stats.csv)\n"
    report += f"- API: `https://raw.githubusercontent.com/Sigurd313/ai-media-empire-analytics/main/data/telegram_latest.json`\n\n"
    
    report += f"## 📅 Update Schedule\n\n"
    report += f"- **YouTube**: Every hour at :00\n"
    report += f"- **Telegram**: Every hour at :30\n"
    report += f"- Data is collected automatically via GitHub Actions\n\n"
    
    report += f"---\n"
    report += f"*Generated by AI Media Empire Analytics Bot | [Dmitry DataDriven]*\n"
    
    # Save report
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Combined report generated successfully!")

if __name__ == "__main__":
    generate_report()
