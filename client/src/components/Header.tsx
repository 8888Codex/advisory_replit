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
import { User, LogOut, Settings, Ticket } from "lucide-react";
import logoImage from "@assets/o conselho_1762287383861.png";

export function Header() {
  const [location, setLocation] = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    setLocation('/login');
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
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
              <span className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer" data-testid="link-dashboard">
                Home
              </span>
            </Link>
          )}
          <Link href="/categories">
            <span className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer" data-testid="link-categories">
              Categorias
            </span>
          </Link>
          <Link href="/test-council">
            <span className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer" data-testid="link-council">
              Conselho Estratégico
            </span>
          </Link>
          <Link href="/personas">
            <span className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer" data-testid="link-personas">
              Persona Builder
            </span>
          </Link>
          <Link href="/analytics">
            <span className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer" data-testid="link-analytics">
              Analytics
            </span>
          </Link>
          <Link href="/create">
            <span className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer" data-testid="link-create">
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
