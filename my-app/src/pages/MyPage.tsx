import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Divider,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
} from "@mui/material";
import EmailIcon from "@mui/icons-material/Email";
import CakeIcon from "@mui/icons-material/Cake";
import WcIcon from "@mui/icons-material/Wc";
import InterestsIcon from "@mui/icons-material/Interests";
import FavoriteIcon from "@mui/icons-material/Favorite";
import { fetchFavorites } from "../api/favorites";

export default function MyPage() {
  const [user, setUser] = useState<any>(null);
  const [favorites, setFavorites] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (!savedUser) {
      alert("로그인이 필요합니다.");
      navigate("/login");
    } else {
      setUser(JSON.parse(savedUser));
    }
  }, [navigate]);

  useEffect(() => {
    if (!user) return;
    const load = async () => {
      try {
        const res = await fetchFavorites();
        const { ok, data } = res?.data || {};
        if (ok && Array.isArray(data?.items)) {
          setFavorites(data.items.slice(0, 10));
        }
      } catch (e) {
        setFavorites([]);
      }
    };
    load();
  }, [user]);

  const handleEdit = () => {
    navigate("/mypage/edit");
  };

  if (!user) return null;

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
          {/* 상단 아바타 & 이름 */}
          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", mb: 3 }}>
            <Avatar
              sx={{
                backgroundColor: "var(--accent)",
                width: 64,
                height: 64,
                mb: 1,
              }}
            >
            </Avatar>
            <Typography variant="h5" fontWeight="bold" sx={{ color: "var(--fg)" }}>
              {user.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              마이페이지
            </Typography>
          </Box>

          <Divider sx={{ mb: 2 }} />

          {/* 정보 리스트 */}
          <List>
            <ListItem>
              <ListItemIcon>
                <EmailIcon />
              </ListItemIcon>
              <ListItemText primary="이메일" secondary={user.email} />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CakeIcon />
              </ListItemIcon>
              <ListItemText primary="나이" secondary={user.age ?? "-"} />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <WcIcon />
              </ListItemIcon>
              <ListItemText primary="성별" secondary={user.gender ?? "-"} />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <InterestsIcon />
              </ListItemIcon>
              <ListItemText primary="관심사" secondary={user.interest || "-"} />
            </ListItem>
          </List>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle1" sx={{ color: "var(--fg)", fontWeight: 600, mb: 1 }}>
            좋아요한 상품
          </Typography>
          {favorites.length === 0 ? (
            <Typography variant="body2" sx={{ color: "var(--muted)" }}>
              좋아요한 상품이 아직 없습니다.
            </Typography>
          ) : (
            <List dense>
              {favorites.map((fav) => {
                const link = fav.link ?? fav.metadata?.link ?? null;
                return (
                  <ListItem key={fav.product_id} disablePadding>
                    <ListItemButton
                      component={link ? "a" : "div"}
                      href={link || undefined}
                      target={link ? "_blank" : undefined}
                      rel={link ? "noopener noreferrer" : undefined}
                      sx={{ pl: 0 }}
                    >
                      <ListItemIcon sx={{ minWidth: 32, color: "var(--accent)" }}>
                        <FavoriteIcon fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={fav.name}
                        secondary={fav.price ?? ""}
                        primaryTypographyProps={{ sx: { color: "var(--fg)" } }}
                        secondaryTypographyProps={{ sx: { color: "var(--muted)" } }}
                      />
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          )}

          {/* 수정 버튼 */}
          <Button
            variant="contained"
            fullWidth
            sx={{
              mt: 3,
              backgroundColor: "var(--accent)",
              color: "#fff",
              "&:hover": { backgroundColor: "var(--accent-600)" },
              "&:active": { backgroundColor: "var(--accent-700)" },
            }}
            onClick={handleEdit}
          >
            프로필 수정
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}

