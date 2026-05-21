import Image from "next/image";

export default function FlagImg({
  iso2,
  size = 48,
  priority = false,
  className = "",
  alt,
}: {
  iso2: string;
  size?: number;
  priority?: boolean;
  className?: string;
  alt?: string;
}) {
  const w = size >= 256 ? 640 : size >= 128 ? 320 : 160;
  const src = `https://flagcdn.com/w${w}/${iso2.toLowerCase()}.png`;
  return (
    <Image
      src={src}
      alt={alt ?? `${iso2} flag`}
      width={size}
      height={Math.round(size * 0.7)}
      priority={priority}
      loading={priority ? undefined : "lazy"}
      unoptimized
      className={`rounded-sm shadow-sm ring-1 ring-white/10 ${className}`}
    />
  );
}
