import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'

export interface User {
  authenticated: boolean
  email: string
  name: string
  picture: string
  is_super_admin: boolean
  github_connected: boolean
}

export function useAuth() {
  const { data, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => apiGet<User>('/api/me'),
    retry: false,
  })

  return {
    user: data?.authenticated ? data : null,
    isLoading,
    isAuthenticated: !!data?.authenticated,
  }
}
