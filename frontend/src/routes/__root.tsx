import { Toaster } from "@/components/ui/sonner"
import { Outlet, createRootRoute } from "@tanstack/react-router"
import { ThemeProvider } from "next-themes"

export const Route = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFound,
})

function RootLayout() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <Outlet />
      <Toaster richColors />
    </ThemeProvider>
  )
}

function NotFound() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-2">
      <p className="text-4xl font-semibold">404</p>
      <p className="text-muted-foreground">This page does not exist.</p>
      <a href="/" className="text-primary underline-offset-4 hover:underline">
        Back to Bloom
      </a>
    </div>
  )
}
