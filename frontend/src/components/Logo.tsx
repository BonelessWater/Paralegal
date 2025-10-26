export default function Logo({ className = "w-16 h-16" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Hexagonal border */}
      <defs>
        <linearGradient id="goldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#fbbf24', stopOpacity: 1 }} />
          <stop offset="50%" style={{ stopColor: '#f59e0b', stopOpacity: 1 }} />
          <stop offset="100%" style={{ stopColor: '#d97706', stopOpacity: 1 }} />
        </linearGradient>
        <linearGradient id="bronzeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#bfa094', stopOpacity: 1 }} />
          <stop offset="100%" style={{ stopColor: '#8B6F47', stopOpacity: 1 }} />
        </linearGradient>
        <filter id="metallic">
          <feGaussianBlur in="SourceAlpha" stdDeviation="1" />
          <feSpecularLighting result="specOut" specularExponent="20" lightingColor="white">
            <fePointLight x="-5000" y="-10000" z="20000" />
          </feSpecularLighting>
          <feComposite in="SourceGraphic" in2="specOut" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" />
        </filter>
      </defs>

      {/* Marble background */}
      <polygon
        points="50,5 85,27.5 85,72.5 50,95 15,72.5 15,27.5"
        fill="#fafaf9"
        stroke="url(#goldGradient)"
        strokeWidth="4"
      />

      {/* Inner hexagon accent */}
      <polygon
        points="50,10 80,27.5 80,72.5 50,90 20,72.5 20,27.5"
        fill="none"
        stroke="#fde68a"
        strokeWidth="1"
        opacity="0.3"
      />

      {/* Circuit lines (left side) */}
      <g stroke="url(#bronzeGradient)" strokeWidth="1.5" fill="none">
        {/* Main circuit paths */}
        <path d="M 25,35 L 35,35" />
        <path d="M 35,35 L 35,45" />
        <path d="M 35,45 L 40,45" />
        
        <path d="M 25,50 L 38,50" />
        
        <path d="M 25,65 L 32,65" />
        <path d="M 32,65 L 32,55" />
        <path d="M 32,55 L 38,55" />
      </g>

      {/* Circuit nodes (left side) */}
      <circle cx="25" cy="35" r="2" fill="#8B6F47" />
      <circle cx="25" cy="50" r="2" fill="#8B6F47" />
      <circle cx="25" cy="65" r="2" fill="#8B6F47" />
      <circle cx="35" cy="35" r="1.5" fill="#C9A961" />
      <circle cx="35" cy="45" r="1.5" fill="#C9A961" />
      <circle cx="32" cy="65" r="1.5" fill="#C9A961" />

      {/* Scale of Justice (right side) */}
      <g filter="url(#metallic)">
        {/* Base */}
        <ellipse cx="65" cy="75" rx="8" ry="2" fill="url(#goldGradient)" />
        
        {/* Vertical column */}
        <rect x="63.5" y="40" width="3" height="35" fill="url(#goldGradient)" />
        
        {/* Horizontal beam */}
        <rect x="52" y="38" width="26" height="2.5" fill="url(#goldGradient)" />
        
        {/* Left chain */}
        <line x1="55" y1="40" x2="55" y2="50" stroke="url(#goldGradient)" strokeWidth="1" />
        
        {/* Right chain */}
        <line x1="75" y1="40" x2="75" y2="50" stroke="url(#goldGradient)" strokeWidth="1" />
        
        {/* Left pan */}
        <ellipse cx="55" cy="50" rx="6" ry="2" fill="url(#goldGradient)" />
        <path d="M 49,50 L 49,52 L 61,52 L 61,50" fill="url(#goldGradient)" opacity="0.8" />
        
        {/* Right pan */}
        <ellipse cx="75" cy="50" rx="6" ry="2" fill="url(#goldGradient)" />
        <path d="M 69,50 L 69,52 L 81,52 L 81,50" fill="url(#goldGradient)" opacity="0.8" />
        
        {/* Top ornament */}
        <circle cx="65" cy="36" r="2.5" fill="url(#goldGradient)" />
      </g>

      {/* Subtle marble texture overlay */}
      <polygon
        points="50,10 80,27.5 80,72.5 50,90 20,72.5 20,27.5"
        fill="url(#marbleTexture)"
        opacity="0.1"
      />
      
      <defs>
        <pattern id="marbleTexture" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M0,10 Q5,8 10,10 T20,10" stroke="#d6d3d1" fill="none" strokeWidth="0.5" opacity="0.3" />
        </pattern>
      </defs>
    </svg>
  );
}
