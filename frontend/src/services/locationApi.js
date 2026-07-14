import { request } from './http'
import { getMockRestroom, getMockRestroomReviews, searchMockRestrooms } from './mockRepository'

const useMock = import.meta.env.VITE_USE_MOCK_API !== 'false'

export function searchRestrooms({ keyword = '', radius = 1000, ...filters } = {}) {
  if (useMock) return searchMockRestrooms({ keyword, radius, ...filters })

  const query = new URLSearchParams()
  query.set('keyword', keyword)
  query.set('radius', String(radius))

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '' && value !== false) {
      query.set(key, String(value))
    }
  })

  return request(`/api/locations?${query.toString()}`)
}


export function getRestroom(restroomId) {
  if (useMock) return getMockRestroom(restroomId)
  return request(`/api/locations/${restroomId}`)
}

export function getRestroomReviews(restroomId, { sort = 'recent' } = {}) {
  if (useMock) return getMockRestroomReviews(restroomId, { sort })
  const query = new URLSearchParams({ sort })
  return request(`/api/locations/${restroomId}/reviews?${query.toString()}`)
}
