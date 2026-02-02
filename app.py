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
        return 0.0

# --- 3. 候補者データの関数 ---
def get_candidates():
    conn = create_connection()
    try:
        df = pd.read_sql("SELECT * FROM candidates", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def add_candidate(name, skill, country):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO candidates (name, skill, target_country) VALUES ('{name}', '{skill}', '{country}')")
    conn.commit()
    conn.close()

# --- 4. 為替データの関数 ---
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

def get_rate_history():
    conn = create_connection()
    try:
        df = pd.read_sql("SELECT * FROM exchange_rates ORDER BY recorded_at DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# --- 🆕 5. 単語帳の関数（削除機能付き！） ---
def add_vocab(german, japanese, memo):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocab_book (
            id INTEGER IDENTITY(1,1),
            german STRING,
            japanese STRING,
            memo STRING,
            created_at TIMESTAMP
        )
    """)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f"INSERT INTO vocab_book (german, japanese, memo, created_at) VALUES ('{german}', '{japanese}', '{memo}', '{now}')")
    conn.commit()
    conn.close()

def get_vocab():
    conn = create_connection()
    try:
        df = pd.read_sql("SELECT id, german, japanese, memo, created_at FROM vocab_book ORDER BY created_at DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def delete_vocab(vocab_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM vocab_book WHERE id = {vocab_id}")
    conn.commit()
    conn.close()

# ==========================================
# 画面レイアウト
# ==========================================

# ここで「3つのタブ」を作っています（これが消えていたのが原因でした！）
tab1, tab2, tab3 = st.tabs(["👥 移住候補者", "💰 為替レート", "🇩🇪 単語帳"])

# --- タブ1：候補者リスト ---
with tab1:
    st.subheader("現在の候補者状況")
    df = get_candidates()
    if not df.empty:
        df.columns = ["ID", "名前", "スキル", "目標の国"]
        st.dataframe(df, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(df["目標の国"].value_counts())
        with col2:
            st.write("📊 スキル分布")
            st.dataframe(df["スキル"].value_counts())
    else:
        st.info("データがまだありません。")

    st.sidebar.header("📝 メンバー登録")
    new_name = st.sidebar.text_input("名前")
    new_skill = st.sidebar.selectbox("スキル", ["Python", "SQL", "英語", "ドイツ語", "マネジメント", "その他"])
    new_country = st.sidebar.radio("目標の国", ["Germany", "Netherlands", "Japan", "Other"])
    
    if st.sidebar.button("メンバー登録"):
        add_candidate(new_name, new_skill, new_country)
        st.success(f"{new_name} さんを登録しました！")
        st.rerun()

# --- タブ2：為替レート ---
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
                st.error("レート取得失敗")
            
    st.divider()
    st.write("📊 履歴")
    history_df = get_rate_history()
    if not history_df.empty:
        st.line_chart(history_df.set_index("RECORDED_AT")["RATE"])
        st.dataframe(history_df, use_container_width=True)

# --- 🔄 タブ3：ドイツ語単語帳（検索＆削除機能付き） ---
with tab3:
    st.header("🇩🇪 My Vocabulary Book")
    
    # ■ 1. 新規登録エリア
    with st.expander("📝 新しい単語を登録する", expanded=True):
        with st.form("vocab_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                in_german = st.text_input("ドイツ語 (German)")
            with c2:
                in_japanese = st.text_input("日本語 (Japanese)")
            with c3:
                in_memo = st.text_input("メモ (Example etc.)")
            
            submitted = st.form_submit_button("単語を保存 📥")
            
            if submitted and in_german and in_japanese:
                add_vocab(in_german, in_japanese, in_memo)
                st.success(f"「{in_german}」を覚えました！")
                st.rerun()

    st.divider()
    
    # ■ 2. 検索・一覧・削除エリア
    st.subheader("📚 覚えた単語リスト")

    vocab_df = get_vocab()
    
    if not vocab_df.empty:
        # 見やすいカラム名にする（大文字のままだと扱いづらいので）
        vocab_df.columns = [col.upper() for col in vocab_df.columns]
        
        # --- 🔍 検索機能 ---
        search_query = st.text_input("🔍 単語を検索する", placeholder="ドイツ語や日本語で検索...")
        
        display_df = vocab_df.copy()
        if search_query:
            display_df = display_df[
                display_df['GERMAN'].str.contains(search_query, case=False) | 
                display_df['JAPANESE'].str.contains(search_query, case=False)
            ]
        
        st.dataframe(display_df, use_container_width=True)
        
        # --- 🗑️ 削除機能 ---
        st.write("🗑️ データを削除する")
        # 削除リストを作る
        delete_options = display_df.apply(lambda x: f"{x['ID']}: {x['GERMAN']} ({x['JAPANESE']})", axis=1)
        target_vocab = st.selectbox("削除する単語を選択してください", options=delete_options)
        
        if st.button("選択した単語を削除する 💥"):
            target_id = target_vocab.split(":")[0]
            delete_vocab(target_id)
            st.success("削除しました！")
            st.rerun()
            
    else:
        st.info("まだ単語がありません。上のフォームから登録してみましょう！")