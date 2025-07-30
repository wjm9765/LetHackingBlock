import boto3
import json
import os
from pathlib import Path

# AWS 설정
AWS_REGION = "ap-northeast-2"  # 리전은 필요에 따라 변경하세요

def connect_to_dynamodb():
    """DynamoDB 리소스에 연결합니다."""
    try:
        # AWS 자격 증명은 ~/.aws/credentials에서 로드됩니다.
        # 또는 환경 변수 AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY로 설정할 수 있습니다.
        return boto3.resource('dynamodb', region_name=AWS_REGION)
    except Exception as e:
        print(f"DynamoDB 연결 오류: {e}")
        return None

def create_table_if_not_exists(dynamodb, table_name, key_name):
    """테이블이 존재하지 않으면 생성합니다."""
    try:
        existing_tables = [table.name for table in dynamodb.tables.all()]
        
        if table_name not in existing_tables:
            print(f"테이블 '{table_name}' 생성 중...")
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': key_name,
                        'KeyType': 'HASH'  # 파티션 키
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': key_name,
                        'AttributeType': 'S'  # 문자열 타입
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            # 테이블이 생성될 때까지 대기
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            print(f"테이블 '{table_name}' 생성 완료")
        else:
            print(f"테이블 '{table_name}'이(가) 이미 존재합니다")
            
        return dynamodb.Table(table_name)
    except Exception as e:
        print(f"테이블 생성 오류: {e}")
        return None

def upload_state_initial(dynamodb):
    """state_initial.json 파일을 DynamoDB에 업로드합니다."""

    
    try:
        current_dir = Path.cwd()
        file_path = current_dir / "HackingBlock" / "State_Initial" / "state_initial.json"
        print(f"파일 경로: {file_path}")
        if not file_path.exists():
            print(f"파일을 찾을 수 없습니다: {file_path}")
            return False
        
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        table = create_table_if_not_exists(dynamodb, "State_initial", "hack_enviornment")
        if table:
            # 키 값 "001"로 저장
            data["hack_enviornment"] = "001"
            
            response = table.put_item(Item=data)
            print(f"state_initial.json 업로드 완료: {response}")
            return True
    except Exception as e:
        print(f"state_initial.json 업로드 오류: {e}")
        return False

def upload_shell_commands(dynamodb):
    """shell_command.json 파일을 명령어별로 DynamoDB에 업로드합니다."""
    try:
        file_path = Path("HackingBlock/Command/shell_command.json")
        if not file_path.exists():
            print(f"파일을 찾을 수 없습니다: {file_path}")
            return False
        
        with open(file_path, 'r') as file:
            commands = json.load(file)
        
        table = create_table_if_not_exists(dynamodb, "Command_Block", "command_name")
        if table:
            success_count = 0
            for command in commands:
                # 각 명령어의 name 필드를 키로 사용
                command_name = command.get("name")
                if not command_name:
                    print(f"경고: name 필드가 없는 명령어를 건너뜁니다: {command}")
                    continue
                
                # command_name 필드를 추가하여 키로 사용
                command["command_name"] = command_name
                
                response = table.put_item(Item=command)
                success_count += 1
            
            print(f"shell_command.json 업로드 완료: {success_count}개 명령어 처리됨")
            return True
    except Exception as e:
        print(f"shell_command.json 업로드 오류: {e}")
        return False

def upload_text_file(dynamodb, file_path, file_name):
    """텍스트 파일을 DynamoDB에 업로드합니다."""
    try:
        if not Path(file_path).exists():
            print(f"파일을 찾을 수 없습니다: {file_path}")
            return False
        
        with open(file_path, 'r') as file:
            content = file.read()
        
        table = create_table_if_not_exists(dynamodb, "to_AI_information", "data_type")
        if table:
            item = {
                "data_type": file_name,
                "content": content
            }
            
            response = table.put_item(Item=item)
            print(f"{file_name} 업로드 완료: {response}")
            return True
    except Exception as e:
        print(f"{file_name} 업로드 오류: {e}")
        return False

def main():
    print("DynamoDB 데이터 업로드 시작...")
    
    # 현재 작업 디렉토리 가져오기
    current_dir = Path.cwd()
    print(f"현재 작업 디렉토리: {current_dir}")
    
    # DynamoDB 연결
    dynamodb = connect_to_dynamodb()
    if not dynamodb:
        print("DynamoDB 연결 실패. 프로그램을 종료합니다.")
        return
    
    # 1. state_initial.json 업로드
    upload_state_initial(dynamodb)
    

    return
    # 2. shell_command.json 업로드
    upload_shell_commands(dynamodb)
    
    # 3. shell_command_list.txt 및 shell_meta.txt 업로드 - 현재 디렉토리 기준 경로 사용
    command_list_path = current_dir / "HackingBlock" / "AI" / "shell_command_list.txt"
    shell_meta_path = current_dir / "HackingBlock" / "AI" / "shell_meta.txt"

    upload_text_file(dynamodb, str(command_list_path), "shell_command_list.txt")
    upload_text_file(dynamodb, str(shell_meta_path), "shell_meta.txt")
    
    print("모든 데이터 업로드가 완료되었습니다.")

if __name__ == "__main__":
    main()