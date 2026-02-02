import streamlit as st
import snowflake.connector
import pandas as pd
import requests
from datetime import datetime
from deep_translator import GoogleTranslator
from gtts import gTTS
import io

# ページ設定
st.set_page_config(page_title="3ヶ国語マスターDB", layout="wide")
st.title("🇯🇵 日本語 ➡ 🇺🇸 英語 ➡ 🇩🇪 ドイツ語")
st.caption("長文・スピーチ練習対応モード 📝")

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
        # 改行があっても翻訳できるようにする
        english_text = GoogleTranslator(source='ja', target='en').translate(text)
        german_text = GoogleTranslator(source='ja', target='de').translate(text)
        return english_text, german_text
    except:
        return "Error", "Error"

# --- 3. 音声を生成する関数 ---
def text_to_speech(text, lang_code):
    try:
        # テキストが空なら何もしない
        if not text:
            return None
        tts = gTTS(text=text, lang=lang_code)
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
    # シングルクォート(')が含まれていてもエラーにならないようにエスケープ処理
    japanese = japanese.replace("'", "''")
    english = english.replace("'", "''")
    german = german.replace("'", "''")
    memo = memo.replace("'", "''")
    
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

st.info("💡 日記やスピーチ原稿などの「長文」も翻訳・再生できます！")

# ■ 入力フォームエリア
with st.container():
    st.subheader("📝 新しいテキストを追加")
    
    with st.form("translation_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            # 【変更点】text_input を text_area に変更し、高さを広げました
            input_jp = st.text_area("日本語を入力", height=150, placeholder="ここに日記、メールの下書き、自己紹介などを入力してください...")
        with col2:
            input_memo = st.text_input("メモ (タイトルなど)")
        
        submitted = st.form_submit_button("翻訳して保存 🚀")
        
        if submitted and input_jp:
            with st.spinner("AIが長文を翻訳中...少々お待ちください 🐢"):
                trans_en, trans_de = translate_text(input_jp)
                add_trilingual_vocab(input_jp, trans_en, trans_de, input_memo)
            st.success("登録完了！下の一覧から再生できます🎧")
            st.rerun()

st.divider()

# ■ リスニング & 一覧エリア
st.subheader("🎧 リスニング・ルーム")

df = get_trilingual_vocab()

if not df.empty:
    df.columns = ["ID", "JAPANESE", "ENGLISH", "GERMAN", "MEMO", "CREATED_AT"]
    
    # セレクトボックス（長い文章の場合は、先頭の20文字だけ表示して見やすくする）
    options = df.apply(lambda x: f"{x['ID']}: {x['JAPANESE'][:20]}... / {x['MEMO']}", axis=1)
    selected_option = st.selectbox("再生したいテキストを選んでください 👇", options)
    
    # 選ばれたデータを取り出す
    selected_id = int(selected_option.split(":")[0])
    row = df[df["ID"] == selected_id].iloc[0]
    
    # 再生エリア（長文が見やすいように expander を使用）
    with st.expander("📖 テキスト全文を表示 & 再生", expanded=True):
        c_jp, c_en, c_de = st.columns(3)
        
        with c_jp:
            st.markdown(f"**🇯🇵 日本語**")
            st.write(row['JAPANESE']) # 長文も折り返して表示
            if st.button("再生 🇯🇵", key="play_jp"):
                with st.spinner("音声を生成中..."):
                    audio = text_to_speech(row['JAPANESE'], 'ja')
                    if audio: st.audio(audio, format='audio/mp3', start_time=0)
            
        with c_en:
            st.markdown(f"**🇺🇸 英語**")
            st.write(row['ENGLISH'])
            if st.button("再生 🇺🇸", key="play_en"):
                with st.spinner("音声を生成中..."):
                    audio = text_to_speech(row['ENGLISH'], 'en')
                    if audio: st.audio(audio, format='audio/mp3', start_time=0)
            
        with c_de:
            st.markdown(f"**🇩🇪 ドイツ語**")
            st.write(row['GERMAN'])
            if st.button("再生 🇩🇪", key="play_de"):
                with st.spinner("音声を生成中..."):
                    audio = text_to_speech(row['GERMAN'], 'de')
                    if audio: st.audio(audio, format='audio/mp3', start_time=0)

    st.divider()
    
    # ■ 一覧リスト
    st.write("📚 履歴リスト")
    st.dataframe(df[["JAPANESE", "ENGLISH", "GERMAN", "MEMO"]], use_container_width=True)
    
    # 削除エリア
    with st.expander("🗑️ データを削除する"):
        if st.button("現在選択中のデータを削除する"):
            delete_vocab(selected_id)
            st.warning("削除しました")
            st.rerun()

else:
    st.write("まだデータがありません。")
