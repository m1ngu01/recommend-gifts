import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  MenuItem,
  Stack,
  Alert,
} from "@mui/material";
import { me, updateProfile } from "../api/auth";

type FormState = {
  name: string;
  gender: string;
  age: string;
  interest: string;
};

const genderOptions = [
  { label: "선택 안 함", value: "" },
  { label: "여성", value: "여성" },
  { label: "남성", value: "남성" },
  { label: "기타", value: "기타" },
];

export default function UserEditPage() {
  const [initialUser, setInitialUser] = useState<any>(null);
  const [form, setForm] = useState<FormState>({
    name: "",
    gender: "",
    age: "",
    interest: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const saved = localStorage.getItem("user");
    if (!saved) {
      alert("로그인이 필요합니다.");
      navigate("/login");
      return;
    }
    const parsed = JSON.parse(saved);
    setInitialUser(parsed);
    setForm({
      name: parsed?.name ?? "",
      gender: parsed?.gender ?? "",
      age: parsed?.age ? String(parsed.age) : "",
      interest: parsed?.interest ?? "",
    });
  }, [navigate]);

  const hasChanges = useMemo(() => {
    if (!initialUser) return false;
    return (
      (form.name ?? "") !== (initialUser.name ?? "") ||
      (form.gender ?? "") !== (initialUser.gender ?? "") ||
      (form.age ?? "") !== (initialUser.age ? String(initialUser.age) : "") ||
      (form.interest ?? "") !== (initialUser.interest ?? "")
    );
  }, [form, initialUser]);

  const handleChange = (field: keyof FormState) => (event: any) => {
    setForm((prev) => ({
      ...prev,
      [field]: event.target.value,
    }));
  };

  const handleSubmit = async (event: any) => {
    event.preventDefault();
    if (!initialUser) return;
    setError(null);
    setSuccess(null);

    if (!hasChanges) {
      setError("변경할 항목이 없습니다.");
      return;
    }

    if (!form.name.trim()) {
      setError("이름을 입력해주세요.");
      return;
    }

    const payload: Record<string, any> = {};
    if (form.name.trim() !== (initialUser.name ?? "")) {
      payload.name = form.name.trim();
    }
    const normalizedGender = form.gender || "";
    if (normalizedGender !== (initialUser.gender ?? "")) {
      payload.gender = normalizedGender || null;
    }
    const ageValue = form.age.trim();
    if (ageValue !== (initialUser.age ? String(initialUser.age) : "")) {
      if (ageValue) {
        const parsedAge = Number(ageValue);
        if (Number.isNaN(parsedAge)) {
          setError("나이는 숫자로 입력해주세요.");
          return;
        }
        payload.age = parsedAge;
      } else {
        payload.age = null;
      }
    }
    if ((form.interest ?? "") !== (initialUser.interest ?? "")) {
      payload.interest = form.interest.trim();
    }

    setSubmitting(true);
    try {
      const res = await updateProfile(payload);
      const { ok, data, error: err } = res?.data || {};
      if (!ok) {
        throw new Error(err?.message || "프로필 수정에 실패했습니다.");
      }

      let freshProfile = data;
      try {
        const profileRes = await me();
        if (profileRes?.data?.ok && profileRes.data.data) {
          freshProfile = profileRes.data.data;
        }
      } catch {
        // ignore, use response data
      }

      if (freshProfile) {
        localStorage.setItem("user", JSON.stringify(freshProfile));
        setInitialUser(freshProfile);
        setForm({
          name: freshProfile.name ?? "",
          gender: freshProfile.gender ?? "",
          age: freshProfile.age ? String(freshProfile.age) : "",
          interest: freshProfile.interest ?? "",
        });
      }
      setSuccess("프로필을 업데이트했습니다.");
      setTimeout(() => {
        navigate("/mypage");
      }, 800);
    } catch (e: any) {
      const message = e?.response?.data?.error?.message || e?.message || "프로필 수정 중 오류가 발생했습니다.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate("/mypage");
  };

  return (
    <Box
      sx={{
        minHeight: "80vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "var(--bg)",
        color: "var(--fg)",
        py: 6,
      }}
    >
      <Card
        component="form"
        onSubmit={handleSubmit}
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
          <Typography variant="h5" gutterBottom sx={{ color: "var(--fg)", fontWeight: 600 }}>
            프로필 수정
          </Typography>

          <Stack spacing={2} mt={2}>
            <TextField
              label="이름"
              value={form.name}
              onChange={handleChange("name")}
              required
              fullWidth
              InputLabelProps={{ sx: { color: "var(--muted)" } }}
              InputProps={{
                sx: {
                  color: "var(--fg)",
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--border)",
                  },
                  "&:hover .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--accent)",
                  },
                  "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--accent-600)",
                  },
                  backgroundColor: "var(--bg-soft)",
                },
              }}
            />
            <TextField
              select
              label="성별"
              value={form.gender}
              onChange={handleChange("gender")}
              fullWidth
              InputLabelProps={{ sx: { color: "var(--muted)" } }}
              InputProps={{
                sx: {
                  color: "var(--fg)",
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--border)",
                  },
                  "&:hover .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--accent)",
                  },
                  "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--accent-600)",
                  },
                  backgroundColor: "var(--bg-soft)",
                },
              }}
            >
              {genderOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="나이"
              value={form.age}
              onChange={handleChange("age")}
              type="number"
              inputProps={{ min: 0, max: 120 }}
              fullWidth
              InputLabelProps={{ sx: { color: "var(--muted)" } }}
              InputProps={{
                sx: {
                  color: "var(--fg)",
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--border)",
                  },
                  "&:hover .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--accent)",
                  },
                  "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--accent-600)",
                  },
                  backgroundColor: "var(--bg-soft)",
                },
              }}
            />
            <TextField
              label="관심사"
              value={form.interest}
              onChange={handleChange("interest")}
              fullWidth
              multiline
              minRows={2}
              InputLabelProps={{ sx: { color: "var(--muted)" } }}
              InputProps={{
                sx: {
                  color: "var(--fg)",
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--border)",
                  },
                  "&:hover .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--accent)",
                  },
                  "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                    borderColor: "var(--accent-600)",
                  },
                  backgroundColor: "var(--bg-soft)",
                },
              }}
            />
          </Stack>

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

          <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={submitting}
              sx={{
                backgroundColor: "var(--accent)",
                color: "#fff",
                "&:hover": { backgroundColor: "var(--accent-600)" },
                "&:active": { backgroundColor: "var(--accent-700)" },
              }}
            >
              저장
            </Button>
            <Button
              type="button"
              variant="outlined"
              fullWidth
              onClick={handleCancel}
              sx={{
                color: "var(--fg)",
                borderColor: "var(--border)",
                "&:hover": {
                  borderColor: "var(--accent)",
                  color: "var(--accent)",
                },
              }}
            >
              취소
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
