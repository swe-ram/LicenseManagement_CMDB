import { format, formatDistanceToNow, differenceInDays, parseISO } from 'date-fns';

export const formatDate = (dateStr, fmt = 'dd MMM yyyy') => {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), fmt);
  } catch {
    return dateStr;
  }
};

export const formatDateTime = (dateStr) => {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), 'dd MMM yyyy, HH:mm');
  } catch {
    return dateStr;
  }
};

export const timeAgo = (dateStr) => {
  if (!dateStr) return '—';
  try {
    return formatDistanceToNow(parseISO(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
};

export const daysUntil = (dateStr) => {
  if (!dateStr) return null;
  try {
    return differenceInDays(parseISO(dateStr), new Date());
  } catch {
    return null;
  }
};

export const formatCurrency = (amount, currency = 'USD') => {
  if (amount == null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
};

export const formatNumber = (n) => {
  if (n == null) return '—';
  return new Intl.NumberFormat('en-US').format(n);
};

export const formatPercent = (n, decimals = 1) => {
  if (n == null) return '—';
  return `${Number(n).toFixed(decimals)}%`;
};

export const getExpiryUrgency = (dateStr) => {
  const days = daysUntil(dateStr);
  if (days === null) return 'none';
  if (days <= 0) return 'expired';
  if (days <= 30) return 'critical';
  if (days <= 90) return 'warning';
  return 'normal';
};

export const getUtilizationLevel = (pct) => {
  if (pct >= 95) return 'critical';
  if (pct >= 80) return 'warning';
  if (pct >= 60) return 'good';
  return 'low';
};

export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export const truncate = (str, len = 40) => {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '…' : str;
};

export const durationSeconds = (startStr, endStr) => {
  if (!startStr || !endStr) return null;
  try {
    const diff = (new Date(endStr) - new Date(startStr)) / 1000;
    if (diff < 60) return `${Math.round(diff)}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ${Math.round(diff % 60)}s`;
    return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
  } catch {
    return '—';
  }
};
