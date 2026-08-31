type IconProps = { size?: number; className?: string };

export function ArrowRight({ size = 16, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M3 8h10" />
      <path d="M9 4l4 4-4 4" />
    </svg>
  );
}

export function Sparkle({ size = 16, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M8 2v3" />
      <path d="M8 11v3" />
      <path d="M2 8h3" />
      <path d="M11 8h3" />
      <path d="M4.2 4.2l2 2" />
      <path d="M9.8 9.8l2 2" />
      <path d="M11.8 4.2l-2 2" />
      <path d="M6.2 9.8l-2 2" />
    </svg>
  );
}

export function Reload({ size = 16, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M2.5 8a5.5 5.5 0 0 1 9.6-3.7" />
      <path d="M12.5 2v3h-3" />
      <path d="M13.5 8a5.5 5.5 0 0 1-9.6 3.7" />
      <path d="M3.5 14v-3h3" />
    </svg>
  );
}

export function Pencil({ size = 16, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M11.5 2.5l2 2L6 12l-3 1 1-3 7.5-7.5z" />
    </svg>
  );
}

export function Doc({ size = 16, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M3.5 2.5h6L12.5 5.5v8h-9z" />
      <path d="M9.5 2.5v3h3" />
    </svg>
  );
}

export function Check({ size = 16, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M3 8.5l3 3L13 4.5" />
    </svg>
  );
}
