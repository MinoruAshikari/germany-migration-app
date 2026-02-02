import streamlit as st
import snowflake.connector
import pandas as pd
import requests
from datetime import datetime
from deep_translator import GoogleTranslator # 翻訳機をインポート

# ページ設定
st.set_page_config(page_title="3ヶ国語マスターDB", layout="wide")
st.title("🇯🇵 日本語 ➡ 🇺🇸 英語 ➡ 🇩🇪 ドイツ語")

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

# --- 2. 自動翻訳する関数（魔法の呪文） ---
def translate_text(text):
    try:
        # 日本語 -> 英語
        english_text = GoogleTranslator(source='ja', target='en').translate(text)
        # 日本語 -> ドイツ語
        german_text = GoogleTranslator(source='ja', target='de').translate(text)
        return english_text, german_text
    except:
        return "Error", "Error"

# --- 3. データを登録する関数 ---
def add_trilingual_vocab(japanese, english, german, memo):
    conn = create_connection()
    cursor = conn.cursor()
    # 3ヶ国語用の新しいテーブルを作る
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trilingual_book (
            id INTEGER IDENTITY(1,1),
            japanese STRING,
            english STRING,
            german STRING,
            memo STRING,
            created_at TIMESTAMP
        )
    """)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f"INSERT INTO trilingual_book (japanese, english, german, memo, created_at) VALUES ('{japanese}', '{english}', '{german}', '{memo}', '{now}')")
    conn.commit()
    conn.close()

# --- 4. データを取得する関数 ---
def get_trilingual_vocab():
    conn = create_connection()
    try:
        df = pd.read_sql("SELECT id, japanese, english, german, memo, created_at FROM trilingual_book ORDER BY created_at DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# --- 5. データを削除する関数 ---
def delete_vocab(vocab_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM trilingual_book WHERE id = {vocab_id}")
    conn.commit()
    conn.close()

# ==========================================
# 画面レイアウト
# ==========================================

st.info("💡 日本語を入力するだけで、AIが自動で英語とドイツ語に翻訳して登録します！")

# ■ 入力フォーム
with st.container():
    st.subheader("📝 新しい単語を追加")
    
    with st.form("translation_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            input_jp = st.text_input("日本語を入力してください", placeholder="例：こんにちは、契約書、ビザ...")
        with col2:
            input_memo = st.text_input("メモ (任意)")
        
        # ボタンを押すと翻訳＆保存
        submitted = st.form_submit_button("自動翻訳して保存 🚀")
        
        if submitted and input_jp:
            with st.spinner("AIが翻訳中..."):
                # ここで翻訳を実行！
                trans_en, trans_de = translate_text(input_jp)
                
                # 結果を保存
                add_trilingual_vocab(input_jp, trans_en, trans_de, input_memo)
                
            st.success(f"登録完了！ 🇺🇸 {trans_en} / 🇩🇪 {trans_de}")
            st.rerun()

st.divider()

# ■ リスト表示
st.subheader("📚 3ヶ国語単語帳")
df = get_trilingual_vocab()

if not df.empty:
    # カラム名をきれいにする
    df.columns = ["ID", "🇯🇵 日本語", "🇺🇸 英語", "🇩🇪 ドイツ語", "メモ", "登録日"]
    
    # メインの表を表示
    st.dataframe(df, use_container_width=True)
    
    # 削除機能
    with st.expander("🗑️ データを削除する"):
        delete_options = df.apply(lambda x: f"{x['ID']}: {x['🇯🇵 日本語']}", axis=1)
        target = st.selectbox("削除する単語を選択", options=delete_options)
        if st.button("削除実行"):
            target_id = target.split(":")[0]
            delete_vocab(target_id)
            st.warning("削除しました")
            st.rerun()
else:
    st.write("まだデータがありません。「こんにちは」と入れてみてください！")
