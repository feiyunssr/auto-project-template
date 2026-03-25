export function formatDateTime(value?: string | null) {
  if (!value) {
    return "--";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatRelativeSeconds(seconds?: number | null) {
  if (seconds == null) {
    return "--";
  }
  if (seconds < 60) {
    return `${seconds}s`;
  }
  if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}m`;
  }
  return `${Math.floor(seconds / 3600)}h`;
}

export function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

export function statusLabel(status: string) {
  const mapping: Record<string, string> = {
    draft: "草稿",
    queued: "排队中",
    running: "执行中",
    succeeded: "已完成",
    failed: "失败",
    cancelled: "已取消",
    review_required: "待复核",
  };
  return mapping[status] ?? status;
}
