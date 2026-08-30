export default function Logo({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="logoGradient" x1="4" y1="4" x2="36" y2="36" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#4F7CFF" />
          <stop offset="55%" stopColor="#8B5CF6" />
          <stop offset="100%" stopColor="#EC4899" />
        </linearGradient>
      </defs>
      <path
        d="M20 3c0 6.5 1.7 11.2 5.1 14.1S33.5 20 33.5 20s-4.5 0-8.4 2.9S20 30.4 20 37c0-6.6-1.7-11.2-5.1-14.1S6.5 20 6.5 20s4.5 0 8.4-2.9S20 9.5 20 3z"
        fill="url(#logoGradient)"
      />
    </svg>
  )
}
