const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  if (options.body && !isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let detail = '요청 처리 중 오류가 발생했습니다.'
    try {
      const body = await response.json()
      detail = body.detail || body.message || detail
    } catch {
      // JSON이 아닌 오류 응답은 기본 문구 사용
    }
    throw new Error(detail)
  }

  if (response.status === 204) return null
  return response.json()
}
