#!/usr/bin/env python3
"""
Telegram Analytics Collector for AI Media Empire (Bot API Version)
Collects basic data for all channels using only Bot API
"""

import os
import json
import requests
from datetime import datetime
import pandas as pd

# Configuration
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Channels to track (SAVED IN MEMORY!)
CHANNELS = {
    '@ai_bez_pravil': {
        'name': 'AI без правил',
        'chat': '@ai_bez_pravil_chat'
    },
    '@agecrisis': {
        'name': 'Исследователь Счастья',
        'chat': None
    },
    '@watchx2': {
        'name': 'После Титров', 
        'chat': None
    },
    '@shum_motora': {
        'name': 'Шум Мотора (Palych)',
        'chat': None
    }
}

def get_chat_info(chat_id):
    """Get basic chat information using Bot API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    params = {'chat_id': chat_id}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('ok'):
            return data['result']
        else:
            print(f"Error for {chat_id}: {data.get('description')}")
            return None
    except Exception as e:
        print(f"Request error for {chat_id}: {e}")
        return None

def get_chat_member_count(chat_id):
    """Try to get member count (works for some channels)"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMemberCount"
    params = {'chat_id': chat_id}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('ok'):
            return data['result']
        else:
            return None
    except:
        return None

def check_bot_is_admin(chat_id):
    """Check if bot is admin in the channel"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    params = {
        'chat_id': chat_id,
        'user_id': BOT_TOKEN.split(':')[0]  # Bot's own ID
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('ok'):
            member = data['result']
            return {
                'is_admin': member['status'] in ['administrator', 'creator'],
                'status': member['status'],
                'can_read': member.get('can_read_messages', False)
            }
        else:
            return None
    except:
        return None

def analyze_chat_activity(chat_id):
    """Analyze recent activity in associated chat (if exists)"""
    # Bot API doesn't allow reading message history
    # But we can try to get chat info for associated discussion groups
    chat_info = get_chat_info(chat_id)
    
    if chat_info:
        return {
            'chat_exists': True,
            'chat_title': chat_info.get('title'),
            'chat_type': chat_info.get('type'),
            'chat_members': get_chat_member_count(chat_id)
        }
    return {'chat_exists': False}

def main():
    """Main collection function"""
    print(f"Starting Telegram data collection (Bot API) at {datetime.now()}")
    
    if not BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not set!")
        print("Add it to GitHub secrets or environment variables")
        return
    
    results = []
    
    # Process each channel
    for username, info in CHANNELS.items():
        print(f"\nProcessing {info['name']} ({username})...")
        
        # Get channel info
        channel_info = get_chat_info(username)
        
        if channel_info:
            # Basic channel data
            result = {
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'name': info['name'],
                'channel_id': channel_info.get('id'),
                'title': channel_info.get('title'),
                'type': channel_info.get('type'),
                'description': channel_info.get('description', ''),
                'invite_link': channel_info.get('invite_link'),
                'has_visible_history': channel_info.get('has_visible_history', False)
            }
            
            # Try to get member count
            member_count = get_chat_member_count(username)
            result['subscribers'] = member_count
            
            # Check bot status
            bot_status = check_bot_is_admin(username)
            if bot_status:
                result['bot_is_admin'] = bot_status['is_admin']
                result['bot_status'] = bot_status['status']
            else:
                result['bot_is_admin'] = False
                result['bot_status'] = 'unknown'
            
            # Check associated chat
            if info['chat']:
                chat_data = analyze_chat_activity(info['chat'])
                result['chat_data'] = chat_data
            
            results.append(result)
            
            print(f"  ✅ Found: {result['title']}")
            if member_count:
                print(f"     Subscribers: {member_count:,}")
            print(f"     Bot is admin: {result.get('bot_is_admin', False)}")
            
        else:
            print(f"  ❌ Could not access channel")
            results.append({
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'name': info['name'],
                'error': 'Bot cannot access channel',
                'bot_is_admin': False
            })
    
    # Check Million Dollar AI (private channel)
    print(f"\nChecking Million Dollar AI (private channel)...")
    # For private channels, we need the numeric ID
    # Bot should be able to access it if it's admin
    
    # Save results
    save_results(results)
    
    return results

def save_results(results):
    """Save results to JSON and CSV"""
    print("\nSaving data...")
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Save latest snapshot
    with open('data/telegram_latest.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'channels': results,
            'bot_api_version': True,
            'limitations': [
                'Cannot get post views/reactions',
                'Member count may not work for all channels',
                'Cannot read message history',
                'Need to be admin for private channels'
            ]
        }, f, indent=2, ensure_ascii=False)
    
    # Save timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'data/telegram_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'channels': results
        }, f, indent=2, ensure_ascii=False)
    
    # Append to CSV for historical tracking
    if results:
        # Filter only successful results
        valid_results = [r for r in results if 'error' not in r]
        
        if valid_results:
            df = pd.DataFrame(valid_results)
            
            # Select available columns
            csv_columns = ['timestamp', 'username', 'title']
            if 'subscribers' in df.columns:
                csv_columns.append('subscribers')
            csv_columns.extend(['bot_is_admin', 'bot_status'])
            
            # Filter existing columns
            csv_columns = [col for col in csv_columns if col in df.columns]
            df_csv = df[csv_columns]
            
            # Append to CSV
            csv_path = 'data/telegram_stats.csv'
            if os.path.exists(csv_path):
                df_csv.to_csv(csv_path, mode='a', header=False, index=False)
            else:
                df_csv.to_csv(csv_path, index=False)
    
    print(f"✅ Data collection complete!")
    print(f"   Channels processed: {len(results)}")
    print(f"   Successful: {len([r for r in results if 'error' not in r])}")

def generate_summary():
    """Generate a summary of what we can and cannot do"""
    print("\n📊 BOT API CAPABILITIES:")
    print("✅ What we CAN get:")
    print("   - Channel name and description")
    print("   - Channel ID and type")
    print("   - Bot admin status")
    print("   - Basic member count (sometimes)")
    print("   - Associated chat info")
    
    print("\n❌ What we CANNOT get:")
    print("   - Post views and reactions")
    print("   - Message history")
    print("   - Detailed engagement metrics")
    print("   - User activity patterns")
    
    print("\n💡 RECOMMENDATIONS:")
    print("1. Add bot as admin to all channels")
    print("2. Use webhook to track new posts in real-time")
    print("3. Consider TGStat API for full analytics ($50/month)")
    print("4. Or manually track key metrics weekly")

if __name__ == "__main__":
    results = main()
    generate_summary()
    
    # Show what we got
    if results:
        accessible = len([r for r in results if 'error' not in r])
        with_subs = len([r for r in results if r.get('subscribers')])
        
        print(f"\n📈 RESULTS:")
        print(f"   Accessible channels: {accessible}/{len(results)}")
        print(f"   With subscriber count: {with_subs}/{len(results)}")
