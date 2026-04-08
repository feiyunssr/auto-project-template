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
    return `${seconds} 秒`;
  }
  if (seconds < 3600) {
    return `${Math.floor(seconds / 60)} 分钟`;
  }
  return `${Math.floor(seconds / 3600)} 小时`;
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
  }
  return mapping[status] ?? status
}

export function scenarioLabel(scenario: string) {
  const mapping: Record<string, string> = {
    general: "通用生成",
    content: "内容生产",
    video: "视频脚本",
  }
  return mapping[scenario] ?? scenario
}

export function roleLabel(role?: string | null) {
  const mapping: Record<string, string> = {
    operator: "操作员",
    admin: "管理员",
    viewer: "查看者",
  }
  return role ? mapping[role] ?? role : "无角色"
}

export function healthStatusLabel(status?: string | null) {
  const mapping: Record<string, string> = {
    healthy: "健康",
    degraded: "降级",
    unhealthy: "异常",
    unknown: "未知",
  }
  return status ? mapping[status] ?? status : "--"
}

export function registrationStatusLabel(status?: string | null) {
  const mapping: Record<string, string> = {
    healthy: "正常",
    degraded: "降级",
    unhealthy: "异常",
    disabled: "未启用",
    unknown: "未知",
  }
  return status ? mapping[status] ?? status : "未知"
}

export function attemptStatusLabel(status: string) {
  const mapping: Record<string, string> = {
    running: "执行中",
    succeeded: "执行成功",
    failed: "执行失败",
  }
  return mapping[status] ?? statusLabel(status)
}

export function artifactRoleLabel(role: string) {
  const mapping: Record<string, string> = {
    input: "输入",
    output: "输出",
    source: "源素材",
    preview: "预览",
    result: "结果",
    log: "日志",
  }
  return mapping[role] ?? role
}

export function translateErrorMessage(message?: string | null, code?: string | null) {
  const codeMapping: Record<string, string> = {
    AUTH_REQUIRED: "登录态已失效，请重新登录 Hub。",
    VALIDATION_ERROR: "提交内容校验失败，请检查表单字段。",
    PROVIDER_TIMEOUT: "AI 调用超时，请稍后重试或调整配置。",
    PROVIDER_TIMEOUT_RETRYING: "AI 响应较慢，系统正在自动重试。",
    PROVIDER_RATE_LIMIT: "AI 服务当前限流，请稍后再试。",
    PROFILE_NOT_FOUND: "当前场景没有可用的 AI 配置。",
    TASK_NOT_FOUND: "任务不存在或已被移除。",
    POST_PROCESSING_FAILED: "结果后处理失败，请稍后重试。",
    REQUEST_FAILED: "请求失败，请稍后重试。",
  }

  if (code && codeMapping[code]) {
    return codeMapping[code]
  }

  if (!message) {
    return ""
  }

  const exactMessageMapping: Record<string, string> = {
    "Request failed.": "请求失败，请稍后重试。",
    "Hub session is required.": "需要有效的 Hub 会话。",
    "Hub session missing or expired.": "Hub 会话缺失或已过期，请重新登录。",
    "Task payload validation failed.": "提交内容校验失败，请检查表单字段。",
    "Task not found.": "任务不存在或已被移除。",
    "Provider rate limited the request.": "AI 服务当前限流，请稍后再试。",
    "Mock provider simulated a persistent timeout.": "模拟模型服务持续超时。",
    "Mock provider simulated a first-attempt timeout.": "模拟模型服务首轮调用超时。",
  }

  if (exactMessageMapping[message]) {
    return exactMessageMapping[message]
  }

  if (/^No active AI profile for scenario /.test(message)) {
    return "当前场景没有可用的 AI 配置。"
  }

  if (/^Cannot transition job from /.test(message)) {
    return "任务状态流转失败，请刷新后重试。"
  }

  if (/timeout/i.test(message)) {
    return "AI 调用超时，请稍后重试或调整配置。"
  }

  return message
}
