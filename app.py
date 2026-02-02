# --- 🆕 削除機能のための関数を追加 ---
def delete_vocab(vocab_id):
    conn = create_connection()
    cur = conn.cursor()
    # 指定されたIDのデータを削除するSQL
    cur.execute(f"DELETE FROM vocab_book WHERE id = {vocab_id}")
    conn.commit()
    conn.close()

# --- 🔄 タブ3：ドイツ語単語帳（進化版） ---
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

    # データを取得
    vocab_df = get_vocab()
    
    if not vocab_df.empty:
        # --- 🔍 検索機能 ---
        search_query = st.text_input("🔍 単語を検索する", placeholder="ドイツ語や日本語で検索...")
        
        if search_query:
            # 検索文字が含まれている行だけをフィルタリング（大文字小文字を区別しない）
            vocab_df = vocab_df[
                vocab_df['GERMAN'].str.contains(search_query, case=False) | 
                vocab_df['JAPANESE'].str.contains(search_query, case=False)
            ]
        
        # --- 🗑️ 削除機能 ---
        # データフレームを表示（IDは隠さずに表示します）
        st.dataframe(vocab_df, use_container_width=True)
        
        # 削除したい単語を選ぶセレクトボックス
        # 「ID: 単語」という形式でリストを作る
        delete_options = vocab_df.apply(lambda x: f"{x['ID']}: {x['GERMAN']} ({x['JAPANESE']})", axis=1)
        target_vocab = st.selectbox("🗑️ 削除する単語を選択", options=delete_options)
        
        if st.button("選択した単語を削除する"):
            # "5: Guten Morgen" のような文字から、最初の数字 "5" だけを取り出す技
            target_id = target_vocab.split(":")[0] 
            delete_vocab(target_id)
            st.warning("データを削除しました！")
            st.rerun()
            
    else:
        st.info("まだ単語がありません。上のフォームから登録してみましょう！")