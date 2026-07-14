import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar"
import { useCurrentUser, useLogout } from "@/lib/auth"
import { ChevronsUpDown, LogOut } from "lucide-react"

export function UserMenu() {
  const { user } = useCurrentUser()
  const logout = useLogout()

  if (!user) return null

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size="lg">
              <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-sidebar-accent text-sm font-medium uppercase">
                {user.email.slice(0, 2)}
              </span>
              <span className="grid flex-1 text-left leading-tight">
                <span className="truncate text-sm font-medium">{user.email}</span>
                <span className="truncate text-xs text-muted-foreground capitalize">
                  {user.role}
                </span>
              </span>
              <ChevronsUpDown className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>

          <DropdownMenuContent side="top" align="start" className="w-56">
            <DropdownMenuLabel className="flex items-center justify-between gap-2">
              <span className="truncate font-normal">{user.email}</span>
              <Badge variant="secondary" className="capitalize">
                {user.role}
              </Badge>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={logout}>
              <LogOut className="size-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
