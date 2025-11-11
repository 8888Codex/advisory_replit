import { useState } from "react";
import { Link, useLocation } from "wouter";
import { Menu, Home, FolderOpen, Users, User, Plus, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const [location] = useLocation();

  const navLinks = [
    { href: "/", label: "Início", icon: Home },
    { href: "/categories", label: "Categorias", icon: FolderOpen },
    { href: "/conversations", label: "Conversas", icon: MessageSquare },
    { href: "/test-council", label: "Conselho Estratégico", icon: Users },
    { href: "/personas", label: "Persona Builder", icon: User },
    { href: "/create", label: "Criar Especialista", icon: Plus },
  ];

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          data-testid="button-mobile-menu"
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Abrir menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[280px] sm:w-[320px]">
        <SheetHeader className="mb-6">
          <SheetTitle className="text-left">Menu</SheetTitle>
        </SheetHeader>
        <nav className="flex flex-col gap-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location === link.href;
            
            return (
              <Link key={link.href} href={link.href}>
                <div
                  onClick={() => setOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-all hover-elevate active-elevate-2 ${
                    isActive
                      ? "bg-accent text-accent-foreground font-medium"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  data-testid={`mobile-link-${link.href}`}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  <span className="text-base">{link.label}</span>
                </div>
              </Link>
            );
          })}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
