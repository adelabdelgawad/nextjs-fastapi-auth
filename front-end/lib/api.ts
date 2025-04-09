// lib/api.ts (Should look like this)
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// This is the instance that should be used for ALL authenticated backend calls
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Crucial for sending HttpOnly cookies
});

// DO NOT add interceptors here that try to manage localStorage or Authorization headers

export default api;