#!/usr/bin/env python3
"""
Test script para enviar correo real con PDF usando la función send_email_confirmation
"""

import sys
import os
from datetime import datetime

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Importar directamente sin usar el sistema de agentes
sys.path.insert(0, '/Users/dariomariscal/Desktop/final_project_ai/gubernamental-agent/services/agent_adk')

# Importar las funciones necesarias directamente del archivo
import uuid
import base64
from io import BytesIO

try:
    import resend
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import black, red, darkgreen
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class MockToolContext:
    """Mock del ToolContext para el test"""
    def __init__(self):
        self.state = {
            "user_data": {
                "full_name": "Dario Mariscal Test",
                "curp": "MARS901015HDFRLR05",
                "address": "Calle Ejemplo #123, Col. Centro, Ciudad de México",
                "postal_code": "06000",
                "birth_date": "1990-10-15",
                "phone": "55-1234-5678",
                "email": "dariolive11@live.com.mx"
            },
            "service_determination": {
                "license_type": "LICENCIA_A",
                "procedure_type": "PRIMERA_VEZ",
                "costs": {"total_cost": 750.00}
            }
        }

def generate_semovi_pdf_bytes(tool_context, appointment_details: dict) -> dict:
    """
    Generate SEMOVI PDF in memory for email attachment.
    Returns PDF as base64 for use with Resend attachments.
    """
    try:
        # 1. RECUPERAR DATOS
        user_data = tool_context.state.get("user_data", {})
        user_name = user_data.get("full_name", "Usuario")
        user_curp = user_data.get("curp", "SIN DATO")
        user_address = user_data.get("address", "Sin dirección")

        confirmation_code = appointment_details.get("confirmation_code", "")
        office = appointment_details.get("office", {})
        license_type = appointment_details.get("license_type", "")
        procedure_type = appointment_details.get("procedure_type", "")
        appointment_date = appointment_details.get("date", "")
        appointment_time = appointment_details.get("time", "")
        total_cost = appointment_details.get("total_cost", 0)

        # 2. CREAR PDF EN MEMORIA
        buffer = BytesIO()
        
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # === HEADER SEMOVI ===
        c.setFillColor(red)
        c.rect(0, height-80, width, 80, fill=1)
        
        c.setFillColor('white')
        c.setFont("Helvetica-Bold", 22)
        c.drawString(50, height-35, "🚗 SEMOVI - COMPROBANTE DE CITA")
        
        c.setFont("Helvetica", 11)
        c.drawString(50, height-55, "Secretaría de Movilidad - Ciudad de México")
        
        # === CONFIRMACIÓN DESTACADA ===
        c.setFillColor(darkgreen)
        c.rect(50, height-150, width-100, 40, fill=1)
        
        c.setFillColor('white')
        c.setFont("Helvetica-Bold", 16)
        text_width = c.stringWidth(f"CONFIRMACIÓN: {confirmation_code}", "Helvetica-Bold", 16)
        c.drawString((width - text_width) / 2, height-135, f"CONFIRMACIÓN: {confirmation_code}")
        
        # === DATOS DEL SOLICITANTE ===
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height-190, "DATOS DEL SOLICITANTE:")
        
        c.setFont("Helvetica", 12)
        y_position = height-210
        solicitante_data = [
            f"👤 Nombre: {user_name}",
            f"🆔 CURP: {user_curp}",
            f"🏠 Dirección: {user_address}"
        ]
        
        for line in solicitante_data:
            c.drawString(70, y_position, line)
            y_position -= 20
        
        # === DETALLES DE LA CITA ===
        y_position -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "DETALLES DE LA CITA:")
        y_position -= 20
        
        c.setFont("Helvetica", 12)
        cita_data = [
            f"🎫 Tipo de Licencia: {license_type}",
            f"🔄 Procedimiento: {procedure_type}",
            f"📅 Fecha: {appointment_date}",
            f"⏰ Hora: {appointment_time}",
            f"📍 Oficina: {office.get('name', 'SEMOVI')}",
            f"💰 Costo Total: ${total_cost:.2f} MXN"
        ]
        
        for line in cita_data:
            c.drawString(70, y_position, line)
            y_position -= 20
        
        # === OFICINA INFORMACIÓN ===
        if office.get('address'):
            y_position -= 10
            c.setFont("Helvetica", 10)
            c.drawString(70, y_position, f"📧 Dirección: {office.get('address', '')}")
            y_position -= 15
            
        if office.get('phone'):
            c.drawString(70, y_position, f"📞 Teléfono: {office.get('phone', '')}")
            y_position -= 20
        
        # === RECORDATORIOS ===
        y_position -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "⚠️ RECORDATORIOS IMPORTANTES:")
        y_position -= 20
        
        c.setFont("Helvetica", 10)
        recordatorios = [
            "• Presente este comprobante el día de su cita",
            "• Llegue 10 minutos antes del horario programado",
            "• Traiga identificación oficial vigente (INE/Pasaporte)",
            "• Lleve el pago exacto en efectivo o tarjeta",
            "• Para reagendar, contacte la oficina con 24 horas de anticipación",
            "• Complete el curso de manejo si es requerido para su tipo de licencia"
        ]
        
        for recordatorio in recordatorios:
            c.drawString(70, y_position, recordatorio)
            y_position -= 16
        
        # === CÓDIGO QR SIMULADO ===
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, 100, "📱 CÓDIGO QR PARA CHECK-IN:")
        c.rect(50, 50, 70, 70, fill=0)
        c.drawString(70, 80, "QR")
        c.drawString(60, 70, f"ID:{confirmation_code[-4:]}")
        
        # === PIE DE PÁGINA ===
        c.setFont("Helvetica", 8)
        text1 = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        text2 = "© 2024 SEMOVI - Válido únicamente para la cita programada"
        text1_width = c.stringWidth(text1, "Helvetica", 8)
        text2_width = c.stringWidth(text2, "Helvetica", 8)
        c.drawString((width - text1_width) / 2, 30, text1)
        c.drawString((width - text2_width) / 2, 15, text2)
        
        c.save()
        
        # 3. CONVERTIR A BASE64
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        buffer.close()
        
        return {
            "status": "success",
            "message": "PDF SEMOVI generado en memoria",
            "pdf_base64": pdf_base64,
            "pdf_size": len(pdf_bytes)
        }
        
    except Exception as e:
        if 'buffer' in locals():
            buffer.close()
        return {"status": "error", "message": f"Error generando PDF: {str(e)}"}


def send_email_confirmation(tool_context, email: str, appointment_details: dict):
    """
    Send email confirmation using Resend with professional PDF attachment.
    """
    try:
        if not email or "@" not in email:
            return {
                "status": "error",
                "message": "Valid email address required"
            }
        
        # Extract appointment details
        confirmation_code = appointment_details.get("confirmation_code", "")
        office = appointment_details.get("office", {})
        office_name = office.get("name", "SEMOVI")
        appointment_date = appointment_details.get("date", "")
        appointment_time = appointment_details.get("time", "")
        license_type = appointment_details.get("license_type", "")
        procedure_type = appointment_details.get("procedure_type", "")
        total_cost = appointment_details.get("total_cost", 0)
        
        # Get user data
        user_data = tool_context.state.get("user_data", {})
        user_name = user_data.get("full_name", "Estimado/a Ciudadano/a")
        
        # 1. GENERAR PDF AUTOMÁTICAMENTE
        pdf_result = generate_semovi_pdf_bytes(tool_context, appointment_details)
        if pdf_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Error generando PDF: {pdf_result.get('message', 'Error desconocido')}"
            }
        
        # 2. CONFIGURAR RESEND
        resend_api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("RESEND_FROM_EMAIL", "Trámites Gubernamentales <notifications@diperion.com>")
        
        if not resend_api_key:
            return {"status": "error", "message": "RESEND_API_KEY no configurada en variables de entorno"}

        resend.api_key = resend_api_key

        # 3. CREAR CONTENIDO HTML PROFESIONAL PARA SEMOVI
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #fef2f2; padding: 30px; border-radius: 0 0 10px 10px; }}
                .appointment-card {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; border-left: 4px solid #dc2626; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 12px 0; padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
                .label {{ font-weight: bold; color: #7f1d1d; }}
                .value {{ color: #1f2937; }}
                .confirmation-box {{ background: #16a34a; color: white; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0; }}
                .cost-box {{ background: #fbbf24; color: #1f2937; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; margin-top: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🚗 SEMOVI</div>
                    <h1>Confirmación de Cita</h1>
                    <p>Secretaría de Movilidad - Ciudad de México</p>
                </div>
                
                <div class="content">
                    <p><strong>{user_name},</strong></p>
                    <p>Su cita para trámite de licencia de conducir ha sido <strong>confirmada exitosamente</strong>.</p>
                    
                    <div class="confirmation-box">
                        <h3>📋 Número de Confirmación: {confirmation_code}</h3>
                    </div>
                    
                    <div class="appointment-card">
                        <h3>🎫 Detalles de su Cita</h3>
                        <div class="detail-row">
                            <span class="label">👤 Solicitante:</span>
                            <span class="value">{user_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📅 Fecha:</span>
                            <span class="value">{appointment_date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">⏰ Hora:</span>
                            <span class="value">{appointment_time}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📍 Oficina SEMOVI:</span>
                            <span class="value">{office_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📋 Tipo de Licencia:</span>
                            <span class="value">{license_type}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">🔄 Procedimiento:</span>
                            <span class="value">{procedure_type}</span>
                        </div>
                    </div>
                    
                    <div class="cost-box">
                        <h4>💰 Costo Total: ${total_cost:.2f} MXN</h4>
                    </div>
                    
                    <div style="background: #fef3c7; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                        <h4>⚠️ Recordatorios Importantes:</h4>
                        <ul>
                            <li>🕘 Presente se <strong>10 minutos antes</strong> de su cita</li>
                            <li>🆔 Traiga su <strong>identificación oficial vigente</strong></li>
                            <li>📄 Adjunto encontrará su <strong>comprobante en PDF</strong></li>
                            <li>💳 Lleve el <strong>pago exacto</strong> en efectivo o tarjeta</li>
                            <li>📞 Para reagendar, contacte la oficina con 24 horas de anticipación</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Este correo fue generado automáticamente por el Sistema de Citas SEMOVI</p>
                    <p><small>© 2024 Secretaría de Movilidad - Ciudad de México</small></p>
                </div>
            </div>
        </body>
        </html>
        """

        # 4. ENVIAR EMAIL CON RESEND (SINTAXIS OFICIAL)
        params = {
            "from": from_email,
            "to": [email],
            "subject": f"✅ Confirmación de Cita SEMOVI - {confirmation_code}",
            "html": html_body,
            "attachments": [
                {
                    "content": pdf_result["pdf_base64"],
                    "filename": f"SEMOVI_Cita_{confirmation_code}.pdf"
                }
            ]
        }
        
        result = resend.Emails.send(params)

        return {
            "status": "success",
            "message": f"📧 Correo de confirmación enviado exitosamente a {email}",
            "confirmation_code": confirmation_code,
            "resend_id": result.get("id"),
            "email": email
        }

    except ImportError:
        return {"status": "error", "message": "Resend no está instalado. Instala con: pip install resend"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error enviando correo: {str(e)}"
        }

def main():
    print("🧪 INICIANDO TEST DE ENVÍO DE CORREO CON PDF")
    print("=" * 50)
    
    # Crear contexto mock
    tool_context = MockToolContext()
    
    # Datos de cita de prueba
    appointment_details = {
        "confirmation_code": "SEMOVI-20241202-TEST",
        "office": {
            "name": "Centro de Servicios SEMOVI Xochimilco",
            "address": "Av. División del Norte #1234, Xochimilco, CDMX",
            "phone": "55-5555-1234"
        },
        "date": "2024-12-10",
        "time": "10:30 AM",
        "license_type": "LICENCIA_A",
        "procedure_type": "PRIMERA_VEZ",
        "total_cost": 750.00,
        "created_at": datetime.now().isoformat()
    }
    
    # Email de destino
    email_destino = "dariolive11@live.com.mx"
    
    print(f"📧 Enviando correo a: {email_destino}")
    print(f"🎫 Código de confirmación: {appointment_details['confirmation_code']}")
    print(f"📅 Fecha de cita: {appointment_details['date']} a las {appointment_details['time']}")
    print()
    
    # Ejecutar envío de correo
    print("⏳ Ejecutando send_email_confirmation...")
    resultado = send_email_confirmation(
        tool_context=tool_context,
        email=email_destino,
        appointment_details=appointment_details
    )
    
    # Mostrar resultados
    print("\n" + "=" * 50)
    print("📋 RESULTADO DEL ENVÍO:")
    print("=" * 50)
    
    if resultado["status"] == "success":
        print("✅ ÉXITO - Correo enviado correctamente!")
        print(f"📧 Email: {resultado['email']}")
        print(f"🎫 Código: {resultado['confirmation_code']}")
        print(f"🆔 Resend ID: {resultado.get('resend_id', 'N/A')}")
        print(f"💌 Mensaje: {resultado['message']}")
    else:
        print("❌ ERROR - No se pudo enviar el correo")
        print(f"⚠️ Mensaje: {resultado['message']}")
    
    print("\n" + "=" * 50)
    print("🔍 VERIFICA TU CORREO:")
    print(f"📬 Revisa la bandeja de entrada de: {email_destino}")
    print(f"📎 El PDF debe estar adjunto como: SEMOVI_Cita_{appointment_details['confirmation_code']}.pdf")
    print("=" * 50)

if __name__ == "__main__":
    main()