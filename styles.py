"""
Premium CSS styles for the FX Trading Dashboard.
Separated for maintainability and clean code structure.
"""

THEME_CSS = """
<style>
    /* ── Import premium font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Base ── */
    .stApp {
        background-color: #080b12;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Top bar ── */
    .top-bar {
        background: linear-gradient(180deg, #0d1117 0%, #080b12 100%);
        border-bottom: 1px solid rgba(56, 189, 248, 0.08);
        padding: 0.8rem 0 0.6rem 0;
        margin-bottom: 1rem;
    }
    .top-bar-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #e2e8f0;
        letter-spacing: -0.02em;
    }
    .top-bar-subtitle {
        font-size: 0.7rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-top: 0.1rem;
    }
    .top-bar-ts {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #475569;
    }

    /* ── Alert bar ── */
    .alert-bar {
        display: flex;
        gap: 0.5rem;
        overflow-x: auto;
        padding: 0.4rem 0;
        margin-bottom: 0.8rem;
        scrollbar-width: thin;
    }
    .alert-card {
        flex-shrink: 0;
        min-width: 280px;
        border-radius: 8px;
        padding: 0.65rem 0.9rem;
        font-size: 0.8rem;
        line-height: 1.4;
    }
    .alert-bullish {
        background: rgba(34, 197, 94, 0.06);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-left: 3px solid #22c55e;
    }
    .alert-bearish {
        background: rgba(239, 68, 68, 0.06);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-left: 3px solid #ef4444;
    }
    .alert-caution {
        background: rgba(245, 158, 11, 0.06);
        border: 1px solid rgba(245, 158, 11, 0.2);
        border-left: 3px solid #f59e0b;
    }
    .alert-level {
        font-weight: 600;
        color: #e2e8f0;
    }
    .alert-detail {
        color: #94a3b8;
        font-size: 0.75rem;
    }
    .alert-time {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        color: #64748b;
    }

    /* ── Summary cards ── */
    .summary-card {
        background: linear-gradient(135deg, #0f1729 0%, #111827 100%);
        border: 1px solid rgba(148, 163, 184, 0.08);
        border-radius: 12px;
        padding: 1.1rem 1.2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .summary-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.15), transparent);
    }
    .summary-label {
        font-size: 0.68rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.45rem;
    }
    .summary-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.7rem;
        font-weight: 700;
        color: #f1f5f9;
        letter-spacing: -0.02em;
    }
    .summary-value-sm {
        font-size: 1.15rem;
    }

    /* ── Signal colors ── */
    .sig-long { color: #22c55e !important; }
    .sig-short { color: #ef4444 !important; }
    .sig-stay { color: #f59e0b !important; }

    /* ── Confidence gauge ── */
    .gauge-track {
        width: 100%;
        height: 4px;
        background: rgba(148, 163, 184, 0.08);
        border-radius: 2px;
        margin-top: 0.7rem;
        overflow: hidden;
    }
    .gauge-bar {
        height: 100%;
        border-radius: 2px;
        transition: width 0.5s ease;
    }

    /* ── Section headers ── */
    .sec-header {
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding-bottom: 0.45rem;
        margin-bottom: 0.7rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.06);
    }

    /* ── Panels ── */
    .panel {
        background: #0f1729;
        border: 1px solid rgba(148, 163, 184, 0.06);
        border-radius: 10px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.6rem;
    }

    /* ── Explanation box ── */
    .explanation-box {
        background: linear-gradient(135deg, #0c1222 0%, #0f172a 100%);
        border: 1px solid rgba(56, 189, 248, 0.1);
        border-left: 3px solid #38bdf8;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        white-space: pre-wrap;
        color: #94a3b8;
        line-height: 1.7;
    }
    .explanation-signal {
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
    }
    .explanation-reason {
        padding-left: 0.4rem;
        border-left: 2px solid rgba(148, 163, 184, 0.1);
        margin: 0.15rem 0 0.15rem 0.2rem;
    }

    /* ── Score breakdown ── */
    .score-row {
        display: flex;
        align-items: center;
        padding: 0.35rem 0;
        gap: 0.6rem;
    }
    .score-row-final {
        border-top: 1px solid rgba(148, 163, 184, 0.1);
        padding-top: 0.55rem;
        margin-top: 0.3rem;
    }
    .score-name {
        font-size: 0.78rem;
        color: #94a3b8;
        flex: 1;
    }
    .score-bar-track {
        width: 80px;
        height: 4px;
        background: rgba(148, 163, 184, 0.06);
        border-radius: 2px;
        overflow: hidden;
        position: relative;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 2px;
        position: absolute;
    }
    .score-bar-fill-pos {
        left: 50%;
        background: #22c55e;
    }
    .score-bar-fill-neg {
        right: 50%;
        background: #ef4444;
    }
    .score-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        font-weight: 600;
        min-width: 52px;
        text-align: right;
    }
    .score-pos { color: #22c55e; }
    .score-neg { color: #ef4444; }
    .score-zero { color: #475569; }

    /* ── Key levels table ── */
    .level-row {
        display: flex;
        align-items: center;
        padding: 0.4rem 0;
        border-bottom: 1px solid rgba(148, 163, 184, 0.04);
        font-size: 0.8rem;
    }
    .level-name {
        flex: 1;
        color: #cbd5e1;
        font-weight: 500;
    }
    .level-price {
        font-family: 'JetBrains Mono', monospace;
        color: #e2e8f0;
        min-width: 80px;
        text-align: right;
        font-size: 0.78rem;
    }
    .level-dist {
        font-family: 'JetBrains Mono', monospace;
        min-width: 65px;
        text-align: right;
        font-size: 0.75rem;
    }
    .level-status {
        font-size: 0.7rem;
        font-weight: 600;
        min-width: 80px;
        text-align: right;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .status-untouched { color: #475569; }
    .status-breached { color: #ef4444; }
    .status-reclaimed { color: #22c55e; }
    .status-resistance { color: #f59e0b; }
    .status-support { color: #38bdf8; }

    /* ── Session levels ── */
    .session-card {
        background: #0f1729;
        border: 1px solid rgba(148, 163, 184, 0.06);
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        margin-bottom: 0.45rem;
    }
    .session-name {
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .session-range {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #94a3b8;
    }
    .session-vals {
        display: flex;
        justify-content: space-between;
        margin-top: 0.3rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    }

    /* ── Breach log ── */
    .breach-row {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.45rem 0;
        border-bottom: 1px solid rgba(148, 163, 184, 0.04);
        font-size: 0.78rem;
    }
    .breach-time {
        font-family: 'JetBrains Mono', monospace;
        color: #64748b;
        font-size: 0.72rem;
        min-width: 90px;
    }
    .breach-level {
        color: #cbd5e1;
        font-weight: 500;
        flex: 1;
    }
    .breach-tag {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .tag-breakout {
        background: rgba(34, 197, 94, 0.1);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.2);
    }
    .tag-sweep {
        background: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .tag-reclaim {
        background: rgba(56, 189, 248, 0.1);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.2);
    }
    .tag-falsebreak {
        background: rgba(148, 163, 184, 0.06);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.12);
    }

    /* ── Regime & market conditions ── */
    .regime-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.35rem 0;
        font-size: 0.82rem;
    }
    .regime-label { color: #94a3b8; }
    .regime-val { color: #e2e8f0; font-weight: 600; }

    /* ── News panel ── */
    .news-risk-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .badge-clear { background: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.2); }
    .badge-caution { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); }
    .badge-block { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }

    .news-item {
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(148, 163, 184, 0.04);
    }
    .news-headline {
        font-size: 0.8rem;
        color: #cbd5e1;
    }
    .news-meta {
        font-size: 0.7rem;
        color: #475569;
        margin-top: 0.1rem;
    }

    /* ── Sweep events ── */
    .sweep-card {
        background: rgba(168, 85, 247, 0.04);
        border: 1px solid rgba(168, 85, 247, 0.12);
        border-left: 3px solid #a855f7;
        border-radius: 0 8px 8px 0;
        padding: 0.55rem 0.8rem;
        margin-bottom: 0.4rem;
        font-size: 0.8rem;
    }
    .sweep-name { font-weight: 600; color: #e2e8f0; }
    .sweep-detail { color: #94a3b8; font-size: 0.75rem; margin-top: 0.15rem; }
    .sweep-time {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        color: #64748b;
    }

    /* ── Indicator table ── */
    .ind-row {
        display: flex;
        justify-content: space-between;
        padding: 0.3rem 0;
        border-bottom: 1px solid rgba(148, 163, 184, 0.04);
        font-size: 0.8rem;
    }
    .ind-name { color: #94a3b8; }
    .ind-val {
        font-family: 'JetBrains Mono', monospace;
        color: #e2e8f0;
        font-weight: 500;
    }

    /* ── Debug ── */
    .debug-panel {
        background: #0d1117;
        border: 1px solid rgba(148, 163, 184, 0.08);
        border-radius: 8px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #64748b;
        line-height: 1.6;
    }

    /* ── Footer ── */
    .dash-footer {
        text-align: center;
        color: #334155;
        font-size: 0.68rem;
        margin-top: 1.5rem;
        padding: 0.8rem 0;
        border-top: 1px solid rgba(148, 163, 184, 0.04);
    }

    /* ── Override Streamlit defaults for cleaner look ── */
    .stSelectbox > div > div { background-color: #111827; border-color: rgba(148, 163, 184, 0.1); }
    .stButton > button {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid rgba(56, 189, 248, 0.15);
        color: #94a3b8;
        font-weight: 500;
        border-radius: 6px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: rgba(56, 189, 248, 0.3);
        color: #e2e8f0;
    }

    div[data-testid="stExpander"] {
        background: #0f1729;
        border: 1px solid rgba(148, 163, 184, 0.06);
        border-radius: 8px;
    }
</style>
"""
