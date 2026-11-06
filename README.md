# 벽람항로 장비 배치기 (al-gear-planner)

벽람항로(아주르 레인) 한국 서버용 장비 배치 계산기다. 창고 장비 개수와 함대 편성을 넣으면, [REGAL 엔드게임 티어 목록](https://azur-lane-regal.suchiguma.com/)의 함선별·칸별 장비 우선순위에 따라 함선마다 장비를 나눠 준다. 게임을 조작하지 않는다. 결과를 보고 게임에서 직접 장비를 낀다.

- 원래 형태: claude.ai 아티팩트(웹 페이지). 저장은 아티팩트 DB, 캡처 인식은 Claude 호출(`sample`)을 쓴다.
- 이 저장소의 `index.html`은 브라우저에서 바로 여는 독립 실행판이다. 저장은 `localStorage`, 캡처 인식은 꺼진다. 처음 열면 `seed/`의 창고·함대 예시가 들어간다.
- 데이터 기준일: 2026-11-07 (REGAL 스냅샷).

## 파일 구성

| 경로 | 내용 |
|---|---|
| `index.html` | 독립 실행판. 브라우저로 열면 바로 동작한다 |
| `al_gear_planner.html` | claude.ai 아티팩트로 게시한 본문 (문서 골격은 게시할 때 붙는다) |
| `src/app_template.html` | 화면과 배치 로직 전체. `__DATA__` 자리에 데이터가 들어간다 |
| `src/build_data.py` | 원본 데이터 → `data/app_data.json` → 두 HTML을 만든다 |
| `data/regal_raw.json` | REGAL 사이트의 `ships.json`, `gear_map.json`, `equips.json` 스냅샷 (필요한 필드만) |
| `data/equip_lite.json` | altoy의 장비 데이터 (한국어 장비 이름, 종류, 진영) |
| `data/ship_group.json` | altoy의 함선 그룹 데이터 (한국어 함선 이름) |
| `data/app_data.json` | 앱에 들어가는 압축 데이터 |
| `seed/inventory.json` | 내 창고 장비 개수 (`{장비 id: 개수}`, 2026-10-28 캡처 기준 148종) |
| `seed/fleets.json` | 내 함대 편성 8개 (우선순위 순서) |
| `tests/render_test.js` | Playwright로 독립 실행판을 열어 배치 결과를 글로 뽑는다 |
| `tests/result_snapshot.txt` | 위 테스트의 현재 출력. 실행하지 않고 결과를 볼 때 쓴다 |

다시 만들기: `python3 src/build_data.py` → `node tests/render_test.js`

## 데이터 구조 (`data/app_data.json`)

- `E`: 장비 id → `[한국어 이름, 등급(1~6, 6=무지개), 종류 코드, 진영 코드]`
- `S`: 함선 목록. 각 항목은 `[uid, 한국어 이름, REGAL 이름, 함종, 진영, 레어도, 평가[14지 쫄, 14지 보스, 15·16지 쫄, 15·16지 보스, META], 칸 종류[5], 탭→usecase id, 잠수함 로드아웃, 진영 조건]`
- 칸별 우선순위는 REGAL 구조를 그대로 쓴다: `U[usecase] = [slot×5]` → `SL[slot] = [row…]`(위가 1순위) → `RW[row] = [equipKey…]` → `EK[equipKey] = 장비 id`(잠수함은 5칸 한 세트 배열)
- REGAL 탭: `C`, `C-13+`, `C-12-`(다중 웨이브), `C-AA`/`C-noAA`(항모: 적기 많음/적음), `L`/`M`/`H`(보스 경·중형·중장갑)
- `NOTE`: REGAL이 줄에 붙인 메모 ("Any 45 FP", "lower rarity ok" 등)

## 배치 규칙 (`allocate()` in `src/app_template.html`)

1. 함대 목록 순서대로 처리한다. 위 함대가 장비를 먼저 받는다.
2. 같은 함선이 두 함대에 있으면 먼저 나온 함대의 세팅을 같이 쓴다.
3. 탭 선택: 메인해역 모드는 `C-13+` → `C` 순. 항모는 `C-AA`(설정에 따라 `C-noAA`). 보스 모드는 `L`/`M`/`H`.
4. 잠수함: REGAL 로드아웃(5칸 한 세트) 중 창고로 가장 많이 채워지는 세트를 고른다. 같으면 위 순위 세트. 빈칸은 다른 세트의 같은 칸 → 같은 종류 장비 순으로 채운다. 이름이 같은 낮은 등급도 허용한다.
5. 수상함: 함대 안에서 1순위 줄을 모든 함선·칸에 먼저 채우고, 2순위 줄로 내려간다. 한 줄 안의 장비는 동급이라, 진영 조건 점수 → 등급 → 남은 개수 순으로 고른다.
6. 진영 조건(`hl`)의 `value`가 2 이상이고 칸이 1~2개면, 그 칸은 조건 진영 장비를 순위에 상관없이 먼저 찾는다.
7. 모든 함대를 처리한 뒤 2차: "any spare gun", "any Sardegna gear" 같은 와일드카드 줄로 빈칸을 채운다.
8. 3차: 그래도 빈칸이면 칸 종류에 맞는 장비 중 등급이 높은 것을 넣고 "목록 밖"으로 표시한다.
9. 진영 조건을 못 채운 함선에는 경고를 띄운다.
10. 요약: 1순위 줄인데 창고에 없는 장비를 필요한 칸 수로 집계한다. 어느 칸에도 안 들어간 5성 이상 장비도 보여 준다.

## 알려진 한계

- 강화 수치(+10, +13)를 모른다. 동급이면 등급과 개수로만 고른다.
- 증강 장비(augment)는 다루지 않는다.
- REGAL 메모 중 "Any 35/45 FP", "any 500+ HP" 같은 스탯 조건은 표시만 하고 계산에는 쓰지 않는다.
- 함대 안 1순위 우선 방식이라, 사람이 손으로 정한 배치와 몇 칸이 다를 수 있다.
- 창고 개수는 캡처 기준이라 함선이 끼고 있던 장비가 빠졌을 수 있다.

## 검토 요청 사항

다른 AI나 사람이 확인해 줬으면 하는 부분이다.

1. `allocate()`의 우선순위 규칙이 REGAL 표를 맞게 해석하는가. 특히 진영 조건(`hl`의 `value` 의미)과 잠수함 로드아웃 처리.
2. `tests/result_snapshot.txt`의 배치 결과에서 명백히 틀린 칸이 있는가 (칸 종류가 안 맞는 장비, 더 좋은 장비가 남아 있는데 낮은 순위가 들어간 칸).
3. `src/build_data.py`의 한국어 이름 매칭(장비 id ↔ altoy, 함선 group ↔ altoy)에 빠진 것이 있는가.
4. 화면(`index.html`)에서 버그나 쓰기 불편한 점.

## 출처

- REGAL: [2026 Endgame Azur Lane Tier List](https://azur-lane-regal.suchiguma.com/) — 함선 평가와 칸별 장비 우선순위. 데이터의 권리는 REGAL 제작자에게 있다.
- altoy: [장비 DB](https://jforplay.github.io/altoy/equip/equip-viewer/) — 한국어 장비·함선 이름.
