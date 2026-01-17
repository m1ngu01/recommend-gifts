import { useEffect, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Stack,
  Alert,
} from "@mui/material";
import { fetchSearchFeedback, approveSearchFeedback, rejectSearchFeedback, fetchAdminInsights } from "../api/admin";
import { me } from "../api/auth";

export default function AdminDashboard() {
  const [feedback, setFeedback] = useState<any[]>([]);
  const [adminProfile, setAdminProfile] = useState<any>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [alert, setAlert] = useState<{ severity: "success" | "error"; message: string } | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    const verifyAdmin = async () => {
      try {
        const res = await me();
        const { ok, data } = res?.data || {};
        if (!mounted) return;
        if (ok && data?.role === "admin") {
          setAdminProfile(data);
          try {
            localStorage.setItem("user", JSON.stringify(data));
          } catch {
            /* ignore */
          }
        } else {
          setAdminProfile(null);
        }
      } catch {
        if (mounted) {
          setAdminProfile(null);
        }
      } finally {
        if (mounted) {
          setAuthChecked(true);
        }
      }
    };

    verifyAdmin();
    return () => {
      mounted = false;
    };
  }, []);

  const loadFeedback = async () => {
    setFeedbackLoading(true);
    try {
      const res = await fetchSearchFeedback("pending");
      const { ok, data } = res?.data || {};
      if (ok && data?.items) {
        setFeedback(data.items);
      } else {
        setFeedback([]);
      }
    } catch (e) {
      console.error(e);
      setAlert({ severity: "error", message: "피드백을 불러오는 중 오류가 발생했습니다." });
    } finally {
      setFeedbackLoading(false);
    }
  };

  const loadInsights = async () => {
    setInsightsLoading(true);
    try {
      const res = await fetchAdminInsights();
      const { ok, data } = res?.data || {};
      if (ok && data) {
        setInsights(data);
      } else {
        setInsights(null);
      }
    } catch (e) {
      console.error(e);
      setAlert({ severity: "error", message: "인사이트를 불러오는 중 오류가 발생했습니다." });
    } finally {
      setInsightsLoading(false);
    }
  };

  const isAdmin = adminProfile?.role === "admin";

  useEffect(() => {
    if (!isAdmin) return;
    loadFeedback();
    loadInsights();
  }, [isAdmin]);

  const handleApprove = async (id: string) => {
    try {
      await approveSearchFeedback(id);
      setAlert({ severity: "success", message: "피드백을 승인했습니다." });
      loadFeedback();
    } catch (e) {
      console.error(e);
      setAlert({ severity: "error", message: "피드백 승인에 실패했습니다." });
    }
  };

  const handleReject = async (id: string) => {
    try {
      await rejectSearchFeedback(id);
      setAlert({ severity: "success", message: "피드백을 거절했습니다." });
      loadFeedback();
    } catch (e) {
      console.error(e);
      setAlert({ severity: "error", message: "피드백 거절에 실패했습니다." });
    }
  };

  if (!authChecked) {
    return (
      <Box sx={{ py: 8, textAlign: "center", color: "var(--fg)" }}>
        <Typography variant="h6">관리자 권한을 확인하는 중입니다...</Typography>
      </Box>
    );
  }

  if (!isAdmin) {
    return (
      <Box sx={{ py: 8, textAlign: "center", color: "var(--fg)" }}>
        <Typography variant="h6">관리자 권한이 필요합니다.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1000, mx: "auto", py: 6, color: "var(--fg)" }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Admin Dashboard
      </Typography>

      <Stack spacing={3} sx={{ mb: 3 }}>
        <Card>
          <CardContent>
            <Stack direction={{ xs: "column", md: "row" }} spacing={3} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }}>
              <Box>
                <Typography variant="h6">운영 인사이트</Typography>
                <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                  인기 상품 · 인기 키워드 · 사용자 분포를 확인하세요.
                </Typography>
              </Box>
              <Stack direction="row" spacing={1}>
                <Button variant="outlined" size="small" onClick={loadInsights} disabled={insightsLoading}>
                  새로고침
                </Button>
              </Stack>
            </Stack>

            <Stack direction={{ xs: "column", md: "row" }} spacing={3} sx={{ mt: 3 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  인기 상품
                </Typography>
                {insightsLoading ? (
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    데이터를 불러오는 중입니다...
                  </Typography>
                ) : !insights?.popular_products?.length ? (
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    최근 집계된 상품 데이터가 없습니다.
                  </Typography>
                ) : (
                  <Stack spacing={1}>
                    {insights.popular_products.map((item: any, idx: number) => (
                      <Box
                        key={`${item.name}-${idx}`}
                        sx={{
                          p: 1.5,
                          border: "1px solid var(--border)",
                          borderRadius: 1,
                          backgroundColor: "var(--bg-soft)",
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          #{idx + 1} {item.name}
                        </Typography>
                        <Typography variant="caption" sx={{ color: "var(--muted)" }}>
                          {item.category || "카테고리 미지정"} · {item.count}회
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                )}
              </Box>

              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  인기 키워드
                </Typography>
                {insightsLoading ? (
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    데이터를 불러오는 중입니다...
                  </Typography>
                ) : !insights?.popular_keywords?.length ? (
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    최근 검색 키워드가 없습니다.
                  </Typography>
                ) : (
                  <Stack spacing={0.5}>
                    {insights.popular_keywords.slice(0, 8).map((item: any, idx: number) => (
                      <Stack direction="row" spacing={1} alignItems="center" key={`${item.keyword}-${idx}`}>
                        <Typography variant="body2" sx={{ minWidth: 40, color: "var(--muted)" }}>
                          #{idx + 1}
                        </Typography>
                        <Typography variant="body2" sx={{ flexGrow: 1 }}>
                          {item.keyword}
                        </Typography>
                        <Typography variant="caption" sx={{ color: "var(--muted)" }}>
                          {item.count}
                        </Typography>
                      </Stack>
                    ))}
                  </Stack>
                )}
              </Box>
            </Stack>

            <Stack direction={{ xs: "column", md: "row" }} spacing={3} sx={{ mt: 3 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  사용자 성비
                </Typography>
                {insightsLoading ? (
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    데이터를 불러오는 중입니다...
                  </Typography>
                ) : !insights?.gender_breakdown?.length ? (
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    사용자 정보가 없습니다.
                  </Typography>
                ) : (
                  <Stack spacing={1}>
                    {insights.gender_breakdown.map((item: any) => (
                      <Box key={item.label}>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography variant="body2">{item.label}</Typography>
                          <Typography variant="body2">{Math.round(item.ratio * 100)}%</Typography>
                        </Stack>
                        <Box sx={{ height: 8, backgroundColor: "var(--border)", borderRadius: 4 }}>
                          <Box
                            sx={{
                              width: `${Math.min(100, Math.round(item.ratio * 100))}%`,
                              backgroundColor: "var(--accent)",
                              height: "100%",
                              borderRadius: 4,
                            }}
                          />
                        </Box>
                      </Box>
                    ))}
                  </Stack>
                )}
              </Box>

              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  사용자 나이 분포
                </Typography>
                {insightsLoading ? (
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    데이터를 불러오는 중입니다...
                  </Typography>
                ) : !insights?.age_distribution?.length ? (
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    나이 정보가 없습니다.
                  </Typography>
                ) : (
                  <Stack spacing={1}>
                    {insights.age_distribution.map((item: any) => (
                      <Box key={item.label}>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography variant="body2">{item.label}</Typography>
                          <Typography variant="body2">
                            {item.count}명 · {Math.round(item.ratio * 100)}%
                          </Typography>
                        </Stack>
                        <Box sx={{ height: 8, backgroundColor: "var(--border)", borderRadius: 4 }}>
                          <Box
                            sx={{
                              width: `${Math.min(100, Math.round(item.ratio * 100))}%`,
                              backgroundColor: "var(--accent-600)",
                              height: "100%",
                              borderRadius: 4,
                            }}
                          />
                        </Box>
                      </Box>
                    ))}
                  </Stack>
                )}
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      <Card>
        <CardContent>
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={1.5}
            alignItems={{ xs: "flex-start", sm: "center" }}
            justifyContent="space-between"
            sx={{ mb: 2 }}
          >
            <Box>
              <Typography variant="h6">검색 피드백 검수</Typography>
              <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                사용자가 남긴 답변과 그 이유를 검토하세요.
              </Typography>
            </Box>
            <Button variant="outlined" onClick={loadFeedback} disabled={feedbackLoading}>
              새로고침
            </Button>
          </Stack>

          {alert && (
            <Alert severity={alert.severity} sx={{ mb: 2 }} onClose={() => setAlert(null)}>
              {alert.message}
            </Alert>
          )}

          <TableContainer
            component={Paper}
            sx={{
              backgroundColor: "var(--card)",
              color: "var(--fg)",
              border: "1px solid var(--border)",
            }}
          >
            <Table
              size="small"
              sx={{
                "& th": {
                  color: "var(--fg)",
                  backgroundColor: "var(--card-hover)",
                  borderBottom: "1px solid var(--border)",
                },
                "& td": {
                  color: "var(--fg)",
                  borderBottom: "1px solid var(--border)",
                },
                "& tr:hover td": {
                  backgroundColor: "var(--card-hover)",
                },
              }}
            >
              <TableHead>
                <TableRow>
                  <TableCell>검색 문장</TableCell>
                  <TableCell>응답</TableCell>
                  <TableCell>이유</TableCell>
                  <TableCell>사용자</TableCell>
                  <TableCell>액션</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {feedbackLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      데이터를 불러오는 중입니다...
                    </TableCell>
                  </TableRow>
                ) : feedback.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4, color: "var(--muted)" }}>
                      대기 중인 피드백이 없습니다.
                    </TableCell>
                  </TableRow>
                ) : (
                  feedback.map((item) => (
                    <TableRow key={item.id} hover>
                      <TableCell sx={{ maxWidth: 260 }}>
                        <Typography variant="body2">{item.search_sentence}</Typography>
                      </TableCell>
                      <TableCell sx={{ maxWidth: 260 }}>
                        <Typography variant="body2">{item.answer}</Typography>
                      </TableCell>
                      <TableCell sx={{ maxWidth: 260 }}>
                        <Typography variant="body2">{item.reason || "-"}</Typography>
                      </TableCell>
                      <TableCell>{item.user_email || "-"}</TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <Button size="small" variant="contained" onClick={() => handleApprove(item.id)}>
                            승인
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="warning"
                            onClick={() => handleReject(item.id)}
                          >
                            거절
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}
