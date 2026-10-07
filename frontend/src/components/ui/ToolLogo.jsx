import React from 'react';

export const ToolLogo = ({ name, size = 32, className = '', style = {} }) => {
  const norm = (name || '').toLowerCase().trim();

  // Microsoft 365
  if (norm.includes('microsoft') || norm.includes('m365') || norm.includes('office 365')) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        className={className}
        style={{ borderRadius: 6, flexShrink: 0, ...style }}
      >
        <rect width="24" height="24" rx="5" fill="#f8fafc" />
        <rect x="3.5" y="3.5" width="7.5" height="7.5" rx="1.5" fill="#F25022" />
        <rect x="13" y="3.5" width="7.5" height="7.5" rx="1.5" fill="#7FBA00" />
        <rect x="3.5" y="13" width="7.5" height="7.5" rx="1.5" fill="#00A4EF" />
        <rect x="13" y="13" width="7.5" height="7.5" rx="1.5" fill="#FFB900" />
      </svg>
    );
  }

  // Slack (Official 4-color geometry with clean border on white background)
  if (norm.includes('slack')) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="-16 -16 160 160"
        fill="none"
        className={className}
        style={{ borderRadius: 6, flexShrink: 0, ...style }}
      >
        <rect x="-16" y="-16" width="160" height="160" rx="34" fill="#FFFFFF" stroke="#E2E8F0" strokeWidth="4" />
        {/* Slack official bezier curves */}
        {/* Red / Aubergine top-left droplet and bar */}
        <path
          d="M27.2 80c0 7.3-5.9 13.2-13.2 13.2C6.7 93.2.8 87.3.8 80c0-7.3 5.9-13.2 13.2-13.2h13.2V80zm6.6 0c0-7.3 5.9-13.2 13.2-13.2 7.3 0 13.2 5.9 13.2 13.2v33c0 7.3-5.9 13.2-13.2 13.2-7.3 0-13.2-5.9-13.2-13.2V80z"
          fill="#E01E5A"
        />
        {/* Blue droplet and bar */}
        <path
          d="M47 27.2c-7.3 0-13.2-5.9-13.2-13.2C33.8 6.7 39.7.8 47 .8c7.3 0 13.2 5.9 13.2 13.2v13.2H47zm0 6.6c7.3 0 13.2 5.9 13.2 13.2 0 7.3-5.9 13.2-13.2 13.2H14C6.7 60.2.8 54.3.8 47c0-7.3 5.9-13.2 13.2-13.2H47z"
          fill="#36C5F0"
        />
        {/* Green droplet and bar */}
        <path
          d="M99.8 47c0-7.3 5.9-13.2 13.2-13.2 7.3 0 13.2-5.9 13.2-13.2 0-7.3-5.9-13.2-13.2-13.2H99.8V47zm-6.6 0c0 7.3-5.9 13.2-13.2 13.2-7.3 0-13.2-5.9-13.2-13.2V14c0-7.3 5.9-13.2 13.2-13.2 7.3 0 13.2 5.9 13.2 13.2v33z"
          fill="#2EB67D"
        />
        {/* Yellow droplet and bar */}
        <path
          d="M80 99.8c7.3 0 13.2 5.9 13.2 13.2 0 7.3-5.9 13.2-13.2 13.2-7.3 0-13.2-5.9-13.2-13.2V99.8H80zm0-6.6c-7.3 0-13.2-5.9-13.2-13.2 0-7.3 5.9-13.2 13.2-13.2h33c7.3 0 13.2 5.9 13.2 13.2 0 7.3-5.9 13.2-13.2 13.2H80z"
          fill="#ECB22E"
        />
      </svg>
    );
  }

  // Jira (matches "jira", "_jira", "zira", "_zira") - Official Atlassian Jira Software icon
  if (norm.includes('jira') || norm.includes('zira')) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        className={className}
        style={{ borderRadius: 6, flexShrink: 0, ...style }}
      >
        <rect width="32" height="32" rx="7" fill="#0052CC" />
        {/* Official Atlassian Jira mark: folding chevrons */}
        <path
          d="M16 4.8a6.4 6.4 0 0 0-6.4 6.4v1.6H16a6.4 6.4 0 0 0 6.4-6.4V4.8H16z"
          fill="#DEEBFF"
          opacity="0.9"
        />
        <path
          d="M16 11.2a6.4 6.4 0 0 0-6.4 6.4v1.6H16a6.4 6.4 0 0 0 6.4-6.4v-1.6H16z"
          fill="#2684FF"
        />
        <path
          d="M16 17.6a6.4 6.4 0 0 0-6.4 6.4v1.6H16a6.4 6.4 0 0 0 6.4-6.4v-1.6H16z"
          fill="#DEEBFF"
          opacity="0.9"
        />
      </svg>
    );
  }

  // Lucidchart
  if (norm.includes('lucid')) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        className={className}
        style={{ borderRadius: 6, flexShrink: 0, ...style }}
      >
        <rect width="24" height="24" rx="5" fill="#F76B1C" />
        <path
          d="M6 7.5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-2z"
          fill="white"
        />
        <path
          d="M12 14.5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2v-2z"
          fill="white"
        />
        <path
          d="M9 11.5v3h3"
          stroke="white"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="15" cy="8.5" r="1.5" fill="white" opacity="0.8" />
      </svg>
    );
  }

  // Box
  if (norm.includes('box')) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        className={className}
        style={{ borderRadius: 6, flexShrink: 0, ...style }}
      >
        <rect width="24" height="24" rx="5" fill="#0061D5" />
        <path
          d="M12 4.5L18.5 8.2v7.6L12 19.5 5.5 15.8V8.2L12 4.5z"
          stroke="white"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <path
          d="M12 19.5V12"
          stroke="white"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
        <path
          d="M18.5 8.2L12 12 5.5 8.2"
          stroke="white"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  // Zoom
  if (norm.includes('zoom')) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        className={className}
        style={{ borderRadius: 6, flexShrink: 0, ...style }}
      >
        <rect width="24" height="24" rx="5" fill="#0B5CFF" />
        <rect x="5.5" y="8" width="8.5" height="8" rx="2" fill="white" />
        <path
          d="M14 10.3l3.8-2.3a.8.8 0 0 1 1.2.7v6.6a.8.8 0 0 1-1.2.7L14 13.7v-3.4z"
          fill="white"
        />
      </svg>
    );
  }

  // Sofia - (Pilot)
  if (norm.includes('sofia')) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        className={className}
        style={{ borderRadius: 6, flexShrink: 0, ...style }}
      >
        <defs>
          <linearGradient id="sofiaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#7C3AED" />
            <stop offset="100%" stopColor="#3B82F6" />
          </linearGradient>
        </defs>
        <rect width="24" height="24" rx="5" fill="url(#sofiaGrad)" />
        <path
          d="M12 4.5L13.8 9.5L18.5 10.2L14.8 13.5L16 18.5L12 15.8L8 18.5L9.2 13.5L5.5 10.2L10.2 9.5L12 4.5Z"
          fill="white"
          stroke="white"
          strokeWidth="0.5"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  // CATO
  if (norm.includes('cato')) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        className={className}
        style={{ borderRadius: 6, flexShrink: 0, ...style }}
      >
        <rect width="24" height="24" rx="5" fill="#18181B" />
        <path
          d="M12 4L18.5 7.5v5.5c0 4.2-2.8 7.2-6.5 8.5C8.3 20.2 5.5 17.2 5.5 13V7.5L12 4z"
          fill="#E61E25"
        />
        <path
          d="M12 7.5L15.5 9.5v3.2c0 2.5-1.5 4.3-3.5 5.1-2-.8-3.5-2.6-3.5-5.1V9.5L12 7.5z"
          fill="white"
        />
      </svg>
    );
  }

  // Default fallback
  return (
    <div
      className={className}
      style={{
        width: size,
        height: size,
        borderRadius: 6,
        background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 700,
        fontSize: size * 0.4,
        flexShrink: 0,
        ...style,
      }}
    >
      {name?.slice(0, 2).toUpperCase() || 'AP'}
    </div>
  );
};

export default ToolLogo;
