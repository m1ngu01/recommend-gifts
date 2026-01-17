import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom"; // useNavigate import 추가
import { Grid, Card, CardContent, CardMedia, Typography, Box } from "@mui/material";
import StarIcon from "@mui/icons-material/Star";
import client from "../api/client";

export default function PopularGifts({ category }: any) {
  const [gifts, setGifts] = useState<any[]>([]);
  const navigate = useNavigate(); // 추가

  useEffect(() => {
    if (!category) return;

    // 서버에 카테고리 전송 및 DB 응답 받아오기
    const fetchGifts = async () => {
      try {
        const res = await client.post("/api/gifts-by-keyword", { category });
        const { ok, data } = res.data;
        setGifts(ok ? data : []);
      } catch (err) {
        console.error("데이터 요청 실패:", err);
        setGifts([]); // 에러 시 빈 배열로 처리
      }
    };

    fetchGifts();
  }, [category]);

  return (
    <>
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
      </Typography>
      <Grid container spacing={4}>
        {gifts.map((item, idx) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={idx}>
            <Card
              sx={{
                height: "100%",
                width: "250px",
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
                cursor: "pointer", // 커서 포인터 추가
              }}
              onClick={() => navigate(`/gift/${item.id ?? idx}`, { state: { item } })}
              tabIndex={0}
              onKeyDown={e => {
                if (e.key === "Enter" || e.key === " ") {
                  navigate(`/gift/${item.id ?? idx}`, { state: { item } });
                }
              }}
              aria-label={`${item.name} 상세보기`}
              role="button"
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
                image={item.image_url}
                alt={item.name}
                sx={{
                  width: "100%",
                  height: "100%",
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
                  {item.price}
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                  <StarIcon sx={{ color: "#FFD700", fontSize: 16, mr: 0.5 }} />
                  <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                    만족도 {item.satisfaction ?? 97}%
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
                  {item.review ?? ""}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </>
  );
}



