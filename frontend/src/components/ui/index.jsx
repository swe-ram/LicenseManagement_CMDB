import React from 'react';

export const Spinner = ({ size = 36 }) => (
  <div className="spinner-wrap">
    <div className="spinner" style={{ width: size, height: size }} />
  </div>
);

export const SkeletonLine = ({ width = '100%', height = 16, style = {} }) => (
  <div className="skeleton" style={{ width, height, ...style }} />
);

export const EmptyState = ({ icon, title, description, action }) => (
  <div className="empty-state">
    {icon && (
      <div className="empty-state-icon">
        {icon}
      </div>
    )}
    <p className="empty-state-title">{title}</p>
    {description && <p className="empty-state-desc">{description}</p>}
    {action}
  </div>
);

export const AlertBanner = ({ type = 'info', message, onDismiss }) => (
  <div className={`alert-banner ${type}`} style={{ marginBottom: 16 }}>
    <span style={{ flex: 1 }}>{message}</span>
    {onDismiss && (
      <button
        onClick={onDismiss}
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, lineHeight: 1 }}
      >
        ×
      </button>
    )}
  </div>
);

export const Badge = ({ variant = 'neutral', children, dot }) => (
  <span className={`badge badge-${variant}`}>
    {dot && (
      <span
        style={{
          width: 5,
          height: 5,
          borderRadius: '50%',
          background: 'currentColor',
          display: 'inline-block',
        }}
      />
    )}
    {children}
  </span>
);

export const ProgressBar = ({ value, max = 100, variant }) => {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const resolvedVariant = variant || (pct >= 95 ? 'critical' : pct >= 80 ? 'warning' : 'good');
  return (
    <div className="progress-bar">
      <div className={`progress-fill ${resolvedVariant}`} style={{ width: `${pct}%` }} />
    </div>
  );
};

export const Card = ({ title, subtitle, actions, children, style }) => (
  <div className="card" style={style}>
    {(title || actions) && (
      <div className="card-header">
        <div>
          {title && <div className="card-title">{title}</div>}
          {subtitle && <div className="card-subtitle">{subtitle}</div>}
        </div>
        {actions && <div className="flex gap-8">{actions}</div>}
      </div>
    )}
    <div className="card-body">{children}</div>
  </div>
);

export const Modal = ({ open, title, onClose, children, footer }) => {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose?.()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-header">
          <h3 className="modal-title" id="modal-title">{title}</h3>
          <button
            className="topbar-icon-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
};

export const Tooltip = ({ label, children }) => (
  <span className="tooltip-wrap">
    {children}
    <span className="tooltip">{label}</span>
  </span>
);

export { ToolLogo } from './ToolLogo';

