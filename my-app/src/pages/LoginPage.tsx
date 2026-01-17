import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Link,
  Alert,
} from "@mui/material";
import { useState } from "react";
import { login } from "../api/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const inputStyles = {
    "& .MuiOutlinedInput-root": {
      color: "var(--fg)",
      backgroundColor: "var(--bg-soft)",
      "& fieldset": { borderColor: "var(--border)" },
      "&:hover fieldset": { borderColor: "var(--accent)" },
      "&.Mui-focused fieldset": { borderColor: "var(--accent-600)" },
    },
    "& .MuiInputLabel-root": { color: "var(--muted)" },
    "& .MuiInputLabel-root.Mui-focused": { color: "var(--accent)" },
  };

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("이메일과 비밀번호를 입력해주세요.");
      return;
    }

    try {
      const res = await login({ email, password });
      const { ok, data } = res.data;
      if (!ok) throw new Error("login_failed");
      const { token, profile } = data;
      localStorage.setItem("user", JSON.stringify({ ...profile, token }));
      const target = profile?.role === "admin" ? "/admin" : "/";
      window.location.href = target;
    } catch (err: any) {
      const message =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        err?.message ||
        "로그인에 실패했습니다. 잠시 후 다시 시도해주세요.";
      setError(message);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "var(--bg)",
        color: "var(--fg)",
        py: 6,
      }}
    >
      <Card
        sx={{
          width: 400,
          p: 3,
          backgroundColor: "var(--card)",
          color: "var(--fg)",
          border: "1px solid var(--border)",
          boxShadow: "0 12px 30px rgba(0, 0, 0, 0.25)",
        }}
      >
        <CardContent>
          <Typography variant="h5" gutterBottom align="center" sx={{ color: "var(--fg)" }}>
            로그인
          </Typography>

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="이메일"
              variant="outlined"
              margin="normal"
              value={email}
              onChange={(e: any) => setEmail(e.target.value)}
              sx={inputStyles}
            />
            <TextField
              fullWidth
              label="비밀번호"
              type="password"
              variant="outlined"
              margin="normal"
              value={password}
              onChange={(e: any) => setPassword(e.target.value)}
              sx={inputStyles}
            />
            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
            <Button
              type="submit"
              variant="contained"
              fullWidth
              sx={{
                mt: 2,
                mb: 1,
                backgroundColor: "var(--accent)",
                color: "#fff",
                "&:hover": { backgroundColor: "var(--accent-600)" },
                "&:active": { backgroundColor: "var(--accent-700)" },
              }}
            >
              로그인
            </Button>
          </form>

          <Box sx={{ display: "flex", justifyContent: "space-between" }}>
            <Link
              href="/find-password"
              underline="hover"
              sx={{ color: "var(--accent)", "&:hover": { color: "var(--accent-600)" } }}
            >
              비밀번호 찾기
            </Link>
            <Link
              href="/register"
              underline="hover"
              sx={{ color: "var(--accent)", "&:hover": { color: "var(--accent-600)" } }}
            >
              회원가입
            </Link>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}


