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
import { zodResolver } from "@hookform/resolvers/zod"
import { Link, createFileRoute } from "@tanstack/react-router"
import { Info } from "lucide-react"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/signup")({
  component: SignupPage,
})

// The API has no sign-up endpoint yet: the form is built and validated, but inert.
// Wiring it up later means replacing the disabled submit with the generated mutation.
const schema = z
  .object({
    email: z.email("Enter a valid email address"),
    password: z.string().min(8, "At least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  })

function SignupPage() {
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", confirmPassword: "" },
  })

  return (
    <AuthShell
      title="Create an account"
      description="Join the shared brew log."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-foreground underline underline-offset-4">
            Log in
          </Link>
        </>
      }
    >
      <div className="mb-4 flex gap-2 rounded-md border border-dashed bg-muted/50 p-3 text-sm text-muted-foreground">
        <Info className="mt-0.5 size-4 shrink-0" />
        <p>
          Sign-up is closed for now. Ask a Bloom admin to create your account, then log in with
          the password they give you.
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={(event) => event.preventDefault()} className="grid gap-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="you@example.com" {...field} />
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
                  <Input type="password" autoComplete="new-password" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="confirmPassword"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirm password</FormLabel>
                <FormControl>
                  <Input type="password" autoComplete="new-password" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled>
            Sign up
          </Button>
        </form>
      </Form>
    </AuthShell>
  )
}
