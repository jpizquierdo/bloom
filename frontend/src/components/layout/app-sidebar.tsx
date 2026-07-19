import { Brand } from "@/components/layout/brand"
import { UserMenu } from "@/components/layout/user-menu"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { isAdmin, useCurrentUser } from "@/lib/auth"
import { Link } from "@tanstack/react-router"
import {
  Bean,
  Factory,
  LayoutDashboard,
  type LucideIcon,
  NotebookPen,
  Settings2,
  Users,
  Wrench,
} from "lucide-react"
import { Coffee } from "lucide-react"

interface NavItem {
  title: string
  to: string
  icon: LucideIcon
}

const LOG_ITEMS: NavItem[] = [
  { title: "Dashboard", to: "/", icon: LayoutDashboard },
  { title: "Beans", to: "/beans", icon: Bean },
  { title: "Brews", to: "/brews", icon: Coffee },
  { title: "Tastings", to: "/tastings", icon: NotebookPen },
]

const CATALOG_ITEMS: NavItem[] = [
  { title: "Roasters", to: "/roasters", icon: Factory },
  { title: "Brew methods", to: "/brew-methods", icon: Settings2 },
  { title: "Equipment", to: "/equipment", icon: Wrench },
]

const ADMIN_ITEMS: NavItem[] = [{ title: "Users", to: "/users", icon: Users }]

export function AppSidebar() {
  const { user } = useCurrentUser()

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <Brand />
      </SidebarHeader>

      <SidebarContent>
        <NavGroup label="Log" items={LOG_ITEMS} />
        <NavGroup label="Catalog" items={CATALOG_ITEMS} />
        {isAdmin(user) ? <NavGroup label="Admin" items={ADMIN_ITEMS} /> : null}
      </SidebarContent>

      <SidebarFooter>
        <UserMenu />
      </SidebarFooter>
    </Sidebar>
  )
}

function NavGroup({ label, items }: { label: string; items: NavItem[] }) {
  return (
    <SidebarGroup>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.to}>
              <SidebarMenuButton asChild>
                <Link
                  to={item.to}
                  activeOptions={{ exact: item.to === "/" }}
                  activeProps={{ "data-active": true }}
                >
                  <item.icon />
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
