import { useEffect, useMemo, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
} from "@mui/material";
import { fetchSurveyPrompt, submitSurveyAnswer } from "../api/survey";

const FALLBACK_PROMPT =
  "최근 검색 문장을 찾지 못했습니다. 최근에 입력했던 검색 문장을 떠올리며 개선 아이디어를 적어주세요.";

type SurveyModalProps = {
  open: boolean;
  onClose?: () => void;
};

export default function SurveyModal({ open, onClose }: SurveyModalProps) {
  const [text, setText] = useState("");
  const [reason, setReason] = useState("");
  const [prompt, setPrompt] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const maxLen = 500;
  const reasonMaxLen = 300;

  useEffect(() => {
    if (!open) {
      setText("");
      setReason("");
      setPrompt(null);
      return;
    }
    let mounted = true;
    const loadPrompt = async () => {
      setLoading(true);
      try {
        const res = await fetchSurveyPrompt();
        if (!mounted) return;
        const { ok, data } = res?.data || {};
        if (ok && data) {
          setPrompt(data);
        } else {
          setPrompt(null);
        }
      } catch (e) {
        if (mounted) {
          setPrompt(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };
    loadPrompt();
    return () => {
      mounted = false;
    };
  }, [open]);

  const activeSentence = useMemo(() => {
    if (prompt?.sentence) return prompt.sentence;
    return FALLBACK_PROMPT;
  }, [prompt]);

  const handleSubmit = async () => {
    if (!text.trim() || !reason.trim()) return;
    try {
      await submitSurveyAnswer({
        search_log_id: prompt?.id ?? null,
        search_sentence: activeSentence,
        answer: text.trim(),
        reason: reason.trim(),
      });
    } finally {
      sessionStorage.setItem("surveyDismissed", "1");
      onClose?.();
    }
  };

  const handleSkip = () => {
    sessionStorage.setItem("surveyDismissed", "1");
    onClose?.();
  };

  const canSubmit = Boolean(text.trim()) && Boolean(reason.trim());

  return (
    <Dialog open={open} onClose={handleSkip} fullWidth maxWidth="sm">
      <DialogTitle sx={{ color: "var(--fg)" }}>질문에 답변을 남겨주세요</DialogTitle>
      <DialogContent>
        <Typography variant="body2" sx={{ mb: 2, color: "var(--fg)" }}>
          {loading ? "검색 문장을 불러오는 중입니다..." : `“${activeSentence}”`}
        </Typography>
        <TextField
          multiline
          minRows={4}
          fullWidth
          value={text}
          onChange={(e) => setText(e.target.value.slice(0, maxLen))}
          helperText={`${text.length}/${maxLen}`}
          InputProps={{
            sx: {
              color: "var(--fg)",
              "& .MuiOutlinedInput-notchedOutline": { borderColor: "var(--border)" },
              "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "var(--accent)" },
              "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "var(--accent-600)" },
              backgroundColor: "var(--bg-soft)",
            },
          }}
        />
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, color: "var(--fg)" }}>
            위 답변을 선택한 이유를 알려주세요
          </Typography>
          <TextField
            multiline
            minRows={3}
            fullWidth
            value={reason}
            onChange={(e) => setReason(e.target.value.slice(0, reasonMaxLen))}
            helperText={`${reason.length}/${reasonMaxLen}`}
            InputProps={{
              sx: {
                color: "var(--fg)",
                "& .MuiOutlinedInput-notchedOutline": { borderColor: "var(--border)" },
                "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "var(--accent)" },
                "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "var(--accent-600)" },
                backgroundColor: "var(--bg-soft)",
              },
            }}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleSkip}>Skip</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={!canSubmit}>
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
}
