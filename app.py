import streamlit as st
import snowflake.connector

# ページの設定（タイトルなど）
st.title("焚き火社長のドイツ移住計画 🇩🇪")
st.write("マレーシアからシンガポールのAWSへデータを送ります！")

# --- 1. Snowflakeに接続する関数 ---
def create_connection():
    return snowflake.connector.connect(
        user='MinoruAshikari',        # ユーザー名
        password='YOUR_PASSWORD',     # パスワード
        account='AKBOOYJ-BU10291',    # アカウント識別子
        warehouse='COMPUTE_WH',
        database='python_db',
        schema='PUBLIC'
    )

# --- 2. 新しいデータを登録する関数（INSERT） ---
def add_data(name, skill, country):
    conn = create_connection()
    cursor = conn.cursor()
    # データを挿入するSQL
    cursor.execute(f"INSERT INTO candidates (name, skill, target_country) VALUES ('{name}', '{skill}', '{country}')")
    conn.commit() # 確定！
    conn.close()

# --- 3. データを取得する関数（SELECT） ---
def get_data():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates")
    result = cursor.fetchall()
    conn.close()
    return result

# ==========================================
# ここから画面のデザイン
# ==========================================

# ■ 入力エリア（サイドバーに作ってみましょう）
st.sidebar.header("新規登録")
new_name = st.sidebar.text_input("名前")
new_skill = st.sidebar.text_input("スキル")
new_country = st.sidebar.text_input("目標の国")

# ■ 登録ボタン
if st.sidebar.button("データを追加する"):
    if new_name and new_country: # 名前と国が空じゃなければ実行
        with st.spinner('シンガポールへ送信中...'):
            add_data(new_name, new_skill, new_country)
            st.success(f"{new_name} さんを登録しました！")
    else:
        st.error("名前と目標の国は必ず入力してください！")

# ■ データ一覧表示エリア
st.subheader("現在の候補者リスト")

# ボタンを押さなくても自動で表示するようにしました
rows = get_data()

st.dataframe(rows, column_config={
    0: "ID",
    1: "名前",
    2: "スキル",
    3: "目標の国"
}, use_container_width=True)