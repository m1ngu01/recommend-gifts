import { useNavigate } from "react-router-dom";
import { useState } from "react";

export default function HeroSection({ selectedCategory }: any) {
  const navigate = useNavigate();
  const [userInput, setUserInput] = useState("");

  const handleClick = () => {
    const trimmed = userInput.trim();
    const fallback = selectedCategory ? `${selectedCategory} 선물 추천` : "";
    const sentence = trimmed || fallback;
    if (!sentence) {
      return;
    }
    navigate("/recommend-result", {
      state: {
        sentence,
        meta: {
          rawInput: userInput,
          selectedCategory: selectedCategory || "",
        },
      },
    });
  };

  const handleChatbotClick = () => {
    navigate("/recommend", {
      state: {
        source: "hero-cta",
        preset: {
          selectedCategory: selectedCategory || null,
          userInput: userInput || null,
        },
      },
    });
  };

  const topLine = userInput
    ? `[${userInput}]`
    : selectedCategory
    ? `[${selectedCategory}]`
    : "선물 추천";

  const bottomLine = userInput || selectedCategory
    ? "어울리는 선물을 추천해드릴게요!"
    : "더 똑똑하게";

  return (
    <section className="bg-gradient-to-b from-bg-soft/40 to-transparent rounded-2xl p-8 border border-border text-center">
      <h1 className="text-3xl md:text-4xl">
        <span className="block font-extrabold text-4xl md:text-5xl">{topLine}</span>
        <span className="mt-3 block text-muted">{bottomLine}</span>
      </h1>
      <p className="mt-2 text-muted">상대의 취향과 상황에 맞춘 큐레이션으로 실패 없는 선물 선택</p>

      <div className="mt-6 flex flex-col sm:flex-row items-stretch gap-3 justify-center">
        <input
          value={userInput}
          onChange={(e: any) => setUserInput(e.target.value)}
          placeholder="예: 20대 남성, 취미 러닝, 예산 5만원"
          className="h-12 w-full sm:flex-1 max-w-2xl rounded-xl bg-card border border-border px-4 outline-none focus:ring-2 focus:ring-accent/40"
          aria-label="선물 추천 검색어"
        />
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            className="h-12 rounded-xl bg-accent hover:bg-accent-600 active:bg-accent-700 text-white px-6 transition-colors"
            onClick={handleClick}
          >
            추천 시작하기
          </button>
          <button
            className="h-12 rounded-xl border border-accent text-accent hover:bg-accent/10 active:bg-accent/20 px-6 transition-colors flex items-center justify-center gap-1"
            onClick={handleChatbotClick}
          >
            <span role="img" aria-hidden="true">
              💬
            </span>
            상담하기
          </button>
        </div>
      </div>
    </section>
  );
}
