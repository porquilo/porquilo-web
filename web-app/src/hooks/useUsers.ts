import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createUser, listUsers, resetUserPassword, setUserActive } from '../api/users'

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  })
}

export function useCreateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { username: string; password: string; role?: string; name?: string }) =>
      createUser(body),
    onSuccess: () => { void qc.invalidateQueries({ queryKey: ['users'] }) },
  })
}

export function useSetUserActive() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
      setUserActive(userId, isActive),
    onSuccess: () => { void qc.invalidateQueries({ queryKey: ['users'] }) },
  })
}

export function useResetUserPassword() {
  return useMutation({
    mutationFn: ({ userId, newPassword }: { userId: string; newPassword: string }) =>
      resetUserPassword(userId, newPassword),
  })
}
