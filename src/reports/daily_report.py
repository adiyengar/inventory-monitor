"""Daily inventory report generator"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Template
import base64
from io import BytesIO

class DailyReportGenerator:
    def __init__(self, config, db_session):
        self.config = config
        self.db_session = db_session
        
        # Load template
        template_path = Path('templates/reports/daily_report.html')
        if template_path.exists():
            with open(template_path) as f:
                self.template = Template(f.read())
    
    def generate_report(self, start_date=None, end_date=None):
        """Generate daily report with charts and statistics"""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        # Query data from database
        from src.utils.database import InventorySnapshot, Alert
        
        snapshots = self.db_session.query(InventorySnapshot).filter(
            InventorySnapshot.timestamp.between(start_date, end_date)
        ).all()
        
        alerts = self.db_session.query(Alert).filter(
            Alert.created_at.between(start_date, end_date)
        ).all()
        
        # Prepare data
        df = pd.DataFrame([{
            'drawer': s.drawer_id,
            'timestamp': s.timestamp,
            'count': s.part_count,
            'status': s.status
        } for s in snapshots])
        
        # Generate statistics
        stats = self._calculate_statistics(df, alerts)
        
        # Generate charts
        charts = self._generate_charts(df)
        
        # Render HTML report
        html_content = self.template.render(
            report_date=end_date.strftime('%Y-%m-%d'),
            statistics=stats,
            charts=charts,
            alerts=alerts
        )
        
        # Save report
        output_path = Path(f"data/outputs/reports/daily_report_{end_date.strftime('%Y%m%d')}.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"✓ Report generated: {output_path}")
        return output_path
    
    def _calculate_statistics(self, df, alerts):
        """Calculate summary statistics"""
        if df.empty:
            return {}
        
        stats = {
            'total_snapshots': len(df),
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a.alert_type == 'CRITICAL']),
            'drawers_monitored': df['drawer'].nunique(),
            'avg_parts_per_drawer': df.groupby('drawer')['count'].mean().to_dict(),
            'min_counts': df.groupby('drawer')['count'].min().to_dict(),
            'max_counts': df.groupby('drawer')['count'].max().to_dict()
        }
        
        return stats
    
    def _generate_charts(self, df):
        """Generate visualization charts"""
        charts = {}
        
        if df.empty:
            return charts
        
        # Timeline chart
        fig, ax = plt.subplots(figsize=(12, 6))
        for drawer in df['drawer'].unique():
            drawer_data = df[df['drawer'] == drawer]
            ax.plot(drawer_data['timestamp'], drawer_data['count'], 
                   marker='o', label=drawer)
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Part Count')
        ax.set_title('Inventory Levels Over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Convert to base64 for HTML embedding
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        charts['timeline'] = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return charts
