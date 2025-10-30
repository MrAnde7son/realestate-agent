"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronDown,
  Building,
  Handshake,
  AlertCircle,
  Calculator,
  FileText,
  BarChart3,
  LineChart,
  User,
  CreditCard,
  Settings,
  LogOut,
  Receipt,
  Banknote,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
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
import * as Tooltip from "@radix-ui/react-tooltip";
import { useAuth } from "@/lib/auth-context";
import { getRoleLabel } from "@/lib/role-constants";

const baseNavigation = [
  {
    name: "נכסים",
    href: "/assets",
    icon: Building,
  },
  {
    name: "עסקאות",
    href: "/deals",
    icon: Handshake,
  },
  {
    name: "לקוחות",
    href: "/crm",
    icon: Users,
  },
  {
    name: "התראות",
    href: "/alerts",
    icon: AlertCircle,
  },
  {
    name: "דוחות",
    href: "/reports",
    icon: BarChart3,
  },
  {
    name: "הוצאות",
    href: "/deal-expenses",
    icon: Receipt,
  },
  {
    name: "משכנתא",
    href: "/mortgage/analyze",
    icon: Banknote,
  },
];

interface AppSidebarProps {
  className?: string;
  isCollapsed?: boolean;
}

function isActive(href: string, path: string) {
  return path === href || path.startsWith(href + "/");
}

export default function AppSidebar({
  className,
  isCollapsed = false,
}: AppSidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const canAccessCrm = ["broker", "appraiser", "admin"].includes(user?.role || "");

  const navigation = baseNavigation
    .filter((item) => item.href !== "/crm" || canAccessCrm)
    .map((item) => ({ ...item }));

  if (user?.role === "admin") {
    navigation.push({ name: "מעקב", href: "/admin/analytics", icon: LineChart });
    navigation.push({ name: "משתמשים", href: "/admin/users", icon: Users });
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
        "flex h-full flex-col bg-card transition-all duration-300 shadow-lg",
        isCollapsed ? "w-16" : "w-52",
        className
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/assets" className="flex items-center gap-3">
          <Logo variant="symbol" size={28} color="var(--brand-teal)" />
          {!isCollapsed && (
            <span className="text-lg font-bold text-logo-title">נדל״נר</span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto p-3">
        <Tooltip.Provider delayDuration={0} skipDelayDuration={0}>
          <nav className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;

              const active = isActive(item.href, pathname);

              return (
                <Tooltip.Root key={item.name}>
                  <Tooltip.Trigger asChild>
                    <Link
                      href={item.href}
                      aria-label={isCollapsed ? item.name : undefined}
                      className={cn(
                        "flex items-center rounded-lg text-sm transition-colors",
                        isCollapsed
                          ? "justify-center px-2 py-3"
                          : "gap-2 px-2.5 py-2",
                        active
                          ? "bg-[var(--brand-teal)]/8 text-[var(--brand-teal)] font-semibold"
                          : "text-muted-foreground hover:text-[var(--brand-teal)] hover:bg-[var(--brand-teal)]/8"
                      )}
                    >
                      <Icon
                        className={cn(
                          isCollapsed ? "h-8 w-8" : "h-4 w-4",
                          active && "text-primary"
                        )}
                      />
                      {!isCollapsed && <span>{item.name}</span>}
                    </Link>
                  </Tooltip.Trigger>
                  {isCollapsed && (
                    <Tooltip.Portal>
                      <Tooltip.Content
                        side="right"
                        sideOffset={8}
                        className="rounded bg-gray-900 px-2 py-1 text-xs font-medium text-white shadow-md"
                      >
                        {item.name}
                        <Tooltip.Arrow className="fill-gray-900" />
                      </Tooltip.Content>
                    </Tooltip.Portal>
                  )}
                </Tooltip.Root>
              );
            })}
          </nav>
        </Tooltip.Provider>
      </div>

      {/* Footer with User Menu - Moved to bottom of sidebar */}
      <div className="p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start gap-2 px-2 py-2 h-auto",
                isCollapsed ? "px-2" : "px-2.5"
              )}
            >
              <Avatar className="h-8 w-8">
                <AvatarFallback>{getUserInitials()}</AvatarFallback>
              </Avatar>
              {!isCollapsed && (
                <div className="flex-1 text-start">
                  <div className="text-sm font-medium">
                    {getUserDisplayName()}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {user?.email || "demo@example.com"}
                  </div>
                </div>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-56 bg-background border shadow-lg"
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
                {user?.role && (
                  <p className="text-xs leading-none text-muted-foreground">
                    {getRoleLabel(user.role)}
                  </p>
                )}
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem asChild>
                <Link href="/profile" className="flex items-center">
                  <User className="ms-2 h-4 w-4" />
                  <span>פרופיל</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/billing" className="flex items-center">
                  <CreditCard className="ms-2 h-4 w-4" />
                  <span>חבילות ותשלומים</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/settings" className="flex items-center">
                  <Settings className="ms-2 h-4 w-4" />
                  <span>הגדרות</span>
                </Link>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-red-600 focus:text-red-600"
              onClick={handleLogout}
            >
              <LogOut className="ms-2 h-4 w-4" />
              <span>התנתק</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
