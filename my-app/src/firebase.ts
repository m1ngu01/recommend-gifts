import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

// Firebase 프로젝트 설정
// Firebase JS SDK v7.20.0 이후에는 measurementId가 선택사항입니다.
const firebaseConfig = {
  apiKey: "AIzaSyB1j8Cv1uN8NvP1rC27lPqRlJZqi7y4g6U",
  authDomain: "recommendgift-67d70.firebaseapp.com",
  projectId: "recommendgift-67d70",
  storageBucket: "recommendgift-67d70.firebasestorage.app",
  messagingSenderId: "904550805753",
  appId: "1:904550805753:web:1e0c1fd279335715ea3228",
  measurementId: "G-VTTNTQ74CD",
};

export const firebaseApp = initializeApp(firebaseConfig);

export const firebaseAnalytics =
  typeof window !== "undefined" ? getAnalytics(firebaseApp) : undefined;

