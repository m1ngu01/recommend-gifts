# RecommendGifts

## 프로젝트 명
- 선물추천 프로그램 (RecommendGifts)

## 기술 스택
- Frontend: React, Vite, TypeScript, Tailwind CSS, MUI, Emotion, Axios, React Router
- Backend: Python, Flask, Flask-CORS, Pydantic, Firebase Admin, PyJWT, bcrypt
- Data/ML: gensim, KoNLPy, scikit-learn, pandas, numpy
- Infra/DB: Firebase Firestore

## 구현 내용
- 회원가입/로그인, 프로필 수정, 마이페이지 등 기본 계정 기능
- 설문/키워드 입력 기반 선물 추천 및 추천 결과 상세 조회
- 즐겨찾기/평점/검색 로그 등 사용자 행동 데이터 수집
- 챗봇 기반 추천 대화 흐름 제공
- 관리자 대시보드 및 설문 피드백 관리
- 추천 모델 파이프라인(전처리, 모델링, 필터링, 스코어링, MMR) 구성

## 실행 방법
1) 백엔드 의존성 설치
```
pip install -r requirements.txt
```
2) 프론트엔드 의존성 설치
```
cd my-app
npm install
```
3) 실행
```
run.bat
```

기본 포트는 백엔드 8000, 프론트엔드 5173(Vite)입니다.

