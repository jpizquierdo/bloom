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
import { useLogin } from "@/lib/auth"
import { isLoggedIn } from "@/lib/token"
import { zodResolver } from "@hookform/resolvers/zod"
import { Link, createFileRoute, redirect } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/login")({
  component: LoginPage,
  beforeLoad: () => {
    if (isLoggedIn()) throw redirect({ to: "/" })
  },
})

const schema = z.object({
  identifier: z.string().min(1, "Enter your email or username"),
  password: z.string().min(1, "Enter your password"),
})

function LoginPage() {
  const { login, error, isPending } = useLogin()
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { identifier: "", password: "" },
  })

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
    </AuthShell>
  )
}
