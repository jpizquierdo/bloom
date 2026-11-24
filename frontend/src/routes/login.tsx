import { AuthShell } from "@/components/auth/auth-shell"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { SSO_LOGIN_URL, useAuthConfig, useLogin } from "@/lib/auth"
import { isLoggedIn, setToken } from "@/lib/token"
import { zodResolver } from "@hookform/resolvers/zod"
import { Link, createFileRoute, redirect } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

const SSO_ERRORS: Record<string, string> = {
  oidc_denied: "Your SSO account is not allowed to use Bloom. Ask an admin for access.",
  oidc_failed: "Single sign-on failed. Please try again.",
}

export const Route = createFileRoute("/login")({
  component: LoginPage,
  validateSearch: z.object({ error: z.string().optional() }),
  beforeLoad: () => {
    // The OIDC callback hands the token over in the fragment, which never reaches a server log.
    const token = new URLSearchParams(window.location.hash.slice(1)).get("token")
    if (token) {
      setToken(token)
      window.history.replaceState(null, "", window.location.pathname)
    }
    if (isLoggedIn()) throw redirect({ to: "/" })
  },
})

const schema = z.object({
  identifier: z.string().min(1, "Enter your email or username"),
  password: z.string().min(1, "Enter your password"),
})

function LoginPage() {
  const { error: ssoError } = Route.useSearch()
  const { data: config } = useAuthConfig()
  const forceSso = config ? !config.local_auth_enabled : false

  useEffect(() => {
    // Skipped after a failed SSO round-trip, or the page would bounce back to the IdP forever.
    if (forceSso && !ssoError) window.location.assign(SSO_LOGIN_URL)
  }, [forceSso, ssoError])

  if (forceSso && !ssoError) {
    return (
      <AuthShell title="Welcome back" description="Redirecting to single sign-on…">
        <Loader2 className="mx-auto animate-spin text-muted-foreground" />
      </AuthShell>
    )
  }

  return (
    <AuthShell
      title="Welcome back"
      description="Log in to your Bloom account."
      footer={
        <>
          No account?{" "}
          <Link to="/signup" className="text-foreground underline underline-offset-4">
            Sign up
          </Link>
        </>
      }
    >
      <div className="grid gap-4">
        {ssoError ? (
          <p className="text-sm text-destructive">{SSO_ERRORS[ssoError] ?? SSO_ERRORS.oidc_failed}</p>
        ) : null}
        {config?.oidc_enabled ? (
          <Button asChild variant={forceSso ? "default" : "outline"} className="w-full">
            <a href={SSO_LOGIN_URL}>Sign in with SSO</a>
          </Button>
        ) : null}
        {config?.oidc_enabled && config.local_auth_enabled ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Separator className="flex-1" />
            or
            <Separator className="flex-1" />
          </div>
        ) : null}
        {forceSso ? null : <PasswordForm />}
      </div>
    </AuthShell>
  )
}

function PasswordForm() {
  const { login, error, isPending } = useLogin()
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { identifier: "", password: "" },
  })

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((values) => login(values.identifier, values.password))}
        className="grid gap-4"
      >
        <FormField
          control={form.control}
          name="identifier"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email or username</FormLabel>
              <FormControl>
                <Input
                  type="text"
                  autoComplete="username"
                  placeholder="you@example.com or barista"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" autoComplete="current-password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* After the password field so Tab goes email → password → this → Log in. */}
        <Link
          to="/recover-password"
          className="block text-right text-sm text-muted-foreground underline-offset-4 hover:underline"
        >
          Forgot password?
        </Link>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}

        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending ? <Loader2 className="animate-spin" /> : null}
          Log in
        </Button>
      </form>
    </Form>
  )
}
