export interface ShareMessagePayload {
  text: string | null
  shareUrl: string | null
  isAIGenerated: boolean
}

const toOptionalString = (value: unknown): string | null => {
  if (typeof value !== 'string') {
    return null
  }
  const trimmed = value.trim()
  return trimmed.length ? trimmed : null
}

export const parseShareMessageResponse = (data: unknown): ShareMessagePayload => {
  if (!data || typeof data !== 'object') {
    return { text: null, shareUrl: null, isAIGenerated: false }
  }

  const candidate = data as { text?: unknown; share_url?: unknown; is_ai_generated?: unknown }

  return {
    text: toOptionalString(candidate.text),
    shareUrl: toOptionalString(candidate.share_url),
    isAIGenerated: typeof candidate.is_ai_generated === 'boolean' ? candidate.is_ai_generated : false,
  }
}
