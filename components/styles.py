"""CSS styles for the VAPI Assistant Manager app."""

import streamlit as st


def inject_custom_css():
    """Inject custom CSS for Skit.ai branding."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&display=swap');

    /* Apply Manrope font to all elements */
    * {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }

    /* Grayish black background */
    .stApp {
        background: #1a1a1a;
    }

    /* Header with logo */
    .main-header {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        position: relative;
    }

    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%);
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .logo-img {
        height: 45px;
        width: auto;
        object-fit: contain;
        display: block;
    }

    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: #1a1a1a;
        border-radius: 8px;
    }

    /* Title styling with brand colors */
    h1 {
        color: #ffffff;
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    h2, h3 {
        color: #ffffff;
        font-weight: 600;
    }

    /* Text color for readability on dark background */
    p, label, .stMarkdown {
        color: #e5e7eb;
    }

    /* Primary button styling - brand blue */
    .stButton > button {
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%) !important;
        color: white !important;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        border: none;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #010066 0%, #2D83C5 100%) !important;
        box-shadow: 0 2px 8px rgba(1, 0, 102, 0.3);
        color: white !important;
    }

    /* Secondary button styling */
    button[kind="secondary"] {
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%) !important;
        color: white !important;
        border: none;
    }

    button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #010066 0%, #2D83C5 100%) !important;
        color: white !important;
    }

    /* All buttons should have white text */
    button {
        color: white !important;
    }

    /* Ensure all button text is white */
    .stButton > button,
    button[type="button"],
    button[type="submit"],
    .stFormSubmitButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] {
        color: white !important;
    }

    button[type="button"] {
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%) !important;
        color: white !important;
    }

    button[type="button"]:hover {
        background: linear-gradient(135deg, #010066 0%, #2D83C5 100%) !important;
        color: white !important;
    }

    /* Ensure button text stays white on hover */
    .stButton > button:hover,
    button[type="button"]:hover,
    button[type="submit"]:hover,
    .stFormSubmitButton > button:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        color: white !important;
    }

    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 1px solid #4b5563;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
        color: #ffffff !important;
        background-color: #2d2d2d !important;
    }

    /* Disabled textarea styling - ensure text is visible */
    .stTextArea > div > div > textarea:disabled {
        color: #e5e7eb !important;
        background-color: #2d2d2d !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #e5e7eb !important;
    }

    /* Fix textarea label and content overlap */
    .stTextArea label {
        position: relative !important;
        z-index: 1 !important;
        display: block !important;
        margin-bottom: 0.5rem !important;
        padding: 0 !important;
        line-height: 1.4 !important;
    }

    .stTextArea > div {
        position: relative !important;
        overflow: visible !important;
    }

    .stTextArea > div > div {
        position: relative !important;
        overflow: visible !important;
    }

    .stTextArea > div > div > textarea {
        position: relative !important;
        z-index: 1 !important;
        background-color: #2d2d2d !important;
        padding: 0.5rem 0.75rem !important;
        line-height: 1.5 !important;
        overflow-y: auto !important;
    }

    /* Hide any placeholder or key text that might show through */
    .stTextArea > div > div > textarea::placeholder {
        opacity: 0 !important;
        color: transparent !important;
    }

    /* Ensure no text overlap in disabled textareas */
    .stTextArea > div > div > textarea:disabled {
        position: relative !important;
        z-index: 1 !important;
        background-color: #2d2d2d !important;
        -webkit-text-fill-color: #e5e7eb !important;
        color: #e5e7eb !important;
        opacity: 1 !important;
        padding: 0.5rem 0.75rem !important;
        line-height: 1.5 !important;
    }

    /* Fix for overlapping labels in expander context */
    div[data-testid="stTextArea"] label,
    div[data-testid="stTextArea"] > div > label,
    div[data-testid="stTextArea"] > div > div > label {
        position: relative !important;
        z-index: 2 !important;
        background-color: transparent !important;
        display: block !important;
        margin-bottom: 0.5rem !important;
    }

    /* Additional fixes - prevent any overlay text */
    .stTextArea [class*="label"],
    .stTextArea [class*="Label"] {
        position: relative !important;
        z-index: 2 !important;
        background: transparent !important;
        pointer-events: none !important;
    }

    /* Ensure textarea content is on top */
    .stTextArea textarea {
        position: relative !important;
        z-index: 3 !important;
        background: #2d2d2d !important;
    }

    /* Expander styling */
    .stExpander {
        isolation: isolate !important;
        position: relative !important;
        clear: both !important;
        overflow: visible !important;
    }

    .stExpander summary {
        padding: 0.75rem 0 !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
        clear: both !important;
    }

    .stExpander > div,
    .stExpander details,
    .stExpander [data-testid="stExpanderDetails"] {
        isolation: isolate !important;
        position: relative !important;
        z-index: 1 !important;
        clear: both !important;
        overflow: visible !important;
        padding-top: 0.5rem !important;
    }

    .stExpander * {
        max-width: 100% !important;
    }

    .stExpander label {
        display: block !important;
        position: relative !important;
        z-index: auto !important;
        margin-bottom: 0.5rem !important;
        clear: both !important;
        width: 100% !important;
        line-height: 1.5 !important;
    }

    .stExpander .stTextArea,
    .stExpander .stTextInput,
    .stExpander .stSelectbox {
        margin-top: 0.5rem !important;
        margin-bottom: 0.75rem !important;
        display: block !important;
        width: 100% !important;
        clear: both !important;
    }

    .stTextArea::before,
    .stTextArea::after,
    .stTextArea > div::before,
    .stTextArea > div::after {
        display: none !important;
        content: none !important;
    }

    /* Hide keyboard hints and debug text */
    [class*="keyboard"],
    [id*="keyboard"],
    [data-keyboard],
    [class*="hint"],
    [class*="debug"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }

    [aria-label]::before,
    [aria-label]::after,
    [title]::before,
    [title]::after {
        content: none !important;
        display: none !important;
    }

    [data-testid]::before,
    [data-testid]::after {
        content: none !important;
        display: none !important;
    }

    /* Hide expander arrow icon */
    [data-testid="stIconMaterial"],
    .stExpander summary span[data-testid="stIconMaterial"],
    .stExpander summary [class*="Material"],
    .stExpander summary [class*="arrow"],
    span[data-testid="stIconMaterial"][translate="no"],
    .st-emotion-cache-zkd0x0,
    .ejhh0er0,
    span[color="inherit"][data-testid="stIconMaterial"],
    .stExpander [translate="no"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    .stExpander summary,
    .stExpander [data-testid="stExpander"] summary {
        z-index: 0 !important;
        position: relative !important;
    }

    .stExpander [data-testid="stExpanderDetails"],
    .stExpander details > div {
        position: relative !important;
        z-index: 100 !important;
        isolation: isolate !important;
        background: #1a1a1a !important;
    }

    .stExpander [data-testid="stExpanderDetails"] *,
    .stExpander details > div * {
        position: relative !important;
        z-index: 1 !important;
    }

    .stTextArea > div > div > textarea,
    .stTextArea > div > div > textarea:disabled {
        z-index: 10 !important;
        position: relative !important;
        background-color: #2d2d2d !important;
        isolation: isolate !important;
    }

    .stTextArea,
    .stTextArea > div,
    .stTextArea > div > div {
        z-index: 5 !important;
        position: relative !important;
    }

    .stExpander [data-testid="stExpanderDetails"] .stTextArea {
        position: relative !important;
        z-index: 2 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #2D83C5;
        box-shadow: 0 0 0 3px rgba(45, 131, 197, 0.3);
        color: #ffffff !important;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: #1a1a1a;
    }

    /* Links */
    a {
        color: #2D83C5;
    }

    a:hover {
        color: #010066;
    }

    /* Success/Error messages */
    .stSuccess {
        background-color: #1a1a1a !important;
        border: 1px solid #10b981;
        color: #e5e7eb !important;
    }

    .stSuccess * {
        color: #e5e7eb !important;
    }

    .stError {
        background-color: #1a1a1a !important;
        border: 1px solid #ef4444;
        color: #e5e7eb !important;
    }

    .stError * {
        color: #e5e7eb !important;
    }

    .stInfo {
        background-color: #1a1a1a !important;
        border: 1px solid #2D83C5;
        color: #e5e7eb !important;
    }

    .stInfo * {
        color: #e5e7eb !important;
    }

    .stWarning {
        background-color: #1a1a1a !important;
        border: 1px solid #f59e0b;
        color: #e5e7eb !important;
    }

    .stWarning * {
        color: #e5e7eb !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        color: #ffffff;
        font-weight: 600;
    }

    /* Sidebar text */
    .css-1d391kg, .css-1d391kg p, .css-1d391kg label {
        color: #e5e7eb;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: transparent !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #e5e7eb;
        font-weight: 500;
        background-color: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        color: #2D83C5;
        background-color: transparent !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        background-color: transparent !important;
    }

    /* Ensure all text is light for dark background */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown ul, .stMarkdown ol {
        color: #e5e7eb !important;
    }

    /* Text input and textarea styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        color: #ffffff !important;
        background-color: #2d2d2d !important;
    }

    /* Selectbox styling */
    .stSelectbox > div > div > select {
        color: #ffffff !important;
        background-color: #2d2d2d !important;
    }

    /* Expander content */
    .streamlit-expanderContent {
        background-color: #1a1a1a !important;
        color: #e5e7eb !important;
        line-height: 1.6 !important;
        overflow: visible !important;
        clear: both !important;
    }

    .streamlit-expanderContent > *,
    .stExpander > div > *,
    [data-testid="stExpanderDetails"] > * {
        line-height: 1.6 !important;
        margin-bottom: 0.75rem !important;
        display: block !important;
        width: 100% !important;
        box-sizing: border-box !important;
        overflow: visible !important;
    }

    /* All Streamlit text elements */
    .element-container, .stText, .stMarkdownContainer {
        color: #e5e7eb !important;
    }

    /* Text within boxes/containers */
    .stTextArea textarea,
    .stTextInput input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {
        color: #ffffff !important;
    }

    /* Expander content */
    .streamlit-expanderContent * {
        color: #e5e7eb !important;
    }

    /* Form submit buttons - use gradient */
    .stFormSubmitButton > button,
    button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%) !important;
        color: white !important;
    }

    .stFormSubmitButton > button:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(135deg, #010066 0%, #2D83C5 100%) !important;
        color: white !important;
    }

    /* Remove Streamlit default styling */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)
