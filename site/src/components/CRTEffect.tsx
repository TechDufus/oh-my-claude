export default function CRTEffect() {
  return (
    <>
      {/* Scanlines */}
      <div
        className="pointer-events-none fixed inset-0 z-40"
        style={{
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 0, 0, 0.1) 2px, rgba(0, 0, 0, 0.1) 4px)',
          opacity: 0.3,
        }}
      />
      {/* Subtle screen flicker */}
      <div
        className="pointer-events-none fixed inset-0 z-40 animate-flicker"
        style={{
          background: 'rgba(0, 229, 204, 0.01)',
        }}
      />
    </>
  )
}
