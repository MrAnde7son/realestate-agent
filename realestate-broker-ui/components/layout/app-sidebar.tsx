"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronDown,
  Home,
  Building,
  AlertCircle,
  Calculator,
  FileText,
  BarChart3,
  LineChart,
  User,
  CreditCard,
  Settings,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Logo from "@/components/Logo";
import * as Collapsible from "@radix-ui/react-collapsible";
import { useAuth } from "@/lib/auth-context";

const baseNavigation = [
  {
    name: "בית",
    href: "/",
    icon: Home,
  },
  {
    name: "נכסים",
    href: "/assets",
    icon: Building,
  },
  {
    name: "התראות",
    href: "/alerts",
    icon: AlertCircle,
  },
  {
    name: "מחשבון משכנתא",
    href: "/mortgage/analyze",
    icon: Calculator,
  },
  {
    name: "דוחות",
    href: "/reports",
    icon: BarChart3,
  },
];

interface AppSidebarProps {
  className?: string;
  isCollapsed?: boolean;
}

function isActive(href: string, path: string) {
  if (href === "/") return path === "/";
  return path === href || path.startsWith(href + "/");
}

export default function AppSidebar({
  className,
  isCollapsed = false,
}: AppSidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navigation = [...baseNavigation];
  if (user?.role === "admin") {
    navigation.push({ name: "Analytics", href: "/admin/analytics", icon: LineChart });
  }

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const getUserDisplayName = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user?.username || user?.email || "משתמש";
  };

  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`;
    }
    if (user?.username) {
      return user.username.substring(0, 2).toUpperCase();
    }
    if (user?.email) {
      return user.email.substring(0, 2).toUpperCase();
    }
    return "משתמש";
  };

  return (
    <div
      className={cn(
        "flex h-full flex-col bg-card border-l transition-all duration-300",
        isCollapsed ? "w-16" : "w-64",
        className
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/" className="flex items-center gap-3">
          <Logo variant="symbol" size={28} color="var(--brand-teal)" />
          {!isCollapsed && (
            <span className="text-xl font-bold text-logo-title">נדל״נר</span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto p-4">
        <nav className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;

            const active = isActive(item.href, pathname);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-[var(--brand-teal)]/8 text-[var(--brand-teal)] font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
                )}
              >
                <item.icon
                  className={cn(
                    "h-4 w-4",
                    active && "text-[var(--brand-teal)]"
                  )}
                />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer with User Menu - Moved to bottom of sidebar */}
      <div className="border-t p-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start gap-3 px-2 py-2 h-auto",
                isCollapsed ? "px-2" : "px-3"
              )}
            >
              <Avatar className="h-8 w-8">
                <AvatarFallback>{getUserInitials()}</AvatarFallback>
              </Avatar>
              {!isCollapsed && (
                <div className="flex-1 text-right">
                  <div className="text-sm font-medium">
                    {getUserDisplayName()}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {user?.email || "demo@example.com"}
                  </div>
                </div>
              )}
              {!isCollapsed && <ChevronDown className="h-4 w-4" />}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-56"
            align={isCollapsed ? "center" : "end"}
            side={isCollapsed ? "right" : "top"}
            forceMount
          >
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">
                  {getUserDisplayName()}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.email || "demo@example.com"}
                </p>
                {user?.company && (
                  <p className="text-xs leading-none text-muted-foreground">
                    {user.company}
                  </p>
                )}
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem asChild>
                <Link href="/profile" className="flex items-center">
                  <User className="ml-2 h-4 w-4" />
                  <span>פרופיל</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/billing" className="flex items-center">
                  <CreditCard className="ml-2 h-4 w-4" />
                  <span>חבילות ותשלומים</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/settings" className="flex items-center">
                  <Settings className="ml-2 h-4 w-4" />
                  <span>הגדרות</span>
                </Link>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-red-600 focus:text-red-600"
              onClick={handleLogout}
            >
              <LogOut className="ml-2 h-4 w-4" />
              <span>התנתק</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
