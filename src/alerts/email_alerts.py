"""Email alert system for inventory notifications"""
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import smtplib
from jinja2 import Template
from pathlib import Path

class EmailAlertSystem:
    def __init__(self, config):
        self.config = config
        self.email_config = config['alerts']['email']
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.from_email = os.getenv('ALERT_EMAIL_FROM')
        self.to_emails = os.getenv('ALERT_EMAIL_TO', '').split(',')
        
        # Load email template
        template_path = Path('templates/email/alert_template.html')
        if template_path.exists():
            with open(template_path) as f:
                self.template = Template(f.read())
        else:
            self.template = None
    
    def send_alert(self, alert_data):
        """Send immediate alert email"""
        subject = f"{self.email_config['subject_prefix']} {alert_data['title']}"
        
        if self.template:
            html_content = self.template.render(
                title=alert_data['title'],
                drawer_name=alert_data['drawer_name'],
                current_count=alert_data['current_count'],
                threshold=alert_data['threshold'],
                timestamp=alert_data['timestamp'],
                priority=alert_data['priority'],
                image_path=alert_data.get('image_path')
            )
        else:
            html_content = f"""
            <html>
            <body>
                <h2 style="color: #d32f2f;">Inventory Alert</h2>
                <p><strong>Drawer:</strong> {alert_data['drawer_name']}</p>
                <p><strong>Current Count:</strong> {alert_data['current_count']}</p>
                <p><strong>Threshold:</strong> {alert_data['threshold']}</p>
                <p><strong>Status:</strong> {alert_data['priority'].upper()}</p>
                <p><strong>Time:</strong> {alert_data['timestamp']}</p>
            </body>
            </html>
            """
        
        self._send_email(subject, html_content, alert_data.get('image_path'))
    
    def _send_email(self, subject, html_content, image_path=None):
        """Internal method to send email via SMTP"""
        try:
            msg = MIMEMultipart('related')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Attach image if provided
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', '<alert_image>')
                    msg.attach(img)
            
            # Send via SMTP
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_user = os.getenv('SMTP_USERNAME')
            smtp_pass = os.getenv('SMTP_PASSWORD')
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            print(f"✓ Alert email sent to {', '.join(self.to_emails)}")
            
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
