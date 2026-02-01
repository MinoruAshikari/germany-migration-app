import streamlit as st
import snowflake.connector
import pandas as pd
import requests
from datetime import datetime

# ページ設定
st.set_page_config(page_title="ドイツ移住計画DB", layout="wide")
st.title("焚き火社長のドイツ移住計画 🇩🇪 x 💹")

# --- 1. Snowflake接続 ---
def create_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )

# --- 2. 為替レートを取得する関数 ---
def get_eur_myr_rate():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        data = response.json()
        return data['rates']['MYR']
    except Exception as e:
        st.warning(f"⚠️ 為替レートが取れませんでした: {e}")
        return 0.0

# --- 3. 為替データを保存する関数 ---
def save_rate(rate):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rates (
            recorded_at TIMESTAMP,
            currency_pair STRING,
            rate FLOAT
        )
    """)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f"INSERT INTO exchange_rates VALUES ('{now}', 'EUR/MYR', {rate})")
    conn.commit()
    conn.close()

# --- 4. 候補者データを表示する関数 ---
def get_candidates():
    conn = create_connection()
    try:
        df = pd.read_sql("SELECT * FROM candidates", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# --- 5. 為替履歴を表示する関数 ---
def get_rate_history():
    conn = create_connection()
    try:
        df = pd.read_sql("SELECT * FROM exchange_rates ORDER BY recorded_at DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# ==========================================
# 画面レイアウト
# ==========================================

tab1, tab2 = st.tabs(["👥 移住候補者リスト", "💰 為替レート監視"])

# タブ1：候補者リスト
with tab1:
    st.subheader("現在の候補者状況")
    df = get_candidates()
    if not df.empty:
        df.columns = ["ID", "名前", "スキル", "目標の国"]
        st.dataframe(df, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📊 国別の割合")
            st.bar_chart(df["目標の国"].value_counts())
        with col2:
            st.write("📊 スキル分布")
            st.dataframe(df["スキル"].value_counts())
    else:
        st.info("データがまだありません。")

    # サイドバー入力フォーム
    st.sidebar.header("📝 新規メンバー登録")
    new_name = st.sidebar.text_input("名前")
    new_skill = st.sidebar.selectbox("スキル", ["Python", "SQL", "英語", "ドイツ語", "マネジメント", "その他"])
    new_country = st.sidebar.radio("目標の国", ["Germany", "Netherlands", "Japan", "Other"])
    
    if st.sidebar.button("メンバー登録"):
        conn = create_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO candidates (name, skill, target_country) VALUES ('{new_name}', '{new_skill}', '{new_country}')")
        conn.commit()
        conn.close()
        st.success(f"{new_name} さんを登録しました！")
        st.rerun()

# タブ2：為替レート
with tab2:
    st.subheader("💶 ユーロ/リンギット (EUR to MYR)")
    
    current_rate = get_eur_myr_rate()
    
    col_rate, col_btn = st.columns([2, 1])
    with col_rate:
        st.metric(label="現在のレート (1 EUR)", value=f"{current_rate} MYR")
    
    with col_btn:
        if st.button("レートを記録する 💾"):
            if current_rate > 0:
                save_rate(current_rate)
                st.success("Snowflakeに保存しました！")
                st.rerun()
            else:
                st.error("レートが取得できていないので保存できません。")
            
    st.divider()
    st.write("📊 記録されたレートの履歴")
    history_df = get_rate_history()
    if not history_df.empty:
        st.line_chart(history_df.set_index("RECORDED_AT")["RATE"])
        st.dataframe(history_df, use_container_width=True)