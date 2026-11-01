import streamlit as st
import streamlit.components.v1 as components
import json
import os

def render_3d_background():
    """
    Injects the 3D animated WebGL background into Streamlit.
    """
    # 1. Custom CSS to make Streamlit transparent and style it
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;600&display=swap');

        :root {
            --bg-glass: rgba(10, 15, 30, 0.65);
            --bg-glass-hover: rgba(15, 22, 40, 0.8);
            --border-glass: rgba(0, 229, 255, 0.15);
            --border-glass-hover: rgba(0, 229, 255, 0.4);
            --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(0, 229, 255, 0.05);
            --shadow-hover: 0 8px 32px rgba(0, 229, 255, 0.15), 0 0 0 1px rgba(0, 229, 255, 0.3);
            
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-cyan: #00e5ff;
            --accent-blue: #1f6feb;
            --accent-purple: #aa00ff;
            
            --font-sans: 'Inter', system-ui, sans-serif;
            --font-mono: 'Fira Code', monospace;
        }

        /* Global Font */
        html, body, [class*="st-"] {
            font-family: var(--font-sans) !important;
        }

        /* Hide standard Streamlit background */
        .stApp, header[data-testid="stHeader"] {
            background: transparent !important;
        }

        /* Fluid Typography */
        h1 { font-size: clamp(2rem, 4vw, 3rem) !important; font-weight: 800 !important; letter-spacing: -0.03em; margin-bottom: 1.5rem !important; }
        h2 { font-size: clamp(1.5rem, 3vw, 2.25rem) !important; font-weight: 700 !important; letter-spacing: -0.02em; }
        h3 { font-size: clamp(1.25rem, 2vw, 1.75rem) !important; font-weight: 600 !important; }
        h1, h2, h3, h4, h5, h6 { color: var(--text-primary) !important; }
        p, span, div, label { color: var(--text-secondary) !important; }

        /* Premium Glassmorphism Cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--bg-glass) !important;
            backdrop-filter: blur(16px) saturate(180%) !important;
            border: 1px solid var(--border-glass) !important;
            border-radius: 16px !important;
            padding: 1rem !important;
            box-shadow: var(--shadow-soft) !important;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-2px) !important;
            background: var(--bg-glass-hover) !important;
            box-shadow: var(--shadow-hover) !important;
            border-color: var(--border-glass-hover) !important;
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-family: var(--font-mono) !important;
            color: var(--accent-cyan) !important;
            text-shadow: 0 0 20px rgba(0, 229, 255, 0.4) !important;
            font-weight: 700 !important;
            font-size: clamp(2rem, 3vw, 3rem) !important;
        }
        [data-testid="stMetricLabel"] {
            color: var(--text-secondary) !important;
            font-size: 1rem !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600 !important;
        }

        /* Segmented Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(0, 0, 0, 0.4);
            padding: 8px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent !important;
            border-radius: 8px !important;
            color: var(--text-secondary) !important;
            padding: 12px 24px !important;
            border: none !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: var(--text-primary) !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)) !important;
            color: white !important;
            box-shadow: 0 4px 15px rgba(170, 0, 255, 0.4) !important;
        }

        /* Buttons */
        .stButton>button {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-shadow: 0 4px 15px rgba(0, 229, 255, 0.2) !important;
        }
        .stButton>button p, .stButton>button span, .stButton>button div {
            color: white !important;
            font-family: var(--font-sans) !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
        }
        .stButton>button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 25px rgba(0, 229, 255, 0.4) !important;
        }
        .stButton>button:focus-visible {
            outline: 2px solid var(--accent-cyan) !important;
            outline-offset: 4px !important;
        }

        /* Dataframes */
        .stDataFrame {
            font-family: var(--font-mono) !important;
            background: rgba(0, 0, 0, 0.5) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        .stDataFrame [data-testid="StyledDataFrameDataCell"] {
            color: var(--text-primary) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 2. Render the actual iframe exactly ONCE
    if "bg_initialized" not in st.session_state:
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        scene_path = os.path.join(assets_dir, "scene.html")
        with open(scene_path, 'r', encoding='utf-8') as f:
            html_code = f.read()
            
        # Escape quotes for srcdoc
        html_code_escaped = html_code.replace("'", "&#39;").replace('"', "&quot;")
            
        components.html(
            f"""
            <div id="bg-3d">
                <iframe id="bg-iframe" srcdoc='{html_code_escaped}' style="width:100%; height:100%; border:none;"></iframe>
            </div>
            <script>
                // We need to pop this iframe out of the Streamlit sandbox so it covers the whole screen
                const iframe = document.getElementById('bg-iframe');
                const parentDiv = window.parent.document.createElement('div');
                parentDiv.id = 'bg-wrapper-3d';
                parentDiv.style.position = 'fixed';
                parentDiv.style.top = '0';
                parentDiv.style.left = '0';
                parentDiv.style.width = '100vw';
                parentDiv.style.height = '100vh';
                parentDiv.style.zIndex = '-999';
                parentDiv.style.pointerEvents = 'none';
                
                // Copy HTML into the parent body if not already there
                if (!window.parent.document.getElementById('bg-wrapper-3d')) {{
                    const newIframe = document.createElement('iframe');
                    newIframe.srcdoc = iframe.srcdoc;
                    newIframe.style.width = '100%';
                    newIframe.style.height = '100%';
                    newIframe.style.border = 'none';
                    newIframe.id = 'main-bg-iframe';
                    parentDiv.appendChild(newIframe);
                    window.parent.document.body.appendChild(parentDiv);
                }}
            </script>
            """,
            height=0, width=0
        )
        st.session_state.bg_initialized = True

def update_3d_state(device_states, attacking_device=None):
    """
    Sends a JS message to the background iframe to update colors and animations.
    (Optional hook for the 3D canvas)
    """
    pass
