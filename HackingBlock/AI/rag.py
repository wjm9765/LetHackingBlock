

import os
import glob
from dotenv import load_dotenv
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader

def create_vector_db():
    """
    프로젝트 내의 텍스트 기반 파일들을 읽어들여 FAISS 벡터 데이터베이스를 생성합니다.
    """
    # .env 파일에서 환경 변수 로드
    load_dotenv()
    
    # OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        return

    print("프로젝트 파일들을 로드하는 중...")
    
    # 프로젝트 루트 디렉토리 설정
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # 로드할 파일 확장자 지정
    file_extensions = ["*.py", "*.json", "*.md", "*.txt"]
    documents = []
    
    # 지정된 확장자 파일들을 재귀적으로 검색하여 로드
    for ext in file_extensions:
        # venv 디렉토리는 제외
        search_pattern = os.path.join(project_root, "**", ext)
        for file_path in glob.glob(search_pattern, recursive=True):
            if "venv/" not in file_path.replace(project_root, ""):
                try:
                    loader = TextLoader(file_path, encoding='utf-8')
                    documents.extend(loader.load())
                    print(f"  - 로드 완료: {file_path}")
                except Exception as e:
                    print(f"  - 로드 실패: {file_path} ({e})")

    if not documents:
        print("로드할 문서가 없습니다.")
        return

    print(f"\n총 {len(documents)}개의 문서를 로드했습니다.")
    print("문서를 청크로 분할하는 중...")

    # 텍스트 분할기 설정
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    print(f"총 {len(texts)}개의 텍스트 청크로 분할되었습니다.")
    print("OpenAI 임베딩을 생성하고 FAISS 벡터 DB를 구축하는 중... (시간이 걸릴 수 있습니다)")

    # OpenAI 임베딩 모델 설정
    embeddings = OpenAIEmbeddings()
    
    # FAISS 벡터 DB 생성
    try:
        vector_db = FAISS.from_documents(texts, embeddings)
        
        # 생성된 벡터 DB 저장
        save_path = os.path.join(project_root, "faiss_index")
        vector_db.save_local(save_path)
        
        print(f"\n✅ 성공: 벡터 DB가 '{save_path}'에 성공적으로 저장되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 실패: 벡터 DB 생성 중 오류가 발생했습니다. ({e})")
        print("OpenAI API 키가 유효한지, 그리고 계정에 크레딧이 남아있는지 확인해주세요.")


if __name__ == "__main__":
    create_vector_db()

