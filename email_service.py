import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_analysis_report(receiver_email, result):
    # Get configuration from .env
    smtp_server = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_PORT", "587"))
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password or "your-email" in sender_email:
        print("ERROR: Email credentials not configured in .env. Skipping email.")
        return False

    plant = result.get("plant", "Unknown Plant")
    disease = result.get("disease", "Unknown Condition")
    confidence = result.get("confidence", "N/A")
    description = result.get("description", "")
    cause = result.get("cause", "")
    solution = result.get("solution", "")

    # Create the email content
    message = MIMEMultipart("alternative")
    message["Subject"] = f"GreenMind AI: Plant Analysis Report ({plant})"
    message["From"] = f"GreenMind AI <{sender_email}>"
    message["To"] = receiver_email

    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #2e7d32; padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Plant Analysis Report</h1>
            </div>
            
            <div style="padding: 30px;">
                <p style="font-size: 16px; color: #333;">Hello,</p>
                <p style="font-size: 16px; color: #555;">We have analyzed your plant image. Here is the detailed report:</p>
                
                <div style="background-color: #f1f8e9; border-left: 5px solid #2e7d32; padding: 20px; margin: 25px 0;">
                    <p style="margin: 5px 0;"><strong>🌿 Plant:</strong> {plant}</p>
                    <p style="margin: 5px 0;"><strong>⚠️ Condition:</strong> <span style="color: {'#d32f2f' if disease != 'Healthy' else '#2e7d32'};">{disease}</span></p>
                    <p style="margin: 5px 0;"><strong>🎯 Confidence:</strong> {confidence}</p>
                </div>
                
                <h3 style="color: #2e7d32; border-bottom: 1px solid #eee; padding-bottom: 10px;">Summary</h3>
                <p style="color: #666; line-height: 1.6;">{description}</p>
                
                <h3 style="color: #2e7d32; border-bottom: 1px solid #eee; padding-bottom: 10px;">Cause</h3>
                <p style="color: #666; line-height: 1.6;">{cause}</p>
                
                <h3 style="color: #2e7d32; border-bottom: 1px solid #eee; padding-bottom: 10px;">Treatment Plan</h3>
                <p style="color: #333; line-height: 1.6; background-color: #fff9c4; padding: 15px; border-radius: 8px;">{solution}</p>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    GreenMind AI - Your Digital Garden Assistant<br>
                    This is an AI-generated report. Always consult a professional for critical plant care.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        # Create a secure SSL context and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            
        print(f"DEBUG: Email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to send email: {e}")
        return False
