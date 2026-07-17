import { authResetPassword } from "@/client/sdk.gen"
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
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

export const Route = createFileRoute("/reset-password")({
  component: ResetPasswordPage,
  validateSearch: (search: Record<string, unknown>) => ({
    token: typeof search.token === "string" ? search.token : "",
  }),
})

const schema = z
  .object({
    new_password: z.string().min(8, "Use at least 8 characters").max(128, "Use at most 128 characters"),
    confirm: z.string(),
  })
  .refine((values) => values.new_password === values.confirm, {
    message: "Passwords do not match",
    path: ["confirm"],
  })

function ResetPasswordPage() {
  const { token } = Route.useSearch()
  const navigate = useNavigate()

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { new_password: "", confirm: "" },
  })

  const mutation = useMutation({
    mutationFn: async (values: z.infer<typeof schema>) => {
      const { data, error } = await authResetPassword({
        body: { token, new_password: values.new_password },
      })
      // A spent or expired link fails here; the message from the API explains which.
      if (error) throw new Error(errorMessage(error, "Could not reset your password"))
      return data
    },
    onSuccess: () => {
      toast.success("Password changed. Log in with your new password.")
      navigate({ to: "/login" })
    },
  })

  const footer = (
    <Link to="/login" className="text-foreground underline underline-offset-4">
      Back to log in
    </Link>
  )

  if (!token) {
    return (
      <AuthShell
        title="Link incomplete"
        description="This reset link is missing its token."
        footer={footer}
      >
        <p className="text-sm text-muted-foreground">
          Open the link straight from the email, or{" "}
          <Link to="/recover-password" className="text-foreground underline underline-offset-4">
            request a new one
          </Link>
          .
        </p>
      </AuthShell>
    )
  }

  return (
    <AuthShell
      title="Choose a new password"
      description="Pick something you don't use anywhere else."
      footer={footer}
    >
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
          className="grid gap-4"
        >
          <FormField
            control={form.control}
            name="new_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>New password</FormLabel>
                <FormControl>
                  <Input type="password" autoComplete="new-password" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="confirm"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirm new password</FormLabel>
                <FormControl>
                  <Input type="password" autoComplete="new-password" {...field} />
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
            Set new password
          </Button>
        </form>
      </Form>
    </AuthShell>
  )
}
