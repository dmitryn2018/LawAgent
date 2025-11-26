import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for handling errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login on unauthorized
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client

