from langchain_chroma import Chroma
from langchain_upstage import UpstageEmbeddings
from langchain.docstore.document import Document
import os
from dotenv import load_dotenv

#API 키 불러오기기
dotenv_path = os.path.join("config", ".env")
load_dotenv(dotenv_path)

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

def load_data_as_chunks(root_folder):
    chunks = []
    for category in os.listdir(root_folder):  # 폴더 탐색
        category_path = os.path.join(root_folder, category)
        if os.path.isdir(category_path):  # 하위 폴더인지 확인
            for file_name in os.listdir(category_path):  # 하위 폴더 내 파일 탐색
                file_path = os.path.join(category_path, file_name)
                if file_path.endswith(".txt"):  # .txt 파일만 처리
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        chunks.append({
                            "category": category,  # 분야명 (폴더명)
                            "file_name": file_name,  # 파일명
                            "content": content  # 파일 내용
                        })
    return chunks

# Document 객체 생성
def create_documents(chunks):
    documents = []
    for chunk in chunks:
        metadata = {
            "category": chunk["category"],  # 메타데이터: 분야명
            "file_name": chunk["file_name"]  # 메타데이터: 파일명
        }
        documents.append(Document(page_content=chunk["content"], metadata=metadata))
    return documents

def initialize_vectorstore(persist_directory="./chroma_db", root_folder="policies"):
    print("initialize_vectorstore 시작")  # 디버깅: 함수 시작
    print(f"Persist Directory: {persist_directory}")
    print(f"Root Folder: {root_folder}")

    # Upstage Embeddings 설정
    try:
        print("Upstage Embeddings 초기화 중...")
        upstage_embeddings = UpstageEmbeddings(
            model="embedding-query",
            api_key=UPSTAGE_API_KEY
        )
        print("Upstage Embeddings 초기화 완료")
        # 메서드 확인
        print(dir(upstage_embeddings))
    except Exception as e:
        print(f"Upstage Embeddings 초기화 실패: {e}")
        raise

    try:
        # 기존 데이터 로드
        print("기존 벡터스토어 로드 시도 중...")
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=upstage_embeddings.embed_query  # 변경된 키워드 사용
        )
        print("기존 벡터스토어가 성공적으로 로드되었습니다.")
    except Exception as e:
        print(f"기존 벡터스토어 로드 실패: {e}")
        print("새로운 데이터 로드 및 저장 시도 중...")

        try:
            # 새로운 데이터 로드 및 저장
            chunks = load_data_as_chunks(root_folder)
            print(f"총 {len(chunks)}개의 청크가 로드되었습니다.")

            documents = create_documents(chunks)
            print(f"총 {len(documents)}개의 문서 객체가 생성되었습니다.")

            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding_function=upstage_embeddings.embed_query,  # 변경된 키워드 사용
                persist_directory=persist_directory
            )
            print("새로운 벡터스토어가 생성되고 저장되었습니다.")
        except Exception as e:
            print(f"새로운 벡터스토어 생성 실패: {e}")
            raise

    print("initialize_vectorstore 완료")  # 디버깅: 함수 종료
    return vectorstore
