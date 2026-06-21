import { useMutation } from '@tanstack/react-query'
import { changePassword } from '../api/auth'

export function useChangePassword() {
  return useMutation({
    mutationFn: ({
      currentPassword,
      newPassword,
    }: {
      currentPassword: string
      newPassword: string
    }) => changePassword(currentPassword, newPassword),
  })
}
