"""Inventory trend report generator — supports single-day and multi-day ranges."""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Template
import base64
from io import BytesIO


class DailyReportGenerator:
    def __init__(self, config, db_session):
        self.config = config
        self.db_session = db_session

        template_path = Path("templates/reports/daily_report.html")
        if template_path.exists():
            with open(template_path) as f:
                self.template = Template(f.read())
        else:
            self.template = None

    def generate_report(self, start_date=None, end_date=None):
        """Generate an inventory trend report for the given date range."""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=5)

        from src.utils.database import InventorySnapshot, Alert

        snapshots = self.db_session.query(InventorySnapshot).filter(
            InventorySnapshot.timestamp.between(start_date, end_date)
        ).all()

        alerts = self.db_session.query(Alert).filter(
            Alert.created_at.between(start_date, end_date)
        ).all()

        df = pd.DataFrame([{
            "drawer": s.drawer_id,
            "timestamp": s.timestamp,
            "count": s.part_count,
            "status": s.status
        } for s in snapshots])

        stats = self._calculate_statistics(df, alerts, start_date, end_date)
        charts = self._generate_charts(df, start_date, end_date)

        if self.template:
            html_content = self.template.render(
                report_date=end_date.strftime("%Y-%m-%d"),
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                statistics=stats,
                charts=charts,
                alerts=alerts
            )
        else:
            html_content = self._render_fallback(stats, charts, alerts, start_date, end_date)

        output_path = Path(f"data/outputs/reports/trend_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(html_content)

        print(f"Report generated: {output_path}")
        return output_path

    def _calculate_statistics(self, df, alerts, start_date, end_date):
        if df.empty:
            return {}

        # Daily average count per partition
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        daily_avg = df.groupby(["date", "drawer"])["count"].mean().unstack(fill_value=0)

        # Reduction from first day to last day per partition
        reduction = {}
        if len(daily_avg) >= 2:
            first_day = daily_avg.iloc[0]
            last_day = daily_avg.iloc[-1]
            for drawer in daily_avg.columns:
                start_val = first_day[drawer]
                end_val = last_day[drawer]
                pct = ((start_val - end_val) / start_val * 100) if start_val > 0 else 0
                reduction[drawer] = {
                    "start": round(start_val, 1),
                    "end": round(end_val, 1),
                    "reduction_pct": round(pct, 1)
                }

        return {
            "total_snapshots": len(df),
            "total_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a.alert_type == "CRITICAL"]),
            "drawers_monitored": df["drawer"].nunique(),
            "days_covered": (end_date - start_date).days,
            "avg_parts_per_drawer": df.groupby("drawer")["count"].mean().round(1).to_dict(),
            "min_counts": df.groupby("drawer")["count"].min().to_dict(),
            "max_counts": df.groupby("drawer")["count"].max().to_dict(),
            "reduction": reduction,
            "daily_avg": daily_avg.reset_index().to_dict(orient="records")
        }

    def _generate_charts(self, df, start_date, end_date):
        charts = {}
        if df.empty:
            return charts

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date

        # --- Chart 1: Daily average count trend per partition ---
        daily_avg = df.groupby(["date", "drawer"])["count"].mean().reset_index()

        fig, ax = plt.subplots(figsize=(12, 5))
        for drawer in daily_avg["drawer"].unique():
            drawer_data = daily_avg[daily_avg["drawer"] == drawer].sort_values("date")
            ax.plot(
                pd.to_datetime(drawer_data["date"]),
                drawer_data["count"],
                marker="o",
                linewidth=2,
                markersize=6,
                label=drawer
            )

        ax.set_xlabel("Date")
        ax.set_ylabel("Average Part Count")
        ax.set_title("Inventory Trend — Daily Average Count per Partition")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        fig.autofmt_xdate()
        plt.tight_layout()

        charts["timeline"] = self._fig_to_base64(fig)

        # --- Chart 2: Reduction bar chart (start vs end) ---
        drawers = df["drawer"].unique()
        dates = sorted(df["date"].unique())
        if len(dates) >= 2:
            first_day = dates[0]
            last_day = dates[-1]

            start_counts = df[df["date"] == first_day].groupby("drawer")["count"].mean()
            end_counts = df[df["date"] == last_day].groupby("drawer")["count"].mean()

            x = range(len(drawers))
            width = 0.35
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            bars1 = ax2.bar([i - width / 2 for i in x],
                            [start_counts.get(d, 0) for d in drawers],
                            width, label=f"Day 1 ({first_day})", color="#667eea", alpha=0.8)
            bars2 = ax2.bar([i + width / 2 for i in x],
                            [end_counts.get(d, 0) for d in drawers],
                            width, label=f"Day {len(dates)} ({last_day})", color="#e53e3e", alpha=0.8)

            ax2.set_xlabel("Partition")
            ax2.set_ylabel("Average Part Count")
            ax2.set_title("Start vs End Count by Partition")
            ax2.set_xticks(list(x))
            ax2.set_xticklabels(list(drawers), rotation=15)
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis="y")
            plt.tight_layout()

            charts["reduction_bar"] = self._fig_to_base64(fig2)

        return charts

    def _fig_to_base64(self, fig):
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        return encoded

    def _render_fallback(self, stats, charts, alerts, start_date, end_date):
        """Minimal HTML fallback if template file is missing."""
        reduction_html = ""
        for drawer, info in stats.get("reduction", {}).items():
            reduction_html += f"""
            <tr>
              <td>{drawer}</td>
              <td>{info['start']}</td>
              <td>{info['end']}</td>
              <td>{info['reduction_pct']}%</td>
            </tr>"""

        timeline_img = f'<img src="data:image/png;base64,{charts["timeline"]}" style="max-width:100%"/>' if charts.get("timeline") else ""
        bar_img = f'<img src="data:image/png;base64,{charts["reduction_bar"]}" style="max-width:100%"/>' if charts.get("reduction_bar") else ""

        return f"""<!DOCTYPE html>
<html>
<head>
  <title>Inventory Trend Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
    h1 {{ color: #667eea; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
    th {{ background: #667eea; color: white; }}
    .chart {{ margin: 30px 0; }}
    .stat {{ display: inline-block; background: #f5f5f5; padding: 15px 25px; margin: 10px; border-radius: 8px; text-align: center; }}
    .stat-val {{ font-size: 28px; font-weight: bold; color: #667eea; }}
  </style>
</head>
<body>
  <h1>Inventory Trend Report</h1>
  <p><strong>Period:</strong> {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({stats.get('days_covered', '?')} days)</p>

  <div>
    <div class="stat"><div class="stat-val">{stats.get('total_snapshots', 0)}</div>Total Checks</div>
    <div class="stat"><div class="stat-val">{stats.get('drawers_monitored', 0)}</div>Partitions</div>
    <div class="stat"><div class="stat-val">{stats.get('total_alerts', 0)}</div>Alerts</div>
    <div class="stat"><div class="stat-val">{stats.get('critical_alerts', 0)}</div>Critical</div>
  </div>

  <h2>Reduction Summary</h2>
  <table>
    <tr><th>Partition</th><th>Day 1 Avg Count</th><th>Final Day Avg Count</th><th>Reduction</th></tr>
    {reduction_html}
  </table>

  <div class="chart"><h2>Count Trend Over Time</h2>{timeline_img}</div>
  <div class="chart"><h2>Start vs End Comparison</h2>{bar_img}</div>

  <h2>Alerts</h2>
  {''.join(f"<p><b>{a.drawer_id}</b> — {a.alert_type} — {a.part_count} parts — {a.created_at.strftime('%Y-%m-%d %H:%M')}</p>" for a in alerts) or '<p>No alerts.</p>'}
</body>
</html>"""
