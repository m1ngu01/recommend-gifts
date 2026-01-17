import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppHeader from "./components/layout/AppHeader";
import { CssBaseline } from "@mui/material";
import { ToastProvider } from "./components/ui/Toast";

// Import existing pages (JSX allowed via tsconfig allowJs)
import Main from "./pages/Main";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import MyPage from "./pages/MyPage";
import RecommendPage from "./pages/RecommendPage";
import RecommendResult from "./pages/RecommendResult";
import FindPasswordPage from "./pages/FindPasswordPage";
import GiftDetail from "./pages/GiftDetail";
import UserEditPage from "./pages/UserEditPage";
import AdminDashboard from "./pages/AdminDashboard";

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <CssBaseline />
        <AppHeader />
        <Routes>
          <Route path="/" element={<Main />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/mypage" element={<MyPage />} />
          <Route path="/mypage/edit" element={<UserEditPage />} />
          <Route path="/recommend" element={<RecommendPage />} />
          <Route path="/recommend-result" element={<RecommendResult />} />
          <Route path="/find-password" element={<FindPasswordPage />} />
          <Route path="/gift/:id" element={<GiftDetail />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;





