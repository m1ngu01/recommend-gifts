import {
  Box,
  Typography,
  Card,
  CardContent,
  CardMedia,
  Grid,
  CircularProgress,
  Chip,
  Stack,
} from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import client from "../api/client";
import axios from "axios";
import StarIcon from "@mui/icons-material/Star";
import CardGiftcardIcon from "@mui/icons-material/CardGiftcard";

type RecommendItem = {
  id?: string | number;
  name: string;
  image_url?: string | null;
  cost?: string | number | null;
  satisfaction?: number | string | null;
  review?: string | null;
  review_count?: number | null;
  tags?: string | null;
};

type FusionPayload = {
  query?: Record<string, unknown>;
  results: RecommendItem[];
  path1?: Array<Record<string, unknown>>;
  path2?: Array<Record<string, unknown>>;
};

type ParsedQuery = {
  sentence?: string;
  keywords?: string[];
  intent_tags?: string[];
  include_tags?: string[];
  category_candidates?: string[];
  notes?: string;
  budget?: {
    min?: number;
    max?: number;
    raw?: string;
  };
};

export default function RecommendResult() {
  const location = useLocation();
  const navState = (location.state as { sentence?: string; meta?: Record<string, unknown> } | null) ?? null;
  const sentence = navState?.sentence?.trim() ?? "";
  const [payload, setPayload] = useState<FusionPayload | null>(null);
  const results = payload?.results ?? [];
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [refreshToken, setRefreshToken] = useState(0);
  const navigate = useNavigate();
  const queryInfo = (payload?.query ?? {}) as ParsedQuery;
  const lastSentenceRef = useRef<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const formatElapsed = (totalSeconds: number) => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  };

  const coreTags = Array.from(
    new Set(
      [
        ...(Array.isArray(queryInfo.intent_tags) ? queryInfo.intent_tags : []),
        ...(Array.isArray(queryInfo.include_tags) ? queryInfo.include_tags : []),
        ...(Array.isArray(queryInfo.category_candidates) ? queryInfo.category_candidates : []),
      ]
        .map((tag) => `${tag}`.trim())
        .filter(Boolean)
    )
  );

  const extractedKeywords = Array.isArray(queryInfo.keywords)
    ? queryInfo.keywords.map((kw) => `${kw}`.trim()).filter(Boolean).slice(0, 15)
    : [];

  const budgetInfo = queryInfo?.budget ?? null;
  const budgetText = (() => {
    if (!budgetInfo) return "";
    const min = typeof budgetInfo.min === "number" && budgetInfo.min > 0 ? budgetInfo.min : undefined;
    const max = typeof budgetInfo.max === "number" && budgetInfo.max > 0 ? budgetInfo.max : undefined;
    const raw = typeof budgetInfo.raw === "string" ? budgetInfo.raw.trim() : "";
    if (raw) return raw;
    if (min && max) return `${min.toLocaleString()}원 ~ ${max.toLocaleString()}원`;
    if (max) return `${max.toLocaleString()}원 이하`;
    if (min) return `${min.toLocaleString()}원 이상`;
    return "";
  })();

  useEffect(() => {
    if (!sentence) {
      navigate("/recommend");
      return;
    }
    const requestKey = `${sentence}::${refreshToken}`;
    const isDuplicateRequest = lastSentenceRef.current === requestKey;
    lastSentenceRef.current = requestKey;
    setLoading(true);
    setError(null);
    setElapsed(0);
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    timerRef.current = setInterval(() => setElapsed((prev) => prev + 1), 1000);

    const fetchData = async () => {
      try {
        const res = await client.post("/api/recommend?engine=v2", { sentence });
        const { ok, data } = res.data;
        if (ok && data) {
          const fusion = data as FusionPayload;
          setPayload({
            query: fusion.query,
            results: Array.isArray(fusion.results) ? fusion.results : [],
            path1: fusion.path1,
            path2: fusion.path2,
          });
        } else {
          setPayload({ results: [] });
        }
      } catch (err: any) {
        console.error("추천 결과 요청 실패:", err);
        const isTimeout = axios.isAxiosError(err) && err.code === "ECONNABORTED";
        const message = isTimeout
          ? "추천 계산에 시간이 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요."
          : "추천 결과를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.";
        setError(message);
        setPayload({ results: [] });
      } finally {
        setLoading(false);
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      }
    };

    if (!isDuplicateRequest) {
      fetchData();
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [sentence, navigate, refreshToken]);

  if (loading) {
    return (
      <Box sx={{ textAlign: "center", py: 8, color: "var(--fg)" }}>
        <CircularProgress sx={{ color: "var(--accent)" }} />
        <Typography sx={{ mt: 2, color: "var(--fg)" }}>
          추천 결과를 불러오는 중입니다... ({formatElapsed(elapsed)})
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: "center", py: 8, color: "var(--fg)" }}>
        <Typography sx={{ color: "var(--fg)", mb: 2 }}>{error}</Typography>
        <Typography
          component="button"
          onClick={() => {
            lastSentenceRef.current = null;
            setElapsed(0);
            setError(null);
            setPayload(null);
            setRefreshToken((prev) => prev + 1);
          }}
          sx={{
            border: "1px solid var(--border)",
            px: 3,
            py: 1,
            borderRadius: 2,
            backgroundColor: "var(--card)",
            cursor: "pointer",
          }}
        >
          다시 시도
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ px: 4, py: 6, alignItems: "center", color: "var(--fg)" }}>
      {/* 추천 문장 강조 영역 */}
      <Box
        sx={{
          backgroundColor: "var(--bg-soft)",
          border: "1px solid var(--border)",
          borderRadius: 2,
          px: 3,
          py: 2,
          mb: 4,
          display: "flex",
          alignItems: "center",
          gap: 1,
        }}
      >
        <CardGiftcardIcon sx={{ color: "var(--accent)" }} />
        <Typography variant="h6" sx={{ fontWeight: "bold", color: "var(--fg)" }}>
          “{sentence}”에 맞는 추천 선물을 모아봤어요!
        </Typography>
      </Box>

      {(coreTags.length > 0 || extractedKeywords.length > 0 || budgetText) && (
        <Box
          sx={{
            backgroundColor: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 2,
            px: 3,
            py: 2.5,
            mb: 4,
          }}
        >
          <Typography variant="subtitle1" sx={{ fontWeight: 600, color: "var(--fg)", mb: 1 }}>
            추천 기준 키워드
          </Typography>
          {coreTags.length > 0 && (
            <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mb: extractedKeywords.length > 0 || budgetText ? 1.5 : 0 }}>
              {coreTags.map((tag) => (
                <Chip key={`core-${tag}`} label={tag} size="small" sx={{ backgroundColor: "var(--bg-soft)", color: "var(--fg)" }} />
              ))}
            </Stack>
          )}
          {extractedKeywords.length > 0 && (
            <Typography variant="body2" sx={{ color: "var(--muted)", mb: budgetText ? 1 : 0 }}>
              추출된 키워드: {extractedKeywords.join(", ")}
            </Typography>
          )}
          {budgetText && (
            <Typography variant="body2" sx={{ color: "var(--muted)" }}>
              예산 조건: {budgetText}
            </Typography>
          )}

        </Box>
      )}

      {/* 제목 */}
      <Typography variant="h5" gutterBottom sx={{ color: "var(--fg)" }}>
        🎁 추천 결과
      </Typography>

      {results.length === 0 ? (
        <Typography sx={{ color: "var(--muted)" }}>추천할 선물이 없습니다.</Typography>
      ) : (
        <Grid container spacing={4} justifyContent="center">
          {results.map((item, idx) => (
            <Grid
              item
              xs={6}
              sm={6}
              md={4}
              lg={3}
              key={idx}
              display="flex"
              justifyContent="center"
              alignItems="stretch"
            >
              <Card
                sx={{
                  height: "100%",
                  minHeight: 420,
                  width: "100%",
                  maxWidth: 320,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  p: 2,
                  backgroundColor: "var(--card)",
                  color: "var(--fg)",
                  border: "1px solid var(--border)",
                  boxShadow: "0 12px 30px rgba(0, 0, 0, 0.25)",
                  borderRadius: 2,
                  position: "relative",
                  cursor: "pointer",
                }}
                onClick={() => navigate(`/gift/${item.id ?? idx}` as string, { state: { item } })}
              >
                {/* 순위 표시 */}
                <Box
                  sx={{
                    position: "absolute",
                    top: 8,
                    left: 8,
                    backgroundColor: "var(--accent)",
                    color: "#fff",
                    borderRadius: "50%",
                    width: 24,
                    height: 24,
                    fontSize: 12,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {idx + 1}
                </Box>

                {/* 이미지 */}
                <CardMedia
                  component="img"
                  image={item.image_url || ""}
                  alt={item.name || "추천 이미지"}
                  sx={{
                    width: "100%",
                    height: 160,
                    objectFit: "cover",
                    borderRadius: 1,
                    mb: 1,
                  }}
                />

                {/* 내용 */}
                <CardContent sx={{ flexGrow: 1, px: 0 }}>
                  <Typography
                    variant="subtitle1"
                    sx={{
                      display: "-webkit-box",
                      overflow: "hidden",
                      WebkitBoxOrient: "vertical",
                      WebkitLineClamp: 2,
                      height: "3rem",
                      fontWeight: 600,
                      mb: 0.5,
                    }}
                  >
                    {item.name}
                  </Typography>
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: "bold", mb: 0.5, color: "var(--accent)" }}
                  >
                    {item.cost ?? "가격 정보 없음"}
                  </Typography>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                    <StarIcon sx={{ color: "#FFD700", fontSize: 16, mr: 0.5 }} />
                    <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                      만족도 {item.satisfaction ? `${item.satisfaction}` : "정보 없음"}
                      {typeof item.review_count === "number" && item.review_count > 0 ? ` · 리뷰 ${item.review_count}` : ""}
                    </Typography>
                  </Box>
                  <Typography
                    variant="body2"
                    sx={{
                      overflow: "hidden",
                      display: "-webkit-box",
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: "vertical",
                      fontSize: "0.85rem",
                      color: "var(--muted)",
                    }}
                  >
                    {item.review ?? item.tags ?? "상세 설명이 제공되지 않은 상품입니다."}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}






