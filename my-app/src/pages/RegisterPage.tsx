// src/pages/RegisterPage.jsx
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
} from "@mui/material";
import { useState } from "react";
import { register as apiRegister } from "../api/auth";

export default function RegisterPage() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [gender, setGender] = useState("");
  const [age, setAge] = useState("");
  const [interest, setInterest] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

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

  const handleChange = (e: any) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!gender || !age || !form.name || !form.email || !form.password) {
      return setError("모든 필수 항목을 입력해주세요.");
    }
    if (form.password !== form.confirm) {
      return setError("비밀번호가 일치하지 않습니다.");
    }

    try {
      const res = await apiRegister({
        name: form.name,
        email: form.email,
        password: form.password,
        gender,
        age: Number(age),
        interest,
      });
      const { ok, error } = res.data;
      if (ok) {
        setSuccess("회원가입이 완료되었습니다. 잠시 후 로그인 페이지로 이동합니다.");
        setTimeout(() => {
          window.location.href = "/login";
        }, 1500);
      } else {
        setError(error?.message || "이미 존재하는 이메일이거나 오류가 발생했습니다.");
      }
    } catch (err: any) {
      // 400 응답 시에도 err.response.data.message가 존재할 수 있음
      const responseData = err.response?.data;
      const serverMessage =
        responseData?.error?.message ||
        responseData?.message ||
        err.message;
      const details = Array.isArray(responseData?.error?.details)
        ? responseData.error.details.join(", ")
        : "";
      const message = details ? `${serverMessage} (${details})` : serverMessage;
      setError(message || "서버 오류가 발생했습니다.");
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
          width: 500,
          p: 3,
          backgroundColor: "var(--card)",
          color: "var(--fg)",
          border: "1px solid var(--border)",
          boxShadow: "0 12px 30px rgba(0, 0, 0, 0.25)",
        }}
      >
        <CardContent>
          <Typography variant="h5" gutterBottom align="center" sx={{ color: "var(--fg)" }}>
            회원가입
          </Typography>
          <form onSubmit={handleSubmit}>
            <Box sx={{ display: "flex", gap: 2 }}>
              <Box
                sx={{
                  flex: 1,
                  backgroundColor: "var(--bg-soft)",
                  border: "1px solid var(--border)",
                  p: 2,
                  borderRadius: 2,
                }}
              >
                <TextField
                  fullWidth
                  label="이름"
                  sx={inputStyles}
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="이메일"
                  sx={inputStyles}
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="비밀번호"
                  type="password"
                  sx={inputStyles}
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="비밀번호 확인"
                  type="password"
                  sx={inputStyles}
                  name="confirm"
                  value={form.confirm}
                  onChange={handleChange}
                  margin="normal"
                />
              </Box>
              {/* 오른쪽 묶음: 성별, 나이, 관심사 (파랑 배경) */}
              <Box
                sx={{
                  flex: 1,
                  backgroundColor: "var(--bg-soft)",
                  border: "1px solid var(--border)",
                  p: 2,
                  borderRadius: 2,
                }}
              >
                <Box sx={{ mt: 1, mb: 2 }}>
                  <FormLabel sx={{ color: "var(--muted)" }}>성별</FormLabel>
                  <RadioGroup row value={gender} onChange={(e: any) => setGender(e.target.value)}>
                    <FormControlLabel
                      value="남성"
                      sx={{ color: "var(--fg)" }}
                      control={<Radio sx={{ color: "var(--muted)", "&.Mui-checked": { color: "var(--accent)" } }} />}
                      label="남성"
                    />
                    <FormControlLabel
                      value="여성"
                      sx={{ color: "var(--fg)" }}
                      control={<Radio sx={{ color: "var(--muted)", "&.Mui-checked": { color: "var(--accent)" } }} />}
                      label="여성"
                    />
                  </RadioGroup>
                </Box>
                <TextField
                  fullWidth
                  label="나이"
                  sx={inputStyles}
                  type="number"
                  value={age}
                  onChange={(e: any) => setAge(e.target.value)}
                  required
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="관심사 (선택)"
                  sx={inputStyles}
                  placeholder="예: 게임, 뷰티, 운동"
                  value={interest}
                  onChange={(e: any) => setInterest(e.target.value)}
                  margin="normal"
                />
              </Box>
            </Box>
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ mt: 2 }}>
                {success}
              </Alert>
            )}
            <Button
              type="submit"
              variant="contained"
              fullWidth
              sx={{
                mt: 2,
                backgroundColor: "var(--accent)",
                color: "#fff",
                "&:hover": { backgroundColor: "var(--accent-600)" },
                "&:active": { backgroundColor: "var(--accent-700)" },
              }}
            >
              회원가입
            </Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}

