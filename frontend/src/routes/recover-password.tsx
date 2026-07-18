import { authRecoverPassword } from "@/client/sdk.gen"
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
import { errorMessage } from "@/lib/api"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { Link, createFileRoute } from "@tanstack/react-router"
import { Loader2, MailCheck } from "lucide-react"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/recover-password")({
  component: RecoverPasswordPage,
})

const schema = z.object({
  email: z.email("Enter a valid email address"),
})

function RecoverPasswordPage() {
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  })

  const mutation = useMutation({
    mutationFn: async (values: z.infer<typeof schema>) => {
      const { data, error } = await authRecoverPassword({ body: values })
      if (error) throw new Error(errorMessage(error, "Could not send the recovery email"))
      return data
    },
  })

  if (mutation.isSuccess) {
    return (
      <AuthShell
        title="Check your inbox"
        description="If that email is registered, a reset link is on its way."
        footer={
          <Link to="/login" className="text-foreground underline underline-offset-4">
            Back to log in
          </Link>
        }
      >
        <div className="flex gap-2 rounded-md border border-dashed bg-muted/50 p-3 text-sm text-muted-foreground">
          <MailCheck className="mt-0.5 size-4 shrink-0" />
          <p>The link expires shortly and can only be used once. Nothing arrived? Check your spam folder.</p>
        </div>
      </AuthShell>
    )
  }

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
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
          className="grid gap-4"
        >
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {mutation.isError ? (
            <p className="text-sm text-destructive">{mutation.error.message}</p>
          ) : null}

          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="animate-spin" /> : null}
            Send recovery link
          </Button>
        </form>
      </Form>
    </AuthShell>
  )
}
