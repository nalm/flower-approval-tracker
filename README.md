# 꽃 데이터노트

이재명 대통령의 국정운영 평가를 여론조사꽃의 전화면접·ARS 조사로 비교하는 정적 웹앱입니다. 외부 차트 라이브러리나 외부 폰트 없이 작동합니다.

## 실행

```powershell
python -m http.server 4318 --bind 127.0.0.1
```

브라우저에서 http://127.0.0.1:4318 을 엽니다. `index.html`을 직접 열어도 동작합니다.

## 자료 범위

- 출처: 중앙선거여론조사심의위원회 등록자료와 첨부 결과표
- 검색: 조사기관 `꽃`, 등록일 2025-06-04부터 2026-10-28까지
- 검색 229건 → 여론조사꽃 전국 정례조사 129건 → 국정운영 평가 128건
- 전화면접 64건 / ARS 64건, 종료일 2025-06-21 ~ 2026-10-24
- 제외: 등록 14406, 2025-06-06~07 CATI의 국정운영 기대감 문항
- 마지막 확인·반영: 2026-10-28 (한국시간)
- 모든 수록 조사의 전국 전체 행과 질문을 원문 PDF 렌더링 이미지로 대조했습니다. 표본 수는 등록 개요와 대조하고 응답 비율 및 세부 응답 합계도 검사했습니다.
- 10일 초과 수록 공백은 선을 끊습니다. 원문 누락과 실제 조사 미실시는 구별할 수 없어 ‘수록 공백’으로 표시합니다.
- 등록자료는 위원회가 사전 검증한 자료라는 뜻이 아닙니다.

## 반자동 업데이트

수집과 공개 반영을 분리합니다. `collect.py`와 `extract.py`는 공개 데이터를 변경하지 않습니다.

```powershell
python -m pip install -r requirements.txt
python scripts/collect.py --details --end 2026-10-28 --refresh
python scripts/extract.py
python scripts/review_sheets.py
```

1. `research/candidates.json`의 문제·제외 목록과 새 회차를 확인합니다.
2. `research/review/` 원문 표 이미지를 `candidates.json`의 표본 수·긍정·부정·기타 수치와 대조합니다. 메타데이터는 `detail-ID.html`과 대조합니다.
3. 검토한 ID와 원문 PDF SHA-256만 `research/review.json`의 `approved`에 기록하고 `reviewedAt`을 한국 날짜로 갱신합니다. 형식: `{"reviewedAt":"YYYY-MM-DD","approved":{"ID":"PDF_SHA256"}}`.
4. 질문 변경 여부도 확인합니다. 문항이 바뀌면 `publish_data.py`의 질문 전사와 포함 기준을 검토합니다.
5. `python scripts/publish_data.py`를 실행합니다. 미승인 원문·중복 ID·동일 방식/종료일 중복·비율 합계 오류는 공개 반영을 막습니다.
6. 브라우저에서 최신 수치·변화·원문을 확인한 뒤 GitHub에 변경을 올려 배포합니다.

`--end`를 생략하면 한국시간 오늘까지 수집합니다. `--refresh`는 캐시를 새 공개 원문으로 갱신하므로 정정 자료 확인 시 사용합니다. 원문 PDF·HTML·검토 이미지는 로컬 `research/`에만 보관하며 공개 저장소에 올리지 않습니다. 새 환경에서는 원문을 재수집하고 다시 검토해야 합니다.

## 파일

- `index.html`, `style.css`, `app.js`: 반응형 화면과 SVG 차트
- `data.json`: 출처와 검토 이력이 포함된 공개 데이터
- `data.js`: 서버 없이도 작동하는 동일 데이터
- `scripts/`: 수집·추출·검토·검증된 데이터 반영
- `research/`: 원문·후보 데이터·원문 대조 기록 (Git 제외)

GitHub Pages는 저장소 루트에서 배포합니다. `.nojekyll`과 모든 상대경로를 포함하므로 프로젝트 하위 경로에서도 작동합니다.
