#!/usr/bin/env python3
"""
Alerts system for AI Media Empire Analytics
Sends notifications when important events happen
"""

import json
import os
from datetime import datetime
import requests

class AlertsSystem:
    def __init__(self):
        self.dashboard = self.load_dashboard()
        self.webhook_url = os.environ.get('DISCORD_WEBHOOK') or os.environ.get('SLACK_WEBHOOK')
        
    def load_dashboard(self):
        """Load latest dashboard data"""
        if os.path.exists('data/dashboard.json'):
            with open('data/dashboard.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def check_critical_alerts(self):
        """Check for critical conditions"""
        if not self.dashboard:
            return []
        
        critical_alerts = []
        
        # Check for urgent alerts
        for alert in self.dashboard.get('alerts', []):
            if alert['type'] == 'drop' and float(alert['change'].strip('%')) < -20:
                critical_alerts.append({
                    'level': 'CRITICAL',
                    'message': f"🚨 {alert['channel']} lost {alert['change']} {alert['metric']}!",
                    'details': f"Expected: {alert['expected']}, Actual: {alert['current']}"
                })
        
        # Check growth stagnation
        if self.dashboard['summary']['growth_last_24h'] < 0:
            critical_alerts.append({
                'level': 'WARNING',
                'message': f"📉 Negative growth: {self.dashboard['summary']['growth_last_24h']:.2f}% per hour",
                'details': "Immediate action required to reverse trend"
            })
        
        # Check ROI
        for channel, roi in self.dashboard.get('roi', {}).items():
            if roi['roi_percent'] < -75:
                critical_alerts.append({
                    'level': 'CRITICAL',
                    'message': f"💸 {channel} is losing money: {roi['roi_percent']:.1f}% ROI",
                    'details': f"Cost: ${roi['cost']}, Revenue: ${roi['potential_revenue']:.0f}"
                })
        
        # Check if close to milestone
        days_to_1000 = self.dashboard['summary'].get('days_to_1000_subs')
        if days_to_1000 and days_to_1000 < 7:
            critical_alerts.append({
                'level': 'INFO',
                'message': f"🎯 Reaching 1000 subscribers in {days_to_1000:.1f} days!",
                'details': "Prepare celebration content"
            })
        
        return critical_alerts
    
    def send_webhook(self, alerts):
        """Send alerts to Discord/Slack webhook"""
        if not self.webhook_url or not alerts:
            return
        
        # Format message
        message = {
            "content": "**🚨 AI Media Empire Analytics Alert**\n",
            "embeds": []
        }
        
        for alert in alerts:
            color = {
                'CRITICAL': 0xFF0000,  # Red
                'WARNING': 0xFFA500,   # Orange
                'INFO': 0x00FF00       # Green
            }.get(alert['level'], 0x808080)
            
            message['embeds'].append({
                "title": alert['message'],
                "description": alert['details'],
                "color": color,
                "timestamp": datetime.now().isoformat()
            })
        
        # Send to webhook
        try:
            response = requests.post(self.webhook_url, json=message)
            if response.status_code == 204:
                print(f"✅ Sent {len(alerts)} alerts to webhook")
            else:
                print(f"❌ Failed to send alerts: {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending alerts: {e}")
    
    def create_github_issue(self, alerts):
        """Create GitHub issue for critical alerts"""
        # This would require GitHub token and API calls
        # For now, just save to file
        
        if not alerts:
            return
        
        issue_content = f"""## 🚨 Analytics Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}

### Critical Issues Detected:

"""
        for alert in alerts:
            issue_content += f"- **{alert['level']}**: {alert['message']}\n"
            issue_content += f"  - {alert['details']}\n\n"
        
        issue_content += f"""
### Dashboard Summary:
- Total Reach: {self.dashboard['summary']['total_reach']:,}
- Growth Rate: {self.dashboard['summary']['growth_last_24h']:.2f}% per hour
- Best Channel: {self.dashboard['summary']['best_channel']}

[View Full Dashboard](dashboard.md)
"""
        
        # Save to file (in real implementation, create GitHub issue)
        with open('alert_issue.md', 'w', encoding='utf-8') as f:
            f.write(issue_content)
        
        print("📝 Alert issue content saved to alert_issue.md")
    
    def generate_daily_summary(self):
        """Generate daily summary email/message"""
        if not self.dashboard:
            return None
        
        summary = f"""
# 📊 Daily Analytics Summary - {datetime.now().strftime('%Y-%m-%d')}

## 🎯 Key Metrics
- **Total Reach**: {self.dashboard['summary']['total_reach']:,} subscribers
- **24h Growth**: {self.dashboard['summary']['growth_last_24h']:.2f}% per hour
- **Best Performer**: {self.dashboard['summary']['best_channel']}
- **Days to 1K**: {self.dashboard['summary']['days_to_1000_subs']:.1f if self.dashboard['summary']['days_to_1000_subs'] else 'N/A'}

## 📈 Channel Performance
"""
        
        for channel in self.dashboard['youtube']['channels']:
            summary += f"\n**{channel['name']}**"
            summary += f"\n- Subscribers: {channel['subscribers']:,}"
            summary += f"\n- Growth: {channel['growth_rate_hourly']:.2f}%/hour"
            summary += f"\n- Engagement: {channel['engagement_rate']:.1f}%"
            if channel['predictions']:
                summary += f"\n- 7-day forecast: {channel['predictions']['predicted_7d']:,}"
            summary += "\n"
        
        summary += "\n## 💰 ROI Summary\n"
        profitable = sum(1 for roi in self.dashboard['roi'].values() if roi['status'] == 'profitable')
        total = len(self.dashboard['roi'])
        summary += f"- Profitable channels: {profitable}/{total}\n"
        summary += f"- Best ROI: {max(self.dashboard['roi'].items(), key=lambda x: x[1]['roi_percent'])[0]}\n"
        
        summary += "\n## 📋 Top Recommendations\n"
        for rec in self.dashboard['recommendations'][:3]:
            summary += f"- **{rec['priority']}**: {rec['action']} ({rec['channel']})\n"
        
        return summary

def main():
    """Run alerts check"""
    alerts = AlertsSystem()
    
    # Check for critical alerts
    critical_alerts = alerts.check_critical_alerts()
    
    if critical_alerts:
        print(f"\n🚨 Found {len(critical_alerts)} alerts!")
        for alert in critical_alerts:
            print(f"- {alert['level']}: {alert['message']}")
        
        # Send notifications
        alerts.send_webhook(critical_alerts)
        alerts.create_github_issue([a for a in critical_alerts if a['level'] == 'CRITICAL'])
    else:
        print("✅ No critical alerts")
    
    # Generate daily summary (run at specific time)
    current_hour = datetime.now().hour
    if current_hour == 9:  # 9 AM
        summary = alerts.generate_daily_summary()
        if summary:
            with open('daily_summary.md', 'w', encoding='utf-8') as f:
                f.write(summary)
            print("📧 Daily summary generated")

if __name__ == "__main__":
    main()
