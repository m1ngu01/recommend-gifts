// src/pages/FindPasswordPage.jsx
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
} from "@mui/material";
import { useState } from "react";
import axios from "axios";

export default function FindPasswordPage() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState("");

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

  const handleFindPassword = async () => {
    try {
      const res = await axios.post("http://localhost:8000/api/find-password", {
        email,
      });

      if (res.data.success) {
        setResult("입력하신 이메일로 임시 비밀번호를 전송했습니다.");
      } else {
        setResult("해당 이메일로 등록된 계정을 찾을 수 없습니다.");
      }
    } catch (err) {
      setResult("요청 중 오류가 발생했습니다.");
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        py: 6,
        color: "var(--fg)",
      }}
    >
      <Card
        sx={{
          width: 400,
          backgroundColor: "var(--card)",
          color: "var(--fg)",
          border: "1px solid var(--border)",
          boxShadow: "0 12px 30px rgba(0, 0, 0, 0.25)",
        }}
      >
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ color: "var(--fg)" }}>
            🔐 비밀번호 찾기
          </Typography>

          <TextField
            fullWidth
            label="이메일"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            sx={{ mb: 2, ...inputStyles }}
          />
          <Button
            fullWidth
            variant="contained"
            onClick={handleFindPassword}
            sx={{
              backgroundColor: "var(--accent)",
              color: "#fff",
              "&:hover": { backgroundColor: "var(--accent-600)" },
              "&:active": { backgroundColor: "var(--accent-700)" },
            }}
          >
            임시 비밀번호 전송
          </Button>

          {result && (
            <Typography sx={{ mt: 2, color: "var(--muted)" }}>
              {result}
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
