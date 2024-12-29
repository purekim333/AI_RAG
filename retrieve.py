from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from langchain.prompts import ChatPromptTemplate
from langchain_upstage import ChatUpstage
from langchain_core.output_parsers import StrOutputParser
from embedding import initialize_vectorstore  # embedding.py에서 함수 임포트
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

# 요청 모델 정의
class QueryRequest(BaseModel):
    query: str

# 글로벌 객체
vectorstore = None
retriever = None

# Lifespan 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    global vectorstore, retriever

    # 서버 시작 작업
    print("서버 초기화 중...")
    try:
        # 벡터 저장소 초기화
        vectorstore = initialize_vectorstore(persist_directory="./chroma_db")
        if vectorstore is None:
            raise RuntimeError("벡터 저장소 초기화 실패")
        print("벡터 저장소가 성공적으로 초기화되었습니다.")

        # Dense Retriever 생성
        retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 3})
        print("Dense Retriever가 성공적으로 초기화되었습니다.")
        yield  # 서버가 실행된 이후의 작업을 허용
    except Exception as e:
        print(f"서버 초기화 중 오류 발생: {str(e)}")
        raise
    finally:
        # 서버 종료 작업
        print("서버 종료 중...")

# FastAPI 초기화
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the chatbot API! Use /docs for Swagger UI or POST to /ask to interact with the chatbot."}

@app.post("/ask")
async def ask_question(request: QueryRequest):
    global retriever

    if retriever is None:
        raise HTTPException(status_code=400, detail="먼저 데이터를 로드하고 인덱싱하세요.")

    try:
        # 1. 검색
        print(f"사용자 입력 쿼리: {request.query}")
        result_docs = retriever.invoke(request.query)  # Deprecation에 따른 변경

        # 2. ChatPromptTemplate 정의
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    너는 인공지능 챗봇으로, 주어진 문서를 정확하게 이해해서 답변을 해야해.
                    문서에 있는 내용으로만 답변하고 내용이 없다면, 잘 모르겠다고 답변해.
                    ---
                    CONTEXT:
                    {context}
                    """,
                ),
                ("human", "{input}"),
            ]
        )

        # 3. LLMChain 정의
        llm = ChatUpstage(model="solar-pro", api_key=UPSTAGE_API_KEY)
        chain = prompt | llm | StrOutputParser()

        # 4. 질문 및 답변 생성
        response = chain.invoke({"context": result_docs, "input": request.query})
        print(f"생성된 응답: {response}")
        return {"query": request.query, "response": response}

    except Exception as e:
        print(f"질문 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"질문 처리 중 오류 발생: {str(e)}")
