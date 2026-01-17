// src/pages/Main.jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "@mui/material";
import HeroSection from "../components/HeroSection";
import CategoryGrid from "../components/CategoryGrid";
import SurveyModal from "../components/SurveyModal";

export default function Main() {
  const [selectedCategory, setSelectedCategory] = useState<any>(null);
  const [showSurvey, setShowSurvey] = useState(false);
  const navigate = useNavigate();

  const handleSelectCategory = (category: string) => {
    setSelectedCategory(category);
    const sentence = `${category} 선물 추천`;
    navigate("/recommend-result", { state: { sentence, meta: { source: "category", category } } });
  };

  useEffect(() => {
    const saved = localStorage.getItem('user');
    const dismissed = sessionStorage.getItem('surveyDismissed');
    if (saved && !dismissed) {
      setShowSurvey(true);
    }
  }, []);

  return (
    <Container maxWidth="lg" sx={{ mt: { xs: 3, sm: 4 }, mb: { xs: 6, sm: 8 } }}>
      <HeroSection selectedCategory={selectedCategory} />
      <CategoryGrid
        selected={selectedCategory}
        onSelectCategory={handleSelectCategory}
      />
      <SurveyModal open={showSurvey} onClose={() => setShowSurvey(false)} />
    </Container>
  );
}




