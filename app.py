import streamlit as st
import snowflake.connector
import pandas as pd
import requests
from datetime import datetime
from deep_translator import GoogleTranslator
from gtts import gTTS # 音声読み上げライブラリ
import io # 音声データをメモリで扱うための道具

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

# --- 2. 自動翻訳関数 ---
def translate_text(text):
    try:
        english_text = GoogleTranslator(source='ja', target='en').translate(text)
        german_text = GoogleTranslator(source='ja', target='de').translate(text)
        return english_text, german_text
    except:
        return "Error", "Error"

# --- 3. 音声を生成する関数（今回の主役！） ---
def text_to_speech(text, lang_code):
    try:
        # Googleのサーバーで音声を生成
        tts = gTTS(text=text, lang=lang_code)
        # データをメモリ上に保存（ファイルとして保存しない）
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except:
        return None

# --- 4. データ登録関数 ---
def add_trilingual_vocab(japanese, english, german, memo):
    conn = create_connection()
    cursor = conn.cursor()
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

# --- 5. データ取得関数 ---
def get_trilingual_vocab():
    conn = create_connection()
    try:
        df = pd.read_sql("SELECT id, japanese, english, german, memo, created_at FROM trilingual_book ORDER BY created_at DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# --- 6. 削除関数 ---
def delete_vocab(vocab_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM trilingual_book WHERE id = {vocab_id}")
    conn.commit()
    conn.close()

# ==========================================
# 画面レイアウト
# ==========================================

st.info("💡 日本語を入れるだけで、翻訳 ＆ 発音チェックまでできます！")

# ■ 入力フォームエリア
with st.container():
    st.subheader("📝 新しい単語を追加")
    
    with st.form("translation_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            input_jp = st.text_input("日本語を入力", placeholder="例：こんにちは")
        with col2:
            input_memo = st.text_input("メモ")
        
        submitted = st.form_submit_button("翻訳して保存 🚀")
        
        if submitted and input_jp:
            with st.spinner("AIが翻訳中..."):
                trans_en, trans_de = translate_text(input_jp)
                add_trilingual_vocab(input_jp, trans_en, trans_de, input_memo)
            st.success(f"登録完了！ 🇺🇸 {trans_en} / 🇩🇪 {trans_de}")
            st.rerun()

st.divider()

# ■ リスニング & 一覧エリア
st.subheader("🎧 リスニング・ルーム")

df = get_trilingual_vocab()

if not df.empty:
    # データを見やすく整理
    df.columns = ["ID", "JAPANESE", "ENGLISH", "GERMAN", "MEMO", "CREATED_AT"]
    
    # -------------------------------------------------------
    # 🎵 ここが新機能！単語を選んで再生するエリア
    # -------------------------------------------------------
    # セレクトボックスで単語を選ばせる
    options = df.apply(lambda x: f"{x['ID']}: {x['JAPANESE']} / {x['GERMAN']}", axis=1)
    selected_option = st.selectbox("再生したい単語を選んでください 👇", options)
    
    # 選ばれた単語のデータを取り出す
    selected_id = int(selected_option.split(":")[0])
    row = df[df["ID"] == selected_id].iloc[0]
    
    # 3つの言語の再生ボタンを並べる
    c_jp, c_en, c_de = st.columns(3)
    
    with c_jp:
        st.write(f"🇯🇵 {row['JAPANESE']}")
        if st.button("再生 🇯🇵", key="play_jp"):
            audio = text_to_speech(row['JAPANESE'], 'ja')
            st.audio(audio, format='audio/mp3', start_time=0)
            
    with c_en:
        st.write(f"🇺🇸 {row['ENGLISH']}")
        if st.button("再生 🇺🇸", key="play_en"):
            audio = text_to_speech(row['ENGLISH'], 'en')
            st.audio(audio, format='audio/mp3', start_time=0)
            
    with c_de:
        st.write(f"🇩🇪 {row['GERMAN']}")
        if st.button("再生 🇩🇪", key="play_de"):
            audio = text_to_speech(row['GERMAN'], 'de')
            st.audio(audio, format='audio/mp3', start_time=0)

    st.divider()
    
    # ■ 一覧リスト（いつもの表）
    st.write("📚 全単語リスト")
    st.dataframe(df[["JAPANESE", "ENGLISH", "GERMAN", "MEMO"]], use_container_width=True)
    
    # 削除エリア
    with st.expander("🗑️ データを削除する"):
        if st.button("選択中の単語を削除"):
            delete_vocab(selected_id)
            st.warning("削除しました")
            st.rerun()

else:
    st.write("まだデータがありません。")
