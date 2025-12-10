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
import sys
from pathlib import Path
# add project root (two levels up if app is in app/)
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

# MODERN PROFESSIONAL AGRICULTURAL THEME - Inspired by top agriculture websites
st.markdown('''
<style>
    /* Hide ALL Streamlit branding */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    
    /* Modern Agricultural Color Palette */
    :root {
        --forest-green: #2D5016;
        --olive-green: #6B8E23;
        --sage-green: #8FBC8F;
        --earth-brown: #8B4513;
        --warm-cream: #FFF8E7;
        --soft-white: #FAFAFA;
        --text-dark: #2C3E2D;
        --text-medium: #4A5F4B;
        --shadow-soft: rgba(45, 80, 22, 0.12);
        --shadow-hover: rgba(45, 80, 22, 0.25);
    }
    
    /* Modern Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7f0 0%, #e8f0e3 100%);
    }
    
    /* Main Container - Clean Modern Card */
    .main .block-container {
        background: white;
        border-radius: 20px;
        padding: 3rem 2.5rem;
        box-shadow: 0 8px 32px var(--shadow-soft);
        max-width: 1200px;
        margin: 2rem auto;
        border-top: 4px solid var(--forest-green);
    }
    
    /* CONSISTENT FONT SIZING - Professional hierarchy */
    h1 {
        font-size: 38px !important;
        font-weight: 700 !important;
        color: var(--forest-green) !important;
        margin-bottom: 16px !important;
        letter-spacing: -0.5px;
    }
    
    h2 {
        font-size: 28px !important;
        font-weight: 600 !important;
        color: var(--forest-green) !important;
        margin-bottom: 14px !important;
    }
    
    h3 {
        font-size: 22px !important;
        font-weight: 600 !important;
        color: var(--olive-green) !important;
        margin-bottom: 12px !important;
    }
    
    h4 {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: var(--olive-green) !important;
        margin-bottom: 10px !important;
    }
    
    /* Body text - CONSISTENT 16px everywhere */
    p, span, div, li, label, .stMarkdown {
        font-size: 16px !important;
        color: var(--text-dark);
        line-height: 1.7;
    }
    
    /* Modern Input Fields - FIXED SIZE 16px */
    input, select, textarea,
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox select,
    [data-baseweb="input"] input {
        font-size: 16px !important;
        padding: 12px 14px !important;
        border: 2px solid var(--sage-green) !important;
        border-radius: 10px !important;
        background: var(--warm-cream) !important;
        color: var(--text-dark) !important;
        transition: all 0.3s ease !important;
    }
    
    input:focus, select:focus, textarea:focus {
        border-color: var(--olive-green) !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(107, 142, 35, 0.15) !important;
    }
    
    /* Labels - CONSISTENT 16px */
    label, .stMarkdown label {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: var(--text-dark) !important;
        margin-bottom: 8px !important;
    }
    
    /* Modern Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--forest-green) 0%, var(--olive-green) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 32px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 16px var(--shadow-soft) !important;
        letter-spacing: 0.3px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 24px var(--shadow-hover) !important;
    }
    
    /* Sidebar - Modern Dark Green with toggle visibility */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--forest-green) 0%, #1a3a0f 100%);
        padding: 1.5rem 1rem;
        box-shadow: 2px 0 10px var(--shadow-soft);
    }
    
    /* Sidebar toggle button - always visible */
    [data-testid="collapsedControl"] {
        background: var(--forest-green) !important;
        color: white !important;
        border-radius: 0 8px 8px 0 !important;
        padding: 8px !important;
    }
    
    [data-testid="collapsedControl"]:hover {
        background: var(--olive-green) !important;
        box-shadow: 0 4px 12px var(--shadow-hover) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        font-size: 18px !important;
        font-weight: 600 !important;
        margin-bottom: 12px !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    [data-testid="stSidebar"] label {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 10px !important;
        transition: background 0.3s ease !important;
        cursor: pointer !important;
    }
    
    [data-testid="stSidebar"] label:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        transform: translateX(4px);
    }
    
    /* Radio button selected state */
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
        background-color: white !important;
    }
    
    /* Result Card - Modern Design */
    .result-card {
        background: linear-gradient(135deg, var(--warm-cream) 0%, white 100%);
        border-left: 5px solid var(--olive-green);
        border-radius: 15px;
        padding: 24px;
        box-shadow: 0 6px 20px var(--shadow-soft);
        margin: 20px 0;
    }
    
    .result-card * {
        color: var(--text-dark) !important;
        font-size: 16px !important;
    }
    
    .result-card h2 {
        color: var(--forest-green) !important;
        font-size: 28px !important;
        margin-bottom: 12px !important;
    }
    
    .result-card h4 {
        color: var(--olive-green) !important;
        font-size: 18px !important;
    }
    
    /* Feature Cards */
    .app-card {
        background: white;
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px var(--shadow-soft);
        border: 1px solid rgba(139, 69, 19, 0.08);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .app-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 40px var(--shadow-hover);
    }
    
    /* Section Dividers */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--sage-green), transparent);
        margin: 32px 0;
    }
    
    /* Info Boxes */
    .stAlert {
        border-radius: 12px !important;
        border-left: 4px solid var(--olive-green) !important;
        background: var(--warm-cream) !important;
        padding: 16px !important;
    }
    
    /* Toast Notifications */
    .stToast {
        background: white !important;
        border-left: 4px solid var(--olive-green) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px var(--shadow-soft) !important;
    }
    
    /* Column spacing */
    [data-testid="column"] {
        padding: 12px;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        color: var(--forest-green) !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 16px !important;
        color: var(--text-medium) !important;
    }
</style>
''', unsafe_allow_html=True)

# Initialize session state if not already done
# Add a floating menu button for easy navigation access
st.markdown('''
<style>
    /* Floating Menu Button - Always visible */
    .floating-menu-btn {
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 999999;
        background: linear-gradient(135deg, var(--forest-green), var(--olive-green));
        color: white;
        padding: 12px 18px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        box-shadow: 0 4px 16px var(--shadow-hover);
        cursor: pointer;
        border: none;
        transition: all 0.3s ease;
    }
    
    .floating-menu-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px var(--shadow-hover);
    }
</style>
''', unsafe_allow_html=True)

st.title('🌾 Climate‑Aware Crop & Organic Fertilizer Recommendation System', anchor=False)
st.markdown('<p style="font-size:18px; color: var(--text-medium); margin-bottom:24px;">Sustainable agriculture powered by climate-aware technology</p>', unsafe_allow_html=True)
st.markdown('<p style="font-size:14px; color: var(--text-medium); font-style: italic;">💡 Tip: Click the <strong>[&gt;]</strong> button at the top-left to show/hide the navigation menu</p>', unsafe_allow_html=True)

# Sidebar with title and navigation
with st.sidebar:
    st.markdown("# 🌾 Navigation")
    st.markdown("*Select a page below*")
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

# Navigation in sidebar with clear labels
with st.sidebar:
    page = st.radio(
        'Choose a page:',
        ['Home', 'Prediction', 'Preparation', 'Community'],
        index=default_index,
        label_visibility="visible"
    )
    
    st.markdown("---")
    st.markdown("#### 💡 Navigation Help")
    st.markdown("""
    **To hide this menu:**  
    Click the **[×]** or **[>]** button at the top
    
    **To show menu again:**  
    Click the **[<]** button that appears
    """)
    st.markdown("---")
    st.markdown("*🌾 Climate-Aware Farming*")

# Update session state with current page
st.session_state['page'] = page

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
    
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    
    # Quick action buttons
    cols = st.columns(3)
    with cols[0]:
        if st.button('🌾 Start Prediction', key='home_pred', use_container_width=True):
            st.session_state['page'] = 'Prediction'
            st.rerun()
    with cols[1]:
        if st.button('📋 View Preparations', key='home_prep', use_container_width=True):
            st.session_state['page'] = 'Preparation'
            st.rerun()
    with cols[2]:
        if st.button('👥 Join Community', key='home_comm', use_container_width=True):
            st.session_state['page'] = 'Community'
            st.rerun()

elif page == 'Prediction':
    # Back button
    if st.button('← Back to Home', key='pred_back'):
        st.session_state['page'] = 'Home'
        st.rerun()
    
    st.header('🌾 Crop & Fertilizer Prediction', anchor=False)
    st.markdown('<p style="font-size:16px; color: var(--text-medium);">Get personalized recommendations based on your soil and climate conditions</p>', unsafe_allow_html=True)
    
    # Two-column layout: left for inputs, right for results
    left, right = st.columns([2, 1], gap='large')

    with left:
        with st.form('input_form'):
            # Location & Soil
            st.markdown('### 📍 Location & Soil')
            cols = st.columns(2)
            with cols[0]:
                region = st.selectbox('Region', ['North','South','East','West','Central'])
            with cols[1]:
                soil = st.selectbox('Soil Type', ['Loamy','Sandy','Clayey','Silty'])

            # Soil Nutrients
            st.markdown('### 🧪 Soil Nutrients (NPK)')
            ncols = st.columns(3)
            with ncols[0]:
                N = st.number_input('Nitrogen (N)', min_value=0.0, value=100.0)
            with ncols[1]:
                P = st.number_input('Phosphorus (P)', min_value=0.0, value=50.0)
            with ncols[2]:
                K = st.number_input('Potassium (K)', min_value=0.0, value=150.0)

            # Climate Conditions
            st.markdown('### 🌤️ Climate Conditions')
            ccols = st.columns(4)
            with ccols[0]:
                pH = st.number_input('Soil pH', min_value=3.0, max_value=9.0, value=6.5, format='%.2f')
            with ccols[1]:
                temp = st.number_input('Temperature (°C)', value=25.0)
            with ccols[2]:
                humidity = st.number_input('Humidity (%)', value=70.0)
            with ccols[3]:
                rainfall = st.number_input('Rainfall (mm/year)', value=800.0)

            st.markdown('<div style="margin-top:20px"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button('🔍 Run Prediction', use_container_width=True)

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

    # RIGHT: Result card
    with right:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('#### 📊 Results', unsafe_allow_html=True)
        
        if 'last_result' in st.session_state:
            lr = st.session_state['last_result']
            
            st.markdown(f"### {lr.get('crop_pred')}")
            st.markdown(f"**Suggested fertilizer:** {lr.get('nf')}")
            
            src = 'Model Prediction' if lr.get('used_fert_model') else 'Heuristic Analysis'
            st.markdown(f"*Source: {src}*")
            
            conv = lr.get('conv', {})
            org = conv.get('organic') or ''
            if org:
                st.markdown(f"**Organic alternative:** {org}")
            
            st.markdown('---')
            st.markdown('**Analysis Summary:**')
            inp = lr.get('input', {})
            st.markdown(f"- **Soil:** {inp.get('soil')}")
            st.markdown(f"- **pH Level:** {inp.get('pH')}")
            st.markdown(f"- **NPK:** {inp.get('N')}-{inp.get('P')}-{inp.get('K')}")
            st.markdown(f"- **Climate:** {inp.get('temperature')}°C, {inp.get('humidity')}% humidity")
            
            notes = conv.get('notes')
            if notes:
                st.info(notes)
                
            if st.button('📋 View Preparation Guide', use_container_width=True):
                st.session_state['page'] = 'Preparation'
                st.rerun()
        else:
            st.info('👈 Fill the form and run prediction to see your personalized recommendations here!')
            
        st.markdown('</div>', unsafe_allow_html=True)

elif page == 'Preparation':
    # Back buttons
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button('← Back', key='prep_back_pred'):
            st.session_state['page'] = 'Prediction'
            st.rerun()
    with cols[1]:
        if st.button('🏠 Home', key='prep_back_home'):
            st.session_state['page'] = 'Home'
            st.rerun()
    
    st.header('📋 Organic Fertilizer Preparation Guide', anchor=False)
    st.markdown('<p style="font-size:16px; color: var(--text-medium);">Step-by-step instructions and video tutorials</p>', unsafe_allow_html=True)
    if 'last_result' not in st.session_state:
        st.info('No saved prediction. Go to Prediction and run a prediction first.')
    else:
        lr = st.session_state['last_result']
        conv = lr.get('conv', {})
        st.success(f"🍃 Last Recommended Organic Equivalent: {conv.get('organic')}")
        st.write('Notes:', conv.get('notes'))
        st.markdown('### Preparation')
        prep = conv.get('preparation_steps') or []
        if isinstance(prep, list) and prep:
            for i, step in enumerate(prep, start=1):
                st.markdown(f"**{i}.** {step}")
            prep_text = '\n'.join([f"{i}. {s}" for i, s in enumerate(prep, start=1)])
            # Prefer a PDF download when we can generate it; otherwise offer a TXT fallback.
            pdf_bytes = None
            try:
                pdf_bytes = generate_preparation_pdf(conv.get('organic') or 'preparation', prep)
            except Exception:
                pdf_bytes = None
            if pdf_bytes:
                st.download_button('Download Preparation (PDF)', data=pdf_bytes, file_name=f"preparation_{conv.get('organic','fert')}.pdf", mime='application/pdf')
            else:
                st.download_button('Download Preparation (TXT)', prep_text, file_name=f"preparation_{conv.get('organic','fert')}.txt")
        else:
            st.write('No preparation steps available.')
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
                st.markdown('### Video Recommendations (preferred: Kannada → Hindi → English)')
                for lang in languages:
                    vids = results_by_lang.get(lang, [])
                    if not vids:
                        continue
                    st.markdown(f"#### {lang}")
                    for i, v in enumerate(vids[:3], start=1):
                        st.markdown(f"**{i}. {v.get('title')}**")
                        try:
                            st.video(v.get('link'))
                        except Exception:
                            st.write(v.get('link'))

elif page == 'Community':
    st.header('👥 Expert Community', anchor=False)
    st.markdown('<p style="font-size:16px; color: var(--text-medium);">Connect with agricultural experts and get verified answers</p>', unsafe_allow_html=True)
    
    # Back button
    if st.button('← Back to Home', key='comm_back'):
        st.session_state['page'] = 'Home'
        st.rerun()
    
    # Initialize show_register state if not exists
    if 'show_register' not in st.session_state:
        st.session_state['show_register'] = False
    
    user = st.session_state.get('user')
    
    # If user is not logged in, show modern login/register form
    if not user:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('## 🌾 Community & Experts')
            st.markdown('Connect with farming experts and fellow farmers')
            st.markdown('<br>', unsafe_allow_html=True)
            
            # Show Register Form
            if st.session_state.get('show_register'):
                st.markdown('### 📝 Create New Account')
                st.markdown('<br>', unsafe_allow_html=True)
                with st.form(key='register_form'):
                    r_user = st.text_input('Username', placeholder='Enter your username')
                    st.markdown('<br>', unsafe_allow_html=True)
                    r_pw = st.text_input('Password', type='password', placeholder='Enter password')
                    st.markdown('<br>', unsafe_allow_html=True)
                    r_pw_confirm = st.text_input('Confirm Password', type='password', placeholder='Re-enter password')
                    st.markdown('<br>', unsafe_allow_html=True)
                    r_role = st.selectbox('I am a', ['farmer', 'expert'])
                    st.markdown('<br>', unsafe_allow_html=True)
                    
                    register_btn = st.form_submit_button('Register', use_container_width=True)
                    
                    if register_btn:
                        if not r_user or not r_pw:
                            st.error('Please fill all fields')
                        elif r_pw != r_pw_confirm:
                            st.error('Passwords do not match')
                        else:
                            ok = cdb.create_user(r_user, r_pw, role=r_role)
                            if ok:
                                # Auto-login after registration
                                u = cdb.authenticate(r_user, r_pw)
                                if u:
                                    st.session_state['user'] = u
                                    st.session_state['show_register'] = False
                                    st.success(f'Welcome {u["username"]}! Registration successful.')
                                    st.rerun()
                            else:
                                st.error('Registration failed (username may already exist)')
                
                st.markdown('<br>', unsafe_allow_html=True)
                if st.button('← Back to Login', use_container_width=True):
                    st.session_state['show_register'] = False
                    st.rerun()
            
            # Show Login Form (default)
            else:
                st.markdown('### 🔐 Login to Your Account')
                st.markdown('<br>', unsafe_allow_html=True)
                with st.form(key='login_form'):
                    username = st.text_input('Username', placeholder='Enter your username')
                    st.markdown('<br>', unsafe_allow_html=True)
                    password = st.text_input('Password', type='password', placeholder='Enter your password')
                    st.markdown('<br>', unsafe_allow_html=True)
                    
                    login_btn = st.form_submit_button('Login', use_container_width=True)
                    
                    if login_btn:
                        if not username or not password:
                            st.error('Please enter username and password')
                        else:
                            u = cdb.authenticate(username, password)
                            if u:
                                st.session_state['user'] = u
                                st.success(f'Welcome back, {u["username"]}!')
                                st.rerun()
                            else:
                                st.error('Invalid username or password')
                
                # Register link below login form
                st.markdown('<br>', unsafe_allow_html=True)
                if st.button('📝 Create New Account', use_container_width=True):
                    st.session_state['show_register'] = True
                    st.rerun()
            
            # DB Init button (for first time setup)
            st.markdown('<br><br>', unsafe_allow_html=True)
            with st.expander('⚙️ Database Setup (First Time Only)'):
                if st.button('Initialize Community Database'):
                    cdb.init_db()
                    st.success('Database initialized successfully!')
    
    # If user is logged in, show dashboard
    # If user is logged in, show dashboard
    else:
        # User header with logout
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f'Welcome, {user.get("username")}!')
            st.markdown(f'*Role: {user.get("role").title()}*')
        with col2:
            if st.button('Logout', key='logout_btn', use_container_width=True):
                st.session_state['user'] = None
                st.session_state['show_register'] = False
                st.info('Logged out successfully')
                st.rerun()
        
        st.markdown('---')
        
        # Farmer Dashboard
        if user.get('role') == 'farmer':
            st.markdown('### 📊 Farmer Dashboard')
            
            # Upcoming Tutorials & Live Sessions
            st.markdown('#### 🎓 Upcoming Tutorials & Live Sessions')
            sessions = cdb.list_sessions()
            if sessions:
                for s in sessions:
                    sid, stitle, slink, swhen, sexpert = s
                    with st.container():
                        st.markdown(f"**{stitle}**")
                        st.markdown(f"📅 Scheduled: {swhen} | 👨‍🏫 By: {sexpert}")
                        st.markdown(f"🔗 Link: {slink}")
                        cols = st.columns([1, 1, 4])
                        with cols[0]:
                            if st.button('Join Session', key=f'join_{sid}', use_container_width=True):
                                st.markdown(f"[Open session link]({slink})")
                        with cols[1]:
                            if st.button('Bookmark', key=f'bm_{sid}', use_container_width=True):
                                cdb.add_bookmark(user.get('username'), stitle, slink)
                                st.success('Bookmarked!')
                        st.markdown('---')
            else:
                st.info('No upcoming sessions scheduled.')
            
            st.markdown('---')
            
            # Farmer Menu Options
            tab1, tab2 = st.tabs(['📜 My History', '🔖 My Bookmarks'])
            
            with tab1:
                st.markdown('#### Prediction History')
                rows = cdb.get_history(user.get('username'))
                if rows:
                    for r in rows:
                        st.markdown(f"**{r[3]}**")
                        st.write('Input:', r[1])
                        st.write('Result:', r[2])
                        st.markdown('---')
                else:
                    st.info('No prediction history yet.')
            
            with tab2:
                st.markdown('#### My Bookmarks')
                bms = cdb.get_bookmarks(user.get('username'))
                if bms:
                    for b in bms:
                        st.markdown(f"- [{b[1]}]({b[2]})")
                else:
                    st.info('No bookmarks yet.')
        
        # Expert Dashboard
        elif user.get('role') == 'expert':
            st.markdown('### 👨‍🏫 Expert Dashboard')
            
            tab1, tab2, tab3 = st.tabs(['❓ Questions', '📅 Schedule Session', '📤 Upload Data'])
            
            with tab1:
                st.markdown('#### Community Questions')
                qs = cdb.list_questions()
                if qs:
                    for q in qs:
                        with st.container():
                            st.markdown(f"**{q[1]}**")
                            st.markdown(f"*Asked by {q[3]} on {q[5]}*")
                            st.write(q[2])
                            if q[4]:
                                st.markdown(f"📎 Attachment: {q[4]}")
                            
                            # Show existing answers
                            ans = cdb.get_answers(q[0])
                            if ans:
                                st.markdown('**Answers:**')
                                for a in ans:
                                    aid, content, expert_name, created, verified = a[0], a[1], a[2], a[3], a[4]
                                    status = '✅ Verified' if verified else '⏳ Pending'
                                    st.markdown(f"- {content} *(by {expert_name})* [{status}]")
                                    if not verified:
                                        if st.button(f'Verify', key=f'verify_{aid}'):
                                            cdb.verify_answer(aid)
                                            st.success('Answer verified!')
                                            st.rerun()
                            
                            # Answer form
                            with st.form(key=f'ans_{q[0]}'):
                                ans_txt = st.text_area('Your answer', key=f'txt_{q[0]}')
                                if st.form_submit_button('Submit Answer'):
                                    if ans_txt:
                                        cdb.create_answer(q[0], ans_txt, user.get('username'))
                                        st.success('Answer submitted!')
                                        st.rerun()
                            
                            st.markdown('---')
                else:
                    st.info('No questions yet.')
            
            with tab2:
                st.markdown('#### Conduct Tutorial / Schedule Session')
                with st.form(key='create_session_form'):
                    s_title = st.text_input('Session title')
                    s_link = st.text_input('Session link (Zoom/YouTube/Meet)')
                    s_when = st.text_input('Scheduled time', value='YYYY-MM-DD HH:MM', placeholder='e.g., 2025-12-15 14:00')
                    
                    if st.form_submit_button('Create Session', use_container_width=True):
                        if s_title and s_link:
                            if hasattr(cdb, 'create_session'):
                                cdb.create_session(s_title, s_link, s_when, user.get('username'))
                                st.success('Session scheduled successfully!')
                                st.rerun()
                            else:
                                st.error('Session feature not available. Please initialize the database.')
                        else:
                            st.error('Please fill in all fields.')
            
            with tab3:
                st.markdown('#### Upload Fertilizer Mapping')
                uploaded = st.file_uploader('Upload CSV file', type=['csv'], key='upload_fert_csv')
                if uploaded:
                    if st.button('Save File'):
                        content = uploaded.getvalue()
                        with open('data/fertilizer_mapping.csv', 'wb') as f:
                            f.write(content)
                        st.success('fertilizer_mapping.csv updated successfully!')
        
        # Show community posts (visible to all logged-in users)
        st.markdown('---')
        st.markdown('### 📰 Recent Community Posts')
        posts = cdb.list_posts()
        if posts:
            for p in posts:
                with st.container():
                    st.markdown(f"**{p[1]}**")
                    st.markdown(f"*By {p[3]} on {p[4]}*")
                    st.write(p[2])
                    st.markdown('---')
        else:
            st.info('No posts found.')

st.markdown('---')
st.subheader('F2C Marketplace (Coming Soon)')
st.markdown('Product cards and farmer storefront UI will be added in next phase.')

