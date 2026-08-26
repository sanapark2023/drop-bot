# IG Auto Drop Post — OpenAI Supply Co. 무인 게시 파이프라인

매일 06:00 KST에 자동 실행: 스토어 감시 → **신규 드롭/재입고가 있을 때만** 캐러셀
10장 + 캡션 생성 → Instagram 공식 API로 @aisn0207에 자동 게시.

## 1회성 세팅 (10분)

1. **GitHub 저장소 생성** — github.com → New repository → 이름 아무거나(예:
   `drop-bot`) → **Public** (이미지가 raw URL로 접근 가능해야 API가 가져갈 수
   있음) → Create
2. **이 폴더 전체 업로드** — 저장소 페이지 → "uploading an existing file" 링크 →
   이 zip 압축 해제한 내용물 전부 드래그 → Commit
   - `.github` 폴더가 숨김이라 안 올라가면: 웹에서 Add file → Create new file →
     경로에 `.github/workflows/auto-post.yml` 입력 후 내용 붙여넣기
3. **Secrets 등록** — 저장소 → Settings → Secrets and variables → Actions →
   New repository secret:
   - `IG_ACCESS_TOKEN` = Generate Token으로 받은 긴 토큰
   - (앱 ID/시크릿은 현재 워크플로우에선 불필요 — 토큰 재발급 때만 개발자
     콘솔에서 다시 사용)
4. 끝. 매일 06:00 KST(21:00 UTC)에 자동 실행됨.

## 즉시 테스트

저장소 → Actions 탭 → "Auto Drop Post" → **Run workflow** → `force_post` 체크 →
Run. 신규 드롭이 없어도 아직 안 다룬 재고 제품 하나로 전체 사이클(생성→게시)을
강제 실행함. 몇 분 후 인스타 피드 확인.

## 동작 규칙

- 신규 드롭 발견 → "NEW DROP" 캐러셀 게시
- 재입고 발견 → "BACK IN STOCK" 캐러셀 게시
- 둘 다 없으면 → **게시 안 함** (스팸 방지; 강제하려면 force_post)
- 첫 실행은 기준 스냅샷만 저장
- 한 번 다룬 제품은 `state.json`의 posted 목록에 기록되어 중복 게시 방지
- 슬라이드 문구는 스크레이핑한 사실 + 고정 문구만 사용 (환각 방지)

## 토큰 관리 (중요)

장기 토큰은 **60일 유효**. 매일 실행되는 `refresh-token-reminder` 잡이 토큰을
검사해서 만료/무효 시 Actions가 **실패 알림**을 보냄. 그때:
개발자 콘솔 → Instagram → API setup with Instagram login → 계정 옆
Generate Token → 새 토큰 복사 → GitHub Secret `IG_ACCESS_TOKEN` 값 교체.
(달력에 55일 주기 알림을 걸어두는 걸 추천)

## 트러블슈팅

- **Actions 실패 + "PARSE FAILURE"**: OpenAI가 페이지 구조를 변경함.
  `pipeline/generate.py`의 `parse_products()` 셀렉터 수정 필요.
- **IG API error (media)**: raw.githubusercontent URL이 아직 전파 안 됐을 수
  있음 — 재실행(Re-run job)으로 대부분 해결.
- **게시 한도**: Instagram API는 계정당 24시간 게시 수 제한이 있음. 하루 1회
  스케줄에서는 문제없음.
- 계정 밴 리스크를 줄이려면 캡션/게시 규칙을 급격히 바꾸지 말고, API 외의
  비공식 자동화(브라우저 봇 등)와 병행하지 말 것.

## 파일 구조

- `pipeline/generate.py` — 감시·감지·선정·렌더링·캡션 (phase 1)
- `pipeline/slides.py` — 레이싱 시트 디자인 캐러셀 렌더러
- `pipeline/publish.py` — 공식 API 게시: 자식 컨테이너 → 캐러셀 컨테이너 →
  media_publish, 상태 폴링 포함 (phase 2)
- `.github/workflows/auto-post.yml` — 스케줄러 + 커밋 + 게시 + 토큰 검사
- `posts/YYYY-MM-DD/` — 그날 생성된 슬라이드와 manifest (자동 커밋됨)
