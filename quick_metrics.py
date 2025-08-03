#!/usr/bin/env python3
"""
Quick 5-minute metrics check for AI Media Empire
Run this for instant insights
"""

import json
import requests
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def get_latest_metrics():
    """Fetch latest metrics from GitHub"""
    base_url = "https://raw.githubusercontent.com/Sigurd313/ai-media-empire-analytics/main"
    
    try:
        # Get dashboard data
        dashboard_response = requests.get(f"{base_url}/data/dashboard.json")
        if dashboard_response.status_code == 200:
            return dashboard_response.json()
    except:
        pass
    
    # Fallback to basic data
    youtube = requests.get(f"{base_url}/data/latest.json").json()
    telegram = requests.get(f"{base_url}/data/telegram_latest.json").json()
    
    return {'youtube': youtube, 'telegram': telegram}

def show_5_minute_summary(data):
    """Display 5-minute decision summary"""
    
    # Header
    console.print(Panel.fit(
        f"[bold cyan]AI Media Empire - 5-Minute Metrics[/bold cyan]\n"
        f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M')}[/dim]",
        box=box.DOUBLE
    ))
    
    # Quick Stats
    if 'summary' in data:
        summary = data['summary']
        
        # Growth indicator
        growth = summary.get('growth_last_24h', 0)
        growth_color = "green" if growth > 0.5 else "yellow" if growth > 0 else "red"
        growth_arrow = "↑" if growth > 0 else "↓" if growth < 0 else "→"
        
        console.print(f"\n[bold]Total Reach:[/bold] {summary.get('total_reach', 0):,} subscribers")
        console.print(f"[bold]24h Growth:[/bold] [{growth_color}]{growth:.2f}% {growth_arrow}[/{growth_color}]")
        console.print(f"[bold]Best Channel:[/bold] {summary.get('best_channel', 'N/A')}")
        
        if summary.get('days_to_1000_subs'):
            console.print(f"[bold]Days to 1K:[/bold] {summary['days_to_1000_subs']:.1f} days")
    
    # Alerts
    if 'alerts' in data and data['alerts']:
        console.print(f"\n[bold red]⚠️  Active Alerts: {len(data['alerts'])}[/bold red]")
        for alert in data['alerts'][:3]:
            console.print(f"  • {alert['channel']}: {alert['change']} {alert['metric']}")
    else:
        console.print("\n[bold green]✅ No alerts[/bold green]")
    
    # Quick Actions
    console.print("\n[bold]🎯 Quick Actions:[/bold]")
    
    if 'recommendations' in data:
        for i, rec in enumerate(data['recommendations'][:3], 1):
            priority_color = {
                'URGENT': 'red',
                'HIGH': 'yellow',
                'MEDIUM': 'cyan',
                'LOW': 'green'
            }.get(rec['priority'], 'white')
            
            console.print(f"{i}. [{priority_color}]{rec['priority']}[/{priority_color}]: {rec['action']}")
    
    # ROI Summary
    if 'roi' in data:
        profitable = sum(1 for r in data['roi'].values() if r['roi_percent'] > 0)
        total = len(data['roi'])
        console.print(f"\n[bold]💰 ROI:[/bold] {profitable}/{total} channels profitable")

def show_channel_table(data):
    """Display channel performance table"""
    
    table = Table(title="Channel Performance", box=box.SIMPLE)
    table.add_column("Channel", style="cyan")
    table.add_column("Subscribers", justify="right")
    table.add_column("Growth/h", justify="right")
    table.add_column("Status", justify="center")
    
    # YouTube channels
    if 'youtube' in data and 'channels' in data['youtube']:
        for channel in data['youtube']['channels']:
            growth = channel.get('growth_rate_hourly', 0)
            status = "🟢" if growth > 0.5 else "🟡" if growth > 0 else "🔴"
            
            table.add_row(
                channel['name'],
                f"{channel['subscribers']:,}",
                f"{growth:.2f}%",
                status
            )
    
    console.print(table)

def main():
    """Run quick metrics check"""
    console.print("[dim]Fetching latest metrics...[/dim]")
    
    try:
        data = get_latest_metrics()
        
        # Show 5-minute summary
        show_5_minute_summary(data)
        
        # Show channel table
        console.print()
        show_channel_table(data)
        
        # Footer
        console.print(f"\n[dim]Full dashboard: https://sigurd313.github.io/ai-media-empire-analytics/[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error fetching metrics: {e}[/red]")
        console.print("[yellow]Check: https://github.com/Sigurd313/ai-media-empire-analytics/actions[/yellow]")

if __name__ == "__main__":
    main()
