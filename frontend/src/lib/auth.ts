import { authReadCurrentUserOptions } from "@/client/@tanstack/react-query.gen"
import { authLogin } from "@/client/sdk.gen"
import type { UserRead } from "@/client/types.gen"
import { errorMessage } from "@/lib/api"
import { clearToken, isLoggedIn, setToken } from "@/lib/token"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"

export function useCurrentUser() {
  const { data, isLoading } = useQuery({
    ...authReadCurrentUserOptions(),
    enabled: isLoggedIn(),
    retry: false,
    staleTime: Infinity,
  })
  return { user: data, isLoading }
}

export function useLogin() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [isPending, setIsPending] = useState(false)

  async function login(username: string, password: string) {
    setError(null)
    setIsPending(true)
    const { data, error: apiError } = await authLogin({
      body: { username, password },
    })
    setIsPending(false)

    if (apiError || !data) {
      setError(errorMessage(apiError, "Incorrect email or password"))
      return
    }
    setToken(data.access_token)
    await queryClient.invalidateQueries()
    navigate({ to: "/" })
  }

  return { login, error, isPending }
}

export function useLogout() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return () => {
    clearToken()
    queryClient.clear()
    navigate({ to: "/login" })
  }
}

/** Bloom is a shared log: everyone reads, only the row's creator (or an admin) writes. */
export function canEdit(row: { user_id: number }, user: UserRead | undefined): boolean {
  if (!user) return false
  return user.role === "admin" || user.id === row.user_id
}

export function isAdmin(user: UserRead | undefined): boolean {
  return user?.role === "admin"
}
