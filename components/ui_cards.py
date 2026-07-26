import streamlit.components.v1 as components

def render_cyber_header(title, subtitle, username, sector):
    """Renders an ultra-modern SaaS top navigation bar with live status indicator."""
    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body {{ background-color: transparent; margin: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
            .saas-nav {{
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(3, 7, 18, 0.95) 100%);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 16px;
                padding: 20px 24px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            }}
            .glow-dot {{
                height: 8px; width: 8px; background-color: #22c55e; border-radius: 50%;
                box-shadow: 0 0 12px #22c55e; animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }}
                70% {{ transform: scale(1); box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }}
                100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
            }}
        </style>
    </head>
    <body>
        <div class="saas-nav">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 12px; border-radius: 14px; font-size: 20px; box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);">🛡️</div>
                <div>
                    <h3 style="margin: 0; font-size: 18px; font-weight: 700; color: #f8fafc; letter-spacing: -0.5px;">{title} <span style="color: #38bdf8; font-size: 11px; border: 1px solid rgba(56, 189, 248, 0.3); padding: 2px 8px; border-radius: 6px; margin-left: 8px; background: rgba(56, 189, 248, 0.1);">ENTERPRISE</span></h3>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">{subtitle}</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 24px; font-size: 13px; color: #cbd5e1;">
                <div>👤 <span style="color: #f8fafc; font-weight: 600;">{username}</span></div>
                <div>📍 <span style="color: #94a3b8;">{sector}</span></div>
                <div style="display: flex; align-items: center; gap: 6px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); padding: 4px 12px; border-radius: 20px;">
                    <span class="glow-dot"></span>
                    <span style="color: #4ade80; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;">ACTIVE</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=95)
