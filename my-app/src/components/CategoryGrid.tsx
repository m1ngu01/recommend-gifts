const categories = [
  "감사", "결혼", "남친", "백일/돌", "생일", "선/후배", "아빠",
  "엄마", "여친", "위로", "응원", "이사/집들이", "임신/출산",
  "재미", "직장동료", "취업/이직", "친구", "형제/자매"
];

export default function CategoryGrid({ selected, onSelectCategory }: any) {
  return (
    <section className="mt-6 bg-bg-soft/60 border border-border rounded-2xl shadow-soft p-6">
      <h2 className="text-lg font-semibold mb-4">키워드</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => onSelectCategory(category)}
            className={`group border border-border rounded-xl p-4 transition-colors ${
              selected === category ? "bg-accent/10" : "bg-card hover:bg-card-hover"
            }`}
            aria-pressed={selected === category}
          >
            <span className="inline-flex w-full justify-center">
              <span className="block max-w-[12ch] text-center truncate text-sm text-fg/90 group-hover:text-fg">
                {category}
              </span>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

