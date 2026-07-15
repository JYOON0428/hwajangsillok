import { request } from './http'
import {
  listMockPosts,
  getMockPost,
  createMockPost,
  updateMockPost,
  deleteMockPost,
  createMockComment,
  updateMockComment,
  deleteMockComment,
} from './mockRepository'

const useMock = import.meta.env.VITE_USE_MOCK_API !== 'false'

function normalizeFiles(imageFiles) {
  if (!imageFiles) return []
  return Array.isArray(imageFiles) ? imageFiles.filter(Boolean) : [imageFiles]
}

function fileToDataUrl(file) {
  if (!file) return Promise.resolve('')
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('사진을 읽지 못했습니다.'))
    reader.readAsDataURL(file)
  })
}

async function filesToDataUrls(files) {
  return Promise.all(normalizeFiles(files).map(fileToDataUrl))
}

function toFormData(payload, imageFiles) {
  const formData = new FormData()
  Object.entries(payload).forEach(([key, value]) => {
    if (value === undefined || value === null) return
    if (Array.isArray(value)) {
      formData.append(key, JSON.stringify(value))
      return
    }
    formData.append(key, String(value))
  })
  normalizeFiles(imageFiles).forEach((file) => formData.append('images', file))
  return formData
}

export function listPosts(params = {}) {
  if (useMock) return listMockPosts(params)
  const query = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null),
  )
  return request(`/api/posts?${query}`)
}

export function getPost(id) {
  return useMock ? getMockPost(id) : request(`/api/posts/${id}`)
}

export async function createPost(payload, imageFiles = []) {
  const files = normalizeFiles(imageFiles)
  if (useMock) {
    const uploadedUrls = await filesToDataUrls(files)
    const existingUrls = Array.isArray(payload.imageUrls) ? payload.imageUrls.filter(Boolean) : []
    const imageUrls = [...existingUrls, ...uploadedUrls]
    return createMockPost({
      ...payload,
      imageUrls,
      imageUrl: imageUrls[0] || '',
    })
  }
  if (files.length) return request('/api/posts', { method: 'POST', body: toFormData(payload, files) })
  return request('/api/posts', { method: 'POST', body: JSON.stringify(payload) })
}

export async function updatePost(id, payload, imageFiles = []) {
  const files = normalizeFiles(imageFiles)
  if (useMock) {
    const uploadedUrls = await filesToDataUrls(files)
    const existingUrls = Array.isArray(payload.imageUrls) ? payload.imageUrls.filter(Boolean) : []
    const imageUrls = [...existingUrls, ...uploadedUrls]
    return updateMockPost(id, {
      ...payload,
      imageUrls,
      imageUrl: imageUrls[0] || '',
    })
  }
  if (files.length) return request(`/api/posts/${id}`, { method: 'PUT', body: toFormData(payload, files) })
  return request(`/api/posts/${id}`, { method: 'PUT', body: JSON.stringify(payload) })
}

export function deletePost(id, password) {
  return useMock
    ? deleteMockPost(id, password)
    : request(`/api/posts/${id}`, { method: 'DELETE', body: JSON.stringify({ password }) })
}

export function verifyPostPassword(id, password) {
  if (useMock) return getMockPost(id).then((post) => {
    if (post.password !== password) throw new Error('비밀번호가 일치하지 않습니다.')
    return { ok: true }
  })
  return request(`/api/posts/${id}/verify-password`, {
    method: 'POST',
    body: JSON.stringify({ password }),
  })
}


export function createComment(postId, payload) {
  return useMock
    ? createMockComment(postId, payload)
    : request(`/api/posts/${postId}/comments`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
}

export function updateComment(postId, commentId, payload) {
  return useMock
    ? updateMockComment(postId, commentId, payload)
    : request(`/api/posts/${postId}/comments/${commentId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
}

export function deleteComment(postId, commentId, password) {
  return useMock
    ? deleteMockComment(postId, commentId, password)
    : request(`/api/posts/${postId}/comments/${commentId}`, {
      method: 'DELETE',
      body: JSON.stringify({ password }),
    })
}
