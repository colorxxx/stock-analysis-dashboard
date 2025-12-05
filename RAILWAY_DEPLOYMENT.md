# 🚂 Railway 배포 가이드

## 개요
Railway에 Streamlit 앱과 자동 AI 분석 시스템을 배포하는 완벽한 가이드입니다.

Railway는 두 가지 서비스를 실행합니다:
1. **Web Service**: Streamlit 앱 (사용자 인터페이스)
2. **Cron Service**: 매일 자동 분석 업데이트 (백그라운드)

## 📋 사전 준비

### 1. Railway 계정 생성
- https://railway.app 접속
- GitHub 계정으로 로그인

### 2. GitHub Repository 준비
```bash
# 모든 변경사항 커밋
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 3. 필요한 파일 확인
✅ `Procfile` - Railway 실행 명령
✅ `railway.json` - Railway 설정
✅ `railway.toml` - 빌드 설정
✅ `requirements.txt` - Python 패키지
✅ `cron_job.py` - 자동 업데이트 서비스
✅ `daily_update.py` - 업데이트 로직
✅ `stock_data.db` - 캐시 데이터베이스 (Git 포함됨)

## 🚀 배포 단계

### Step 1: Railway 프로젝트 생성

1. **Railway Dashboard 접속**
   - https://railway.app/dashboard

2. **New Project 클릭**

3. **Deploy from GitHub repo 선택**
   - GitHub repository: `stock-analysis-dashboard` 선택
   - Branch: `main` 선택

### Step 2: Web Service 설정 (Streamlit 앱)

Railway가 자동으로 감지하지만, 확인이 필요합니다:

1. **프로젝트 생성 후 서비스 클릭**

2. **Settings 탭 이동**

3. **Environment Variables 추가**
   ```
   PERPLEXITY_API_KEY=your_api_key_here
   PORT=8501
   ```

4. **Deploy 설정 확인**
   - Start Command: 자동 감지됨 (`Procfile` 사용)
   - 또는 수동 설정:
     ```
     streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
     ```

5. **Generate Domain**
   - Settings → Networking
   - "Generate Domain" 클릭
   - 예: `stock-analysis-dashboard.up.railway.app`

### Step 3: Cron Service 추가 (자동 업데이트)

Railway에서는 같은 프로젝트에 여러 서비스를 추가할 수 있습니다.

#### Option A: 별도 Cron Service (추천)

1. **프로젝트 내에서 "New" 클릭**

2. **"Empty Service" 선택**

3. **서비스 이름 변경**
   - 서비스 클릭 → Settings → Name: "cron-service"

4. **GitHub Repo 연결**
   - Settings → Source
   - "Connect Repo" 클릭
   - 같은 repository 선택

5. **Environment Variables 추가**
   ```
   PERPLEXITY_API_KEY=your_api_key_here
   ```

6. **Start Command 설정**
   - Settings → Deploy
   - Start Command:
     ```
     python3 cron_job.py
     ```

7. **Watch Paths 설정 (선택사항)**
   - Settings → Deploy → Watch Paths
   - `cron_job.py, daily_update.py, perplexity_analyzer.py`

#### Option B: Railway Cron Plugin (대안)

Railway Cron Plugin을 사용할 수도 있습니다:

1. **프로젝트에서 "New" → "Plugin" → "Cron"**

2. **Schedule 설정**
   ```
   0 22 * * 1-5
   ```
   (월-금 22:00 UTC)

3. **Command 설정**
   ```
   python3 daily_update.py
   ```

### Step 4: 데이터베이스 지속성

Railway는 ephemeral storage를 사용하므로 데이터베이스를 Git에 커밋해야 합니다.

✅ **이미 완료됨:**
- `.gitignore`에 `!stock_data.db` 추가됨
- `stock_data.db`가 Git에 포함됨

**업데이트 방식:**

1. **Cron Service가 daily_update.py 실행**
2. **stock_data.db 업데이트**
3. **변경사항을 Git에 자동 커밋** (옵션)

#### 자동 Git Push 설정 (선택사항)

Cron service에서 자동으로 DB를 커밋하려면:

**cron_job.py 수정 필요:**
```python
# After successful update
subprocess.run(['git', 'config', 'user.name', 'Railway Bot'])
subprocess.run(['git', 'config', 'user.email', 'bot@railway.app'])
subprocess.run(['git', 'add', 'stock_data.db'])
subprocess.run(['git', 'commit', '-m', f'Auto-update cache: {datetime.now()}'])
subprocess.run(['git', 'push'])
```

**Railway에 GitHub Token 추가:**
- Settings → Environment Variables
- `GITHUB_TOKEN=ghp_...` (Personal Access Token)

## 🔒 환경 변수 설정

### Web Service (Streamlit)
```
PERPLEXITY_API_KEY=pplx-xxxxx
PORT=8501
```

### Cron Service
```
PERPLEXITY_API_KEY=pplx-xxxxx
GITHUB_TOKEN=ghp_xxxxx (선택사항, 자동 커밋용)
```

## 📊 배포 확인

### 1. Web Service 확인
- Railway Dashboard → Web Service → Logs
- 또는 생성된 도메인 접속

예상 로그:
```
You can now view your Streamlit app in your browser.
Network URL: http://0.0.0.0:8501
```

### 2. Cron Service 확인
- Railway Dashboard → Cron Service → Logs

예상 로그:
```
🚀 Railway Cron Job Service Started
📅 Current time: 2025-12-05 22:00:00
⏰ Schedule: Daily at 22:00 UTC
```

### 3. 앱 테스트
1. 생성된 도메인 접속
2. 종목 선택 (예: AAPL, TSLA)
3. 차트 확장
4. **✅ AI 분석** 섹션에서 캐시된 결과 즉시 표시 확인

## 🛠️ 문제 해결

### Q: Web service가 시작되지 않음
**A:**
1. Logs 확인
2. Requirements.txt의 모든 패키지가 설치되었는지 확인
3. PORT 환경변수 설정 확인
4. Start command 확인:
   ```
   streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

### Q: Cron service가 실행되지 않음
**A:**
1. Start command 확인: `python3 cron_job.py`
2. Logs에서 에러 확인
3. PERPLEXITY_API_KEY 설정 확인

### Q: Database 업데이트가 반영되지 않음
**A:**
1. Cron service 로그 확인
2. GitHub repository에 커밋이 되었는지 확인
3. Web service를 수동으로 재배포:
   - Settings → "Redeploy" 클릭

### Q: API 키 오류
**A:**
```
⚠️ API 키 오류: Perplexity API 키가 필요합니다
```
- Environment Variables에 `PERPLEXITY_API_KEY` 추가
- 서비스 재시작

### Q: "분석이 준비되지 않았습니다" 메시지
**A:**
1. stock_data.db에 해당 종목 캐시가 있는지 확인
2. Cron service가 실행 중인지 확인
3. 수동으로 batch_analyze_all.py 실행 필요할 수 있음

## 💰 비용 예상

Railway 무료 플랜:
- ✅ $5/월 크레딧 제공
- ✅ 500시간 실행 시간
- ✅ 소규모 앱에 충분

예상 사용량:
- **Web Service**: 24/7 실행 = ~720시간/월
- **Cron Service**: 1분 실행/일 × 30일 = ~30분/월
- **총**: ~720시간/월

**무료 플랜 초과 시:**
- Pro Plan: $20/월부터 시작

## 🔄 업데이트 및 유지보수

### 코드 업데이트
```bash
# 로컬에서 변경
git add .
git commit -m "Update feature"
git push

# Railway가 자동으로 재배포
```

### 수동 업데이트 실행
Railway Dashboard에서:
1. Cron Service 클릭
2. Logs 탭에서 현재 실행 확인
3. 또는 서비스 재시작

### 캐시 확인
```bash
# 로컬에서
python3 check_analysis_length.py

# 또는 Railway Shell에서
# Settings → Shell → "Open Shell"
python3 check_analysis_length.py
```

## 📈 모니터링

### Railway Logs
- Dashboard → Service → Logs
- 실시간 로그 스트리밍
- 에러 확인 가능

### Metrics
- Dashboard → Service → Metrics
- CPU, Memory, Network 사용량
- 응답 시간

### Alerts (Pro Plan)
- Settings → Notifications
- 에러 발생 시 이메일 알림

## 🎯 최적화 팁

### 1. 메모리 사용량 줄이기
```python
# app.py에서
import gc
gc.collect()  # 주기적으로 호출
```

### 2. 로그 레벨 조정
```python
import logging
logging.basicConfig(level=logging.WARNING)
```

### 3. 캐시 정리 (선택사항)
```python
# 6개월 이전 데이터 삭제
# daily_update.py에 추가
conn = sqlite3.connect(DB_FILE)
conn.execute("DELETE FROM perplexity_analysis WHERE date < date('now', '-6 months')")
conn.commit()
```

## 🔐 보안

### API 키 관리
- ✅ Railway Environment Variables 사용
- ❌ 코드에 하드코딩 금지
- ❌ .env 파일을 Git에 커밋 금지

### GitHub Token (자동 커밋용)
- Personal Access Token 생성
- Scope: `repo` (Full control)
- Railway Environment Variables에 추가

## 📚 참고 자료

- Railway 공식 문서: https://docs.railway.app
- Streamlit 배포 가이드: https://docs.streamlit.io/deploy
- 자동화 시스템 문서: `AUTOMATIC_ANALYSIS_README.md`

## ✅ 배포 체크리스트

배포 전:
- [ ] GitHub에 모든 파일 푸시
- [ ] Perplexity API 키 준비
- [ ] stock_data.db가 Git에 포함되어 있는지 확인

Railway 설정:
- [ ] Web Service 생성 및 배포
- [ ] Web Service 도메인 생성
- [ ] Cron Service 생성 및 배포
- [ ] 두 서비스에 환경변수 추가
- [ ] Logs에서 에러 없는지 확인

테스트:
- [ ] 웹사이트 접속
- [ ] 종목 차트 확인
- [ ] AI 분석 결과 표시 확인
- [ ] Cron service 로그 확인
- [ ] 매일 22:00 UTC에 업데이트 실행 확인

완료!
- [ ] 도메인 URL 북마크
- [ ] Railway 대시보드 북마크
- [ ] 매주 로그 확인

---

**준비 완료!** Railway에 배포하세요! 🚀
