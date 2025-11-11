import { Link, useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { ThemeToggle } from "./ThemeToggle";
import { MobileNav } from "./MobileNav";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { User, LogOut, Settings, Ticket, MessageSquare, Crown } from "lucide-react";
import logoImage from "@assets/o conselho_1762287383861.png";
import { cn } from "@/lib/utils";

export function Header() {
  const [location, setLocation] = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    setLocation('/login');
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 backdrop-blur-xl bg-background/80 shadow-sm">
      <div className="container mx-auto flex h-20 items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <MobileNav />
          <Link href={user ? "/home" : "/"}>
            <div className="hover-elevate active-elevate-2 px-3 py-2 rounded-lg -ml-3 cursor-pointer" data-testid="link-home">
              <img src={logoImage} alt="θconselho" className="h-16 w-auto invert dark:invert-0" />
            </div>
          </Link>
        </div>

        <nav className="hidden md:flex items-center gap-6">
          {user && (
            <Link href="/home">
              <span className={cn(
                "text-sm font-medium transition-all cursor-pointer relative",
                "after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary after:transition-all hover:after:w-full",
                location === "/home" ? "text-primary after:w-full" : "text-muted-foreground hover:text-foreground"
              )} data-testid="link-dashboard">
                Home
              </span>
            </Link>
          )}
          <Link href="/categories">
            <span className={cn(
              "text-sm font-medium transition-all cursor-pointer relative",
              "after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary after:transition-all hover:after:w-full",
              location === "/categories" ? "text-primary after:w-full" : "text-muted-foreground hover:text-foreground"
            )} data-testid="link-categories">
              Categorias
            </span>
          </Link>
          <Link href="/conversations">
            <span className={cn(
              "text-sm font-medium transition-all cursor-pointer relative",
              "after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary after:transition-all hover:after:w-full",
              location === "/conversations" ? "text-primary after:w-full" : "text-muted-foreground hover:text-foreground"
            )} data-testid="link-conversations">
              Conversas
            </span>
          </Link>
          <Link href="/test-council">
            <span className={cn(
              "text-sm font-medium transition-all cursor-pointer relative",
              "after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary after:transition-all hover:after:w-full",
              location === "/test-council" ? "text-primary after:w-full" : "text-muted-foreground hover:text-foreground"
            )} data-testid="link-council">
              Conselho Estratégico
            </span>
          </Link>
          <Link href="/personas">
            <span className={cn(
              "text-sm font-medium transition-all cursor-pointer relative",
              "after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary after:transition-all hover:after:w-full",
              location === "/personas" ? "text-primary after:w-full" : "text-muted-foreground hover:text-foreground"
            )} data-testid="link-personas">
              Persona Builder
            </span>
          </Link>
          <Link href="/create">
            <span className={cn(
              "text-sm font-medium transition-all cursor-pointer relative",
              "after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary after:transition-all hover:after:w-full",
              location === "/create" ? "text-primary after:w-full" : "text-muted-foreground hover:text-foreground"
            )} data-testid="link-create">
              Criar Especialista
            </span>
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full" data-testid="button-user-menu">
                  <User className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col gap-1">
                    <p className="text-sm font-medium">{user.username}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setLocation('/settings')} data-testid="menu-settings">
                  <Settings className="mr-2 h-4 w-4" />
                  Configurações
                </DropdownMenuItem>
                {user.role === 'superadmin' && (
                  <DropdownMenuItem onClick={() => setLocation('/superadmin')} data-testid="menu-superadmin">
                    <Crown className="mr-2 h-4 w-4 text-yellow-500" />
                    SuperAdmin Panel
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={() => setLocation('/settings')} data-testid="menu-invites">
                  <Ticket className="mr-2 h-4 w-4" />
                  Códigos de Convite ({user.availableInvites})
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} data-testid="menu-logout">
                  <LogOut className="mr-2 h-4 w-4" />
                  Sair
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button variant="ghost" size="sm" className="rounded-xl" data-testid="button-login">
                  Entrar
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm" className="rounded-xl" data-testid="button-register">
                  Criar conta
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
