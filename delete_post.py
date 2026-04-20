# post 삭제 요청 처리 (상세보기나 목록에서 삭제 버튼 클릭 시)
@app.post("/post/delete")
def postDelete(num: int = Form(...), db: Session = Depends(get_db)):
    # 1. SELECT: 삭제할 데이터를 먼저 가져옵니다. (존재 확인 및 백업용)
    select_query = text("""
        SELECT num, writer, title, content 
        FROM post 
        WHERE num = :num
    """)
    result = db.execute(select_query, {"num": num})
    post = result.fetchone()

    # 데이터가 존재하는 경우에만 이후 작업 진행
    if post:
        # 2. INSERT: 삭제될 데이터를 백업용 테이블(deleted_post)에 저장합니다.
        backup_query = text("""
            INSERT INTO deleted_post (origin_num, writer, title, content, deleted_at)
            VALUES (:num, :writer, :title, :content, NOW())
        """)
        db.execute(backup_query, {
            "num": post.num,
            "writer": post.writer,
            "title": post.title,
            "content": post.content
        })

        # 3. DELETE: 실제 post 테이블에서 행을 삭제합니다.
        delete_query = text("""
            DELETE FROM post 
            WHERE num = :num
        """)
        db.execute(delete_query, {"num": num})
        
        # 트랜잭션 확정
        db.commit()

    # 글 목록 페이지로 리다이렉트
    return RedirectResponse("/post", status_code=303)