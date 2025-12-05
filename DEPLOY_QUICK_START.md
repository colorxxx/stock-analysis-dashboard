# ⚡ Railway 빠른 배포 가이드

## 5분 안에 배포하기

### 1️⃣ GitHub Push (1분)
```bash
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### 2️⃣ Railway 프로젝트 생성 (2분)

1. https://railway.app 접속 → GitHub 로그인
2. "New Project" → "Deploy from GitHub repo"
3. Repository: `stock-analysis-dashboard` 선택
4. "Deploy Now" 클릭

### 3️⃣ 환경변수 설정 (1분)

**Web Service에서:**
- Settings → Variables
- Add Variable 클릭
  ```
  PERPLEXITY_API_KEY = pplx-your-key-here
  ```

### 4️⃣ 도메인 생성 (30초)

- Settings → Networking
- "Generate Domain" 클릭
- 예: `your-app.up.railway.app`

### 5️⃣ Cron Service 추가 (1분)

1. 프로젝트에서 "New" → "Empty Service"
2. Settings → Source → "Connect Repo" (같은 repo)
3. Settings → Deploy → Start Command:
   ```
   python3 cron_job.py
   ```
4. Settings → Variables:
   ```
   PERPLEXITY_API_KEY = pplx-your-key-here
   ```

### ✅ 완료!

- 🌐 웹사이트: `https://your-app.up.railway.app`
- 🤖 자동 업데이트: 매일 22:00 UTC
- 💾 캐시: 81개 종목 이미 준비됨

---

## 문제 발생 시

### 앱이 안 보이면?
```
Settings → Logs 확인
```

### "API 키 오류" 뜨면?
```
Settings → Variables에서 PERPLEXITY_API_KEY 확인
```

### 더 자세한 가이드?
```
RAILWAY_DEPLOYMENT.md 참조
```

---

**That's it!** 🎉
