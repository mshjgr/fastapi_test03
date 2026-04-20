# main.py

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

# fastapi 객체 생성
app = FastAPI()
# jinja2 템플릿 객체 생성 (templates 파일들이 어디에 있는지 알려야 한다.)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        # 응답에 필요한 data 를 context 로 전달 할수 있다.
        context={
            "fortuneToday":"동쪽으로 가면 귀인을 만나요"
        }
    )

# get 방식 /post 요청 처리
@app.get("/post", response_class=HTMLResponse)
def getPosts(request: Request, db:Session = Depends(get_db)):
    # DB 에서 글목록을 가져오기 위한 sql 문 준비
    query = text("""
        SELECT num, writer, title, content, created_at
        FROM post
        ORDER BY num DESC
    """)
    # 글 목록을 얻어와서
    result = db.execute(query)
    posts = result.fetchall()
    # 응답하기
    return templates.TemplateResponse(
        request=request,
        name="post/list.html", # templates/post/list.html jinja2 를 해석한 결과를 응답
        context={
            "posts":posts
        }
    )

@app.get("/post/new", response_class=HTMLResponse)
def postNewForm(request: Request):
    return templates.TemplateResponse(request=request, name="post/new-form.html")

@app.post("/post/new")
def postNew(writer: str = Form(...), title: str = Form(...), content: str = Form(...),
            db: Session = Depends(get_db)):
    # DB 에 저장할 sql 문  준비
    query = text("""
        INSERT INTO post
        (writer, title, content)
        VALUES(:writer, :title, :content)
    """)
    db.execute(query, {"writer":writer, "title":title, "content":content})
    db.commit()

    # 특정 경로로 요청을 다시 하도록 리다일렉트 응답을 준다.
    return RedirectResponse("/post", status_code=302)

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