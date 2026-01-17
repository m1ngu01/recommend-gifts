import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Card,
  CardMedia,
  CardContent,
  Button,
  IconButton,
  Stack,
} from "@mui/material";
import FavoriteIcon from "@mui/icons-material/Favorite";
import Rating from "@mui/material/Rating";
import client from "../api/client";
import { fetchFavorites, upsertFavorite } from "../api/favorites";
import { fetchRatingSummary, submitRating } from "../api/ratings";

type GiftItem = {
  id?: string | number;
  idx?: string | number;
  name: string;
  image_url?: string | null;
  cost?: string | number | null;
  price?: string | number | null;
  satisfaction?: number | string | null;
  review?: string | null;
  category_path?: string;
  category?: string;
  link?: string;
};

export default function GiftDetail() {
  const location = useLocation();
  const navigate = useNavigate();
  const item = (location as any).state?.item as GiftItem | undefined;
  const [liked, setLiked] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasUser, setHasUser] = useState(false);
  const [ratingSummary, setRatingSummary] = useState<{ average: number; count: number }>({
    average: 0,
    count: 0,
  });
  const [userRating, setUserRating] = useState<number | null>(null);

  const productId = useMemo(() => {
    if (typeof item?.id === "string" && item.id.trim()) return item.id.trim();
    if (typeof item?.id === "number") return String(item.id);
    if (typeof item?.idx === "string" && item.idx.trim()) return item.idx.trim();
    if (typeof item?.idx === "number") return String(item.idx);
    if (item?.name) return `name:${item.name}`;
    return "unknown";
  }, [item]);

  const purchaseUrl =
    typeof item?.link === "string" && item.link.trim().length > 0
      ? item.link
      : null;

  useEffect(() => {
    const saved = localStorage.getItem("user");
    const loggedIn = !!saved;
    setHasUser(loggedIn);
    if (!loggedIn) {
      setLiked(false);
      setUserRating(null);
    }

    const loadFavorites = async () => {
      if (!loggedIn) return;
      try {
        const res = await fetchFavorites();
        const { ok, data } = res?.data || {};
        if (ok && Array.isArray(data?.items)) {
          const exists = data.items.some(
            (fav: any) => fav.product_id === productId && fav.liked !== false
          );
          setLiked(exists);
        }
      } catch (e) {
        // ignore errors
      }
    };
    loadFavorites();

    const loadRating = async () => {
      try {
        const res = await fetchRatingSummary(productId);
        const { ok, data } = res?.data || {};
        if (ok && data) {
          setRatingSummary({ average: data.average ?? 0, count: data.count ?? 0 });
        }
      } catch (e) {
        console.error(e);
      }
    };
    loadRating();
  }, [productId]);

  const handleToggleLike = async () => {
    if (!item) return;
    if (!hasUser) {
      if (window.confirm("로그인이 필요한 기능입니다. 로그인 페이지로 이동할까요?")) {
        navigate("/login");
      }
      return;
    }
    const next = !liked;
    setLiked(next);
    setSaving(true);
    try {
      await upsertFavorite({
        product_id: productId,
        name: item.name,
        image_url: item.image_url ?? null,
        price: item.cost ?? item.price ?? null,
        link: purchaseUrl,
        metadata: {
          category_path: item.category_path ?? item.category ?? "",
          source: "gift_detail",
        },
        liked: next,
      });
    } catch (e) {
      setLiked(!next);
      alert("좋아요 정보를 저장하는 중 문제가 발생했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const handleBuyClick = async () => {
    if (!hasUser || !item) return;
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    try {
      await client.post("/api/log-activity", {
        event: "buy_click",
        payload: {
          user_name: user.name,
          gender: user.gender,
          age: user.age,
          interest: user.interest,
          gift_name: item?.name,
          gift_category: item?.category_path ?? item?.category,
          timestamp: new Date().toISOString(),
        },
      });
    } catch (e) {
      // logging failure can be ignored
    }
  };

  const handleRatingChange = async (_: any, value: number | null) => {
    if (!item || !value) return;
    if (!hasUser) {
      if (window.confirm("로그인이 필요한 기능입니다. 로그인 페이지로 이동할까요?")) {
        navigate("/login");
      }
      return;
    }
    try {
      setUserRating(value);
      const res = await submitRating({ product_id: productId, rating: value });
      const { ok, data } = res?.data || {};
      if (ok && data) {
        setRatingSummary({ average: data.average ?? value, count: data.count ?? ratingSummary.count });
      }
    } catch (e) {
      alert("평점 저장 중 오류가 발생했습니다.");
    }
  };

  if (!item) {
    return <Typography>선물 정보를 불러올 수 없습니다.</Typography>;
  }

  return (
    <Box sx={{ p: 4, color: "var(--fg)" }}>
      <Card
        sx={{
          maxWidth: 600,
          mx: "auto",
          backgroundColor: "var(--card)",
          color: "var(--fg)",
          border: "1px solid var(--border)",
          boxShadow: "0 12px 30px rgba(0, 0, 0, 0.25)",
        }}
      >
        <CardMedia
          component="img"
          image={item.image_url || undefined}
          alt={item.name}
          height="300"
          sx={{
            borderTopLeftRadius: 8,
            borderTopRightRadius: 8,
            borderBottom: "1px solid var(--border)",
          }}
        />
        <CardContent>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Typography variant="h5" gutterBottom sx={{ color: "var(--fg)" }}>
              {item.name}
            </Typography>
            <IconButton
              sx={{
                color: liked ? "var(--danger)" : "var(--muted)",
                "&:hover": {
                  color: liked ? "var(--danger)" : "var(--accent)",
                },
              }}
              onClick={handleToggleLike}
              aria-label="좋아요"
              disabled={saving}
            >
              <FavoriteIcon />
            </IconButton>
          </Box>
          <Typography
            variant="subtitle1"
            gutterBottom
            sx={{ color: "var(--accent)", fontWeight: 600 }}
          >
            가격: {item.cost ?? item.price ?? "가격 정보 없음"}
          </Typography>
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
            <Typography variant="body2" sx={{ color: "var(--muted)" }}>
              만족도: {item.satisfaction ? `${item.satisfaction}` : "정보 없음"}
              {typeof item.review_count === "number" && item.review_count > 0 ? ` · 리뷰 ${item.review_count}` : ""}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <Rating
                name="product-rating"
                value={userRating ?? ratingSummary.average}
                precision={0.5}
                onChange={handleRatingChange}
                readOnly={!hasUser}
              />
              <Typography variant="body2" sx={{ color: "var(--muted)" }}>
                ({ratingSummary.count})
              </Typography>
            </Stack>
          </Stack>
          {(item.review || item.tags) && (
            <Typography variant="body2" sx={{ mt: 2, color: "var(--muted)" }}>
              {item.review ?? item.tags}
            </Typography>
          )}

          <Button
            variant="contained"
            component={purchaseUrl ? "a" : "button"}
            href={purchaseUrl ?? undefined}
            target={purchaseUrl ? "_blank" : undefined}
            rel={purchaseUrl ? "noopener noreferrer" : undefined}
            sx={{
              mt: 3,
              mr: 2,
              backgroundColor: "var(--accent)",
              color: "#fff",
              "&:hover": { backgroundColor: "var(--accent-600)" },
              "&:active": { backgroundColor: "var(--accent-700)" },
            }}
            onClick={purchaseUrl ? handleBuyClick : undefined}
            disabled={!purchaseUrl}
          >
            {purchaseUrl ? "구매하러 가기" : "구매 링크 준비 중"}
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate(-1)}
            sx={{
              mt: 3,
              color: "var(--fg)",
              borderColor: "var(--border)",
              "&:hover": {
                borderColor: "var(--accent)",
                color: "var(--accent)",
              },
            }}
          >
            뒤로 가기
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
