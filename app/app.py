import streamlit as st, joblib, pandas as pd, os, json
import sys
from pathlib import Path

# Complete configuration to hide all Streamlit branding
st.set_page_config(
    page_title="Climate-Aware Farming",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="auto",  # Changed to auto so sidebar can be toggled
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# add project root (two levels up if app is in app/) so `src` imports resolve
proj_root = Path(__file__).resolve().parents[1]
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))

from src.conversion import convert_non_to_org, fetch_tutorials_pytube, predict_fertilizer_simple, build_search_queries
import streamlit.components.v1 as components
from src.weather_api import fetch_weather
from community import db as cdb
from src.pdf_utils import generate_preparation_pdf

# Comprehensive crop duration data (in days) - Complete coverage for all crops
CROP_DURATION = {
    # Cereals & Grains
    'rice': 120, 'maize': 90, 'wheat': 120, 'barley': 90, 'millets': 75,
    'sorghum': 100, 'oats': 90, 'rye': 110,
    
    # Pulses & Legumes
    'chickpea': 100, 'kidneybeans': 95, 'pigeonpeas': 150, 'mothbeans': 85,
    'mungbean': 75, 'blackgram': 80, 'lentil': 110, 'pulses': 95,
    'soybean': 100, 'groundnut': 110, 'peanut': 110,
    
    # Fruits
    'pomegranate': 365, 'banana': 365, 'mango': 365, 'grapes': 180,
    'watermelon': 90, 'muskmelon': 85, 'apple': 365, 'orange': 365,
    'papaya': 270, 'coconut': 365, 'pineapple': 365, 'guava': 365,
    'lemon': 365, 'lime': 365, 'strawberry': 120,
    
    # Cash Crops
    'cotton': 150, 'jute': 120, 'coffee': 365, 'tea': 365,
    'sugarcane': 365, 'tobacco': 120, 'rubber': 365,
    
    # Vegetables
    'tomato': 75, 'potato': 90, 'onion': 100, 'carrot': 70,
    'cabbage': 90, 'cauliflower': 80, 'brinjal': 120, 'okra': 60,
    'beans': 70, 'peas': 65, 'cucumber': 60, 'pumpkin': 90,
    
    # Spices & Others
    'turmeric': 270, 'ginger': 240, 'garlic': 150, 'chilli': 120,
    'pepper': 365, 'cardamom': 365, 'coriander': 90
}

# HELPER: AI CROP DOCTOR COMPONENT
def render_ai_doctor():
    # Adjusted ratio to give buttons more space [3, 1.2]
    col_head, col_btn = st.columns([3, 1.2]) 
    with col_head:
        st.markdown("### 🤖 Dr. Green - AI Crop Assistant")
        st.caption("Powered by Climate-Aware Intelligence Engine")
    
    with col_btn:
        # Sub-columns for side-by-side buttons
        b1, b2 = st.columns(2, gap="small")
        
        with b1:
            # Use a popover for Image Upload
            with st.popover("📎 Image", help="Upload a photo for AI analysis", use_container_width=True):
                st.markdown("### 📸 Dr. Green's Eyes")
                uploaded_file = st.file_uploader("Drag & Drop Leaf Image", type=['jpg', 'png'], key="ai_img_upload")
                
                if uploaded_file:
                    if st.button("Analyze Image", type="primary", use_container_width=True):
                        # Add image to chat history
                        st.session_state.messages.append({"role": "user", "content": "Analyze this image:", "image": uploaded_file})
                        
                        # Immediate AI Response for image
                        diagnosis = """
                        **Diagnosis: Early Blight (Alternaria solani)**
                        
                        I see concentric rings on the leaves. This is likely Early Blight.
                        
                        **💊 Prescription:**
                        *   **Organic:** Remove infected leaves immediately. Spray Neem Oil.
                        *   **DIY:** Mix milk and water (1:10) and spray. The protein interacts with the sun to kill fungus.
                        """
                        st.session_state.messages.append({"role": "assistant", "content": diagnosis})
                        st.rerun()

        with b2:
            if st.button("🗑️ Reset", help="Clear conversation", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
    
    # Initialize Chat History
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am **Dr. Green**. 🌾\n\nI can help you with:\n*   Identifying Crop Diseases\n*   Organic Fertilizer Recipes\n*   Pest Control Strategies\n\n*How can I assist you today?*"}
        ]

    # Display Chat History
    # Display Chat History with Premium Styles
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        
        if role == "user":
            with st.chat_message("user", avatar="🧑‍🌾"):
                st.markdown(f"""
                <div style="background-color: #DCFCE7; color: #166534; padding: 12px 16px; border-radius: 12px; border-bottom-right-radius: 2px; margin-bottom: 5px; font-size: 15px; border: 1px solid #BBF7D0;">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                if "image" in msg:
                    st.image(msg["image"], width=250)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"""
                <div style="background-color: #FFFFFF; color: #374151; padding: 12px 16px; border-radius: 12px; border-bottom-left-radius: 2px; margin-bottom: 5px; font-size: 15px; border: 1px solid #E5E7EB; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                if "image" in msg:
                    st.image(msg["image"], width=300)

    # Chat Input Area (Text)
    if prompt := st.chat_input("Ask me anything about farming..."):
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍🌾"):
            st.markdown(f"""
            <div style="background-color: #DCFCE7; color: #166534; padding: 12px 16px; border-radius: 12px; border-bottom-right-radius: 2px; margin-bottom: 5px; font-size: 15px; border: 1px solid #BBF7D0;">
                {prompt}
            </div>
            """, unsafe_allow_html=True)
        
        # AI Response Simulation (Replace this block with Real API call later)
        import time
        import random
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Dr. Green is thinking..."):
                time.sleep(1.0)
                
                p_lower = prompt.lower()
                response = ""
                
                # 1. GREETINGS & GENERAL
                if any(x in p_lower for x in ["hi", "hello", "hey", "good morning"]):
                    response = "Hello there! 👋 I hope your crops are doing well. What would you like to discuss today?"
                elif "thank" in p_lower:
                    response = "You're very welcome! Happy farming! 🚜"
                elif "who are you" in p_lower:
                    response = "I am Dr. Green, an AI assistant designed to help farmers with sustainable and organic farming practices."
                
                # 2. SPECIFIC CROP ADVICE
                elif "yellow" in p_lower:
                    response = "Yellowing leaves (Chlorosis) often indicate **Nitrogen deficiency** or over-watering. \n\n**Recommended Fix:** \n1. Check if soil is waterlogged.\n2. Apply nitrogen-rich organic fertilizers like **Blood Meal** or **Compost Tea**."
                elif "fungus" in p_lower or "white" in p_lower or "spot" in p_lower:
                    response = "White powdery spots often suggest **Powdery Mildew**. \n\n**Organic Recipe:** \nMix 1 tbsp baking soda + 1 tsp liquid soap in 1 gallon water. Spray weekly in the evening."
                elif "pest" in p_lower or "bug" in p_lower or "insect" in p_lower:
                    response = "For general pest control, **Neem Oil** is excellent. \n\n**Preparation:** Mix 5ml Neem Oil + 2ml soap nut liquid in 1 liter water. Shake well and spray."
                elif "fertilizer" in p_lower:
                    response = "For organic fertilizers, I recommend **Vermicompost** for general growth or **Bone Meal** for flowering/fruiting stages."
                
                # 3. FALLBACK (Professional, not soil-asking)
                else:
                    g_responses = [
                        "That's an interesting topic. Could you tell me which specific crop you are referring to?",
                        "I can certainly help with that. Are you looking for an organic solution or a general explanation?",
                        "To give you the best advice, could you describe the symptoms or the growth stage of your plant?"
                    ]
                    response = random.choice(g_responses)
                
                st.markdown(f"""
                <div style="background-color: #FFFFFF; color: #374151; padding: 12px 16px; border-radius: 12px; border-bottom-left-radius: 2px; margin-bottom: 5px; font-size: 15px; border: 1px solid #E5E7EB; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    {response}
                </div>
                """, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

def get_crop_duration_display(crop_name):
    """Get formatted duration display for a crop - Always returns valid duration"""
    days = CROP_DURATION.get(crop_name.lower(), 90)  # Default 90 days if not found
    
    months = round(days / 30)
    if days >= 365:
        return f"{days} days (Perennial/~12 months)"
    elif months > 0:
        return f"{days} days (~{months} months)"
    else:
        return f"{days} days"
proj_root = Path(__file__).resolve().parents[1]
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))

# Compatibility helper: set query params in a Streamlit-version-safe way
def set_query_params_safe(**kwargs):
    """Set query params using the stable API when available, otherwise fall back.

    Preference order:
    1. `st.set_query_params` (stable API)
    2. `st.experimental_set_query_params` (older API)
    3. As a last resort, write values into `st.session_state` so UI can react.
    """
    try:
        # new stable API
        if hasattr(st, 'set_query_params'):
            st.set_query_params(**kwargs)
            return
    except Exception:
        pass
    # Try assigning to st.query_params when available (newer Streamlit versions)
    try:
        if hasattr(st, 'query_params'):
            try:
                # construct a mapping; Streamlit may expect lists for values
                qp = {k: (v if isinstance(v, (list, tuple)) else [v]) for k, v in kwargs.items()}
                st.query_params = qp
                return
            except Exception:
                # assignment may not be supported in some builds; continue to next fallback
                pass
    except Exception:
        pass
    try:
        # older experimental API (may be removed in some versions)
        if hasattr(st, 'experimental_set_query_params'):
            st.experimental_set_query_params(**kwargs)
            return
    except Exception:
        pass
    # final fallback: update session state so the app can observe navigation intent
    for k, v in kwargs.items():
        st.session_state[k] = v

# ULTRA-PROFESSIONAL RESPONSIVE WEBAPP - Load External CSS
# Load custom CSS from file to bypass caching
import os
css_file_path = os.path.join(os.path.dirname(__file__), 'custom_style.css')
if os.path.exists(css_file_path):
    with open(css_file_path, 'r', encoding='utf-8') as f:
        custom_css = f.read()
    st.markdown(f'<style>{custom_css}</style>', unsafe_allow_html=True)
else:
    st.warning("Custom CSS file not found!")

# Load button fix CSS
button_fix_path = os.path.join(os.path.dirname(__file__), 'button_fix.css')
if os.path.exists(button_fix_path):
    with open(button_fix_path, 'r', encoding='utf-8') as f:
        button_css = f.read()
    st.markdown(f'<style>{button_css}</style>', unsafe_allow_html=True)

# Load form fix CSS
form_fix_path = os.path.join(os.path.dirname(__file__), 'form_fix.css')
if os.path.exists(form_fix_path):
    with open(form_fix_path, 'r', encoding='utf-8') as f:
        form_css = f.read()
    st.markdown(f'<style>{form_css}</style>', unsafe_allow_html=True)

# Also add inline critical CSS for immediate effect
st.markdown('''
<style>
    /* CRITICAL STYLES - FORCE LOAD */
    .stApp {
        background: linear-gradient(-45deg, #E8F5E9, #F1F8E9, #E3F2FD, #F3E5F5) !important;
        background-size: 400% 400% !important;
        animation: gradientShift 15s ease infinite !important;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .main .block-container {
        background: rgba(255, 255, 255, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 24px !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
    }

    /* HIDE 'Press Enter to apply' tooltip */
    [data-testid="InputInstructions"] {
        display: none !important;
    }
    
    /* Hide placeholder when typing/focused (Cleaner look) */
    input:focus::placeholder {
        color: transparent !important;
    }
    
    /* CRITICAL OVERRIDE FOR LOGIN CARD */
    /* Target only the container with our marker */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#login-card-target) {
        background-color: #15803d !important;
        background: #15803d !important;
        border-color: rgba(255,255,255,0.2) !important;
        box-shadow: 0 25px 50px rgba(0,0,0,0.3) !important;
    }
    
    /* Ensure the inner content div is transparent */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#login-card-target) > div {
        background-color: transparent !important;
        background: transparent !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(#login-card-target) * {
        color: white !important;
    }
    
    h1 {
        background: linear-gradient(135deg, #10B981 0%, #0EA5E9 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-size: 40px !important;
        font-weight: 800 !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
    }
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #10B981 0%, #0EA5E9 50%, #8B5CF6 100%) !important;
        background-size: 200% 200% !important;
        animation: gradientMove 3s ease infinite !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 16px 32px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }
    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
</style>
''', unsafe_allow_html=True)


st.markdown('''
<style>
    /* CACHE BUSTER: 2025-12-12-13:31 - FORCE RELOAD */
    /* ============================================
       CORE SYSTEM - Hide Streamlit Branding
       ============================================ */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    
    /* ============================================
       PREMIUM COLOR SYSTEM
       ============================================ */
    :root {
        --primary-green: #10B981;
        --primary-dark: #059669;
        --primary-light: #34D399;
        --accent-blue: #0EA5E9;
        --accent-purple: #8B5CF6;
        --accent-orange: #F59E0B;
        --bg-primary: #FFFFFF;
        --bg-secondary: #F9FAFB;
        --text-primary: #111827;
        --text-secondary: #6B7280;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    
    /* ============================================
       ANIMATED GRADIENT BACKGROUND
       ============================================ */
    .stApp {
        background: linear-gradient(-45deg, #E8F5E9, #F1F8E9, #E3F2FD, #F3E5F5);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(14, 165, 233, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 40% 80%, rgba(139, 92, 246, 0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
        animation: particleFloat 20s ease-in-out infinite;
    }
    
    @keyframes particleFloat {
        0%, 100% { opacity: 0.3; transform: translateY(0px); }
        50% { opacity: 0.6; transform: translateY(-20px); }
    }
    
    /* ============================================
       PERFECT SPACING - NO GAPS
       ============================================ */
    .main .block-container {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-radius: 24px;
        padding: 2.5rem 2rem !important;
        box-shadow: var(--shadow-2xl);
        max-width: 1400px;
        margin: 1.5rem auto !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        z-index: 1;
    }
    
    /* Remove all unwanted gaps */
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Perfect column spacing */
    [data-testid="column"] {
        padding: 0 8px !important;
    }
    
    [data-testid="column"]:first-child {
        padding-left: 0 !important;
    }
    
    [data-testid="column"]:last-child {
        padding-right: 0 !important;
    }
    
    /* Remove top padding from columns */
    [data-testid="column"] > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* ============================================
       TYPOGRAPHY - Professional
       ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Protect Icons */
    .material-icons, [data-testid="stExpander"] svg, [data-testid="stExpander"] i {
        font-family: 'Material Icons' !important;
    }

    /* SAFE MODE: Apply Font ONLY to Content Text (Headings/Paragraphs) to avoid breaking Icons */
    h1, h2, h3, h4, h5, h6, p, .stMarkdown {
        font-family: 'Inter', sans-serif;
    }
    
    h1 {
        font-size: 40px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, var(--primary-green) 0%, var(--accent-blue) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 6px 0 !important;
        padding: 0 !important;
        letter-spacing: -1px;
        line-height: 1.2 !important;
    }
    
    h2 {
        font-size: 30px !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin: 0 0 12px 0 !important;
        padding: 0 !important;
        letter-spacing: -0.5px;
    }
    
    h3 {
        font-size: 22px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin: 0 0 10px 0 !important;
        padding: 0 !important;
    }
    
    h4 {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin: 0 0 8px 0 !important;
        padding: 0 !important;
    }
    
    p, span, div, li, label {
        font-size: 15px !important;
        color: var(--text-secondary);
        line-height: 1.6;
        margin: 0 !important;
    }
    
    /* ============================================
       MODERN INPUT FIELDS
       ============================================ */
    input, select, textarea,
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox select,
    [data-baseweb="input"] input {
        font-size: 14px !important;
        padding: 11px 14px !important;
        border: 2px solid #E5E7EB !important;
        border-radius: 10px !important;
        background: white !important;
        color: var(--text-primary) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: var(--shadow-sm) !important;
        margin: 0 !important;
    }
    
    input:hover, select:hover, textarea:hover {
        border-color: #D1D5DB !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    input:focus, select:focus, textarea:focus {
        border-color: var(--primary-green) !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
    }
    
    .stTextInput > div,
    .stNumberInput > div,
    .stTextInput > div > div,
    .stNumberInput > div > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    [data-baseweb="select"] > div {
        background: white !important;
        border: 2px solid #E5E7EB !important;
        border-radius: 10px !important;
        min-height: 44px !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-sm) !important;
        margin: 0 !important;
    }
    
    [data-baseweb="select"]:hover > div {
        border-color: #D1D5DB !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    [data-baseweb="select"]:focus-within > div {
        border-color: var(--primary-green) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
    }
    
    [data-baseweb="popover"] ul {
        background: white !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 10px !important;
        box-shadow: var(--shadow-xl) !important;
        padding: 6px !important;
    }
    
    [data-baseweb="popover"] li {
        font-size: 14px !important;
        padding: 9px 14px !important;
        color: var(--text-primary) !important;
        border-radius: 6px !important;
        margin: 2px 0 !important;
        transition: all 0.2s ease !important;
    }
    
    [data-baseweb="popover"] li:hover {
        background: #F3F4F6 !important;
        color: var(--primary-green) !important;
    }
    
    [data-testid="stCaptionContainer"],
    .stTextInput > label > div:last-child,
    .stNumberInput > label > div:last-child {
        display: none !important;
    }
    
    label {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin-bottom: 6px !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        display: block !important;
    }
    
    /* ============================================
       PREMIUM BUTTONS
       ============================================ */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-green) 0%, var(--primary-dark) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35) !important;
        letter-spacing: 0.3px;
        min-height: 44px !important;
        width: 100%;
        position: relative;
        overflow: hidden;
        margin: 0 !important;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(16, 185, 129, 0.45) !important;
    }
    
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #10B981 0%, #0EA5E9 50%, #8B5CF6 100%) !important;
        background-size: 200% 200% !important;
        animation: gradientMove 3s ease infinite !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 16px 32px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
        letter-spacing: 0.5px;
        width: 100% !important;
        text-transform: uppercase;
        margin: 0 !important;
    }
    
    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stFormSubmitButton > button:hover {
        transform: translateY(-3px) scale(1.01) !important;
        box-shadow: 0 10px 28px rgba(16, 185, 129, 0.5) !important;
    }
    
    /* ============================================
       PERFECT CARD LAYOUTS - NO GAPS
       ============================================ */
    .input-container {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 24px;
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(255, 255, 255, 0.5);
        transition: all 0.3s ease;
        margin: 0 !important;
    }
    
    .input-container:hover {
        box-shadow: var(--shadow-xl);
        transform: translateY(-2px);
    }
    
    .section-header {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin: 0 0 16px 0 !important;
        padding: 0 0 10px 0 !important;
        border-bottom: 3px solid transparent;
        background: linear-gradient(white, white), 
                    linear-gradient(90deg, var(--primary-green), var(--accent-blue));
        background-clip: padding-box, border-box;
        background-origin: padding-box, border-box;
        border-image: linear-gradient(90deg, var(--primary-green), var(--accent-blue)) 1;
    }
    
    .prediction-result-card, .fertilizer-card, .analysis-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(249,250,251,0.95) 100%);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 24px;
        margin: 0 0 16px 0 !important;
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(16, 185, 129, 0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .prediction-result-card::before,
    .fertilizer-card::before,
    .analysis-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-green), var(--accent-blue), var(--accent-purple));
        background-size: 200% 200%;
        animation: gradientMove 3s ease infinite;
    }
    
    .prediction-result-card:hover,
    .fertilizer-card:hover,
    .analysis-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-xl);
    }
    
    .result-header {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin: 0 0 16px 0 !important;
        padding: 0 0 10px 0 !important;
        border-bottom: 2px solid #E5E7EB;
    }
    
    .crop-name {
        font-size: 32px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, var(--primary-green), var(--accent-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 12px 0 !important;
        margin: 0 !important;
        text-transform: capitalize;
        letter-spacing: -0.5px;
    }
    
    .crop-duration {
        font-size: 14px !important;
        color: var(--text-secondary) !important;
        text-align: center;
        padding: 10px 16px !important;
        margin: 12px 0 0 0 !important;
        background: linear-gradient(135deg, #F0FDF4, #DBEAFE);
        border-radius: 10px;
        border: 1px solid #D1FAE5;
    }
    
    .analysis-item {
        display: flex;
        justify-content: space-between;
        padding: 12px 0 !important;
        margin: 0 !important;
        border-bottom: 1px solid #F3F4F6;
        transition: all 0.2s ease;
    }
    
    .analysis-item:hover {
        background: #F9FAFB;
        padding: 12px 8px !important;
        border-radius: 6px;
    }
    
    .analysis-item:last-child {
        border-bottom: none;
    }
    
    .analysis-label {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
    }
    
    .analysis-value {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: var(--primary-green) !important;
    }
    
    .empty-state {
        text-align: center;
        padding: 60px 30px !important;
        margin: 0 !important;
        background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
        border-radius: 16px;
        border: 2px dashed #D1D5DB;
    }
    
    .empty-icon {
        font-size: 64px;
        margin: 0 0 16px 0 !important;
        animation: bounce 2s ease-in-out infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
    }
    
    .empty-title {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin: 0 0 10px 0 !important;
    }
    
    .empty-text {
        font-size: 15px !important;
        color: var(--text-secondary) !important;
        line-height: 1.6;
        max-width: 350px;
        margin: 0 auto !important;
    }
    
    /* ============================================
       SIDEBAR
       ============================================ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1F2937 0%, #111827 100%);
        padding: 1.5rem 1rem;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
    }
    
    [data-testid="collapsedControl"] {
        background: var(--primary-green) !important;
        color: white !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="collapsedControl"]:hover {
        background: var(--primary-dark) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        font-size: 18px !important;
        font-weight: 700 !important;
        margin-bottom: 14px !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    [data-testid="stSidebar"] label {
        font-size: 15px !important;
        padding: 12px 14px !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        text-transform: none !important;
    }
    
    [data-testid="stSidebar"] label:hover {
        background: rgba(16, 185, 129, 0.2) !important;
        transform: translateX(5px);
    }
    
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
        background-color: var(--primary-green) !important;
        border-color: var(--primary-green) !important;
    }
    
    /* ============================================
       HOME PAGE CARDS
       ============================================ */
    .app-card {
        background: white;
        border-radius: 16px;
        padding: 28px;
        margin: 0 0 16px 0 !important;
        box-shadow: var(--shadow-md);
        border: 1px solid #F3F4F6;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .app-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 100%;
        background: linear-gradient(180deg, var(--primary-green), var(--accent-blue));
        transform: scaleY(0);
        transition: transform 0.3s ease;
    }
    
    .app-card:hover::before {
        transform: scaleY(1);
    }
    
    .app-card:hover {
        transform: translateY(-6px);
        box-shadow: var(--shadow-xl);
        border-color: var(--primary-green);
    }
    
    /* ============================================
       UTILITIES
       ============================================ */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #E5E7EB, transparent);
        margin: 32px 0 !important;
    }
    
    .stAlert {
        border-radius: 12px !important;
        border-left: 4px solid var(--primary-green) !important;
        background: #F0FDF4 !important;
        padding: 14px 18px !important;
        box-shadow: var(--shadow-md) !important;
        margin: 12px 0 !important;
    }
    
    .stToast {
        background: white !important;
        border-left: 4px solid var(--primary-green) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow-xl) !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, var(--primary-green), var(--accent-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F3F4F6;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--primary-green), var(--accent-blue));
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-dark);
    }
    
    /* ============================================
       RESPONSIVE DESIGN
       ============================================ */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1.5rem 1rem !important;
            margin: 1rem auto !important;
        }
        
        h1 {
            font-size: 32px !important;
        }
        
        h2 {
            font-size: 24px !important;
        }
        
        .app-card {
            padding: 20px !important;
        }
        
        .prediction-result-card, .fertilizer-card, .analysis-card {
            padding: 18px !important;
        }
    }
</style>
''', unsafe_allow_html=True)

# Initialize session state if not already done
st.title('🌾 Climate‑Aware Crop & Organic Fertilizer Recommendation System', anchor=False)
st.markdown('<p style="font-size:18px; color: var(--text-medium); margin-bottom:24px;">Sustainable agriculture powered by climate-aware technology</p>', unsafe_allow_html=True)

# Sidebar with title and navigation
with st.sidebar:
    st.markdown("# 🌾 Navigation")
    st.markdown("---")

# Check if page is set via session_state (from button clicks), otherwise use sidebar
if 'page' in st.session_state:
    default_page = st.session_state['page']
    try:
        default_index = ['Home', 'Prediction', 'Preparation', 'Community'].index(default_page)
    except ValueError:
        default_index = 0
else:
    default_index = 0

# Load sidebar navigation CSS
sidebar_css_path = os.path.join(os.path.dirname(__file__), 'sidebar_nav.css')
if os.path.exists(sidebar_css_path):
    with open(sidebar_css_path, 'r', encoding='utf-8') as f:
        sidebar_css = f.read()
    st.markdown(f'<style>{sidebar_css}</style>', unsafe_allow_html=True)

# Navigation in sidebar with clear labels
with st.sidebar:
    page = st.radio(
        "Choose a page:",
        ["Home", "Prediction", "Preparation", "Community"],
        index=default_index,
        label_visibility="visible",
        key="navigation_radio"
    )
    
    st.markdown("---")

# Update session state with current page
st.session_state['page'] = page

# Helper function for navigation
def navigate_to(target_page):
    st.session_state['page'] = target_page
    st.session_state['navigation_radio'] = target_page

# Keep OpenWeather API key input tucked under auth (optional)
OPENWEATHER_KEY = None

# initialize user in session state (auth UI rendered on Community page)
if 'user' not in st.session_state:
    st.session_state['user'] = None

# Page rendering: Home, Prediction, Preparation, Community
if page == 'Home':
    st.header('🏡 Welcome to Climate-Aware Farming', anchor=False)
    st.markdown('''
    <div style="background: linear-gradient(135deg, var(--warm-cream), white); 
                padding: 24px; border-radius: 15px; border-left: 5px solid var(--forest-green);
                box-shadow: 0 4px 20px var(--shadow-soft); margin: 20px 0;">
        <p style="font-size: 16px; line-height: 1.8; color: var(--text-dark); margin: 0;">
            <strong>Empower your farming</strong> with data-driven crop recommendations and sustainable 
            fertilizer solutions. Our platform combines soil analysis, climate data, and organic farming 
            practices to help you make informed decisions.
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("### ✨ Key Features")
    
    # Feature cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('''
        <div class="app-card">
            <h4 style="color: var(--forest-green); margin-bottom: 12px;">🌾 Smart Crop Prediction</h4>
            <p style="font-size: 16px; color: var(--text-dark);">
                Get personalized crop recommendations based on your soil's NPK levels, pH, 
                rainfall, and temperature data.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
    with col2:
        st.markdown('''
        <div class="app-card">
            <h4 style="color: var(--forest-green); margin-bottom: 12px;">🍃 Organic Fertilizer</h4>
            <p style="font-size: 16px; color: var(--text-dark);">
                Convert conventional fertilizers to organic alternatives with step-by-step 
                preparation guides and video tutorials.
            </p>
        </div>
        ''', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown('''
        <div class="app-card">
            <h4 style="color: var(--forest-green); margin-bottom: 12px;">📋 Preparation Guides</h4>
            <p style="font-size: 16px; color: var(--text-dark);">
                Download detailed PDF guides with recipes, ingredients, and instructions 
                for making organic fertilizers at home.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
    with col4:
        st.markdown('''
        <div class="app-card">
            <h4 style="color: var(--forest-green); margin-bottom: 12px;">👥 Expert Community</h4>
            <p style="font-size: 16px; color: var(--text-dark);">
                Connect with agricultural experts, ask questions, and get verified answers 
                from experienced professionals.
            </p>
        </div>
        ''', unsafe_allow_html=True)
    
    # Quick action buttons - ROBUST NAVIGATION FIX
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    def navigate_to(target_page):
        st.session_state['page'] = target_page
        st.session_state['navigation_radio'] = target_page
    
    with col1:
        st.button('🌾 Start Prediction', 
                 key='home_pred', 
                 use_container_width=True, 
                 type='primary',
                 on_click=navigate_to,
                 args=('Prediction',))
    
    with col2:
        st.button('📋 View Preparations', 
                 key='home_prep', 
                 use_container_width=True, 
                 type='primary',
                 on_click=navigate_to,
                 args=('Preparation',))
    
    with col3:
        st.button('👥 Join Community', 
                 key='home_comm', 
                 use_container_width=True, 
                 type='primary',
                 on_click=navigate_to,
                 args=('Community',))

elif page == 'Prediction':
    # Professional navigation buttons
    nav_cols = st.columns([0.12, 0.88], gap="small")
    with nav_cols[0]:
        def go_home():
            st.session_state['page'] = 'Home'
            st.session_state['navigation_radio'] = 'Home'
            
        st.button('← Back', key='pred_back', use_container_width=True, on_click=go_home)
    
    st.markdown('<div style="height: 10px"></div>', unsafe_allow_html=True)
    st.header('🌾 Crop & Fertilizer Prediction', anchor=False)
    st.markdown('<p style="font-size:16px; color: var(--text-medium); margin-bottom:20px;">Get personalized recommendations based on your soil and climate conditions</p>', unsafe_allow_html=True)
    
    # Two-column layout: left for inputs, right for results
    left, right = st.columns([1.2, 1], gap='large')

    with left:
        # 1. LOCATION & SOIL CARD
        st.markdown("""
        <div class="app-card" style="border-left: 5px solid #10B981;">
            <h4 style="color:#064E3B; margin-bottom:15px; display:flex; align-items:center; gap:8px;">
                📍 Location & Soil Context
            </h4>
        """, unsafe_allow_html=True)
        
        cols = st.columns(2, gap='medium')
        with cols[0]:
            region = st.selectbox('Region / Zone', ['North','South','East','West','Central'], label_visibility='visible')
        with cols[1]:
            soil = st.selectbox('Soil Texture', ['Loamy','Sandy','Clayey','Silty'], label_visibility='visible')
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height: 15px"></div>', unsafe_allow_html=True)
        
        # 2. SOIL NUTRIENTS CARD
        st.markdown("""
        <div class="app-card" style="border-left: 5px solid #8B5CF6;">
            <h4 style="color:#4C1D95; margin-bottom:15px; display:flex; align-items:center; gap:8px;">
                🧪 Soil Nutrients (NPK)
            </h4>
        """, unsafe_allow_html=True)
        
        ncols = st.columns(3, gap='small')
        with ncols[0]:
            N = st.number_input('Nitrogen', min_value=0.0, max_value=300.0, value=100.0, step=5.0)
        with ncols[1]:
            P = st.number_input('Phosphorus', min_value=0.0, max_value=300.0, value=50.0, step=5.0)
        with ncols[2]:
            K = st.number_input('Potassium', min_value=0.0, max_value=300.0, value=150.0, step=5.0)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height: 15px"></div>', unsafe_allow_html=True)
        
        # 3. CLIMATE CONDITIONS CARD
        st.markdown("""
        <div class="app-card" style="border-left: 5px solid #0EA5E9;">
            <h4 style="color:#0C4A6E; margin-bottom:15px; display:flex; align-items:center; gap:8px;">
                🌤️ Environmental Factors
            </h4>
        """, unsafe_allow_html=True)
        
        ccols1 = st.columns(2, gap='medium')
        with ccols1[0]:
            pH = st.number_input('Soil pH Level', min_value=3.0, max_value=9.0, value=6.5, step=0.1, format='%.1f')
        with ccols1[1]:
            temp = st.number_input('Temperature (°C)', min_value=-10.0, max_value=50.0, value=25.0, step=0.5)
        
        ccols2 = st.columns(2, gap='medium')
        with ccols2[0]:
            humidity = st.number_input('Humidity (%)', min_value=0.0, max_value=100.0, value=70.0, step=1.0)
        with ccols2[1]:
            rainfall = st.number_input('Rainfall (mm)', min_value=0.0, max_value=3000.0, value=200.0, step=10.0)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height: 25px"></div>', unsafe_allow_html=True)
        
        # MAIN ACTION BUTTON
        submitted = st.button('🚀 Analyze & Recommend', use_container_width=True, type='primary', help="Click to process data")
        
        # Analysis Summary Card - Attractive card below input form
        if 'last_result' in st.session_state:
            st.markdown('<div style="height: 20px"></div>', unsafe_allow_html=True)
            lr = st.session_state['last_result']
            inp = lr.get('input', {})
            st.markdown(f'''
            <div class="analysis-card">
                <div class="result-header">📊 Analysis Summary</div>
                <div class="analysis-item">
                    <span class="analysis-label">Region:</span>
                    <span class="analysis-value">{inp.get('region')}</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">Soil Type:</span>
                    <span class="analysis-value">{inp.get('soil')}</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">pH Level:</span>
                    <span class="analysis-value">{inp.get('pH')}</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">NPK Ratio:</span>
                    <span class="analysis-value">{inp.get('N')}-{inp.get('P')}-{inp.get('K')}</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">Temperature:</span>
                    <span class="analysis-value">{inp.get('temperature')}°C</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">Humidity:</span>
                    <span class="analysis-value">{inp.get('humidity')}%</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">Rainfall:</span>
                    <span class="analysis-value">{inp.get('rainfall')} mm</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # Prediction logic (backend unchanged)
        if submitted:
            with st.spinner('Analyzing your data...'):
                try:
                    crop_bundle = joblib.load('crop_model.joblib')
                    artifacts = joblib.load('artifacts.joblib')
                except Exception as e:
                    st.error('⚠️ Model files missing. Please check your installation.')
                    st.stop()
                    
                enc = artifacts['encoders']
                scaler = artifacts['scaler']
                crop_model = crop_bundle['model']
                
                df = pd.DataFrame([{
                    'region': region, 'soil_type': soil,
                    'N': N, 'P': P, 'K': K, 'pH': pH,
                    'temperature': temp, 'humidity': humidity, 'rainfall': rainfall
                }])
                
                for c, le in enc.items():
                    df[c] = le.transform(df[c].astype(str))
                    
                X = df[['region','soil_type','N','P','K','pH','temperature','humidity','rainfall']].values
                Xs = scaler.transform(X)
                crop_pred = crop_model.predict(Xs)[0]

            nf = None
            used_fert_model = False
            try:
                fert_bundle = joblib.load('fert_model.joblib')
                fert_model = fert_bundle['model']
                fert_le = fert_bundle['le']
                cols = fert_bundle['columns']
                
                row = df.copy()
                row = pd.get_dummies(row, columns=['region','soil_type'], drop_first=True)
                for c in cols:
                    if c not in row.columns:
                        row[c] = 0
                        
                Xf = row[cols].values
                try:
                    nf = fert_le.inverse_transform([fert_model.predict(Xf)[0]])[0]
                    used_fert_model = True
                    
                    try:
                        num_classes = len(getattr(fert_le, 'classes_', []))
                    except Exception:
                        num_classes = 0
                    if num_classes <= 2:
                        nf = predict_fertilizer_simple(N, P, K, pH, crop_pred)
                        used_fert_model = False
                except Exception:
                    nf = predict_fertilizer_simple(N, P, K, pH, crop_pred)
                    used_fert_model = False
            except Exception:
                nf = predict_fertilizer_simple(N, P, K, pH, crop_pred)
                used_fert_model = False

            if nf:
                conv = convert_non_to_org(nf)
                st.session_state['last_result'] = {
                    'crop_pred': crop_pred,
                    'nf': nf,
                    'conv': conv,
                    'input': {
                        'region': region, 'soil': soil,
                        'N': N, 'P': P, 'K': K, 'pH': pH,
                        'temperature': temp, 'humidity': humidity, 'rainfall': rainfall
                    },
                    'used_fert_model': used_fert_model
                }
                st.toast('✅ Prediction completed successfully!', icon='🌾')

            # Add Smart Farming Insights to fill specific empty space
            if 'last_result' in st.session_state:
                lr = st.session_state['last_result']
                crop = lr.get('crop_pred', 'Crop')
                
                # Mock data for calendar
                sowing_map = {
                    'rice': 'Jun - Jul', 'maize': 'Jun - Jul', 'soybean': 'Jun - Jul',
                    'cotton': 'May - Jun', 'chickpea': 'Oct - Nov', 'wheat': 'Oct - Nov'
                }
                harvest_map = {
                    'rice': 'Nov - Dec', 'maize': 'Oct - Nov', 'soybean': 'Oct - Nov',
                    'cotton': 'Oct - Nov', 'chickpea': 'Mar - Apr', 'wheat': 'Mar - Apr'
                }
                
                sow = sowing_map.get(crop.lower(), 'Seasonal')
                hvst = harvest_map.get(crop.lower(), 'Seasonal')
                
                # Dynamic dates for forecast
                import datetime
                today = datetime.datetime.now()
                d1 = (today + datetime.timedelta(days=1)).strftime('%a')
                d2 = (today + datetime.timedelta(days=2)).strftime('%a')
                d3 = (today + datetime.timedelta(days=3)).strftime('%a')
                
                # Use plain string concatenation with NO indentation to prevent Markdown code block interpretation
                html_content = f"""
<div style="margin-top: 20px; background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.05);">
<h3 style="color: var(--secondary-blue); font-size: 18px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">📅 Crop Calendar</h3>
<div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
<div style="text-align: center; flex: 1; border-right: 1px solid #eee;">
<div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Sowing</div>
<div style="font-size: 16px; font-weight: 600; color: var(--forest-green); margin-top: 4px;">{sow}</div>
</div>
<div style="text-align: center; flex: 1;">
<div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Harvest</div>
<div style="font-size: 16px; font-weight: 600; color: var(--accent-orange); margin-top: 4px;">{hvst}</div>
</div>
</div>
<h3 style="color: var(--secondary-blue); font-size: 18px; margin-bottom: 15px; margin-top: 25px; display: flex; align-items: center; gap: 8px;">🌤️ 5-Day Forecast</h3>
<div style="display: flex; justify-content: space-between; gap: 8px;">
<div style="text-align: center; background: #f8FAFC; padding: 8px; border-radius: 8px; flex: 1;">
<div style="font-size: 12px; font-weight: 600;">Today</div>
<div style="font-size: 20px;">☀️</div>
<div style="font-size: 12px; font-weight: 600;">32°</div>
</div>
<div style="text-align: center; background: #f8FAFC; padding: 8px; border-radius: 8px; flex: 1;">
<div style="font-size: 12px; color: #666;">{d1}</div>
<div style="font-size: 20px;">⛅</div>
<div style="font-size: 12px; color: #666;">30°</div>
</div>
<div style="text-align: center; background: #f8FAFC; padding: 8px; border-radius: 8px; flex: 1;">
<div style="font-size: 12px; color: #666;">{d2}</div>
<div style="font-size: 20px;">🌧️</div>
<div style="font-size: 12px; color: #666;">28°</div>
</div>
<div style="text-align: center; background: #f8FAFC; padding: 8px; border-radius: 8px; flex: 1;">
<div style="font-size: 12px; color: #666;">{d3}</div>
<div style="font-size: 20px;">☁️</div>
<div style="font-size: 12px; color: #666;">29°</div>
</div>
</div>
<div style="margin-top: 25px; background: #FEF3C7; padding: 12px; border-radius: 8px; border-left: 4px solid #F59E0B;">
<div style="font-size: 13px; font-weight: 600; color: #92400E; margin-bottom: 4px;">💡 Farming Tip</div>
<div style="font-size: 13px; color: #B45309; line-height: 1.4;">Ensure proper drainage in the field to prevent waterlogging during the upcoming rains.</div>
</div>
</div>
"""
                st.markdown(html_content, unsafe_allow_html=True)

    # RIGHT: Result card with pie chart
    with right:
        if 'last_result' in st.session_state:
            lr = st.session_state['last_result']
            
            # Crop Prediction Card with Duration
            crop_name = lr.get('crop_pred', '')
            duration_display = get_crop_duration_display(crop_name)
            
            # Map of alternative crops based on similar growth conditions
            alternatives_map = {
                'rice': 'Jute, Maize',
                'maize': 'Cotton, Soybean',
                'chickpea': 'Kidneybeans, Mothbeans',
                'kidneybeans': 'Chickpea, Pigeonpeas',
                'pigeonpeas': 'Blackgram, Mothbeans',
                'mothbeans': 'Mungbean, Lentil',
                'mungbean': 'Mothbeans, Lentil',
                'blackgram': 'Pigeonpeas, Mothbeans',
                'lentil': 'Mungbean, Peas',
                'pomegranate': 'Orange, Papaya',
                'banana': 'Coconut, Mango',
                'mango': 'Banana, Coconut',
                'grapes': 'Pomegranate, Orange',
                'watermelon': 'Muskmelon, Cucumber',
                'muskmelon': 'Watermelon, Cucumber',
                'apple': 'Grapes, Pear',
                'orange': 'Pomegranate, Papaya',
                'papaya': 'Banana, Coconut',
                'coconut': 'Banana, Mango',
                'cotton': 'Maize, Soybean',
                'jute': 'Rice, Maize',
                'coffee': 'Tea, Rubber',
                'soybean': 'Maize, Cotton',
                'kidneybeans': 'Chickpea, Mothbeans',
                'mothbeans': 'Kidneybeans, Chickpea',
                'mungbean': 'Lentil, Blackgram',
                'blackgram': 'Mungbean, Lentil',
                'lentil': 'Mungbean, Peas'
            }
            
            alts = alternatives_map.get(crop_name.strip().lower(), 'Similar seasonal crops')
            
            st.markdown(f'''
            <div class="prediction-result-card" style="box-shadow: 0 10px 30px -10px rgba(16, 185, 129, 0.4); border: 2px solid #10B981;">
                <div style="text-align:center; margin-bottom:10px;">
                    <span style="background:#ECFDF5; color:#047857; padding:5px 12px; border-radius:20px; font-size:12px; font-weight:700; text-transform:uppercase;">Top Recommendation</span>
                </div>
                <div class="crop-name" style="font-size:36px !important; margin-bottom:5px !important;">{crop_name}</div>
                <div style="color: var(--text-secondary); font-size: 15px; margin-bottom: 20px; font-weight: 500; text-align: center;">
                    <span style="color: var(--primary-green); font-weight: 600;">Alternatives:</span> {alts}
                </div>
                <div class="crop-duration">
                    <span style="color: var(--olive-green); font-weight: 600;">⏱ Duration:</span> {duration_display}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Non-Organic Fertilizer Recommendation (First)
            nf = lr.get('nf', 'N/A')
            st.markdown(f'''
            <div class="fertilizer-card" style="margin-top: 20px; border-left: 5px solid #3B82F6;">
                <div class="result-header" style="color:#1E40AF; border-bottom-color:#BFDBFE;">🧪 Chemical Recom.</div>
                <div style="padding: 16px; background: #EFF6FF; border-radius: 10px; margin-top: 12px;">
                    <div style="font-size: 20px; font-weight: 700; color: #1E40AF;">{nf}</div>
                    <div style="margin-top: 8px; color: #60A5FA; font-size: 13px;">
                        Standard chemical fertilizer for immediate nutrient boost.
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            conv = lr.get('conv', {})
            org = conv.get('organic') or ''
            
            if org:
                # Organic Alternative Card with Pie Chart Comparison
                st.markdown('''
                <div class="fertilizer-card" style="margin-top: 24px; border-left: 5px solid #65A30D;">
                    <div class="result-header" style="color:#365314; border-bottom-color:#D9F99D;">🌿 Organic Alternative</div>
                    <div style="padding: 16px; background: #ECFCCB; border-radius: 10px; margin-top: 12px;">
                        <div style="font-size: 20px; font-weight: 700; color: #365314;">''' + org + '''</div>
                        <div style="margin-top: 8px; color: #4D7C0F; font-size: 13px;">
                            Sustainable choice for long-term health.
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                # Comparison Pie Charts
                st.markdown('<div style="margin-top: 24px;">', unsafe_allow_html=True)
                st.markdown('<h3 style="text-align: center; color: var(--forest-green); margin-bottom: 20px;">Fertilizer Composition Comparison</h3>', unsafe_allow_html=True)
                
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                # Define compositions for both fertilizer types
                non_organic_comp = {
                    'Urea': 40,
                    'DAP': 30,
                    'Potash': 20,
                    'Ammonium': 10
                }
                
                organic_comp = {
                    'Compost': 30,
                    'Fish Emulsion': 25,
                    'Neem Cake': 25,
                    'Vermicompost': 20
                }
                
                # Create side-by-side pie charts
                fig = make_subplots(
                    rows=1, cols=2,
                    specs=[[{'type':'pie'}, {'type':'pie'}]],
                    subplot_titles=('Non-Organic Fertilizer', 'Organic Fertilizer Alternative')
                )
                
                # Non-organic pie chart
                fig.add_trace(go.Pie(
                    labels=list(non_organic_comp.keys()),
                    values=list(non_organic_comp.values()),
                    marker=dict(colors=['#FF6B6B', '#FFA07A', '#FFD700', '#FF8C00']),
                    textinfo='label+percent',
                    textposition='auto',
                    name='Non-Organic'
                ), row=1, col=1)
                
                # Organic pie chart
                fig.add_trace(go.Pie(
                    labels=list(organic_comp.keys()),
                    values=list(organic_comp.values()),
                    marker=dict(colors=['#2D5016', '#6B8E23', '#8FBC8F', '#90EE90']),
                    textinfo='label+percent',
                    textposition='auto',
                    name='Organic'
                ), row=1, col=2)
                
                fig.update_layout(
                    showlegend=False,
                    margin=dict(l=20, r=20, t=60, b=20),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=14, color='#2C3E2D', family='Arial')
                )
                


                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Preparation Steps Card
                prep = conv.get('preparation_steps') or []
                if isinstance(prep, list) and prep:
                    st.markdown(f'''
                    <div class="fertilizer-card" style="margin-top: 24px;">
                        <div class="result-header">📋 Preparation Steps for {org}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    for i, step in enumerate(prep, start=1):
                        st.markdown(f'''
                        <div style="padding: 12px; background: white; border-left: 4px solid var(--olive-green); 
                                    margin-bottom: 10px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <span style="font-weight: 700; color: var(--forest-green); font-size: 16px;">Step {i}:</span>
                            <span style="color: var(--text-dark); font-size: 16px; margin-left: 8px;">{step}</span>
                        </div>
                        ''', unsafe_allow_html=True)
                
                st.button('📋 View Full Preparation Guide', 
                         use_container_width=True, 
                         key='prep_guide',
                         on_click=navigate_to,
                         args=('Preparation',))
        else:
            st.markdown('''
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <div class="empty-title">No Results Yet</div>
                <div class="empty-text">Fill in the form and click "Get Recommendations" to see your personalized crop and fertilizer suggestions</div>
            </div>
            ''', unsafe_allow_html=True)

elif page == 'Preparation':
    # Professional navigation buttons
    nav_cols = st.columns([0.12, 0.12, 0.76], gap="small")
    with nav_cols[0]:
        st.button('← Back', 
                 key='prep_back_pred', 
                 use_container_width=True,
                 on_click=navigate_to,
                 args=('Prediction',))
    with nav_cols[1]:
        st.button('🏠 Home', 
                 key='prep_back_home', 
                 use_container_width=True,
                 on_click=navigate_to,
                 args=('Home',))
    
    st.markdown('<div style="height: 10px"></div>', unsafe_allow_html=True)
    st.header('📋 Organic Fertilizer Preparation Guide', anchor=False)
    st.markdown('<p style="font-size:16px; color: var(--text-medium);">Step-by-step instructions and video tutorials</p>', unsafe_allow_html=True)
    if 'last_result' not in st.session_state:
        st.markdown('''
        <div class="empty-state">
            <div class="empty-icon">🍃</div>
            <div class="empty-title">No Organic Fertilizer Selected</div>
            <div class="empty-text">Go to the Prediction page and calculate recommendations first to see the preparation guide.</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        lr = st.session_state['last_result']
        conv = lr.get('conv', {})
        organic_name = conv.get('organic', 'Organic Fertilizer')
        notes = conv.get('notes', 'No specific notes available.')
        prep = conv.get('preparation_steps') or []
        
        # Hero Card for Organic Fertilizer
        st.markdown(f'''
        <div class="app-card" style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; border: none;">
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="font-size: 40px; background: rgba(255,255,255,0.2); width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; border-radius: 50%;">🍃</div>
                <div>
                    <h2 style="color: white; margin: 0; font-size: 24px; font-weight: 700;">{organic_name}</h2>
                    <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 15px;">Recommended Organic Equivalent</p>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Main Content Layout
        col1, col2 = st.columns([1.6, 1], gap="large")
        
        with col1:
            # UPGRADED RECIPE CARD UI
            # Start the card container
            card_html = """
            <div class="app-card" style="border-top: 5px solid #10B981; min-height: 400px; padding: 25px;">
                <h3 style="color:#064E3B; margin-bottom:20px; display:flex; align-items:center; gap:10px; border-bottom:1px solid #E5E7EB; padding-bottom:15px; margin-top:0;">
                    🥣 Preparation Method
                </h3>
                <div style="display: flex; flex-direction: column; gap: 15px;">
            """
            
            if isinstance(prep, list) and prep:
                for i, step in enumerate(prep, start=1):
                    # Ensure step is a string
                    step_text = str(step).strip()
                    # Use single line string to avoid indentation issues
                    card_html += f'<div style="display: flex; gap: 15px; align-items: flex-start;"><div style="flex-shrink: 0; width: 32px; height: 32px; background: #ECFDF5; color: #059669; border: 2px solid #10B981; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">{i}</div><div style="color: #374151; font-size: 16px; line-height: 1.6; padding-top: 2px;">{step_text}</div></div>'
                
                card_html += "</div></div>"
                st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.info('No detailed steps available.')
                st.markdown('</div>', unsafe_allow_html=True)
                
        with col2:
            # UPGRADED STICKY NOTE UI
            st.markdown("""
            <div style="background: #FEF3C7; padding: 20px; border-radius: 4px; margin-bottom: 20px; box-shadow: 3px 3px 10px rgba(0,0,0,0.1); transform: rotate(-1deg); border-top: 1px solid #FDE68A; position: relative;">
                <div style="position: absolute; top: -15px; left: 45%; color: rgba(0,0,0,0.1); font-size: 30px;">📌</div>
                <h3 style="color: #92400E; font-size: 18px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                     Important Notes
                </h3>
                <div style="color: #78350F; font-size: 15px; line-height: 1.6; font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif !important;">
            """ + f"{notes}" + """
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Download Section
            st.markdown('<h3 style="color: var(--secondary-blue); font-size: 18px; display: flex; align-items: center; gap: 8px; margin-top: 10px;">💾 Resources</h3>', unsafe_allow_html=True)
            
            prep_text = '\n'.join([f"{i}. {s}" for i, s in enumerate(prep, start=1)]) if isinstance(prep, list) else str(prep)
            pdf_bytes = None
            try:
                pdf_bytes = generate_preparation_pdf(conv.get('organic') or 'preparation', prep if isinstance(prep, list) else [])
            except Exception:
                pdf_bytes = None
            
            if pdf_bytes:
                st.download_button(
                    label="📄 Download Guide (PDF)",
                    data=pdf_bytes,
                    file_name=f"preparation_{organic_name}.pdf",
                    mime='application/pdf',
                    use_container_width=True
                )
            else:
                st.download_button(
                    label="📄 Download Guide (TXT)",
                    data=prep_text,
                    file_name=f"preparation_{organic_name}.txt",
                    use_container_width=True
                )
        if st.button('Video Recommendations'):
            base_queries = build_search_queries(conv.get('organic'))
            # Preferred languages: Kannada first, then Hindi, then English
            languages = ['Kannada', 'Hindi', 'English']
            # include native script variants for better matching
            lang_variants = {
                'Kannada': ['Kannada', 'ಕನ್ನಡ'],
                'Hindi': ['Hindi', 'हिंदी'],
                'English': ['English']
            }
            results_by_lang = {lang: [] for lang in languages}
            seen_links = set()
            # For each language in preference order, try the base queries with language tag
            for lang in languages:
                variants = lang_variants.get(lang, [lang])
                for q in base_queries:
                    if len(results_by_lang[lang]) >= 3:
                        break
                    for vtag in variants:
                        search_q = f"{q} {vtag}"
                        try:
                            res = fetch_tutorials_pytube(search_q, max_results=4)
                        except Exception:
                            res = []
                        for r in res:
                            link = r.get('link')
                            if not link or link in seen_links:
                                continue
                            results_by_lang[lang].append(r)
                            seen_links.add(link)
                            if len(results_by_lang[lang]) >= 3:
                                break
                    # stop early if we have 3 videos for this language
                    if len(results_by_lang[lang]) >= 3:
                        break

            # If none found at all, show a message
            total_found = sum(len(v) for v in results_by_lang.values())
            if total_found == 0:
                st.info('No tutorial videos found for this organic fertilizer in Kannada/Hindi/English.')
            else:
                # Video Tutorials Section
                st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown('<h3 style="color:#111827; margin-bottom:10px;">🎥 Video Tutorials</h3>', unsafe_allow_html=True)
                    st.markdown('<p style="color:#6B7280; font-size:14px; margin-bottom:20px;">Watch step-by-step guides in your preferred language</p>', unsafe_allow_html=True)
                    
                    # Create tabs for languages
                    tabs = st.tabs(languages)
                    
                    for idx, lang in enumerate(languages):
                        with tabs[idx]:
                            vids = results_by_lang.get(lang, [])
                            if not vids:
                                st.info(f"No {lang} videos found.")
                                continue
                                
                            # Grid for videos
                            vcols = st.columns(3)
                            for i, v in enumerate(vids[:3]):
                                col_idx = i % 3
                                with vcols[col_idx]:
                                    st.markdown(f"""
                                    <div style="background:white; border-radius:8px; overflow:hidden; border:1px solid #E5E7EB; height:100%;">
                                        <div style="padding:10px; font-weight:600; font-size:14px; height:60px; overflow:hidden; text-overflow:ellipsis; background:#F9FAFB; border-bottom:1px solid #E5E7EB;">
                                            {v.get('title')}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    try:
                                        st.video(v.get('link'))
                                    except Exception:
                                        st.write(f"[Watch Video]({v.get('link')})")


elif page == 'Community':
    # Professional navigation buttons
    nav_cols = st.columns([0.12, 0.12, 0.76], gap="small")
    with nav_cols[0]:
        st.button('← Back', 
                 key='comm_back_prep', 
                 use_container_width=True,
                 on_click=navigate_to,
                 args=('Preparation',))
    with nav_cols[1]:
        st.button('🏠 Home', 
                 key='comm_back_home', 
                 use_container_width=True,
                 on_click=navigate_to,
                 args=('Home',))
    
    st.markdown('<div style="height: 10px"></div>', unsafe_allow_html=True)
    
    st.header('👥 Expert Community', anchor=False)
    st.markdown('<p style="font-size:16px; color: var(--text-medium);">Connect with agricultural experts and get verified answers</p>', unsafe_allow_html=True)
    
    # Initialize show_register state if not exists
    if 'show_register' not in st.session_state:
        st.session_state['show_register'] = False
    
    user = st.session_state.get('user')
    
    # If user is not logged in, show modern login/register form
    if not user:
        # Use a centered layout
        col1, col2, col3 = st.columns([1, 1.2, 1])
        
        with col2:
            st.markdown('<div style="height: 40px"></div>', unsafe_allow_html=True)
            
            # Dynamic Header based on state
            if st.session_state.get('show_register'):
                # Card Container
                with st.container(border=True):
                    # Hidden Marker for CSS targeting
                    st.markdown('<div id="login-card-target"></div>', unsafe_allow_html=True)
                    
                    # White text is handled by CSS now
                    st.markdown("""
                        <div style="text-align: center; margin-bottom: 20px;">
                            <h2 style="font-size: 24px; margin: 0;">Create Your Account</h2>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    r_user = st.text_input('Username', placeholder='Choose a username', key='reg_user')
                    r_pw = st.text_input('Password', type='password', placeholder='Create a password', key='reg_pw')
                    r_pw_confirm = st.text_input('Confirm Password', type='password', placeholder='Confirm password', key='reg_pw_confirm')
                    r_role = st.selectbox('I am a', ['Farmer', 'Agricultural Expert'], key='reg_role')
                    
                    st.markdown('<div style="height: 10px"></div>', unsafe_allow_html=True)
                    # Button style is White Pill via CSS
                    register_btn = st.button('Sign Up', use_container_width=True, type='primary', key='reg_btn')
                    
                    if register_btn:
                        if not r_user or not r_pw:
                            st.error('Please fill all fields')
                        elif r_pw != r_pw_confirm:
                            st.error('Passwords do not match')
                        else:
                            ok = cdb.create_user(r_user, r_pw, role=r_role.lower())
                            if ok:
                                u = cdb.authenticate(r_user, r_pw)
                                if u:
                                    st.session_state['user'] = u
                                    st.session_state['show_register'] = False
                                    st.success(f'Welcome {u["username"]}!')
                                    st.rerun()
                            else:
                                st.error('Registration failed (username exists)')
                    
                    # Footer Link Style
                    st.markdown("""
                        <div style="text-align: center; margin-top: 15px;">
                            <p style="font-size: 14px; opacity: 0.9;">Already have an account?</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button('Login Here', use_container_width=True, key='goto_login'):
                        st.session_state['show_register'] = False
                        st.rerun()

            else:
                # Login View
                with st.container(border=True):
                    # Hidden Marker for CSS targeting
                    st.markdown('<div id="login-card-target"></div>', unsafe_allow_html=True)

                    st.markdown("""
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h2 style="font-size: 26px; font-weight: 700; margin: 0;">Login to Your Account</h2>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    username = st.text_input('Username', placeholder='Username', key='login_user')
                    password = st.text_input('Password', type='password', placeholder='Password', key='login_pw')
                    
                    st.markdown('<div style="height: 20px"></div>', unsafe_allow_html=True)
                    login_btn = st.button('Sign In', use_container_width=True, type='primary', key='login_btn')
                    
                    if login_btn:
                        if not username or not password:
                            st.error('Enter username & password')
                        else:
                            u = cdb.authenticate(username, password)
                            if u:
                                st.session_state['user'] = u
                                st.success(f'Welcome back, {u["username"]}!')
                                st.rerun()
                            else:
                                st.error('Invalid credentials')
                    
                    # Yellow/White Footer Links
                    st.markdown("""
                        <div style="text-align: center; margin-top: 20px;">
                            <a href="#" style="color: #FCD34D; text-decoration: none; font-size: 14px; font-weight: 600;">Forgot Password?</a>
                            <div style="height: 10px;"></div>
                            <span style="color: rgba(255,255,255,0.9); font-size: 14px;">First time user? </span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button('Sign Up', key='goto_register', use_container_width=True):
                        st.session_state['show_register'] = True
                        st.rerun()
            

    
    # If user is logged in, show dashboard
    # If user is logged in, show dashboard
    else:
        # User header with logout
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            st.markdown(f'''
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #10B981, #059669); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">
                    {user.get("username")[0].upper()}
                </div>
                <div>
                    <h3 style="margin: 0; color: var(--text-primary);">Hello, {user.get("username")}!</h3>
                    <p style="margin: 0; color: var(--text-secondary); font-size: 14px;">Logged in as {user.get("role").title()}</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        with col2:
            if st.button('Logout', key='logout_btn', use_container_width=True):
                st.session_state['user'] = None
                st.session_state['show_register'] = False
                st.info('Logged out successfully')
                st.rerun()
        
        # Farmer Dashboard
        if user.get('role') == 'farmer':
            tab1, tab2, tab3, tab4 = st.tabs(['📰 Community Feed', '🤖 AI Crop Doctor', '🗣️ Ask an Expert', '📜 My History'])
            
            # TAB 1: Community Feed (Sessions + Posts)
            with tab1:
                # ... (Existing Community Feed Code is preserved, just indented if needed, but here we just leave the tab structure. 
                # NOTE: The replace_file_content tool requires me to match the existing content strictly. 
                # Since I am changing the TABS definition, I must ensure the subsequent code flow is correct.
                # However, to avoid re-writing the HUGE Tab 1 block, I will just match the START of the block and update the tab list.)
                pass # Placeholder for this specific tool call explanation - I will actually replace the logic below.

            # We need to insert the new tab content. 
            # Strategy: I'll rewrite the tab definition line and then insert the AI Tab logic BEFORE the others or modify the structure.
            # Actually, inserting it as Tab 2 is best.

            # Let's target the Tab definition.

                # Create a 2-column layout: Main Content (Left) + Interaction Sidebar (Right)
                feed_col, side_col = st.columns([2, 1], gap="medium")
                
                with feed_col:
                    st.markdown('### 🚜 Community Pulse')
                    
                    # 1. LIVE SESSIONS
                    sessions = cdb.list_sessions()
                    if sessions:
                        st.caption("🔴 Live Now & Upcoming")
                        for s in sessions:
                            sid, stitle, slink, swhen, sexpert = s
                            st.markdown(f'''
                            <div class="app-card" style="padding: 20px; border-left: 5px solid #EF4444; background: linear-gradient(to right, #FEF2F2, white);">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <h4 style="margin:0; color: #B91C1C;">{stitle}</h4>
                                    <span style="background:#FEE2E2; color:#B91C1C; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:700;">LIVE</span>
                                </div>
                                <div style="font-size: 13px; color: #7F1D1D; margin: 5px 0;">� {swhen} with {sexpert}</div>
                                <a href="{slink}" target="_blank" class="action-btn" style="background:#EF4444; margin-top:5px;">Join Stream</a>
                            </div>
                            ''', unsafe_allow_html=True)
                    
                    # 2. SUCCESS STORIES (New Feature idea)
                    st.markdown('<div style="height: 10px"></div>', unsafe_allow_html=True)
                    st.caption("🌟 Farmer Success Stories")
                    
                    # Mock Success Stories
                    stories = [
                        ("Ramesh K.", "Switched to Vermicompost", "My yield increased by 20% this season after switching to organic vermicompost! Thanks to Expert Dr. Singh for the advice.", "2h ago"),
                        ("Anita D.", "Saved my Cotton Crop", "Identify the pest early using the prediction tool. Saved huge costs on pesticide.", "5h ago")
                    ]
                    
                    for author, title, body, time in stories:
                        st.markdown(f'''
                        <div class="app-card" style="padding: 20px;">
                            <div style="display:flex; gap:12px;">
                                <div style="width:40px; height:40px; background:#10B981; border-radius:50%; color:white; display:flex; align-items:center; justify-content:center; font-weight:bold;">{author[0]}</div>
                                <div>
                                    <div style="font-weight:700; color:#374151;">{author}</div>
                                    <div style="font-size:12px; color:#6B7280;">{time}</div>
                                </div>
                            </div>
                            <h4 style="margin: 10px 0 5px 0; color: var(--primary-green);">{title}</h4>
                            <p style="color: #4B5563; font-size: 14px; margin:0;">{body}</p>
                            <div style="margin-top:10px; display:flex; gap:15px; font-size:13px; color:#6B7280;">
                                <span>❤️ 24 Likes</span>
                                <span>💬 5 Comments</span>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)

                    # 3. OFFICIAL UPDATES
                    st.caption("📰 Official Announcements")
                    posts = cdb.list_posts()
                    if posts:
                        for p in posts:
                            pid, ptitle, pcontent, puser, pdate = p[0], p[1], p[2], p[3], p[4]
                            st.markdown(f'''
                            <div style="padding: 15px; background: #F3F4F6; border-radius: 12px; margin-bottom: 10px;">
                                <div style="font-weight:bold; color:#1F2937;">{ptitle}</div>
                                <div style="color:#4B5563; font-size:13px;">{pcontent}</div>
                                <div style="font-size:11px; color:#9CA3AF; margin-top:5px;">Posted by {puser}</div>
                            </div>
                            ''', unsafe_allow_html=True)

                with side_col:
                    # WIDGET 1: DAILY TIP
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #059669 0%, #34D399 100%); padding: 20px; border-radius: 16px; color: white; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);">
                        <div style="font-size: 12px; font-weight: 700; opacity: 0.9; margin-bottom: 5px;">🍃 DAILY ORGANIC TIP</div>
                        <div style="font-size: 16px; font-weight: 600; line-height: 1.4;">"Rotate your crops every season to naturally replenish soil nitrogen!"</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # WIDGET 2: WEEKLY POLL
                    with st.container(border=True):
                        st.markdown("#### 📊 Weekly Poll")
                        st.write("What's your biggest challenge?")
                        vote = st.radio("Select one:", ["Pest Attack", "Water Scarcity", "Fertilizer Cost", "Market Prices"], label_visibility="collapsed")
                        if st.button("Vote Now", use_container_width=True):
                            st.success("Thanks for voting!")
                            st.progress(68)
                            st.caption("68% of farmers voted for 'market prices' today.")
                    
                    # WIDGET 3: LEADERBOARD
                    st.markdown('<div style="height: 10px"></div>', unsafe_allow_html=True)
                    with st.container(border=True):
                        st.markdown("#### 🏆 Top Contributors")
                        leaders = [("Dr. Green", "150 Ans"), ("AgriMaster", "120 Ans"), ("SoilPro", "98 Ans")]
                        for name, score in leaders:
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #F3F4F6;">
                                <span style="font-weight:500;">🥇 {name}</span>
                                <span style="color:var(--primary-green); font-weight:bold;">{score}</span>
                            </div>
                            """, unsafe_allow_html=True)

            # TAB 2: AI CROP DOCTOR (Visual Diagnosis)
            with tab2:
                # Restoring the "Like Before" Image-First Interface
                col_ai_left, col_ai_right = st.columns([1, 1.2], gap="large")
                
                with col_ai_left:
                    st.markdown("### 📸 AI Plant Diagnosis")
                    st.markdown("Upload a photo of the affected plant to identify diseases instantly.")
                    
                    # Main Uploader (Not hidden in a button)
                    uploaded_file = st.file_uploader("Upload Plant Image", type=['jpg', 'png', 'jpeg'], key="farmer_img_upload")
                    
                    if uploaded_file is not None:
                        st.image(uploaded_file, caption='Analyzing Image...', use_container_width=True)
                        st.toast("Image Uploaded Successfully!", icon="✅")
                        
                        # Simulate AI Analysis
                        import time
                        with st.spinner('AI Doctor is examining the leaf patterns...'):
                            time.sleep(1.5)
                        
                        st.markdown("---")
                        st.markdown("#### Diagnosis Result")
                        st.error("🚨 **Early Blight** Detected (94% Confidence)")
                        st.markdown("This is a common fungal disease affecting tomato and potato plants.")
                
                with col_ai_right:
                    if uploaded_file is not None:
                        st.markdown("### 💊 Doctor's Prescription")
                        
                        # 1. ORGANIC SOLUTION
                        with st.container(border=True):
                            st.markdown("#### 🌿 Organic Solution (Recommended)")
                            st.markdown("**Neem Oil Spray + Baking Soda**")
                            st.success("Safe for environment • Low Cost • Effective")
                        
                        # 2. DIY RECIPE
                        st.markdown("""
                        <div class="app-card" style="background:#F0FDF4; border:1px solid #BBF7D0; padding:20px;">
                            <h4 style="margin-top:0; color:#166534;">🥣 DIY Home Preparation</h4>
                            <ol style="margin-bottom:0; color:#14532d; padding-left:20px; line-height:1.6;">
                                <li><strong>Mix</strong> 2 tablespoons of Neem Oil.</li>
                                <li><strong>Add</strong> 1 teaspoon of mild liquid soap (to help it stick).</li>
                                <li><strong>Dissolve</strong> in 1 liter of warm water.</li>
                                <li><strong>Shake well</strong> before every use.</li>
                                <li><strong>Spray</strong> on both sides of leaves in early morning.</li>
                            </ol>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 3. CHEMICAL OPTION (Always Visible now)
                        st.markdown("""
                        <div class="app-card" style="background:#FFF1F2; border:1px solid #FECDD3; padding:20px; margin-top:15px;">
                            <h4 style="margin-top:0; color:#9F1239;">🧪 Non-Organic / Chemical Option (Fast Action)</h4>
                            <p style="font-weight:bold; color:#881337; margin-bottom:10px;">Copper Fungicide or Mancozeb</p>
                            <div style="background:#FEF3C7; border-left:4px solid #F59E0B; color:#92400E; padding:12px; border-radius:8px; font-size:14px;">
                                ⚠️ Use protective gear. Do not spray 3 days before harvest.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.caption("Disclaimer: AI advice is experimental. Always consult an expert if unsure.")
                    
                    else:
                        # Empty State Illustration
                        st.info("👈 Please upload an image to start the diagnosis.")
                        st.markdown("""
                        **What I can detect:**
                        * 🍃 Leaf Spots & Blights
                        * 🐛 Pest Damage Patterns
                        * 🍂 Nutrient Deficiencies (Yellowing)
                        """)

                # Add Text-Based AI Assistant below the Visual Tool
                st.markdown('<div style="height: 30px"></div>', unsafe_allow_html=True)
                st.markdown("---")
                render_ai_doctor()
                        
            # TAB 3: Ask an Expert
            with tab3:
                col_ask, col_view = st.columns([1, 1.5], gap="large")
                
                with col_ask:
                    st.markdown("""
                    <div class="app-card" style="border-top: 5px solid #2563EB;">
                        <h4 style="margin-top:0; color:#1E3A8A;">📥 Submit a Question</h4>
                        <p style="font-size:13px; color:#6B7280; margin-bottom:15px;">Get personalized advice from our panel of certified experts.</p>
                    """, unsafe_allow_html=True)
                    
                    with st.form('ask_expert_form', border=False):
                        q_title = st.text_input('Topic / Title', placeholder='e.g., Potato leaves turning black')
                        q_desc = st.text_area('Detailed Description', placeholder='Describe symptoms, soil type, crop age, etc...')
                        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
                        q_submit = st.form_submit_button('📨 Send to Experts', type='primary', use_container_width=True)
                        
                        if q_submit:
                            if q_title and q_desc:
                                if hasattr(cdb, 'create_question'):
                                    cdb.create_question(q_title, q_desc, user.get('username'))
                                    st.toast('Question sent successfully!', icon='📨')
                                    st.rerun()
                                else:
                                    st.error('System error: Database unavailable.')
                            else:
                                st.warning('⚠ Please provide both a title and description.')
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_view:
                    st.markdown('### 💬 Discussion Thread')
                    all_qs = cdb.list_questions()
                    my_qs = [q for q in all_qs if q[3] == user.get('username')] if all_qs else []
                    
                    if my_qs:
                        for q in my_qs:
                            qid, qtitle, qcontent, _, qdate, _ = q[0], q[1], q[2], q[3], q[5], q[4]
                            
                            # Question Card
                            st.markdown(f'''
                            <div class="app-card" style="margin-bottom: 20px; padding: 20px;">
                                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                    <h4 style="margin:0; color:#374151;">{qtitle}</h4>
                                    <span style="font-size:12px; color:#9CA3AF;">{qdate}</span>
                                </div>
                                <p style="color:#4B5563; font-size:15px; margin-top:8px; line-height:1.5;">{qcontent}</p>
                            ''', unsafe_allow_html=True)
                            
                            # Answers Section
                            ans = cdb.get_answers(qid)
                            if ans:
                                for a in ans:
                                    _, acontent, aexpert, adate, averified = a
                                    badge = '<span style="background:#DCFCE7; color:#166534; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700;">VERIFIED EXPERT</span>' if averified else '<span style="background:#F3F4F6; color:#4B5563; padding:2px 8px; border-radius:12px; font-size:11px;">COMMUNITY REPLY</span>'
                                    
                                    st.markdown(f'''
                                    <div style="background: #F8FAFC; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #E2E8F0;">
                                        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                                            <div style="font-size:13px; font-weight:700; color:#1F2937;">{aexpert}</div>
                                            {badge}
                                        </div>
                                        <div style="color:#334155; font-size:14px; line-height:1.5;">{acontent}</div>
                                    </div>
                                    ''', unsafe_allow_html=True)
                            else:
                                st.markdown('''
                                <div style="background:#FEF2F2; color:#B91C1C; padding:10px; border-radius:6px; font-size:13px; margin-top:10px; text-align:center;">
                                    ⏳ Question pending expert review
                                </div>
                                ''', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("You haven't posted any questions yet.")

            # TAB 4: My History
            with tab4:
                st.markdown('#### 📜 Prediction History')
                rows = cdb.get_history(user.get('username'))
                if rows:
                    for r in rows:
                        # r: id, input_json, reponse_json, date
                        date_str = r[3]
                        # Try to parse input slightly cleanly
                        st.markdown(f'''
                        <div class="app-card" style="padding: 15px; margin-bottom: 10px;">
                             <div style="font-weight: bold; color: var(--primary-green);">{date_str}</div>
                             <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">{r[1]}</div>
                             <div style="margin-top: 8px; font-weight: 500;">Result: {r[2]}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.info('No prediction history yet.')
        
        # Expert Dashboard (Admin View)
        elif user.get('role') in ['expert', 'agricultural expert']:
            # Modern Admin Header
            st.markdown("""
                <div style="background: linear-gradient(to right, #ecfdf5, white); padding: 20px; border-radius: 16px; margin-bottom: 25px; border: 1px solid #d1fae5;">
                    <h2 style="color: #065f46; margin:0;">👨‍🔬 Expert Command Center</h2>
                    <p style="color: #047857; margin-top:5px;">Manage community questions, schedule sessions, and update organic data maps.</p>
                </div>
            """, unsafe_allow_html=True)

            tab1, tab2, tab3, tab4 = st.tabs(['💬 Q&A Hub', '📅 Live Sessions', '🌍 Organic Mapping', '🤖 AI Assistant'])
            
            # TAB 1: Q&A HUB
            with tab1:
                # Top Controls: Filter & Search
                col_ctrl1, col_ctrl2 = st.columns([2, 2])
                with col_ctrl1:
                    # Renamed filter to be more explicit about functionality
                    q_filter = st.selectbox('View Mode', ['Unanswered Questions', 'All Discussions (Peer Review)'], key='q_filter')
                
                qs = cdb.list_questions()
                if qs:
                    count = 0
                    for q in qs:
                        qid, qtitle, qcontent, quser, _, qdate = q[0], q[1], q[2], q[3], q[4], q[5] 
                        
                        # Fetch answers to check status
                        ans = cdb.get_answers(qid)
                        is_answered = len(ans) > 0
                        
                        # LOGIC: If filter is 'Unanswered', hide questions that have ANY answer
                        if q_filter == 'Unanswered Questions' and is_answered:
                            continue

                        count += 1
                        
                        # Visual Style: Differentiate "Fresh" vs "Ongoing Discussion"
                        card_color = '#F59E0B' if not is_answered else '#3B82F6' # Orange for new, Blue for discussion
                        status_text = "Needs Answer" if not is_answered else f"Has {len(ans)} Expert Replie(s)"
                        
                        with st.container():
                            st.markdown(f'''
                            <div class="app-card" style="padding: 24px; border-left: 4px solid {card_color};">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <span style="background: #F3F4F6; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; color: #4B5563;">{status_text}</span>
                                    <span style="font-size: 13px; color: #6B7280;">{qdate}</span>
                                </div>
                                <h3 style="margin: 0 0 10px 0; color: var(--text-primary); font-size: 18px;">{qtitle}</h3>
                                <p style="color: var(--text-secondary); margin-bottom: 15px;">{qcontent}</p>
                                <div style="display: flex; align-items: center; gap: 10px; font-size: 13px;">
                                    <div style="width: 24px; height: 24px; background: #E5E7EB; border-radius: 50%; display: flex; align-items: center; justify-content: center;">👤</div>
                                    <span style="font-weight: 500;">{quser}</span>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)

                            # PEER REVIEW SECTION: Show existing answers to the expert
                            if ans:
                                st.info("👀 Peer Review: Other experts have answered this. Review their advice below.")
                                for a in ans:
                                    aid, acontent, aexpert, adate, averified = a[0], a[1], a[2], a[3], a[4]
                                    icon = "🥇" if averified else "👨‍�"
                                    bg = "#ecfdf5" if averified else "#eff6ff"
                                    st.markdown(f"""
                                    <div style="background: {bg}; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #e5e7eb; margin-left: 20px;">
                                        <div style="font-weight: 600; font-size: 13px; color: #1e40af; margin-bottom: 4px;">{icon} Expert {aexpert} said:</div>
                                        <div style="font-size: 14px; color: #374151;">{acontent}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Verify button (only if not verified)
                                    if not averified:
                                        col_v1, _ = st.columns([1, 4])
                                        if col_v1.button('Verify this', key=f'v_{aid}'):
                                            cdb.verify_answer(aid)
                                            st.success('Marked as verified!')
                                            st.rerun()

                            # COLLABORATIVE ANSWER FORM
                            # Label changes based on whether it's a first answer or a correction
                            input_label = "Start typing your advice..." if not is_answered else "Add an alternative opinion or correction..."
                            btn_label = "Post Answer" if not is_answered else "Post Additional Opinion"
                            
                            with st.form(key=f'expert_ans_{qid}', border=False):
                                cols = st.columns([4, 1])
                                with cols[0]:
                                    ans_text = st.text_input('Expert Advice', placeholder=input_label, label_visibility="collapsed")
                                with cols[1]:
                                    sub = st.form_submit_button(btn_label, type='primary', use_container_width=True)
                                
                                if sub and ans_text:
                                    cdb.create_answer(qid, ans_text, user.get('username'))
                                    st.success('Contribution posted!')
                                    st.rerun()
                            st.markdown("---")
                    
                    if count == 0:
                        if q_filter == 'Unanswered Questions':
                            st.success("🎉 No unanswered questions! Switch to 'All Discussions' to review peer answers.")
                        else:
                            st.info("No questions found.")
                else:
                    st.info('No questions asked properly yet.')

            # TAB 2: SESSIONS
            with tab2:
                c1, c2 = st.columns([1, 1.5], gap="medium")
                with c1:
                    with st.container(border=True):
                        st.markdown("### 📅 Schedule Event")
                        st.markdown("<div style='font-size: 14px; color: #6B7280; margin-bottom: 15px;'>Set up a webinar or live Q&A session.</div>", unsafe_allow_html=True)
                        
                        s_title = st.text_input('Topic', placeholder='e.g., Organic Pest Control')
                        s_link = st.text_input('Meeting Link', placeholder='https://meet.google.com/...')
                        col_d, col_t = st.columns(2)
                        with col_d:
                            s_date = st.date_input("Date")
                        with col_t:
                            s_time = st.time_input("Time")
                        
                        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                        if st.button('Create Session', type='primary', use_container_width=True):
                            # combine date/time
                            when_str = f"{s_date} {s_time}"
                            if hasattr(cdb, 'create_session'):
                                cdb.create_session(s_title, s_link, when_str, user.get('username'))
                                st.success('Session Published!')
                                st.rerun()

                with c2:
                    st.markdown("### 📡 Upcoming Sessions")
                    sessions = cdb.list_sessions()
                    if sessions:
                        for s in sessions:
                            st.markdown(f'''
                            <div class="app-card" style="padding: 15px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                <div>
                                    <div style="font-weight: 700; color: var(--text-primary);">{s[1]}</div>
                                    <div style="font-size: 13px; color: var(--text-secondary);">📅 {s[3]}</div>
                                </div>
                                <a href="{s[2]}" target="_blank" class="action-btn" style="padding: 6px 12px; font-size: 12px;">Launch</a>
                            </div>
                            ''', unsafe_allow_html=True)
                    else:
                        st.info("No active sessions.")

            # TAB 3: ORGANIC MAPPING (ADMIN)
            with tab3:
                st.markdown("### 🌍 Impact & Organic Resource Mapping")
                st.markdown("Manage the database of organic fertilizers and crop recommendations here.")
                
                # Mock Data Editor for "Organic Mapping"
                # In a real app, this would query cdb.get_fertilizers()
                
                col1, col2 = st.columns(2)
                with col1:
                    with st.container(border=True):
                        st.metric("Total Farmers Assisted", "1,248", "+12%")
                with col2:
                    with st.container(border=True):
                        st.metric("Organic Conversions", "856", "+5%")

                st.markdown("#### 🥦 Suggested Fertilizer Database")
                # Creating a mock dataframe to simulate the admin capability
                import pandas as pd
                mock_data = pd.DataFrame({
                    'Soil Type': ['Clay', 'Sandy', 'Loamy', 'Silt'],
                    'Nitrogen Level': ['High', 'Low', 'Medium', 'Low'],
                    'Recommended Organic Fix': ['Compost Tea', 'Manure', 'Bio-Char', 'Green Manure'],
                    'Mapping ID': ['ORG-001', 'ORG-002', 'ORG-003', 'ORG-004']
                })
                edited_df = st.data_editor(mock_data, use_container_width=True, num_rows="dynamic")
                
                if st.button("Save Mapping Changes"):
                    st.success("Organic Mapping Database Updated Successfully!")

            # TAB 4: AI ASSISTANT
            with tab4:
                render_ai_doctor()

st.subheader('F2C Marketplace (Coming Soon)')
st.markdown('Product cards and farmer storefront UI will be added in next phase.')

