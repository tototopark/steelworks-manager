# checklist.md

- [x] Analyze legacy MariaDB schemas and PHP business logic
- [x] Configure core AGENTS.md, CLAUDE.md, and HOOKS_GUIDE.md policy documents
- [x] **1회성 관리 도구 및 데이터 이식 완료 (tests/)**:
  - [tests/db_init.py](file:///F:/pe/public_html/steelworks-manager/tests/db_init.py): 18개 테이블의 신규 스키마 자동 생성기 (메뉴 `101`).
  - [tests/import_legacy.py](file:///F:/pe/public_html/steelworks-manager/tests/import_legacy.py): 15MB 덤프 SQL에서 레코드를 파싱하여 이식하는 마이그레이션 도구 (메뉴 `102`).
  - [tests/smoke_check.py](file:///F:/pe/public_html/steelworks-manager/tests/smoke_check.py): 전수 테이블의 row count를 집계하여 데이터 무결성을 검증 (메뉴 `104`).
  - [tests/mock_data_generator.py](file:///F:/pe/public_html/steelworks-manager/tests/mock_data_generator.py): 현재 시간 기준의 테스트용 가상 난수 데이터 삽입기 (메뉴 `103`).
  - [tests/mock_data_cleaner.py](file:///F:/pe/public_html/steelworks-manager/tests/mock_data_cleaner.py): 가상 데이터 정리 유틸리티 (메뉴 `105`).
  - [tests/db_inspector.py](file:///F:/pe/public_html/steelworks-manager/tests/db_inspector.py): 테이블 구조 조회 및 마지막 10개 레코드 미리보기와 데이터 상위/하위 N개(입력 가능) 확인 도구 (메뉴 `100`).
- [x] **기초/사내 관리 마스터 파이프라인 완료 (skills/)**:
  - [skills/110_employee_master.py](file:///F:/pe/public_html/steelworks-manager/skills/110_employee_master.py): 사원 기본 정보 등록 및 조회 파이프라인 (메뉴 `110`).
  - [skills/120_reminder_master.py](file:///F:/pe/public_html/steelworks-manager/skills/120_reminder_master.py): 차량 및 기타 리마인더 등록 및 조회 파이프라인 (메뉴 `120`).
- [x] Implement skills/010_job_pipeline.py with special member prefix logic and Lot auto 'ready' rules
- [x] Implement skills/020_task_pipeline.py for group task creation and 10-person worker assignments
- [x] Implement skills/030_punch_pipeline.py for punchsheets logging and daily work man-hours calculation
- [x] Implement skills/040_inspect_pipeline.py for QA auditing and WIP version incremental reporting
- [x] Setup FastAPI based core/api_router.py boilerplate for future frontend integration
