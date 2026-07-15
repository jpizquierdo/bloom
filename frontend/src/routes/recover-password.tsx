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

export const Route = createFileRoute("/recover-password")({
  component: RecoverPasswordPage,
})

// No password-reset endpoint exists yet (it needs an email sender); the form is inert.
const schema = z.object({
  email: z.email("Enter a valid email address"),
})

function RecoverPasswordPage() {
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  })

  return (
    <AuthShell
      title="Forgot your password?"
      description="We'll send you a link to choose a new one."
      footer={
        <Link to="/login" className="text-foreground underline underline-offset-4">
          Back to log in
        </Link>
      }
    >
      <div className="mb-4 flex gap-2 rounded-md border border-dashed bg-muted/50 p-3 text-sm text-muted-foreground">
        <Info className="mt-0.5 size-4 shrink-0" />
        <p>
          Password recovery is not available yet. Ask a Bloom admin to reset your password for
          you.
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

          <Button type="submit" className="w-full" disabled>
            Send recovery link
          </Button>
        </form>
      </Form>
    </AuthShell>
  )
}
