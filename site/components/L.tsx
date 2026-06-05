// Bilingual text helper. Renders BOTH languages; CSS (driven by the <html> lang-* class
// set in layout) shows only the active one. Server-component safe (no hooks).
// Use for visible TEXT children only — NOT for string props (title/alt/placeholder),
// which stay in English.
export function L({ es, en }: { es: string; en: string }) {
  return (
    <>
      <span data-l="es">{es}</span>
      <span data-l="en">{en}</span>
    </>
  );
}

export default L;
