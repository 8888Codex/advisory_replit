import { Link } from "wouter";
import { ThemeToggle } from "./ThemeToggle";
import { Sparkles } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/">
          <div className="flex items-center gap-2 hover-elevate active-elevate-2 px-3 py-2 rounded-lg -ml-3 cursor-pointer" data-testid="link-home">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold tracking-tight">AdvisorIA</span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          <Link href="/experts">
            <span className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer" data-testid="link-experts">
              Especialistas
            </span>
          </Link>
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
          <Link href="/create">
            <span className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer" data-testid="link-create">
              Criar Especialista
            </span>
          </Link>
        </nav>

        <ThemeToggle />
      </div>
    </header>
  );
}
