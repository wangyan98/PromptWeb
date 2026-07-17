import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

apiClient.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body.code !== 0) {
      console.warn(`API warning: ${body.message}`)
    }
    return body
  },
  (error) => {
    console.error('API error:', error.message)
    return Promise.reject(error)
  }
)

export default apiClient
