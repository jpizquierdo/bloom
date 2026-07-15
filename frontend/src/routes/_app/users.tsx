import {
  usersCreateUserMutation,
  usersListUsersOptions,
  usersUpdateUserMutation,
} from "@/client/@tanstack/react-query.gen"
import type { UserRead } from "@/client/types.gen"
import { DataTable } from "@/components/data/data-table"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { ResourceDialog } from "@/components/data/resource-dialog"
import { RowActions } from "@/components/data/row-actions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { isAdmin, useCurrentUser } from "@/lib/auth"
import { formatDate } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/_app/users")({ component: UsersPage })

const username = z
  .string()
  .min(3, "At least 3 characters")
  .max(32)
  .regex(/^[a-z0-9_.-]+$/, "Lowercase letters, digits, and . _ - only")

const createSchema = z.object({
  email: z.email("Enter a valid email address"),
  username,
  password: z.string().min(8, "At least 8 characters").max(128),
})

const editSchema = z.object({
  username,
  role: z.enum(["admin", "user"]),
  is_active: z.boolean(),
})

type CreateValues = z.infer<typeof createSchema>
type EditValues = z.infer<typeof editSchema>

function UsersPage() {
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()
  const { data, isLoading } = useQuery({
    ...usersListUsersOptions(),
    enabled: isAdmin(user),
  })

  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<UserRead | null>(null)
  const [disabling, setDisabling] = useState<UserRead | null>(null)

  const createForm = useForm<CreateValues>({
    resolver: zodResolver(createSchema),
    defaultValues: { email: "", username: "", password: "" },
  })
  const editForm = useForm<EditValues>({
    resolver: zodResolver(editSchema),
    defaultValues: { username: "", role: "user", is_active: true },
  })

  const create = useMutation({
    ...usersCreateUserMutation(),
    onSuccess: feedback.onSuccess("User created"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...usersUpdateUserMutation(),
    onSuccess: feedback.onSuccess("User updated"),
    onError: feedback.onError,
  })

  if (!isAdmin(user)) {
    return (
      <div className="rounded-lg border border-dashed p-10 text-center text-sm text-muted-foreground">
        Only admins can manage users.
      </div>
    )
  }

  const columns: ColumnDef<UserRead, unknown>[] = [
    { accessorKey: "username", header: "Username" },
    { accessorKey: "email", header: "Email" },
    {
      accessorKey: "role",
      header: "Role",
      cell: ({ row }) => (
        <Badge variant={row.original.role === "admin" ? "default" : "secondary"}>
          {row.original.role}
        </Badge>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) =>
        row.original.is_active ? (
          <Badge variant="outline">Active</Badge>
        ) : (
          <Badge variant="destructive">Disabled</Badge>
        ),
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => formatDate(row.original.created_at),
    },
    {
      id: "actions",
      header: "",
      enableSorting: false,
      cell: ({ row }) => (
        <div className="text-right">
          <RowActions
            canEdit
            deleteLabel="Disable"
            onEdit={() => {
              setEditing(row.original)
              editForm.reset({
                username: row.original.username,
                role: row.original.role === "admin" ? "admin" : "user",
                is_active: row.original.is_active,
              })
            }}
            onDelete={() => setDisabling(row.original)}
          />
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Users"
        description="There is no public sign-up: you create the accounts here."
        actions={
          <Button
            onClick={() => {
              createForm.reset({ email: "", username: "", password: "" })
              setCreateOpen(true)
            }}
          >
            <Plus className="size-4" />
            New user
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        searchPlaceholder="Search users…"
      />

      <ResourceDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New user"
        description="They log in with this password; there is no way to reset it yet."
        form={createForm}
        onSubmit={(values) =>
          submitAndClose(create.mutateAsync({ body: values }), () => setCreateOpen(false))
        }
        isPending={create.isPending}
        submitLabel="Create user"
      >
        <FormField
          control={createForm.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="taster@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={createForm.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="barista" autoComplete="off" {...field} />
              </FormControl>
              <FormDescription>Unique handle they can also log in with.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={createForm.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" autoComplete="new-password" {...field} />
              </FormControl>
              <FormDescription>At least 8 characters.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
      </ResourceDialog>

      <ResourceDialog
        open={editing !== null}
        onOpenChange={(open) => !open && setEditing(null)}
        title={editing?.email ?? "Edit user"}
        description="Roles and access. You cannot demote or disable yourself."
        form={editForm}
        onSubmit={(values) => {
          if (!editing) return
          return submitAndClose(
            update.mutateAsync({ path: { user_id: editing.id }, body: values }),
            () => setEditing(null),
          )
        }}
        isPending={update.isPending}
      >
        <FormField
          control={editForm.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="barista" autoComplete="off" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={editForm.control}
          name="role"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Role</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={editForm.control}
          name="is_active"
          render={({ field }) => (
            <FormItem className="flex items-center justify-between rounded-lg border p-3">
              <div className="grid gap-0.5">
                <FormLabel>Active</FormLabel>
                <FormDescription>Disabled users cannot log in.</FormDescription>
              </div>
              <FormControl>
                <Switch checked={field.value} onCheckedChange={field.onChange} />
              </FormControl>
            </FormItem>
          )}
        />
      </ResourceDialog>

      <DeleteAlert
        open={disabling !== null}
        onOpenChange={(open) => !open && setDisabling(null)}
        title="Disable this user?"
        description={`${disabling?.email} will no longer be able to log in. Their beans, brews and tastings stay in the log.`}
        isPending={update.isPending}
        onConfirm={() => {
          if (disabling) {
            update.mutate({ path: { user_id: disabling.id }, body: { is_active: false } })
          }
          setDisabling(null)
        }}
      />
    </>
  )
}
