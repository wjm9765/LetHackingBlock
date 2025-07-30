import json
import boto3
from typing import List, Dict, Any
from pathlib import Path
from botocore.exceptions import ClientError

# ===== AWS 설정 =====
AWS_REGION = "ap-northeast-2"  # 필요에 따라 변경

# ===== 테이블 및 키 필드 정보 정의 =====
# 테이블명을 전역변수로 설정하고 해당 테이블의 키 필드 정보 포함
COMMAND_BLOCK = {
    "table_name": "Command_Block",
    "key_field": "command_name"
}

STATE_INITIAL = {
    "table_name": "State_initial",
    "key_field": "hack_enviornment"
}

TO_AI_INFORMATION = {
    "table_name": "to_AI_information",
    "key_field": "data_type"
}

USER_STATES = {
    "table_name": "UserStates",
    "key_field": "user_id"
}

USER ={
    "table_name": "Users",
    "key_field": "user_id"
}
# ===== DynamoDB 연결 =====
def get_dynamodb_resource():
    """DynamoDB 리소스에 연결합니다."""
    try:
        return boto3.resource('dynamodb', region_name=AWS_REGION)
    except Exception as e:
        print(f"⚠️ DynamoDB 연결 실패: {e}")
        return None

def load_file(table_info: Dict, key_value: str) -> List[str]:#to_ai_information
    """
    텍스트 파일을 로드하여 라인별로 리스트로 반환합니다.
    
    Args:
        table_info: 테이블 정보 딕셔너리 (table_name, key_field 포함)
        key_value: 검색할 키 값
    
    Returns:
        텍스트 내용을 줄 단위로 분할한 리스트
    """
    try:
        # 테이블 정보 추출
        table_name = table_info["table_name"]
        key_field = table_info["key_field"]
        
        # DynamoDB 연결
        dynamodb = get_dynamodb_resource()
        if not dynamodb:
            print("❌ DynamoDB 연결 실패")
            return []
        
        table = dynamodb.Table(table_name)
        
        # 데이터 가져오기
        response = table.get_item(Key={key_field: key_value})
        
        if "Item" not in response:
            print(f"❌ load.py: 항목을 찾을 수 없음: {table_name}/{key_field}={key_value}")
            return []
        
        # 텍스트 내용 추출 및 라인으로 분할
        content = response["Item"].get("content", "")
        return [line.strip() for line in content.split("\n") if line.strip()]
            
    except ClientError as e:
        print(f"❌ DynamoDB 오류: {e}")
        return []
    except Exception as e:
        print(f"❌ 파일 로드 중 오류: {e}")
        return []

def load_json(table_info: Dict, key_value: str = None) -> Dict[str, Any]:#state_initial,state,users 
    """
    JSON 파일을 로드하여 딕셔너리로 반환합니다.
    
    Args:
        table_info: 테이블 정보 딕셔너리 (table_name, key_field 포함)
        key_value: 검색할 키 값 (None이면 전체 테이블 스캔)
    
    Returns:
        JSON 형식의 데이터 (딕셔너리 또는 리스트)
    """
    try:
        # 테이블 정보 추출
        table_name = table_info["table_name"]
        key_field = table_info["key_field"]
        
        # DynamoDB 연결
        dynamodb = get_dynamodb_resource()
        if not dynamodb:
            print("❌ DynamoDB 연결 실패")
            return {}
        
        table = dynamodb.Table(table_name)
        
        # 데이터 가져오기
        if key_value:
            # 특정 키 값으로 항목 가져오기
            response = table.get_item(Key={key_field: key_value})
            if "Item" not in response:
                print(f"❌ 항목을 찾을 수 없음: {table_name}/{key_field}={key_value}")
                return {}
            
            # 키 필드 제외하고 반환 (원본 JSON 형식 유지)
            item = response["Item"]
            if key_field in item:
                del item[key_field]  # 키 필드 제거
            
            return item
        else:
            print("키 값이 없습니다")
            return {}

    except ClientError as e:
        print(f"❌ DynamoDB 오류: {e}")
        return {}
    except Exception as e:
        print(f"❌ JSON 로드 중 오류: {e}")
        return {}

def load_command_json(table_name: str, key_value: str = None, base_block_type: str = None) -> List[Dict]:
    """
    DynamoDB에서 명령어 데이터를 로드합니다.
    
    Args:
        table_name: 테이블 이름 (예: "Command_Block")
        key_value: 기본 키 값 (지정 시 해당 항목만 검색)
        base_block_type: 명령어 기본 블록 타입 (예: "generic_shell_command")
    
    Returns:
        검색 결과 (항목 목록)
    """
    try:
        # DynamoDB 연결
        dynamodb = get_dynamodb_resource()
        if not dynamodb:
            print("❌ DynamoDB 연결 실패")
            return []
        
        table = dynamodb.Table(table_name)
        
        # 케이스 1: 테이블 이름과 키 값이 모두 제공된 경우 (단일 항목 검색)
        if key_value and not base_block_type:
            # 테이블 정보 확인하여 키 필드 결정
            key_field = None
            for table_info in [COMMAND_BLOCK, STATE_INITIAL, TO_AI_INFORMATION, USER_STATES, USER]:
                if table_info["table_name"] == table_name:
                    key_field = table_info["key_field"]
                    break
            
            if not key_field:
                print(f"⚠️ 테이블 '{table_name}'의 키 필드 정보를 찾을 수 없습니다")
                return []
            
            # 항목 가져오기
            response = table.get_item(Key={key_field: key_value})
            if "Item" not in response:
                print(f"❌ 항목을 찾을 수 없음: {table_name}/{key_field}={key_value}")
                return []
                
            return [response["Item"]]  # 리스트 형태로 반환
            
        # 케이스 2: base_block_type이 제공된 경우 (보조 인덱스 검색)
        elif base_block_type:
            print(f"🔍 base_block_type='{base_block_type}'으로 검색 중...")
            
            # 스캔 + 필터링 사용 (보조 인덱스가 없는 경우)
            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr("base_block_type").eq(base_block_type)
            )
            
            items = response.get("Items", [])
            
            # 결과가 많은 경우 페이지네이션 처리
            while "LastEvaluatedKey" in response:
                response = table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr("base_block_type").eq(base_block_type),
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                items.extend(response.get("Items", []))
            
            if not items:
                print(f"❌ 결과 없음: {table_name}/base_block_type={base_block_type}")
                return []
                
            print(f"✅ {len(items)}개 항목 찾음")
            return items
            
        # 케이스 3: 테이블 이름만 제공된 경우 (전체 테이블 스캔)
        else:
            print(f"📊 테이블 '{table_name}' 전체 스캔 중...")
            response = table.scan()
            items = response.get("Items", [])
            
            # 결과가 많은 경우 페이지네이션 처리
            while "LastEvaluatedKey" in response:
                print(f"🔄 추가 항목 로드 중... ({len(items)}개 로드됨)")
                response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))
            
            print(f"✅ 총 {len(items)}개 항목 로드됨")
            return items
    
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "ResourceNotFoundException":
            print(f"❌ 테이블 '{table_name}'을 찾을 수 없습니다")
        else:
            print(f"❌ DynamoDB 오류 ({error_code}): {e}")
        return []
    except Exception as e:
        print(f"❌ 명령어 로드 중 오류: {e}")
        return []
