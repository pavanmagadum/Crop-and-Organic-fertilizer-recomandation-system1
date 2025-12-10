import streamlit as st, joblib, pandas as pd, os, json
import sys
from pathlib import Path

# Hide Streamlit menu with GitHub link
st.set_page_config(
    page_title="Climate-Aware Farming",
    page_icon="🌾",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Climate-Aware Crop & Organic Fertilizer Recommendation System"
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

st.set_page_config(page_title='Climate Aware Crop & Organic Fertilizer', layout='wide')
# Enhanced theme + CSS with larger fonts and better color contrast
st.markdown('''
<style>
    /* Hide ALL Streamlit branding and GitHub links */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    
    [data-testid="stToolbar"] {
        display: none !important;
    }
    
    .viewerBadge_container__1QSob {
        display: none !important;
    }
    
    /* Professional Green Theme - Consistent for all modes */
    :root {
        --primary-green: #1f8f3f;
        --primary-green-dark: #156b2f;
        --card-bg: rgba(255, 255, 255, 0.85);
        --card-border: rgba(31, 143, 63, 0.2);
        --text-primary: #156b2f;
        --text-secondary: #2d5f2d;
        --text-muted: #4a7c4a;
        --bg-overlay: rgba(255, 255, 255, 0.75);
        --shadow-color: rgba(15, 15, 15, 0.1);
        --button-text: #ffffff;
    }
    
    /* Global Styles - EVEN LARGER FONTS */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: var(--text-primary);
        font-size: 27px;
    }
    
    .main-title {
        font-size: 60px;
        font-weight: 700;
        margin-bottom: 8px;
        color: var(--text-primary);
    }
    
    .subtitle {
        color: var(--text-muted);
        margin-top: 0;
        margin-bottom: 24px;
        font-size: 33px;
        line-height: 1.6;
    }
    
    .app-card {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 18px;
        box-shadow: 0 4px 20px var(--shadow-color);
        border: 1px solid var(--card-border);
        transition: all 0.3s ease;
    }
    
    .app-card:hover {
        box-shadow: 0 6px 28px var(--shadow-color);
        transform: translateY(-2px);
    }
    
    .result-card {
        padding: 20px;
        border-radius: 8px;
        background: transparent;
        color: #156b2f;
    }
    
    .result-card * {
        color: #156b2f !important;
    }
    
    .result-card h1,
    .result-card h2,
    .result-card h3,
    .result-card h4,
    .result-card p,
    .result-card span,
    .result-card div,
    .result-card li {
        color: #156b2f !important;
    }
    
    .section-title {
        font-size: 36px;
        font-weight: 700;
        color: var(--primary-green);
        margin-bottom: 14px;
        letter-spacing: 0.3px;
    }
    
    .small-muted {
        color: var(--text-muted);
        font-size: 26px;
        line-height: 1.6;
    }
    
    /* Button Styles - EVEN LARGER */
    .stButton>button {
        background: var(--primary-green) !important;
        border-radius: 8px;
        color: var(--button-text) !important;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border: none;
        transition: all 0.3s ease;
        font-size: 29px;
    }
    
    .stButton>button:hover {
        background: var(--primary-green-dark) !important;
        box-shadow: 0 4px 12px rgba(31, 143, 63, 0.3);
        transform: translateY(-1px);
    }
    
    /* Form Elements - EVEN LARGER FONTS */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        background: var(--card-bg);
        color: var(--text-primary);
        border: 1px solid var(--card-border);
        font-size: 27px;
        padding: 0.6rem;
    }
    
    /* Headings - EVEN LARGER */
    h1 {
        color: var(--text-primary) !important;
        font-size: 63px !important;
    }
    
    h2 {
        color: var(--text-primary) !important;
        font-size: 45px !important;
        font-weight: 700 !important;
    }
    
    h3 {
        color: var(--primary-green) !important;
        font-size: 39px !important;
    }
    
    h4 {
        color: var(--text-primary) !important;
        font-size: 33px !important;
    }
    
    /* Labels - EVEN LARGER & BETTER COLOR */
    label {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 27px !important;
    }
    
    /* Paragraphs - EVEN LARGER */
    p, li {
        font-size: 27px;
        line-height: 1.7;
        color: var(--text-primary);
    }
    
    /* Streamlit emotion cache containers - light transparent white background */
    .st-emotion-cache-zuyloh {
        background: rgba(255, 255, 255, 0.45) !important;
        border: 1px solid rgba(31, 143, 63, 0.2) !important;
    }
    
    .st-emotion-cache-zuyloh * {
        color: #156b2f !important;
    }
    
    .st-emotion-cache-zuyloh label,
    .st-emotion-cache-zuyloh input,
    .st-emotion-cache-zuyloh select,
    .st-emotion-cache-zuyloh p,
    .st-emotion-cache-zuyloh span,
    .st-emotion-cache-zuyloh div {
        color: #156b2f !important;
        font-weight: 600 !important;
    }
    
    .st-emotion-cache-18kf3ut {
        background: transparent !important;
    }
    
    .st-emotion-cache-18kf3ut * {
        color: #156b2f !important;
    }
    
    .st-emotion-cache-18kf3ut button {
        color: #156b2f !important;
    }
    
    /* Mobile responsive fixes for light theme */
    @media (max-width: 768px) {
        /* Reduce heading sizes for mobile */
        h1 {
            font-size: 32px !important;
            line-height: 1.2 !important;
        }
        
        h2 {
            font-size: 28px !important;
            line-height: 1.3 !important;
        }
        
        h3 {
            font-size: 24px !important;
        }
        
        h4 {
            font-size: 20px !important;
        }
        
        body {
            font-size: 16px !important;
        }
        
        /* Make input containers solid white on mobile in light theme */
        .st-emotion-cache-zuyloh {
            background: #ffffff !important;
            border: 2px solid #1f8f3f !important;
            padding: 1rem !important;
            border-radius: 8px !important;
        }
        
        /* Force all inputs to have solid white background with dark green text */
        input[type="text"],
        input[type="number"],
        select,
        textarea,
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox select,
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stSelectbox>div>div>select,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div > input {
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #156b2f !important;
            border: 2px solid #1f8f3f !important;
            font-weight: 700 !important;
            -webkit-text-fill-color: #156b2f !important;
        }
        
        /* Force dropdown/select text to be visible */
        [data-baseweb="select"] [role="button"],
        [data-baseweb="select"] > div > div {
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #156b2f !important;
            -webkit-text-fill-color: #156b2f !important;
        }
        
        /* Green text for ALL labels on mobile */
        label,
        .stTextInput label,
        .stNumberInput label,
        .stSelectbox label,
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p {
            color: #156b2f !important;
            font-weight: 700 !important;
            -webkit-text-fill-color: #156b2f !important;
        }
        
        /* Section titles visible on mobile */
        .section-title {
            color: #1f8f3f !important;
            font-weight: 700 !important;
        }
        
        /* Form containers */
        [data-testid="stForm"] {
            background: #ffffff !important;
            border: 2px solid #1f8f3f !important;
            padding: 1.5rem !important;
            border-radius: 12px !important;
        }
    }
    
    /* Back button styling - same size and padding */
    button[key="prep_back_pred"],
    button[key="prep_back_home"] {
        width: 100% !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 18px !important;
    }
    
    /* Quick Actions buttons on Home page - green text */
    .stButton > button[key="home_pred"],
    .stButton > button[key="home_prep"],
    .stButton > button[key="home_comm"] {
        color: #156b2f !important;
    }

    }
</style>
''', unsafe_allow_html=True)
st.title('🌾 Climate‑Aware Crop & Organic Fertilizer Recommendation System', anchor=False)
st.markdown('<div class="subtitle">Quickly predict suitable crops and organic fertilizer equivalents using local soil and climate inputs.</div>', unsafe_allow_html=True)
# Sidebar settings (removed unused API key inputs)
# Navigation: replace generic Settings with clear page navigation
# Enhanced sidebar with WHITE TEXT on GREEN background
st.markdown('''
<style>
    /* Light Mode Sidebar - WHITE TEXT ON GREEN */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(31,143,63,0.92), rgba(21,107,47,0.92)),
                    url('https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=800&q=80') center/cover;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: rgba(31,143,63,0.25);
        border-radius: 12px;
        padding: 1.2rem;
    }
    
    /* WHITE TEXT for navigation labels - LARGER */
    [data-testid="stSidebar"] .stRadio > label {
        font-weight: 700;
        color: #ffffff !important;
        font-size: 22px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        letter-spacing: 0.5px;
    }
    
    /* WHITE TEXT for radio options - LARGER */
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 19px;
    }
    
    /* WHITE TEXT for all sidebar content */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Radio button hover effect */
    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(255,255,255,0.15);
        border-radius: 6px;
        padding: 6px 10px;
    }
</style>
''', unsafe_allow_html=True)

# Check if page is set via session_state (from button clicks), otherwise use sidebar
if 'page' in st.session_state:
    default_page = st.session_state['page']
    try:
        default_index = ['Home', 'Prediction', 'Preparation', 'Community'].index(default_page)
    except ValueError:
        default_index = 0
else:
    default_index = 0

page = st.sidebar.radio('Navigate', ['Home', 'Prediction', 'Preparation', 'Community'], index=default_index)

# Update session state with current page
st.session_state['page'] = page

# Keep OpenWeather API key input tucked under auth (optional)
OPENWEATHER_KEY = None

# initialize user in session state (auth UI rendered on Community page)
if 'user' not in st.session_state:
    st.session_state['user'] = None
# Page rendering: Home, Prediction, Preparation, Community
st.markdown('''
<style>
    /* Feature cards with GREEN background and WHITE text - LARGER */
    .feature {
        display: inline-block;
        padding: 14px 22px;
        margin: 10px;
        border-radius: 8px;
        background: linear-gradient(135deg, #1f8f3f, #156b2f);
        color: #ffffff;
        font-size: 19px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(31,143,63,0.3);
        transition: all 0.3s ease;
    }
    
    .feature:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(31,143,63,0.4);
    }
    
    /* Card styling with better contrast - LARGER TEXT */
    .card {
        background: transparent;
        padding: 24px;
        border-radius: 12px;
        margin: 18px 0;
        box-shadow: none;
    }
    
    .card h3 {
        color: #1f8f3f;
        font-size: 28px;
        margin-bottom: 14px;
    }
    
    .sidebar .stRadio>div {
        padding: 8px;
    }
</style>
''', unsafe_allow_html=True)

if page == 'Home':
    # Agriculture-themed background for Home page - supports light and dark mode
    st.markdown('''
    <style>
        /* Light Mode */
        .stApp {
            background: linear-gradient(135deg, rgba(230,255,230,0.7), rgba(200,240,200,0.7)),
                        url('https://images.unsplash.com/photo-1560493676-04071c5f467b?w=1920&q=80') center/cover fixed;
        }
        .main .block-container {
            background: rgba(255, 255, 255, 0.85) !important;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(31,143,63,0.2);
            border: 2px solid #1f8f3f;
        }
    </style>
    ''', unsafe_allow_html=True)
    st.header('Welcome to Climate-Aware Farming')
    st.markdown('''
    This demo helps farmers choose appropriate crops and simple organic fertilizer preparations based on local soil and climate inputs.
    - Predict crop suitability
    - Convert common fertilizers to organic alternatives
    - Download step-by-step preparation PDF
    - Ask experts and get verified answers
    ''')
    st.markdown('<div class="card"> <h3>Quick Actions</h3></div>', unsafe_allow_html=True)
    # Quick action buttons with functionality
    cols = st.columns(3)
    with cols[0]:
        if st.button('🌾 Prediction', key='home_pred', use_container_width=True):
            st.session_state['page'] = 'Prediction'
            st.rerun()
    with cols[1]:
        if st.button('📋 Preparation', key='home_prep', use_container_width=True):
            st.session_state['page'] = 'Preparation'
            st.rerun()
    with cols[2]:
        if st.button('👥 Community', key='home_comm', use_container_width=True):
            st.session_state['page'] = 'Community'
            st.rerun()
    
    st.markdown('### Demo Checklist')
    st.markdown('''
    - Activate venv and run the app
    - Login as `farmer1` / `secret123` and `expert1` / `secret123`
    - Try Prediction → Prepare → Ask Expert flows
    ''')

elif page == 'Prediction':
    # Agriculture-themed background for Prediction page
    st.markdown('''
    <style>
        .stApp {
            background: linear-gradient(135deg, rgba(220,255,220,0.55), rgba(180,235,180,0.55)),
                        url('https://images.unsplash.com/photo-1560493676-04071c5f467b?w=1920&q=80') center/cover fixed;
        }
        .main .block-container {
            background: rgba(255, 255, 255, 0.85) !important;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(31,143,63,0.2);
            border: 2px solid #1f8f3f;
        }
        
        /* Force green text on white background */
        .main .block-container h1,
        .main .block-container h2,
        .main .block-container h3,
        .main .block-container h4,
        .main .block-container p,
        .main .block-container span,
        .main .block-container div:not(.stButton),
        .main .block-container label,
        .main .block-container [data-testid="stMarkdownContainer"],
        .main .block-container [data-testid="stMarkdownContainer"] * {
            color: #156b2f !important;
        }
        
        .main .block-container .section-title {
            color: #1f8f3f !important;
        }
        
        .main .block-container .small-muted {
            color: #4a5568 !important;
        }
        
        .main .block-container input,
        .main .block-container select,
        .main .block-container textarea {
            color: #156b2f !important;
            background: #ffffff !important;
        }
        
        /* Mobile responsive - solid backgrounds for inputs in light theme */
        @media (max-width: 768px) {
            /* Reduce heading sizes for mobile */
            h1 {
                font-size: 32px !important;
                line-height: 1.2 !important;
            }
            
            h2 {
                font-size: 28px !important;
                line-height: 1.3 !important;
            }
            
            h3 {
                font-size: 24px !important;
            }
            
            h4 {
                font-size: 20px !important;
            }
            
            body {
                font-size: 16px !important;
            }
            
            .main .block-container {
                padding: 1rem !important;
            }
            
            /* Solid white background for input containers on mobile */
            [data-testid="stForm"],
            .st-emotion-cache-zuyloh {
                background: #ffffff !important;
                border: 2px solid #1f8f3f !important;
                padding: 1rem !important;
                border-radius: 8px !important;
            }
            
            /* Force ALL inputs to have white background and dark green text */
            input[type="text"],
            input[type="number"],
            select,
            textarea,
            .stTextInput input,
            .stNumberInput input,
            .stSelectbox select,
            .stTextInput>div>div>input,
            .stNumberInput>div>div>input,
            .stSelectbox>div>div>select,
            input, select, textarea,
            [data-baseweb="select"] > div,
            [data-baseweb="input"] > div > input {
                background: #ffffff !important;
                background-color: #ffffff !important;
                color: #156b2f !important;
                border: 2px solid #1f8f3f !important;
                font-weight: 700 !important;
                -webkit-text-fill-color: #156b2f !important;
            }
            
            /* Force dropdown/select text to be visible */
            [data-baseweb="select"] [role="button"],
            [data-baseweb="select"] > div > div {
                background: #ffffff !important;
                background-color: #ffffff !important;
                color: #156b2f !important;
                -webkit-text-fill-color: #156b2f !important;
            }
            
            /* Labels green and bold */
            label,
            .stTextInput label,
            .stNumberInput label,
            .stSelectbox label,
            [data-testid="stWidgetLabel"],
            [data-testid="stWidgetLabel"] p {
                color: #156b2f !important;
                font-weight: 700 !important;
                -webkit-text-fill-color: #156b2f !important;
            }
            
            /* Section titles green and bold */
            .section-title {
                color: #1f8f3f !important;
                font-weight: 700 !important;
            }
        }
    </style>
    ''', unsafe_allow_html=True)
    
    # Back button
    if st.button('← Back to Home', key='pred_back'):
        st.session_state['page'] = 'Home'
        st.rerun()
    
    # Two-column layout: left for inputs (grouped), right for a Result card
    left, right = st.columns([2, 1], gap='large')

    # LEFT: Inputs grouped into cards
    with left:
        st.subheader('Crop & Fertilizer Recommendation')
        st.markdown('<div class="small-muted">Fill the form and run prediction to see results on the right.</div>', unsafe_allow_html=True)
        with st.form('input_form'):
            # Location & Soil
            st.markdown('<div class="section-title">Location & Soil</div>', unsafe_allow_html=True)
            cols = st.columns(2)
            with cols[0]:
                region = st.selectbox('Region', ['North','South','East','West','Central'])
            with cols[1]:
                soil = st.selectbox('Soil Type', ['Loamy','Sandy','Clayey','Silty'])

            # Soil Nutrients
            st.markdown('<div class="section-title">Soil Nutrients (NPK)</div>', unsafe_allow_html=True)
            ncols = st.columns(3)
            with ncols[0]:
                N = st.number_input('Nitrogen (N)', min_value=0.0, value=100.0)
            with ncols[1]:
                P = st.number_input('Phosphorus (P)', min_value=0.0, value=50.0)
            with ncols[2]:
                K = st.number_input('Potassium (K)', min_value=0.0, value=150.0)

            # Climate Conditions
            st.markdown('<div class="section-title">Climate Conditions</div>', unsafe_allow_html=True)
            ccols = st.columns(4)
            with ccols[0]:
                pH = st.number_input('Soil pH', min_value=3.0, max_value=9.0, value=6.5, format='%.2f')
            with ccols[1]:
                temp = st.number_input('Temperature (°C)', value=25.0)
            with ccols[2]:
                humidity = st.number_input('Humidity (%)', value=70.0)
            with ccols[3]:
                rainfall = st.number_input('Rainfall (mm annual)', value=800.0)

            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button('Run Prediction')

        # Keep prediction logic intact; only change UI presentation
        if submitted:
            with st.spinner('Running predictions...'):
                try:
                    crop_bundle = joblib.load('crop_model.joblib'); artifacts = joblib.load('artifacts.joblib')
                except Exception as e:
                    st.error('Model files missing.'); st.stop()
                enc = artifacts['encoders']; scaler = artifacts['scaler']; crop_model = crop_bundle['model']
                df = pd.DataFrame([{'region':region,'soil_type':soil,'N':N,'P':P,'K':K,'pH':pH,'temperature':temp,'humidity':humidity,'rainfall':rainfall}])
                for c,le in enc.items():
                    df[c] = le.transform(df[c].astype(str))
                X = df[['region','soil_type','N','P','K','pH','temperature','humidity','rainfall']].values
                Xs = scaler.transform(X)
                crop_pred = crop_model.predict(Xs)[0]

            nf = None
            used_fert_model = False
            try:
                fert_bundle = joblib.load('fert_model.joblib')
                fert_model = fert_bundle['model']; fert_le = fert_bundle['le']; cols = fert_bundle['columns']
                row = df.copy(); row = pd.get_dummies(row, columns=['region','soil_type'], drop_first=True)
                for c in cols:
                    if c not in row.columns: row[c]=0
                Xf = row[cols].values
                try:
                    nf = fert_le.inverse_transform([fert_model.predict(Xf)[0]])[0]
                    used_fert_model = True
                    # If the trained fertilizer model only knows a very small set of classes,
                    # it's probably undertrained; prefer the heuristic to provide richer suggestions.
                    try:
                        num_classes = len(getattr(fert_le, 'classes_', []))
                    except Exception:
                        num_classes = 0
                    if num_classes <= 2:
                        # model appears limited; use heuristic instead
                        nf = predict_fertilizer_simple(N, P, K, pH, crop_pred)
                        used_fert_model = False
                        st.warning(f'Fertilizer model appears limited (only {num_classes} classes). Using heuristic suggestion instead.')
                except Exception:
                    # model prediction failed; fall back to heuristic
                    nf = predict_fertilizer_simple(N, P, K, pH, crop_pred)
                    used_fert_model = False
            except Exception:
                # fallback heuristic predictor if model file missing
                nf = predict_fertilizer_simple(N, P, K, pH, crop_pred)
                used_fert_model = False

            if nf:
                conv = convert_non_to_org(nf)
                # persist last result so actions survive reruns
                st.session_state['last_result'] = {
                    'crop_pred': crop_pred,
                    'nf': nf,
                    'conv': conv,
                    'input': {'region': region, 'soil': soil, 'N': N, 'P': P, 'K': K, 'pH': pH, 'temperature': temp, 'humidity': humidity, 'rainfall': rainfall}
                    , 'used_fert_model': used_fert_model
                }
                st.toast('✅ Prediction completed successfully!', icon='🌾')

    # RIGHT: Result card
    with right:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-top:0;color:#1f8f3f !important;font-weight:700">Result</h4>', unsafe_allow_html=True)
        if 'last_result' in st.session_state:
            lr = st.session_state['last_result']
            # Big crop title
            st.markdown(f"<h2 style='margin:6px 0 4px 0;color:#1f8f3f !important;font-weight:700'>{lr.get('crop_pred')}</h2>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight:600;color:#156b2f !important;margin-bottom:8px'>Suggested fertilizer: {lr.get('nf')}</div>", unsafe_allow_html=True)
            # show source of recommendation
            src = 'Model' if lr.get('used_fert_model') else 'Heuristic'
            st.markdown(f"**Source:** {src}")
            conv = lr.get('conv', {})
            org = conv.get('organic') or ''
            st.markdown(f"**Organic equivalent:** {org}")
            # Why this recommendation (use small bullets from existing output variables)
            st.markdown('**Why this recommendation?**')
            reasons = []
            inp = lr.get('input', {})
            reasons.append(f"Soil type: {inp.get('soil')}")
            reasons.append(f"pH: {inp.get('pH')}")
            reasons.append(f"N-P-K: {inp.get('N')}-{inp.get('P')}-{inp.get('K')}")
            reasons.append(f"Temperature/Humidity: {inp.get('temperature')}°C / {inp.get('humidity')}%")
            for r in reasons:
                st.markdown(f"- {r}")
            notes = conv.get('notes')
            if notes:
                st.markdown('**Notes:**')
                st.markdown(notes)
            # Small action buttons
            st.markdown('<div style="margin-top:8px">', unsafe_allow_html=True)
            if st.button('Open Preparation'):
                # navigate to Preparation page
                st.session_state['page'] = 'Preparation'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="small-muted">Run prediction to see recommended crop and fertilizer here.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif page == 'Preparation':
    # Agriculture-themed background for Preparation page - supports light and dark mode
    st.markdown('''
    <style>
        /* Light Mode */
        .stApp {
            background: linear-gradient(135deg, rgba(215,250,215,0.7), rgba(190,240,190,0.7)),
                        url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1920&q=80') center/cover fixed;
        }
        .main .block-container {
            background: rgba(255, 255, 255, 0.85) !important;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(31,143,63,0.2);
            border: 2px solid #1f8f3f;
        }
    </style>
    ''', unsafe_allow_html=True)
    
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
    
    st.subheader('Preparation Steps & Tutorials')
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
    # Agriculture-themed background for Community page - supports light and dark mode
    st.markdown('''
    <style>
        /* Light Mode */
        .stApp {
            background: linear-gradient(135deg, rgba(225,250,225,0.7), rgba(195,240,195,0.7)),
                        url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1920&q=80') center/cover fixed;
        }
        .main .block-container {
            background: rgba(255, 255, 255, 0.85) !important;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(31,143,63,0.2);
            border: 2px solid #1f8f3f;
        }
    </style>
    ''', unsafe_allow_html=True)
    
    # Back button
    if st.button('← Back to Home', key='comm_back'):
        st.session_state['page'] = 'Home'
        st.rerun()
    
    # Initialize show_register state if not exists
    if 'show_register' not in st.session_state:
        st.session_state['show_register'] = False
    
    user = st.session_state.get('user')
    
    # If user is not logged in, show login/register form
    if not user:
        # Center the login/register box
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

