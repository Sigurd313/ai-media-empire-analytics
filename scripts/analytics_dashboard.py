#!/usr/bin/env python3
"""
Real-time Analytics Dashboard for AI Media Empire
Calculates metrics, predictions, and alerts
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class AnalyticsDashboard:
    def __init__(self):
        self.youtube_data = self.load_json('data/latest.json')
        self.telegram_data = self.load_json('data/telegram_latest.json')
        self.youtube_history = self.load_csv('data/youtube_stats.csv')
        self.telegram_history = self.load_csv('data/telegram_stats.csv')
        
    def load_json(self, path):
        """Load JSON data"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def load_csv(self, path):
        """Load CSV data"""
        if os.path.exists(path):
            df = pd.read_csv(path)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return pd.DataFrame()
    
    def calculate_growth_rate(self, df, metric='subscribers'):
        """Calculate daily/hourly growth rate"""
        if df.empty or metric not in df.columns:
            return 0
        
        # Get last 24 hours
        last_24h = df[df['timestamp'] > datetime.now() - timedelta(days=1)]
        if len(last_24h) < 2:
            return 0
        
        start_val = last_24h.iloc[0][metric]
        end_val = last_24h.iloc[-1][metric]
        
        if start_val == 0:
            return 0
        
        hours_diff = (last_24h.iloc[-1]['timestamp'] - last_24h.iloc[0]['timestamp']).total_seconds() / 3600
        if hours_diff == 0:
            return 0
        
        # Calculate hourly growth rate
        growth_rate = ((end_val - start_val) / start_val) / hours_diff * 100
        return growth_rate
    
    def predict_growth(self, df, metric='subscribers', days_ahead=7):
        """Predict future growth using linear regression"""
        if df.empty or len(df) < 3:
            return None
        
        # Prepare data
        df = df.sort_values('timestamp')
        df['hours_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 3600
        
        # Simple linear regression
        x = df['hours_since_start'].values
        y = df[metric].values
        
        if len(x) < 2:
            return None
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Predict future
        future_hours = np.arange(x[-1], x[-1] + (days_ahead * 24), 1)
        predictions = slope * future_hours + intercept
        
        return {
            'current': int(y[-1]),
            'predicted_7d': int(predictions[-1]),
            'daily_growth': int(slope * 24),
            'reach_1000_days': (1000 - y[-1]) / (slope * 24) if slope > 0 else None
        }
    
    def calculate_engagement_rate(self, channel_data):
        """Calculate engagement rate for channels"""
        # For YouTube
        if 'views' in channel_data and 'videos' in channel_data:
            avg_views = channel_data['views'] / channel_data['videos'] if channel_data['videos'] > 0 else 0
            if channel_data.get('subscribers', 0) > 0:
                return (avg_views / channel_data['subscribers']) * 100
        return 0
    
    def detect_anomalies(self, df, metric='subscribers'):
        """Detect sudden drops or spikes"""
        if df.empty or len(df) < 10:
            return []
        
        alerts = []
        
        # Calculate rolling average and std
        df = df.sort_values('timestamp')
        df['rolling_mean'] = df[metric].rolling(window=5, min_periods=1).mean()
        df['rolling_std'] = df[metric].rolling(window=5, min_periods=1).std()
        
        # Check last value
        last_row = df.iloc[-1]
        prev_mean = df.iloc[-6:-1]['rolling_mean'].mean() if len(df) > 5 else last_row['rolling_mean']
        
        if prev_mean > 0:
            change_pct = ((last_row[metric] - prev_mean) / prev_mean) * 100
            
            if change_pct < -10:
                alerts.append({
                    'type': 'drop',
                    'metric': metric,
                    'change': f"{change_pct:.1f}%",
                    'current': last_row[metric],
                    'expected': int(prev_mean)
                })
            elif change_pct > 50:
                alerts.append({
                    'type': 'spike',
                    'metric': metric,
                    'change': f"+{change_pct:.1f}%",
                    'current': last_row[metric],
                    'expected': int(prev_mean)
                })
        
        return alerts
    
    def calculate_roi(self, channel_data, costs=None):
        """Calculate ROI for each channel"""
        # Default costs if not provided
        if costs is None:
            costs = {
                'youtube': 500,  # $/month for video production
                'telegram': 100  # $/month for content
            }
        
        roi_data = {}
        
        # YouTube ROI (based on views monetization potential)
        if self.youtube_data:
            for channel in self.youtube_data.get('channels', []):
                monthly_views = channel.get('views', 0) / 12  # Rough estimate
                potential_revenue = monthly_views * 0.002  # $2 per 1000 views
                roi = ((potential_revenue - costs['youtube']) / costs['youtube']) * 100
                
                roi_data[channel['title']] = {
                    'cost': costs['youtube'],
                    'potential_revenue': potential_revenue,
                    'roi_percent': roi,
                    'status': 'profitable' if roi > 0 else 'loss'
                }
        
        # Telegram ROI (based on conversion to paid)
        if self.telegram_data:
            for channel in self.telegram_data.get('channels', []):
                if 'error' not in channel:
                    subscribers = channel.get('subscribers', 0)
                    # Assume 1% conversion at 10k RUB/month
                    potential_revenue = subscribers * 0.01 * 10000 / 70  # Convert to USD
                    roi = ((potential_revenue - costs['telegram']) / costs['telegram']) * 100
                    
                    roi_data[channel['name']] = {
                        'cost': costs['telegram'],
                        'potential_revenue': potential_revenue,
                        'roi_percent': roi,
                        'status': 'profitable' if roi > 0 else 'loss'
                    }
        
        return roi_data
    
    def generate_dashboard(self):
        """Generate complete dashboard data"""
        dashboard = {
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'youtube': {},
            'telegram': {},
            'predictions': {},
            'alerts': [],
            'roi': {},
            'recommendations': []
        }
        
        # YouTube metrics
        if self.youtube_data:
            youtube_total_subs = sum(ch['subscribers'] for ch in self.youtube_data.get('channels', []))
            youtube_total_views = sum(ch['views'] for ch in self.youtube_data.get('channels', []))
            
            dashboard['youtube'] = {
                'total_subscribers': youtube_total_subs,
                'total_views': youtube_total_views,
                'channels': []
            }
            
            for channel in self.youtube_data.get('channels', []):
                # Get channel history
                channel_history = self.youtube_history[
                    self.youtube_history['channel_id'] == channel['channel_id']
                ] if not self.youtube_history.empty else pd.DataFrame()
                
                growth_rate = self.calculate_growth_rate(channel_history)
                predictions = self.predict_growth(channel_history)
                engagement = self.calculate_engagement_rate(channel)
                alerts = self.detect_anomalies(channel_history)
                
                dashboard['youtube']['channels'].append({
                    'name': channel['title'],
                    'subscribers': channel['subscribers'],
                    'views': channel['views'],
                    'growth_rate_hourly': growth_rate,
                    'engagement_rate': engagement,
                    'predictions': predictions,
                    'alerts': alerts
                })
                
                dashboard['alerts'].extend([{**a, 'channel': channel['title']} for a in alerts])
        
        # Telegram metrics
        if self.telegram_data:
            dashboard['telegram'] = {
                'channels': []
            }
            
            for channel in self.telegram_data.get('channels', []):
                if 'error' not in channel:
                    # Limited data from Bot API
                    dashboard['telegram']['channels'].append({
                        'name': channel['name'],
                        'username': channel['username'],
                        'subscribers': channel.get('subscribers', 'N/A'),
                        'bot_is_admin': channel.get('bot_is_admin', False)
                    })
        
        # Overall predictions
        if not self.youtube_history.empty:
            total_history = self.youtube_history.groupby('timestamp').agg({
                'subscribers': 'sum',
                'views': 'sum'
            }).reset_index()
            
            dashboard['predictions'] = {
                'total_subscribers': self.predict_growth(total_history, 'subscribers'),
                'total_views': self.predict_growth(total_history, 'views')
            }
        
        # ROI calculations
        dashboard['roi'] = self.calculate_roi(None)
        
        # Generate recommendations
        dashboard['recommendations'] = self.generate_recommendations(dashboard)
        
        # Key metrics for 5-minute decisions
        youtube_total_subs = dashboard['youtube'].get('total_subscribers', 0) if 'youtube' in dashboard else 0
        
        # Find best channel
        best_channel = 'N/A'
        if dashboard.get('youtube', {}).get('channels'):
            best = max(dashboard['youtube']['channels'], 
                      key=lambda x: x.get('growth_rate_hourly', 0),
                      default=None)
            if best:
                best_channel = best.get('name', 'N/A')
        
        dashboard['summary'] = {
            'total_reach': youtube_total_subs,
            'growth_last_24h': self.calculate_growth_rate(self.youtube_history) if not self.youtube_history.empty else 0,
            'best_channel': best_channel,
            'alerts_count': len(dashboard['alerts']),
            'days_to_1000_subs': dashboard['predictions'].get('total_subscribers', {}).get('reach_1000_days') if dashboard.get('predictions', {}).get('total_subscribers') else None
        }
        
        return dashboard
    
    def generate_recommendations(self, dashboard):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check growth rates
        for channel in dashboard.get('youtube', {}).get('channels', []):
            if channel.get('growth_rate_hourly', 0) < 0.1:
                recommendations.append({
                    'priority': 'HIGH',
                    'channel': channel.get('name', 'Unknown'),
                    'action': 'Increase posting frequency or improve content quality',
                    'reason': f"Growth rate only {channel.get('growth_rate_hourly', 0):.2f}% per hour"
                })
            
            if channel.get('engagement_rate', 0) < 50:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'channel': channel.get('name', 'Unknown'),
                    'action': 'Improve thumbnails and titles',
                    'reason': f"Low engagement rate: {channel.get('engagement_rate', 0):.1f}%"
                })
        
        # Check ROI
        for channel, roi in dashboard.get('roi', {}).items():
            if roi.get('roi_percent', 0) < -50:
                recommendations.append({
                    'priority': 'HIGH',
                    'channel': channel,
                    'action': 'Reduce costs or pivot strategy',
                    'reason': f"ROI is {roi.get('roi_percent', 0):.1f}% (losing money)"
                })
        
        # Check alerts
        if len(dashboard.get('alerts', [])) > 0:
            recommendations.append({
                'priority': 'URGENT',
                'channel': 'Multiple',
                'action': 'Investigate anomalies immediately',
                'reason': f"{len(dashboard.get('alerts', []))} alerts detected"
            })
        
        return recommendations
    
    def save_dashboard(self, dashboard):
        """Save dashboard to JSON and Markdown with proper None handling"""
        # Save JSON
        with open('data/dashboard.json', 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
        
        # Safe get with defaults for all values
        summary = dashboard.get('summary', {})
        total_reach = summary.get('total_reach', 0) or 0
        growth_24h = summary.get('growth_last_24h', 0) or 0
        best_channel = summary.get('best_channel', 'N/A') or 'N/A'
        alerts_count = summary.get('alerts_count', 0) or 0
        days_to_1000 = summary.get('days_to_1000_subs')
        
        # Generate Markdown report with defensive formatting
        report = f"""# 🚀 AI Media Empire - Real-time Analytics Dashboard

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 🎯 5-Minute Decision Summary

- **Total Reach**: {total_reach:,} subscribers
- **24h Growth**: {growth_24h:.2f}% per hour
- **Best Performer**: {best_channel}
- **Active Alerts**: {alerts_count}
- **Days to 1000 subs**: {f'{days_to_1000:.1f}' if days_to_1000 is not None else 'N/A'}

## 🚨 Alerts & Anomalies

"""
        # Handle alerts safely
        alerts = dashboard.get('alerts', [])
        if alerts:
            for alert in alerts:
                emoji = '📉' if alert.get('type') == 'drop' else '📈'
                channel = alert.get('channel', 'Unknown')
                metric = alert.get('metric', 'metric')
                change = alert.get('change', 'N/A')
                expected = alert.get('expected', 0)
                current = alert.get('current', 0)
                report += f"- {emoji} **{channel}**: {metric} {change} (expected: {expected}, actual: {current})\n"
        else:
            report += "✅ No anomalies detected\n"
        
        report += "\n## 📊 Channel Performance\n\n"
        report += "| Channel | Subscribers | Growth/hour | Engagement | 7-day Prediction |\n"
        report += "|---------|------------|-------------|------------|------------------|\n"
        
        # Handle YouTube channels safely
        youtube_channels = dashboard.get('youtube', {}).get('channels', [])
        for channel in youtube_channels:
            name = channel.get('name', 'Unknown')
            subscribers = channel.get('subscribers', 0) or 0
            growth_rate = channel.get('growth_rate_hourly', 0) or 0
            engagement = channel.get('engagement_rate', 0) or 0
            predictions = channel.get('predictions', {})
            pred_7d = predictions.get('predicted_7d') if predictions else None
            pred_str = str(pred_7d) if pred_7d is not None else 'N/A'
            
            report += f"| {name} | {subscribers:,} | {growth_rate:.2f}% | {engagement:.1f}% | {pred_str} |\n"
        
        report += "\n## 💰 ROI Analysis\n\n"
        report += "| Channel | Cost | Potential Revenue | ROI | Status |\n"
        report += "|---------|------|------------------|-----|--------|\n"
        
        # Handle ROI safely
        roi_data = dashboard.get('roi', {})
        for channel, roi in roi_data.items():
            cost = roi.get('cost', 0) or 0
            revenue = roi.get('potential_revenue', 0) or 0
            roi_percent = roi.get('roi_percent', 0) or 0
            status = roi.get('status', 'unknown')
            status_emoji = '✅' if status == 'profitable' else '❌'
            report += f"| {channel} | ${cost} | ${revenue:.0f} | {roi_percent:.1f}% | {status_emoji} {status} |\n"
        
        report += "\n## 📋 Recommendations\n\n"
        
        # Handle recommendations safely
        recommendations = dashboard.get('recommendations', [])
        priority_order = {'URGENT': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_recs = sorted(recommendations, key=lambda x: priority_order.get(x.get('priority', 'LOW'), 99))
        
        for rec in sorted_recs:
            priority = rec.get('priority', 'LOW')
            emoji = {'URGENT': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(priority, '⚪')
            channel = rec.get('channel', 'Unknown')
            action = rec.get('action', 'No action specified')
            reason = rec.get('reason', 'No reason provided')
            report += f"{emoji} **{priority}** - {channel}: {action}\n"
            report += f"   - *Reason: {reason}*\n\n"
        
        # Save markdown
        with open('dashboard.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("✅ Dashboard saved to dashboard.md and data/dashboard.json")
        
        return report

def main():
    """Generate dashboard"""
    dashboard = AnalyticsDashboard()
    data = dashboard.generate_dashboard()
    report = dashboard.save_dashboard(data)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 DASHBOARD GENERATED SUCCESSFULLY")
    print("="*60)
    print(f"Total Reach: {data['summary']['total_reach']:,}")
    print(f"Growth Rate: {data['summary']['growth_last_24h']:.2f}% per hour")
    print(f"Alerts: {data['summary']['alerts_count']}")
    print(f"Best Channel: {data['summary']['best_channel']}")
    
    if data['summary']['days_to_1000_subs']:
        print(f"\n🎯 Reaching 1000 subscribers in {data['summary']['days_to_1000_subs']:.1f} days")
    
    if data['alerts']:
        print("\n⚠️  REQUIRES IMMEDIATE ATTENTION:")
        for alert in data['alerts'][:3]:  # Show top 3
            print(f"   - {alert['channel']}: {alert['metric']} {alert['change']}")

if __name__ == "__main__":
    main()
