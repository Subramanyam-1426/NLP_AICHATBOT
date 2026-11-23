import streamlit as st


_LIGHT = {
    "app_bg": "#f5f7fb",
    "surface": "#ffffff",
    "surface_alt": "#eef2f8",
    "text": "#1b2434",
    "muted": "#667085",
    "border": "#dce3ee",
    "sidebar_start": "#111827",
    "sidebar_end": "#29245b",
    "sidebar_text": "#f7f8ff",
    "chat_user": "#e9e8ff",
    "chat_user_text": "#302b62",
    "chat_assistant": "#ffffff",
}

_DARK = {
    "app_bg": "#10131d",
    "surface": "#191e2b",
    "surface_alt": "#222a3a",
    "text": "#edf0f8",
    "muted": "#a3adc0",
    "border": "#30394c",
    "sidebar_start": "#0c1120",
    "sidebar_end": "#211b49",
    "sidebar_text": "#f7f8ff",
    "chat_user": "#2a2850",
    "chat_user_text": "#eeecff",
    "chat_assistant": "#191e2b",
}


def inject_theme(dark_mode: bool = False) -> None:
    """Inject the app's single shared light/dark design system."""
    colors = _DARK if dark_mode else _LIGHT
    tokens = "\n".join(f"  --{name.replace('_', '-')}: {value};" for name, value in colors.items())
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700&display=swap');

:root {{
{tokens}
  --accent: #5147d9;
  --accent-2: #7558e8;
  --accent-cyan: #1ba9b7;
  --accent-gradient: linear-gradient(115deg, #4b45d6 0%, #7655e7 58%, #20a7b5 100%);
  --positive: #16845b;
  --neutral: #667085;
  --negative: #cf4557;
  --shadow-soft: 0 10px 28px rgba(29, 40, 73, .08);
  --shadow-hover: 0 16px 36px rgba(29, 40, 73, .14);
  --radius-card: 16px;
  --radius-control: 11px;
}}

html, body, .stApp, [data-testid="stAppViewContainer"] {{
  background: var(--app-bg) !important;
  color: var(--text) !important;
  font-family: Inter, "Segoe UI", sans-serif !important;
}}
[data-testid="stAppViewBlockContainer"] {{
  max-width: 1320px;
  padding: 1.6rem clamp(1rem, 3.2vw, 3rem) 3rem !important;
}}
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stHeader"] {{ background: transparent !important; }}

h1, h2, h3, h4, h5, p, li, label, [data-testid="stMarkdownContainer"] {{
  color: var(--text);
}}
h1, h2, h3, h4 {{ letter-spacing: 0; }}
hr {{ border-color: var(--border) !important; }}
small, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
  color: var(--muted) !important;
}}

/* Sidebar and its accessible radio navigation */
section[data-testid="stSidebar"] {{
  background: linear-gradient(155deg, var(--sidebar-start), var(--sidebar-end)) !important;
  border-right: 1px solid rgba(255,255,255,.08);
}}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
  color: var(--sidebar-text) !important;
}}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
  color: #d5d5f2 !important;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 1rem);
}}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {{
  flex: 1;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] > label,
section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {{
  display: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {{
  display: flex;
  align-items: stretch !important;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div {{
  width: 100% !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] {{
  width: 100% !important;
}}
section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stRadio"]) {{
  width: 100% !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] {{
  position: relative;
  display: flex;
  align-self: stretch;
  align-items: center;
  width: 100% !important;
  flex: 0 0 100%;
  box-sizing: border-box;
  min-height: 42px;
  padding: 8px 12px !important;
  margin: 0 !important;
  border: 1px solid transparent;
  border-radius: 11px;
  background: rgba(255,255,255,.045);
  color: #ebeafd !important;
  transition: background .18s ease, border-color .18s ease, transform .18s ease;
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover {{
  background: rgba(255,255,255,.12);
  transform: translateX(2px);
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) {{
  background: linear-gradient(100deg, rgba(115,97,236,.34), rgba(46,184,197,.13));
  border-color: rgba(177,169,255,.36);
  box-shadow: inset 3px 0 0 #a99cff;
  color: #ffffff !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] input[type="radio"] {{
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  opacity: 0 !important;
  pointer-events: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] > div:first-child {{
  display: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {{
  display: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] > span:first-child {{
  display: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] {{
  color: inherit !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] p {{
  color: inherit !important;
  margin: 0 !important;
}}
.sidebar-footer {{
  display: grid;
  gap: 5px;
  margin-top: 22px;
  padding: 14px 12px;
  border-top: 1px solid rgba(255,255,255,.16);
  color: #ebeafd;
  font-size: .78rem;
}}
section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sidebar-footer) {{
  margin-top: auto;
}}

/* Surfaces, cards, metrics, dataframes, and expanders */
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stMetric"],
div[data-testid="stExpander"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-card) !important;
  box-shadow: var(--shadow-soft);
}}
div[data-testid="stMetric"] {{ padding: 14px 16px; }}
div[data-testid="stMetricLabel"] {{ color: var(--muted) !important; }}
div[data-testid="stMetricValue"] {{ color: var(--accent) !important; }}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary p {{ color: var(--text) !important; }}
div[data-testid="stDataFrame"] {{
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--surface);
  color-scheme: {"dark" if dark_mode else "light"};
}}
div[data-testid="stJson"], div[data-testid="stJson"] pre,
div[data-testid="stDataFrame"], [data-baseweb="popover"], [data-baseweb="menu"] {{
  color: var(--text) !important;
}}

/* Controls */
button[data-testid^="stBaseButton-"],
.stDownloadButton > button, [data-testid="stFormSubmitButton"] button {{
  min-height: 40px;
  border-radius: var(--radius-control) !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  font-weight: 550 !important;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease, background .18s ease;
}}
button[data-testid="stBaseButton-secondary"],
.stDownloadButton > button[data-testid="stBaseButton-secondary"] {{
  background: var(--surface-alt) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
}}
button[data-testid^="stBaseButton-"]:hover, .stDownloadButton > button:hover {{
  border-color: #8e87e7 !important;
  box-shadow: var(--shadow-soft);
}}
button[data-testid="stBaseButton-secondary"]:hover,
.stDownloadButton > button[data-testid="stBaseButton-secondary"]:hover {{
  background: var(--surface-alt) !important;
}}
button[data-testid^="stBaseButton-"]:focus-visible, .stDownloadButton > button:focus-visible,
input:focus-visible, textarea:focus-visible {{
  outline: 3px solid rgba(96, 84, 224, .35) !important;
  outline-offset: 2px;
}}
button[data-testid="stBaseButton-primary"],
button[kind="primary"],
[data-testid="stFormSubmitButton"] button {{
  background: var(--accent-gradient) !important;
  border-color: transparent !important;
  color: white !important;
  box-shadow: 0 7px 18px rgba(81,71,217,.23);
}}
input, textarea, [data-baseweb="select"] > div {{
  border-radius: var(--radius-control) !important;
  background-color: var(--surface) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}}
[data-baseweb="popover"], [data-baseweb="menu"] {{
  background: var(--surface) !important;
  color: var(--text) !important;
}}
[data-testid="stSelectbox"] [role="group"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
  background: var(--surface) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
}}
[data-testid="stSelectbox"] input {{
  background: var(--surface) !important;
  color: var(--text) !important;
}}
[data-testid="stFileUploader"] section {{
  background: var(--surface) !important;
  border: 1px dashed #8b86d9 !important;
  border-radius: 15px !important;
}}
.stTabs [data-baseweb="tab-list"] {{
  gap: 5px;
  background: var(--surface-alt);
  border-radius: 12px;
  padding: 5px;
  overflow-x: auto;
  flex-wrap: nowrap;
  scrollbar-width: thin;
}}
.stTabs [data-baseweb="tab"] {{
  flex: 0 0 auto;
  border-radius: 9px;
  color: var(--muted) !important;
  transition: background .18s ease, color .18s ease;
}}
.stTabs [aria-selected="true"] {{
  background: var(--surface) !important;
  color: var(--accent) !important;
  box-shadow: 0 2px 7px rgba(24,34,61,.08);
}}

/* Chat transcript */
div[data-testid="stChatMessage"] {{
  display: flex;
  gap: 10px;
  align-items: flex-start;
  width: 100%;
  margin: 8px 0 !important;
  background: transparent !important;
  animation: message-enter .32s cubic-bezier(.22, .75, .25, 1) both;
}}
div[data-testid="stChatMessage"] [data-testid^="stChatMessageAvatar"] {{
  display: grid;
  place-items: center;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: 11px;
  background: var(--surface);
}}
div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarCustom"] [data-testid="stIconMaterial"] {{
  color: var(--text) !important;
}}
div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {{
  flex: 0 1 auto !important;
  width: fit-content !important;
  margin: 0 !important;
  min-width: 0;
  max-width: 78%;
  padding: 12px 16px !important;
  border: 1px solid var(--border) !important;
  border-radius: 18px 18px 18px 4px !important;
  background: var(--chat-assistant) !important;
  color: var(--text) !important;
  line-height: 1.62;
  overflow-wrap: anywhere;
  box-shadow: 0 4px 14px rgba(27,36,62,.045);
}}
div[class*="st-key-msg_user_"] [data-testid="stChatMessage"] {{
  position: relative;
  justify-content: flex-end;
  box-sizing: border-box;
  padding-right: 44px;
}}
div[class*="st-key-msg_user_"] [data-testid="stChatMessageAvatarCustom"] {{
  position: absolute;
  top: 0;
  right: 0;
}}
div[class*="st-key-msg_user_"] [data-testid="stChatMessageContent"] {{
  max-width: 70%;
  margin-left: auto !important;
  margin-right: 0 !important;
  border: 0 !important;
  border-radius: 18px 18px 4px 18px !important;
  background: var(--accent-gradient) !important;
  color: #fff !important;
  box-shadow: 0 7px 18px rgba(81,71,217,.2);
}}
div[class*="st-key-msg_user_"] [data-testid="stChatMessageContent"] p {{
  color: #fff !important;
}}
div[class*="st-key-msg_bot_"] [data-testid="stChatMessageContent"] {{
  max-width: 78%;
}}
div[class*="st-key-msg_user_"] [data-testid="stChatMessage"],
div[class*="st-key-msg_bot_"] [data-testid="stChatMessage"] {{
  background: transparent !important;
}}
div[class*="st-key-meta_bot_"] [data-testid="stHorizontalBlock"] {{
  margin-left: 44px;
  gap: 8px !important;
}}
div[class*="st-key-meta_bot_"] .stButton > button {{
  min-height: 32px;
  padding: 4px 9px !important;
  border-radius: 9px !important;
  box-shadow: none !important;
}}
div[class*="st-key-meta_bot_"] .stButton > button[data-testid="stBaseButton-secondary"] {{
  background: transparent !important;
}}
div[class*="st-key-meta_bot_"] .stButton > button:has([data-testid="stIconMaterial"]) {{
  min-width: 36px;
  padding-inline: 0 !important;
}}
div[class*="st-key-msg_user_"] [data-testid="stVerticalBlock"],
div[class*="st-key-msg_bot_"] [data-testid="stVerticalBlock"] {{
  gap: 0;
}}
div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p {{
  color: inherit !important;
  line-height: 1.62;
  margin-bottom: .4rem;
}}
div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p:last-child {{ margin-bottom: 0; }}
[data-testid="stChatInput"] > div {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 18px !important;
  box-shadow: 0 12px 32px rgba(26,35,63,.13) !important;
  padding: 5px 8px !important;
}}
[data-testid="stBottomBlockContainer"] > div {{
  background: var(--app-bg) !important;
}}
[data-testid="stChatInput"]:focus-within > div {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(96,84,224,.14), 0 12px 32px rgba(26,35,63,.13) !important;
}}
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] textarea {{
  border: 0 !important;
  outline: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  line-height: 1.55;
}}
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] textarea:focus-visible {{
  outline: 0 !important;
  box-shadow: none !important;
}}
[data-testid="stChatInputSubmitButton"] {{
  border: 0 !important;
  border-radius: 12px !important;
  background: var(--accent-gradient) !important;
  color: #fff !important;
}}
[data-testid="stChatInputSubmitButton"]:focus {{
  outline: 0 !important;
}}
[data-testid="stProgress"] > div {{
  height: 5px;
  border-radius: 999px;
  background: var(--surface-alt) !important;
}}
[data-testid="stProgress"] > div > div {{
  border-radius: inherit;
  background: var(--accent-gradient) !important;
}}
.doc-snippet {{
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent-cyan);
  border-radius: 11px;
  background: var(--surface-alt);
  color: var(--text);
  line-height: 1.7;
  overflow-wrap: anywhere;
}}
.doc-snippet mark {{
  padding: 0 2px;
  border-radius: 3px;
  background: rgba(236, 194, 96, .36);
  color: inherit;
}}
.typing-indicator {{ display: inline-flex; gap: 6px; align-items: center; min-height: 20px; padding: 4px 2px; }}
.typing-indicator span {{
  width: 7px; height: 7px; border-radius: 50%; background: var(--accent);
  box-shadow: 0 0 8px rgba(81,71,217,.28);
  animation: typing-pulse 1.05s cubic-bezier(.4, 0, .2, 1) infinite;
}}
.typing-indicator span:nth-child(2) {{ animation-delay: .16s; }}
.typing-indicator span:nth-child(3) {{ animation-delay: .32s; }}
.typing-indicator .typing-label {{
  margin-left: 4px; color: var(--muted); font-size: .83rem; font-weight: 500;
  letter-spacing: .01em;
}}
.confidence-track {{ height: 4px; border-radius: 99px; background: var(--surface-alt); overflow: hidden; }}
.confidence-fill {{ height: 100%; border-radius: inherit; background: var(--accent-gradient); }}
.token-chip {{
  display: inline-flex; margin: 3px 4px 3px 0; padding: 4px 9px;
  border: 1px solid var(--border); border-radius: 999px;
  background: var(--surface-alt); color: var(--text); font-size: .85rem;
}}
.hero-title {{
  background: var(--accent-gradient); background-clip: text; color: transparent !important;
}}
.feature-card {{ min-height: 178px; }}
.empty-state {{ text-align: center; padding: 18px 12px 12px; }}
.chart-card {{ border-radius: var(--radius-card); }}
.empty-state h3 {{ margin: 8px 0 4px; }}
.empty-state p {{ color: var(--muted); margin: 0; }}
.sentence-list {{
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}}
.sentence-list li {{
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 11px;
  background: var(--surface-alt);
}}
.sentence-number {{
  display: inline-grid;
  flex: 0 0 24px;
  width: 24px;
  height: 24px;
  place-items: center;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-size: .8rem;
}}
.training-stepper {{
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 1rem 0 1.4rem;
}}
.training-step {{
  display: flex;
  flex: 1;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  color: var(--muted);
}}
.training-step span {{
  display: grid;
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 50%;
  background: var(--surface-alt);
  color: var(--muted);
  font-weight: 700;
}}
.training-step.active {{
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 9%, var(--surface));
  color: var(--text);
}}
.training-step.active span,
.training-step.complete span {{
  background: var(--accent-gradient);
  color: #fff;
}}
.training-step.complete {{
  border-color: color-mix(in srgb, var(--accent) 35%, var(--border));
}}
div[class*="st-key-home_card_"] [data-testid="stVerticalBlockBorderWrapper"] {{
  min-height: 206px;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}}
div[class*="st-key-home_card_"] [data-testid="stVerticalBlockBorderWrapper"]:hover {{
  border-color: color-mix(in srgb, var(--accent) 30%, var(--border)) !important;
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}}
div[class*="st-key-home_card_"] [data-testid="stVerticalBlock"] {{
  height: 100%;
}}
div[class*="st-key-home_card_"] [data-testid="stButton"] {{
  margin-top: auto;
}}
div[class*="st-key-home_stat_"] [data-testid="stVerticalBlockBorderWrapper"] {{
  padding: 10px 14px;
}}
div[class*="st-key-home_stat_"] [data-testid="stMetric"] {{
  padding: 3px 0 !important;
  border: 0 !important;
  background: transparent !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}}
div[class*="st-key-home_stat_"] [data-testid="stMetricValue"] {{
  font-size: 1.45rem;
}}
div[class*="st-key-analytics_chart_"] [data-testid="stVerticalBlockBorderWrapper"] {{
  min-height: 390px;
}}
.page-title-row {{ margin: .35rem 0 1.15rem; }}
@keyframes message-enter {{
  0% {{ opacity: 0; transform: translateY(10px) scale(.985); }}
  100% {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes typing-pulse {{
  0%, 80%, 100% {{ opacity: .45; transform: translateY(0) scale(.82); }}
  40% {{ opacity: 1; transform: translateY(-3px) scale(1.08); }}
}}

@media (max-width: 760px) {{
  [data-testid="stAppViewBlockContainer"] {{ padding: 1rem .75rem 2rem !important; }}
  div[class*="st-key-msg_user_"] [data-testid="stChatMessageContent"] {{ max-width: 70%; padding: 10px 12px !important; }}
  div[class*="st-key-msg_bot_"] [data-testid="stChatMessageContent"] {{ max-width: 78%; padding: 10px 12px !important; }}
  div[class*="st-key-meta_bot_"] [data-testid="stHorizontalBlock"] {{ margin-left: 40px; }}
  .stTabs [data-baseweb="tab-list"] {{ max-width: 100%; }}
  section[data-testid="stSidebar"] {{ min-width: 16rem; }}
  div[class*="st-key-home_card_"] [data-testid="stVerticalBlockBorderWrapper"] {{ min-height: 190px; }}
  .training-stepper {{ gap: 6px; }}
  .training-step {{ justify-content: center; padding: 8px 6px; }}
  .training-step strong {{ font-size: .8rem; }}
}}
section[data-testid="stSidebar"] [class*="st-key-history_chat_"] button[data-testid^="stBaseButton-"] {{
  background: rgba(255,255,255,.09) !important;
  border-color: rgba(255,255,255,.16) !important;
  color: #f7f8ff !important;
}}
section[data-testid="stSidebar"] [class*="st-key-history_chat_"] button[data-testid^="stBaseButton-"] p {{
  color: #f7f8ff !important;
}}
section[data-testid="stSidebar"] [class*="st-key-history_chat_active_"] button[data-testid^="stBaseButton-"] {{
  background: rgba(132,119,255,.28) !important;
  border-color: rgba(197,190,255,.48) !important;
  color: #fff !important;
}}
section[data-testid="stSidebar"] [class*="st-key-history_chat_active_"] button[data-testid^="stBaseButton-"] p {{
  color: #fff !important;
}}
section[data-testid="stSidebar"] [data-testid="stTextInput"] input {{
  background: rgba(255,255,255,.09) !important;
  border-color: rgba(255,255,255,.18) !important;
  color: #fff !important;
}}
section[data-testid="stSidebar"] [data-testid="stTextInput"] input::placeholder {{
  color: rgba(255,255,255,.55) !important;
}}
section[data-testid="stSidebar"] [class*="st-key-history_chat_"] button[data-testid^="stBaseButton-"] {{
  transition: transform .18s cubic-bezier(.2, .75, .25, 1),
              background-color .18s ease, border-color .18s ease, box-shadow .18s ease;
  will-change: transform;
}}
section[data-testid="stSidebar"] [class*="st-key-history_chat_"] button[data-testid^="stBaseButton-"]:hover {{
  transform: translateX(3px);
  background: rgba(255,255,255,.17) !important;
  border-color: rgba(197,190,255,.48) !important;
  box-shadow: 0 5px 16px rgba(5,8,20,.2) !important;
}}
section[data-testid="stSidebar"] [class*="st-key-history_chat_active_"] button[data-testid^="stBaseButton-"]:hover {{
  background: rgba(146,132,255,.38) !important;
  border-color: rgba(213,208,255,.68) !important;
}}
@media (prefers-reduced-motion: reduce) {{
  div[data-testid="stChatMessage"] {{ animation: none !important; }}
  .typing-indicator span {{ animation: none !important; opacity: .8; transform: none; }}
  section[data-testid="stSidebar"] [class*="st-key-history_chat_"] button[data-testid^="stBaseButton-"] {{
    transition: none !important; transform: none !important; will-change: auto;
  }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_page_header(title: str, icon: str, subtitle: str) -> None:
    """Render the shared title and subtitle used by all workspace pages."""
    with st.container(key="page_header"):
        st.title(title, icon=f":material/{icon}:")
        st.caption(subtitle)


def apply_plotly_theme(figure, dark_mode: bool | None = None):
    """Apply the active app palette to a Plotly figure."""
    if dark_mode is None:
        dark_mode = st.session_state.get("dark_mode", False)
    colors = _DARK if dark_mode else _LIGHT
    figure.update_layout(
        template="plotly_dark" if dark_mode else "plotly_white",
        paper_bgcolor=colors["surface"],
        plot_bgcolor=colors["surface"],
        font=dict(color=colors["text"]),
        colorway=(
            ["#a99cff", "#55c3cc", "#edb66d", "#e56b7a", "#45b88e", "#be9bec"]
            if dark_mode
            else ["#5147d9", "#20a7b5", "#e39b44", "#cf4557", "#16845b", "#8a63d2"]
        ),
    )
    figure.update_xaxes(
        gridcolor=colors["border"],
        linecolor=colors["border"],
        zerolinecolor=colors["border"],
        tickfont_color=colors["muted"],
        title_font_color=colors["muted"],
    )
    figure.update_yaxes(
        gridcolor=colors["border"],
        linecolor=colors["border"],
        zerolinecolor=colors["border"],
        tickfont_color=colors["muted"],
        title_font_color=colors["muted"],
    )
    return figure
