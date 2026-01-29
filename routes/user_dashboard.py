"""
User Dashboard Routes
Provides user-specific dashboard data and prediction history
Enhanced with PDF generation support
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from dependencies import get_current_user
from database import db, predictions_col, chat_col
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
import tempfile
from routes.notifications import notify_admins_event

router = APIRouter()

@router.get("/user")
async def get_user_dashboard(user: dict = Depends(get_current_user)):
    """Get user dashboard data with enhanced data structure for better visualization"""
    try:
        user_email = user.get("email")
        
        # Get user statistics
        total_chats = await chat_col.count_documents(
            {"user_email": user_email, "type": "chat_interaction"}
        )
        total_predictions = await predictions_col.count_documents({"user_email": user_email})
        heart_predictions = await predictions_col.count_documents({"user_email": user_email, "type": "heart"})
        alzheimer_predictions = await predictions_col.count_documents({"user_email": user_email, "type": "alzheimer"})
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_chats = await chat_col.count_documents(
            {
                "user_email": user_email,
                "type": "chat_interaction",
                "timestamp": {"$gte": thirty_days_ago},
            }
        )
        recent_predictions = await predictions_col.count_documents({
            "user_email": user_email,
            "timestamp": {"$gte": thirty_days_ago}
        })
        
        # Get daily activity for the last 30 days with better formatting
        daily_activity = []
        for i in range(30):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            start_date = datetime.combine(date, datetime.min.time())
            end_date = datetime.combine(date, datetime.max.time())
            
            daily_chats = await chat_col.count_documents(
                {
                    "user_email": user_email,
                    "type": "chat_interaction",
                    "timestamp": {"$gte": start_date, "$lte": end_date},
                }
            )
            
            daily_predictions = await predictions_col.count_documents({
                "user_email": user_email,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            daily_activity.append({
                "date": date.strftime("%m/%d"),  # Shorter date format for better display
                "fullDate": date.strftime("%Y-%m-%d"),
                "chats": daily_chats,
                "predictions": daily_predictions,
                "total": daily_chats + daily_predictions
            })
        
        daily_activity.reverse()  # Show oldest to newest
        
        # Get risk level distribution with enhanced data
        risk_distribution = {"Low": 0, "Medium": 0, "High": 0}
        prediction_types = {"heart": 0, "alzheimer": 0, "other": 0}
        
        async for prediction in predictions_col.find({"user_email": user_email}):
            risk_level = prediction.get("risk_level", "Low")
            pred_type = prediction.get("type", "other")
            
            # Normalize risk level
            if risk_level.lower() in ["high", "critical", "severe"]:
                risk_distribution["High"] += 1
            elif risk_level.lower() in ["medium", "moderate", "intermediate"]:
                risk_distribution["Medium"] += 1
            else:
                risk_distribution["Low"] += 1
            
            # Normalize prediction type
            if pred_type.lower() in ["heart", "cardiac", "cardiovascular"]:
                prediction_types["heart"] += 1
            elif pred_type.lower() in ["alzheimer", "cognitive", "dementia", "memory"]:
                prediction_types["alzheimer"] += 1
            else:
                prediction_types["other"] += 1
        
        # Format data for pie charts
        risk_data = [
            { "name": "Low Risk", "value": risk_distribution["Low"], "color": "#27ae60" },
            { "name": "Medium Risk", "value": risk_distribution["Medium"], "color": "#f39c12" },
            { "name": "High Risk", "value": risk_distribution["High"], "color": "#e74c3c" }
        ]
        
        prediction_type_data = [
            { "name": "Heart Predictions", "value": prediction_types["heart"], "color": "#3498db" },
            { "name": "Alzheimer Predictions", "value": prediction_types["alzheimer"], "color": "#9b59b6" },
            { "name": "Other Predictions", "value": prediction_types["other"], "color": "#95a5a6" }
        ]
        
        # Get recent activity summary
        recent_activity_summary = []
        for i in range(7):  # Last 7 days
            date = (datetime.utcnow() - timedelta(days=i)).date()
            start_date = datetime.combine(date, datetime.min.time())
            end_date = datetime.combine(date, datetime.max.time())
            
            day_chats = await chat_col.count_documents(
                {
                    "user_email": user_email,
                    "type": "chat_interaction",
                    "timestamp": {"$gte": start_date, "$lte": end_date},
                }
            )
            
            day_predictions = await predictions_col.count_documents({
                "user_email": user_email,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            recent_activity_summary.append({
                "day": date.strftime("%a"),  # Mon, Tue, etc.
                "date": date.strftime("%m/%d"),
                "chats": day_chats,
                "predictions": day_predictions,
                "total": day_chats + day_predictions
            })
        
        recent_activity_summary.reverse()
        
        return {
            "user": {
                "email": user_email,
                "is_admin": user.get("is_admin", False),
                "role": user.get("role", "user")
            },
            "stats": {
                "total_chats": total_chats,
                "total_predictions": total_predictions,
                "heart_predictions": heart_predictions,
                "alzheimer_predictions": alzheimer_predictions,
                "recent_chats": recent_chats,
                "recent_predictions": recent_predictions,
                "medicine_recommendations": total_chats,  # Approximate based on chats
                "avg_daily_activity": round((recent_chats + recent_predictions) / 30, 1)
            },
            "daily_activity": daily_activity,
            "recent_activity": recent_activity_summary,
            "risk_distribution": risk_distribution,
            "risk_data": risk_data,
            "prediction_types": prediction_types,
            "prediction_type_data": prediction_type_data,
            "engagement_metrics": {
                "most_active_day": max(daily_activity, key=lambda x: x["total"])["date"] if daily_activity else None,
                "total_days_active": len([day for day in daily_activity if day["total"] > 0]),
                "streak_days": len([day for day in daily_activity[-7:] if day["total"] > 0]),  # Last 7 days
                "peak_activity": max([day["total"] for day in daily_activity]) if daily_activity else 0
            }
        }
        
    except Exception as e:
        print(f"Error getting user dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user dashboard data")

@router.get("/user/chat-history")
async def get_user_chat_history(user: dict = Depends(get_current_user)):
    """Get user's chat history"""
    try:
        user_email = user.get("email")
        
        chat_history = []
        async for chat in (
            chat_col.find({"user_email": user_email, "type": "chat_interaction"})
            .sort("timestamp", -1)
            .limit(50)
        ):
            chat_history.append({
                "user_message": chat["user_message"],
                "ai_response": chat["ai_response"],
                "condition": chat.get("condition"),
                "medicines": chat.get("medicines"),
                "timestamp": chat["timestamp"],
                "urgency": chat.get("urgency"),
                "category": chat.get("category"),
                "keywords": chat.get("keywords", [])
            })
        
        return chat_history
        
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")


@router.get("/user/admin-messages")
async def get_user_admin_messages(user: dict = Depends(get_current_user)):
    """
    Get direct admin messages for the logged-in user.

    Used by the frontend 'Mail' / notifications UI to show
    admin-to-user communications separately from AI chat.
    """
    try:
        user_email = user.get("email")

        messages: List[Dict[str, Any]] = []
        async for msg in chat_col.find(
            {
                "user_email": user_email,
                "type": "admin_message",
            }
        ).sort("timestamp", -1):
            messages.append(
                {
                    "subject": msg.get("subject", "Message from Admin"),
                    "message": msg.get("admin_message") or msg.get("message", ""),
                    "timestamp": msg.get("timestamp"),
                    "admin_email": msg.get("admin_email"),
                    "is_read": msg.get("is_read", False),
                }
            )

        return messages

    except Exception as e:
        print(f"Error getting admin messages: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch admin messages"
        )


@router.get("/user/direct-messages")
async def get_user_direct_messages(user: dict = Depends(get_current_user)):
    """
    Get the direct (human-to-human) conversation between the logged-in user and admins.
    This intentionally excludes AI medical chat interactions.
    """
    try:
        user_email = user.get("email")

        messages: List[Dict[str, Any]] = []
        async for msg in (
            chat_col.find(
                {"user_email": user_email, "type": {"$in": ["admin_message", "user_message"]}},
                {"_id": 0},
            )
            .sort("timestamp", -1)
        ):
            is_admin = bool(msg.get("type") == "admin_message" or msg.get("is_admin"))
            messages.append(
                {
                    "sender": "admin" if is_admin else "user",
                    "subject": msg.get("subject"),
                    "message": msg.get("admin_message") or msg.get("message") or msg.get("user_message") or "",
                    "timestamp": msg.get("timestamp"),
                    "admin_email": msg.get("admin_email"),
                }
            )

        return messages
    except Exception as e:
        print(f"Error getting direct messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch direct messages")


@router.post("/user/contact-admin")
async def contact_admin(payload: dict, user: dict = Depends(get_current_user)):
    """
    User -> Admin direct message (separate from AI medical chat).
    Persists a 'user_message' and notifies admins via WebSocket for real-time inbox updates.
    """
    try:
        user_email = user.get("email")
        message = (payload.get("message") or "").strip()
        subject = (payload.get("subject") or "Message from user").strip()

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        entry = {
            "user_email": user_email,
            "message": message,
            "subject": subject,
            "timestamp": datetime.utcnow(),
            "type": "user_message",
            "is_admin": False,
        }
        await chat_col.insert_one(entry)

        try:
            await notify_admins_event(
                "admin_inbox",
                {
                    "user_email": user_email,
                    "preview": message[:200],
                    "subject": subject,
                    "timestamp": entry["timestamp"].isoformat(),
                },
            )
        except Exception as e:
            print(f"⚠️ Failed to notify admins via WebSocket: {e}")

        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending message to admin: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message to admin")
@router.get("/user/predictions")
async def get_user_predictions(user: dict = Depends(get_current_user)):
    """Get user's prediction history"""
    try:
        user_email = user.get("email")
        
        predictions = []
        async for prediction in predictions_col.find({"user_email": user_email}).sort("timestamp", -1).limit(50):
            predictions.append({
                "type": prediction["type"],
                "result": prediction["result"],
                "risk_percentage": prediction.get("risk_percentage", 0),
                "risk_level": prediction.get("risk_level", "Low"),
                "confidence": prediction.get("confidence", 0.5),
                "timestamp": prediction["timestamp"],
                "model_used": prediction.get("model_used", "unknown"),
                "details": prediction.get("details", {})
            })
        
        return predictions
        
    except Exception as e:
        print(f"Error getting predictions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch predictions")

def _fmt_ts(ts) -> str:
    """Format timestamp for report display; tolerate datetime, str, or None."""
    if ts is None:
        return "N/A"
    if hasattr(ts, "strftime"):
        return ts.strftime("%Y-%m-%d %H:%M")
    return str(ts)


@router.get("/user/download-report")
async def download_user_report(user: dict = Depends(get_current_user)):
    """Download user's personal medical report as PDF or HTML"""
    try:
        user_email = user.get("email")
        
        # Only AI consultations (chat_interaction) for report
        chat_history = []
        async for chat in chat_col.find(
            {"user_email": user_email, "type": "chat_interaction"}
        ).sort("timestamp", -1):
            chat_history.append(chat)
        
        predictions = []
        async for prediction in predictions_col.find({"user_email": user_email}).sort("timestamp", -1):
            predictions.append(prediction)
        
        # Try to generate PDF, fallback to HTML if PDF generation fails
        try:
            pdf_content = generate_user_report_pdf(user_email, chat_history, predictions)
            if pdf_content:
                return Response(
                    content=pdf_content,
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=medical_report_{user_email}_{datetime.now().strftime('%Y%m%d')}.pdf"}
                )
        except Exception as pdf_error:
            print(f" PDF generation failed, falling back to HTML: {pdf_error}")
        
        # Fallback to HTML
        html_content = generate_user_report_html(user_email, chat_history, predictions)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=medical_report_{user_email}_{datetime.now().strftime('%Y%m%d')}.html"}
        )
        
    except Exception as e:
        print(f"Error generating user report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate user report")

def generate_user_report_pdf(user_email: str, chat_history: List[Dict], predictions: List[Dict]) -> bytes:
    """Generate PDF report using weasyprint or reportlab"""
    try:
        # Try using weasyprint first (better HTML to PDF conversion)
        try:
            from weasyprint import HTML, CSS
            html_content = generate_user_report_html(user_email, chat_history, predictions)
            
            # Create PDF from HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
            
        except ImportError:
            print(" WeasyPrint not available, trying ReportLab...")
            
            # Fallback to ReportLab
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib import colors
                from io import BytesIO
                
                # Create PDF buffer
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                
                # Get styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    spaceAfter=30,
                    textColor=colors.HexColor('#667eea')
                )
                
                # Build story
                story = []
                
                # Title
                story.append(Paragraph("Medical AI Report", title_style))
                story.append(Paragraph(f"Generated for: {user_email}", styles['Normal']))
                story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Statistics
                story.append(Paragraph("Usage Statistics", styles['Heading2']))
                
                stats_data = [
                    ['Metric', 'Count'],
                    ['AI Consultations', str(len(chat_history))],
                    ['Health Predictions', str(len(predictions))],
                    ['Heart Assessments', str(len([p for p in predictions if (p.get('type') or '').lower() == 'heart']))],
                    ['Cognitive Assessments', str(len([p for p in predictions if (p.get('type') or '').lower() == 'alzheimer']))]
                ]
                
                stats_table = Table(stats_data)
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(stats_table)
                story.append(Spacer(1, 20))
                
                # Recent Predictions
                if predictions:
                    story.append(Paragraph("Recent Health Predictions", styles['Heading2']))
                    
                    for pred in predictions[:5]:
                        ptype = pred.get("type") or "unknown"
                        result = pred.get("result") or "—"
                        pct = pred.get("risk_percentage", 0)
                        level = pred.get("risk_level", "Low")
                        ts = _fmt_ts(pred.get("timestamp"))
                        lines = [f"Type: {str(ptype).title()}", f"Result: {result}", f"Risk: {pct}% - {level}", f"Date: {ts}"]
                        story.append(Paragraph("<br/>".join(lines), styles['Normal']))
                        story.append(Spacer(1, 12))
                
                # Build PDF
                doc.build(story)
                
                # Get PDF bytes
                pdf_bytes = buffer.getvalue()
                buffer.close()
                
                return pdf_bytes
                
            except ImportError:
                print(" ReportLab not available, cannot generate PDF")
                return None
                
    except Exception as e:
        print(f" Error generating PDF: {e}")
        return None

def generate_user_report_html(user_email: str, chat_history: List[Dict], predictions: List[Dict]) -> str:
    """Generate a beautiful HTML report for the user"""
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Medical AI Report - {user_email}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f7fa;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 1.1em;
            }}
            .content {{
                padding: 30px;
            }}
            .section {{
                margin-bottom: 40px;
            }}
            .section h2 {{
                color: #667eea;
                border-bottom: 2px solid #e0e6ed;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border-left: 4px solid #667eea;
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }}
            .stat-label {{
                color: #666;
                font-size: 0.9em;
            }}
            .prediction-item {{
                background: #f8f9fa;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 8px;
                border-left: 4px solid #28a745;
            }}
            .prediction-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }}
            .prediction-type {{
                background: #667eea;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
            }}
            .risk-level {{
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 0.8em;
                font-weight: bold;
            }}
            .risk-high {{ background: #dc3545; color: white; }}
            .risk-medium {{ background: #ffc107; color: #333; }}
            .risk-low {{ background: #28a745; color: white; }}
            .chat-item {{
                background: #f8f9fa;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 8px;
                border-left: 4px solid #17a2b8;
            }}
            .chat-message {{
                margin-bottom: 10px;
            }}
            .chat-response {{
                background: white;
                padding: 15px;
                border-radius: 5px;
                margin-top: 10px;
            }}
            .condition-tag {{
                background: #6f42c1;
                color: white;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 0.7em;
                margin-left: 10px;
            }}
            .timestamp {{
                color: #666;
                font-size: 0.8em;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                border-top: 1px solid #e0e6ed;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Medical AI Report</h1>
                <p>Personal Health Analytics & AI Consultations</p>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2>📊 Usage Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{len(chat_history)}</div>
                            <div class="stat-label">AI Consultations</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{len(predictions)}</div>
                            <div class="stat-label">Health Predictions</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{len([p for p in predictions if (p.get('type') or '').lower() == 'heart'])}</div>
                            <div class="stat-label">Heart Assessments</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{len([p for p in predictions if (p.get('type') or '').lower() == 'alzheimer'])}</div>
                            <div class="stat-label">Cognitive Assessments</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🔮 Health Predictions</h2>
    """
    
    if predictions:
        for pred in predictions[:10]:
            ptype = (pred.get("type") or "unknown").lower()
            risk_class = f"risk-{(pred.get('risk_level') or 'low').lower()}"
            pct = pred.get("risk_percentage", 0)
            level = pred.get("risk_level") or "Low"
            result = pred.get("result") or "—"
            conf = pred.get("confidence", 0)
            try:
                conf_pct = f"{float(conf):.1%}"
            except (TypeError, ValueError):
                conf_pct = "—"
            ts = _fmt_ts(pred.get("timestamp"))
            html += f"""
                    <div class="prediction-item">
                        <div class="prediction-header">
                            <span class="prediction-type">{(pred.get('type') or 'unknown').title()}</span>
                            <span class="risk-level {risk_class}">{pct}% Risk - {level}</span>
                        </div>
                        <div class="prediction-message">
                            <strong>Result:</strong> {result}<br>
                            <strong>Confidence:</strong> {conf_pct}<br>
                            <span class="timestamp">{ts}</span>
                        </div>
                    </div>
            """
    else:
        html += "<p>No predictions available yet.</p>"
    
    html += """
                </div>
                
                <div class="section">
                    <h2>💬 AI Consultations</h2>
    """
    
    if chat_history:
        for chat in chat_history[:10]:
            um = chat.get("user_message") or ""
            ar = chat.get("ai_response") or ""
            cond = chat.get("condition")
            condition_tag = f'<span class="condition-tag">{cond}</span>' if cond else ''
            ts = _fmt_ts(chat.get("timestamp"))
            html += f"""
                    <div class="chat-item">
                        <div class="chat-message"><strong>You:</strong> {um}</div>
                        <div class="chat-response"><strong>AI Assistant:</strong> {ar} {condition_tag}</div>
                        <span class="timestamp">{ts}</span>
                    </div>
            """
    else:
        html += "<p>No chat history available yet.</p>"
    
    html += f"""
                </div>
            </div>
            
            <div class="footer">
                <p>This report was generated by Medical AI Assistant</p>
                <p>For user: {user_email}</p>
                <p><em>This report is for informational purposes only and should not replace professional medical advice.</em></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html