import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Divider,
  Stack,
  Chip,
  CircularProgress,
} from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ChatBotBox from "../components/ChatBotBox";
import { triggerChatbotEvent, ChatbotAction, ChatbotResponse } from "../api/chatbot";
import { useToastContext } from "../components/ui/Toast";

type ChatMessage = {
  id: string;
  sender: "bot" | "user";
  message: string;
};

const SLOT_LABELS: Record<string, string> = {
  context: "상황",
  relationship: "관계",
  budget: "예산",
};

const PROFILE_LABELS: Record<string, string> = {
  gender: "성별",
  age: "나이",
  interest: "관심사",
};

export default function RecommendPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [actions, setActions] = useState<ChatbotAction[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expectedSlot, setExpectedSlot] = useState<string | null>(null);
  const [expectedField, setExpectedField] = useState<string | null>(null);
  const [slots, setSlots] = useState<Record<string, any>>({});
  const [profile, setProfile] = useState<Record<string, any>>({});
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [insights, setInsights] = useState<Array<Record<string, any>>>([]);
  const [querySentence, setQuerySentence] = useState<string | null>(null);
  const [autoNavigate, setAutoNavigate] = useState(false);
  const toast = useToastContext();
  const initializedRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const navigate = useNavigate();

  const appendMessage = useCallback((sender: "bot" | "user", message?: string) => {
    if (!message) return;
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), sender, message }]);
  }, []);

  const processResponse = useCallback(
    (resp: ChatbotResponse) => {
      appendMessage("bot", resp.message);
      setSessionId(resp.session_id);
      setActions(resp.actions || []);
      setSlots(resp.slots || {});
      setProfile(resp.profile || {});

      const extra = resp.data || {};
      setExpectedSlot(extra.expected_slot ?? null);
      setExpectedField(extra.expected_field ?? null);
      setRecommendations(Array.isArray(extra.items) ? extra.items : []);
      const keywordList =
        Array.isArray(extra.insights) && extra.insights.length > 0
          ? extra.insights
          : Array.isArray(extra.keywords)
          ? extra.keywords
          : [];
      setInsights(keywordList);
      const queryText = typeof extra.query_sentence === "string" ? extra.query_sentence : null;
      setQuerySentence(queryText);
      const hasItems = Array.isArray(extra.items) && extra.items.length > 0;
      const shouldAutoNavigate =
        queryText &&
        hasItems &&
        ((resp.flow === "similar" && resp.state === "SHOW_SIMILAR") ||
          (resp.flow === "keyword" && resp.state === "SHOW_RESULTS"));
      setAutoNavigate(!!shouldAutoNavigate);
    },
    [appendMessage]
  );

  const dispatchEvent = useCallback(
    async (event: string, payload?: Record<string, any>, userEcho?: string) => {
      if (userEcho) {
        appendMessage("user", userEcho);
      }
      try {
        setLoading(true);
        const data = await triggerChatbotEvent({
          session_id: sessionId,
          event,
          payload,
        });
        processResponse(data);
      } catch (error: any) {
        const message = error?.message || "챗봇 통신 중 오류가 발생했습니다.";
        toast.push({ type: "error", message });
        appendMessage("bot", "잠시 후 다시 시도해주세요.");
        setAutoNavigate(false);
      } finally {
        setLoading(false);
      }
    },
    [appendMessage, processResponse, sessionId, toast]
  );

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;
    dispatchEvent("start");
  }, [dispatchEvent]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (autoNavigate && querySentence && querySentence.trim()) {
      navigate("/recommend-result", { state: { sentence: querySentence.trim() } });
      setAutoNavigate(false);
    }
  }, [autoNavigate, querySentence, navigate]);

  const canType = Boolean(expectedSlot || expectedField);
  const placeholder = useMemo(() => {
    if (expectedSlot) {
      return `${SLOT_LABELS[expectedSlot] || "정보"}를 입력해주세요.`;
    }
    if (expectedField) {
      return `${PROFILE_LABELS[expectedField] || "정보"}를 입력해주세요.`;
    }
    return "현재는 제공된 버튼으로 진행해주세요.";
  }, [expectedSlot, expectedField]);

  const handleInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const value = input.trim();
     setAutoNavigate(false);
    if (expectedSlot) {
      dispatchEvent("submit_slot", { slot: expectedSlot, value }, value);
      setInput("");
      return;
    }
    if (expectedField) {
      dispatchEvent("provide_profile", { field: expectedField, value }, value);
      setInput("");
      return;
    }
    toast.push({ type: "info", message: "현재는 버튼을 통해 진행해주세요." });
  };

  const handleAction = (action: ChatbotAction) => {
    if (action.event === "confirm_keyword" && action.payload?.confirmed) {
      setAutoNavigate(true);
    } else {
      setAutoNavigate(false);
    }
    dispatchEvent(action.event, action.payload, action.label);
  };

  return (
    <Box sx={{ display: "flex", justifyContent: "center", py: 6, px: 2 }}>
      <Card
        sx={{
          width: "100%",
          maxWidth: 900,
          backgroundColor: "var(--card)",
          color: "var(--fg)",
          border: "1px solid var(--border)",
          boxShadow: "0 12px 30px rgba(0, 0, 0, 0.2)",
        }}
      >
        <CardContent>
          <Typography variant="h5" gutterBottom sx={{ color: "var(--fg)" }}>
            💬 선물 추천 챗봇
          </Typography>
          <Typography variant="body2" sx={{ mb: 2, color: "var(--muted)" }}>
            키워드 기반 질문 또는 비슷한 이용자 인기템 보기 플로우를 선택해 대화를 진행해보세요.
          </Typography>

          <Box
            sx={{
              height: 320,
              overflowY: "auto",
              backgroundColor: "var(--bg-soft)",
              border: "1px solid var(--border)",
              p: 2,
              borderRadius: 2,
              mb: 2,
            }}
          >
            {messages.map((msg) => (
              <ChatBotBox key={msg.id} sender={msg.sender} message={msg.message} />
            ))}
            {loading && (
              <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
                <CircularProgress size={24} sx={{ color: "var(--accent)" }} />
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>

          {actions.length > 0 && (
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mb: 2 }}>
              {actions.map((action) => (
                <Button
                  key={`${action.event}-${action.label}`}
                  variant="outlined"
                  size="small"
                  onClick={() => handleAction(action)}
                  disabled={loading}
                  sx={{
                    borderColor: "var(--accent)",
                    color: "var(--accent)",
                    "&:hover": { borderColor: "var(--accent-600)", color: "var(--accent-600)" },
                  }}
                >
                  {action.label}
                </Button>
              ))}
            </Stack>
          )}

          <form onSubmit={handleInputSubmit}>
            <TextField
              fullWidth
              placeholder={placeholder}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={!canType || loading}
              helperText={!canType ? "질문 버튼을 선택하면 입력창이 활성화됩니다." : ""}
              sx={{
                "& .MuiOutlinedInput-root": {
                  color: "var(--fg)",
                  backgroundColor: "var(--bg-soft)",
                  "& fieldset": { borderColor: "var(--border)" },
                  "&:hover fieldset": { borderColor: "var(--accent)" },
                  "&.Mui-focused fieldset": { borderColor: "var(--accent-600)" },
                },
                "& .MuiFormHelperText-root": { color: "var(--muted)" },
              }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{
                mt: 2,
                backgroundColor: "var(--accent)",
                color: "#fff",
                "&:hover": { backgroundColor: "var(--accent-600)" },
                "&:active": { backgroundColor: "var(--accent-700)" },
              }}
              disabled={!canType || loading}
            >
              전송
            </Button>
          </form>

          <Divider sx={{ my: 3, borderColor: "var(--border)" }} />

          {(Object.keys(slots).length > 0 || Object.keys(profile).length > 0) && (
            <Stack spacing={2} sx={{ mb: 3 }}>
              {Object.keys(slots).length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1, color: "var(--fg)" }}>
                    입력한 조건
                  </Typography>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    {Object.entries(slots).map(([key, value]) => (
                      <Chip key={key} label={`${SLOT_LABELS[key] || key}: ${value}`} size="small" />
                    ))}
                  </Stack>
                </Box>
              )}
              {Object.keys(profile).length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1, color: "var(--fg)" }}>
                    비슷한 이용자 정보
                  </Typography>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    {Object.entries(profile).map(([key, value]) => (
                      <Chip key={key} label={`${PROFILE_LABELS[key] || key}: ${value}`} size="small" color="secondary" />
                    ))}
                  </Stack>
                </Box>
              )}
            </Stack>
          )}

          {insights.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, color: "var(--fg)" }}>
                비슷한 이용자 키워드
              </Typography>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                {insights.map((item, idx) => (
                  <Chip key={`${item.keyword || idx}-${idx}`} label={`${item.keyword ?? "키워드"} (${item.count ?? "-"})`} variant="outlined" />
                ))}
              </Stack>
            </Box>
          )}

        </CardContent>
      </Card>
    </Box>
  );
}
