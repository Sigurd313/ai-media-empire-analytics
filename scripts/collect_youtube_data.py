#!/usr/bin/env python3
"""
YouTube Data Collector for AI Media Empire
Collects data for all channels and saves to JSON/CSV
"""

import os
import json
import requests
from datetime import datetime
import pandas as pd

# Configuration
API_KEY = os.environ.get('YOUTUBE_API_KEY')
if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY environment variable not set!")

# Channels to track
CHANNELS = {
    'shum_motora': 'Шум Мотора (Palych)',
    # Add more channels as needed
}

def search_channel(query):
    """Search for channel by name/handle"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "key": API_KEY,
        "maxResults": 3
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if 'error' in data:
        print(f"API Error: {data['error']['message']}")
        return None
    
    if data.get('items'):
        # Try to find best match
        for item in data['items']:
            title = item['snippet']['title'].lower()
            if query.lower() in title or 'палыч' in title or 'мотор' in title:
                return item['snippet']['channelId']
        # Return first result if no exact match
        return data['items'][0]['snippet']['channelId']
    
    return None

def get_channel_stats(channel_id):
    """Get channel statistics"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics,snippet,contentDetails",
        "id": channel_id,
        "key": API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get('items'):
        channel = data['items'][0]
        return {
            'channel_id': channel_id,
            'title': channel['snippet']['title'],
            'description': channel['snippet'].get('description', '')[:200],
            'published_at': channel['snippet']['publishedAt'],
            'country': channel['snippet'].get('country', 'N/A'),
            'subscribers': int(channel['statistics'].get('subscriberCount', 0)),
            'views': int(channel['statistics'].get('viewCount', 0)),
            'videos': int(channel['statistics'].get('videoCount', 0)),
            'uploads_playlist': channel['contentDetails']['relatedPlaylists']['uploads']
        }
    
    return None

def get_recent_videos(playlist_id, max_results=5):
    """Get recent videos from uploads playlist"""
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "contentDetails,snippet",
        "playlistId": playlist_id,
        "maxResults": max_results,
        "key": API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if not data.get('items'):
        return []
    
    # Get video IDs
    video_ids = [item['contentDetails']['videoId'] for item in data['items']]
    
    # Get video details
    videos_url = "https://www.googleapis.com/youtube/v3/videos"
    videos_params = {
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": API_KEY
    }
    
    videos_response = requests.get(videos_url, params=videos_params)
    videos_data = videos_response.json()
    
    videos = []
    for video in videos_data.get('items', []):
        videos.append({
            'video_id': video['id'],
            'title': video['snippet']['title'],
            'published_at': video['snippet']['publishedAt'],
            'duration': video['contentDetails']['duration'],
            'views': int(video['statistics'].get('viewCount', 0)),
            'likes': int(video['statistics'].get('likeCount', 0)),
            'comments': int(video['statistics'].get('commentCount', 0))
        })
    
    return videos

def main():
    """Main collection function"""
    print(f"Starting YouTube data collection at {datetime.now()}")
    
    # Results storage
    results = []
    all_videos = []
    
    # Process each channel
    for handle, name in CHANNELS.items():
        print(f"\nProcessing {name} (@{handle})...")
        
        # Find channel ID
        channel_id = search_channel(handle)
        if not channel_id:
            print(f"  ❌ Channel not found: {handle}")
            continue
        
        # Get channel stats
        stats = get_channel_stats(channel_id)
        if not stats:
            print(f"  ❌ Could not get stats for: {channel_id}")
            continue
        
        print(f"  ✅ Found: {stats['title']}")
        print(f"     Subscribers: {stats['subscribers']:,}")
        print(f"     Total views: {stats['views']:,}")
        
        # Add timestamp and save
        stats['timestamp'] = datetime.now().isoformat()
        stats['handle'] = handle
        results.append(stats)
        
        # Get recent videos
        videos = get_recent_videos(stats['uploads_playlist'])
        for video in videos:
            video['channel_id'] = channel_id
            video['channel_title'] = stats['title']
            all_videos.append(video)
    
    # Save results to JSON
    print("\nSaving data...")

    os.makedirs('data', exist_ok=True)
    
    # Save latest snapshot
    with open('data/latest.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'channels': results,
            'recent_videos': all_videos
        }, f, indent=2, ensure_ascii=False)
    
    # Save timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'data/youtube_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'channels': results,
            'recent_videos': all_videos
        }, f, indent=2, ensure_ascii=False)
    
    # Append to CSV for historical tracking
    if results:
        df = pd.DataFrame(results)
        # Select key columns for CSV
        csv_columns = ['timestamp', 'channel_id', 'title', 'subscribers', 'views', 'videos']
        df_csv = df[csv_columns]
        
        # Append to CSV
        if os.path.exists('data/youtube_stats.csv'):
            df_csv.to_csv('data/youtube_stats.csv', mode='a', header=False, index=False)
        else:
            df_csv.to_csv('data/youtube_stats.csv', index=False)
    
    print(f"✅ Data collection complete!")
    print(f"   Channels processed: {len(results)}")
    print(f"   Videos collected: {len(all_videos)}")
    
    # API quota check
    print(f"\n📊 API Usage estimate: ~{len(CHANNELS) * 3} units used")

if __name__ == "__main__":
    main()
