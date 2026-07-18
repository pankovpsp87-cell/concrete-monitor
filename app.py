# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime
import database

DB_NAME = os.path.join(os.path.dirname(__file__), "prices.db")

# ── Константи ──────────────────────────────────────────────────────────────
COMPANIES = [
    "Бетон Мікс", "Beton-X", "Panbeton", "Budservis", "IFCEM",
    "ZGBK Etalon", "Beton-IF", "Krubeton",
    "Моноліт Буд Інвест", "Титан Бетон Захід"
]

GRADES = [
    "М100", "М150", "М200", "М250",
    "М300", "М350", "М400", "М450", "М500"
]

MANUAL_SOURCE = "(вручну)"

# ── Ініціалізація БД ────────────────────────────────────────────────────────
database.init_db()

# ── Допоміжні функції ───────────────────────────────────────────────────────
def get_data():
    return database.get_prices()

def delete_price(row_id):
    database.delete_price(row_id)

# ── Конфігурація сторінки ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Моніторинг цін на бетон | Івано-Франківськ",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Стилі ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 12px;
    }
    .metric-card .value { font-size: 2rem; font-weight: 700; }
    .metric-card .label { font-size: 0.85rem; opacity: 0.75; margin-top: 4px; }
    
    .manual-badge {
        background: #ff6b35;
        color: white;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .auto-badge {
        background: #28a745;
        color: white;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 12px 16px;
        color: #155724;
        margin: 8px 0;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2744 0%, #1a3d6e 100%);
    }
    div[data-testid="stSidebar"] * { color: white !important; }
    div[data-testid="stSidebar"] .stSelectbox label,
    div[data-testid="stSidebar"] .stNumberInput label { color: #adc8e6 !important; }
</style>
""", unsafe_allow_html=True)

# ── Авторизація ─────────────────────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "beton")
is_admin = False

# ── Сайдбар ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️ Бетон Мікс")
    st.markdown("### Моніторинг цін конкурентів")
    st.markdown("---")
    
    # Введення пароля для доступу до функцій адміністрування
    pwd_input = st.text_input("🔑 Пароль адміністратора", type="password", placeholder="Введіть для редагування")
    if pwd_input == ADMIN_PASSWORD:
        is_admin = True
        st.success("🔓 Режим адміністратора")
    elif pwd_input:
        st.error("❌ Невірний пароль")

    if is_admin:
        st.markdown("### ✏️ Додати ціну вручну")
        with st.form("manual_price_form", clear_on_submit=True):
            company_sel = st.selectbox("🏢 Компанія", COMPANIES)
            grade_sel   = st.selectbox("🪨 Марка бетону", GRADES)
            price_sel   = st.number_input(
                "💰 Ціна (грн/м³)", 
                min_value=500, max_value=30000, 
                value=4000, step=50
            )
            note_sel = st.text_input("📝 Примітка (необов'язково)", 
                                      placeholder="напр. «по телефону 15.07»")
            date_sel = st.date_input("📅 Дата", value=datetime.date.today())
            
            submitted = st.form_submit_button("💾 Зберегти", use_container_width=True)
            
            if submitted:
                product_name = f"Tovarnyi beton {grade_sel}"
                if note_sel:
                    product_name += f" ({note_sel})"
                
                ts = datetime.datetime.combine(date_sel, datetime.time(12, 0)).isoformat()
                database.insert_price(company_sel, MANUAL_SOURCE, product_name, grade_sel, price_sel, ts)
                st.success(f"✅ Збережено: {company_sel} | {grade_sel} | {price_sel:,} ₴")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔄 Оновити дані")
        scraper_path = os.path.join(os.path.dirname(__file__), "scraper.py")
        if os.path.exists(scraper_path):
            if st.button("▶ Запустити парсер", use_container_width=True):
                import subprocess, sys
                result = subprocess.run(
                    [sys.executable, "scraper.py"],
                    cwd=os.path.dirname(__file__),
                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                )
                if result.returncode == 0:
                    st.success("Парсер завершив роботу!")
                else:
                    st.error(f"Помилка: {result.stderr[-500:]}")
                st.rerun()
        else:
            st.caption("ℹ️ Скрипт автоматичного парсингу виконується локально на вашому ПК щопонеділка і передає дані в хмару.")
    else:
        st.info("ℹ️ Дашборд працює в режимі перегляду. Для внесення змін введіть пароль.")
    
    st.markdown("---")
    st.caption("📌 Автоматичний збір: Beton-X, ZGBK Etalon, Budservis, Моноліт Буд Інвест")
    st.caption("📞 Вручну: Panbeton, Krubeton, IFCEM, Beton-IF, Титан Бетон Захід")

# ── Основний контент ────────────────────────────────────────────────────────
st.markdown("# 📊 Моніторинг цін на бетон")

df = get_data()

if df.empty:
    st.info("🚀 База даних порожня. Запустіть парсер або введіть ціни вручну у бічній панелі.")
    st.stop()

# ── KPI ─────────────────────────────────────────────────────────────────────
latest = df.sort_values('timestamp').groupby(['company', 'grade']).last().reset_index()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="value">{df['company'].nunique()}</div>
        <div class="label">Конкурентів</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="value">{len(latest)}</div>
        <div class="label">Актуальних цін</div>
    </div>""", unsafe_allow_html=True)
with col3:
    manual_count = (df['url'] == MANUAL_SOURCE).sum()
    st.markdown(f"""<div class="metric-card">
        <div class="value">{manual_count}</div>
        <div class="label">Введено вручну</div>
    </div>""", unsafe_allow_html=True)
with col4:
    last_update = df['timestamp'].max()
    # Safely strip timezone for display (works with both naive and aware timestamps)
    try:
        last_update_naive = pd.Timestamp(last_update).tz_convert('UTC').tz_localize(None)
    except Exception:
        last_update_naive = pd.Timestamp(last_update).replace(tzinfo=None)
    st.markdown(f"""<div class="metric-card">
        <div class="value">{last_update_naive.strftime('%d.%m')}</div>
        <div class="label">Останнє оновлення</div>
    </div>""", unsafe_allow_html=True)

st.markdown("Івано-Франківськ · Останнє оновлення даних: " + last_update_naive.strftime("%d.%m.%Y %H:%M"))

st.markdown("---")

# ── Таб-навігація ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Порівняльна таблиця",
    "📈 Динаміка цін",
    "✏️ Ручні записи",
    "🗃️ Всі дані"
])

# ── TAB 1: Зведена таблиця ──────────────────────────────────────────────────
with tab1:
    st.subheader("Поточні ціни конкурентів (грн/м³)")
    
    pivot = latest.pivot_table(index='company', columns='grade', values='price', aggfunc='min')
    # Відсортуємо колонки
    ordered_grades = [g for g in GRADES if g in pivot.columns]
    pivot = pivot[ordered_grades]
    
    # Форматуємо + підсвічуємо мінімальну ціну
    def highlight_min(col):
        is_min = col == col.min()
        return ['background-color: #d4edda; font-weight: bold; color: #155724' if v 
                else '' for v in is_min]
    
    styled = pivot.style.apply(highlight_min).format("{:.0f} ₴", na_rep="—")
    st.dataframe(styled, use_container_width=True)
    
    st.caption("🟢 Зелений = найдешевша ціна серед конкурентів")

    # Порівняльна гістограма для обраної марки
    st.subheader("Порівняння за маркою")
    available_grades = sorted(latest['grade'].dropna().unique())
    grade_for_bar = st.selectbox("Марка для порівняння:", available_grades, key="bar_grade")
    
    bar_df = latest[latest['grade'] == grade_for_bar].sort_values('price')
    if not bar_df.empty:
        fig_bar = px.bar(
            bar_df, x='company', y='price',
            color='company',
            text='price',
            title=f"Ціна на {grade_for_bar} у конкурентів",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_bar.update_traces(texttemplate='%{text:,.0f} ₴', textposition='outside')
        fig_bar.update_layout(
            showlegend=False,
            yaxis_title="Ціна (грн/м³)",
            xaxis_title="",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ── TAB 2: Динаміка цін ─────────────────────────────────────────────────────
with tab2:
    st.subheader("Зміна цін у часі")
    
    col_a, col_b = st.columns(2)
    with col_a:
        grade_line = st.selectbox(
            "Марка бетону:", 
            sorted(df['grade'].dropna().unique()),
            key="line_grade"
        )
    with col_b:
        companies_sel = st.multiselect(
            "Конкуренти:",
            sorted(df['company'].unique()),
            default=sorted(df['company'].unique()),
            key="line_companies"
        )
    
    filtered = df[(df['grade'] == grade_line) & (df['company'].isin(companies_sel))]
    
    if filtered.empty:
        st.info("Немає даних для обраних фільтрів.")
    else:
        fig_line = px.line(
            filtered.sort_values('timestamp'),
            x='timestamp', y='price', color='company',
            markers=True,
            title=f"Динаміка цін: {grade_line}",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        # Відмічаємо вручну введені точки іншим символом
        manual_pts = filtered[filtered['url'] == MANUAL_SOURCE]
        if not manual_pts.empty:
            fig_line.add_trace(go.Scatter(
                x=manual_pts['timestamp'], y=manual_pts['price'],
                mode='markers',
                marker=dict(symbol='star', size=12, color='#ff6b35', line=dict(width=1, color='white')),
                name='⭐ Введено вручну',
                hovertext=manual_pts['company'] + ' (вручну)',
            ))
        
        fig_line.update_layout(
            yaxis_title="Ціна (грн/м³)", xaxis_title="Дата",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend_title="Конкурент",
        )
        st.plotly_chart(fig_line, use_container_width=True)

# ── TAB 3: Ручні записи ─────────────────────────────────────────────────────
with tab3:
    st.subheader("✏️ Ціни, введені вручну")
    
    manual_df = df[df['url'] == MANUAL_SOURCE].copy()
    
    if manual_df.empty:
        st.info("Ще немає вручну введених цін. Скористайтесь формою у бічній панелі зліва.")
    else:
        st.markdown(f"**Всього записів:** {len(manual_df)}")
        
        display_df = manual_df[['id', 'timestamp', 'company', 'grade', 'price', 'product_name']].copy()
        display_df['timestamp'] = display_df['timestamp'].apply(
            lambda t: pd.Timestamp(t).tz_convert('UTC').tz_localize(None).strftime('%d.%m.%Y')
            if pd.Timestamp(t).tzinfo else pd.Timestamp(t).strftime('%d.%m.%Y')
        )
        display_df.columns = ['ID', 'Дата', 'Компанія', 'Марка', 'Ціна (₴)', 'Примітка']
        display_df['Ціна (₴)'] = display_df['Ціна (₴)'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(display_df.set_index('ID'), use_container_width=True)
        
        if is_admin:
            st.markdown("---")
            st.subheader("🗑️ Видалити запис")
            del_id = st.number_input("ID запису для видалення:", min_value=1, step=1, value=1)
            if st.button("Видалити", type="secondary"):
                delete_price(del_id)
                st.success(f"Запис #{del_id} видалено.")
                st.rerun()

# ── TAB 4: Всі дані ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("🗃️ Всі записи в базі даних")
    
    # Фільтри
    fc1, fc2 = st.columns(2)
    with fc1:
        company_filter = st.multiselect(
            "Фільтр за компанією:", 
            sorted(df['company'].unique()),
            default=sorted(df['company'].unique())
        )
    with fc2:
        grade_filter = st.multiselect(
            "Фільтр за маркою:",
            sorted(df['grade'].dropna().unique()),
            default=sorted(df['grade'].dropna().unique())
        )
    
    show_df = df[
        (df['company'].isin(company_filter)) &
        (df['grade'].isin(grade_filter))
    ].copy()
    show_df['timestamp'] = show_df['timestamp'].apply(
        lambda t: pd.Timestamp(t).tz_convert('UTC').tz_localize(None).strftime('%d.%m.%Y %H:%M')
        if pd.Timestamp(t).tzinfo else pd.Timestamp(t).strftime('%d.%m.%Y %H:%M')
    )
    show_df['Джерело'] = show_df['url'].apply(
        lambda u: '✏️ Вручну' if u == MANUAL_SOURCE else '🤖 Авто'
    )
    
    st.dataframe(
        show_df[['id', 'timestamp', 'company', 'grade', 'price', 'Джерело', 'product_name']],
        use_container_width=True,
        column_config={
            'id': 'ID',
            'timestamp': 'Дата',
            'company': 'Компанія',
            'grade': 'Марка',
            'price': st.column_config.NumberColumn('Ціна (₴)', format="%,.0f ₴"),
            'Джерело': 'Джерело',
            'product_name': 'Опис'
        }
    )
    
    # Завантаження CSV
    csv = show_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Завантажити CSV",
        csv,
        "concrete_prices.csv",
        "text/csv",
        use_container_width=False
    )
