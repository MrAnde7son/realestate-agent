"use client";

import Link from "next/link";
import {
  Building,
  Handshake,
  AlertCircle,
  BarChart3,
  LineChart,
  User,
  Settings,
  LogOut,
  LogIn,
  Receipt,
  Banknote,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
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
import {
  getRouteMatchState,
  usePersistentPathname,
} from "@/lib/navigation-state";

export const baseNavigation = [
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
  // {
  //   name: "לקוחות",
  //   href: "/crm",
  //   icon: Users,
  // },
  // {
  //   name: "התראות",
  //   href: "/alerts",
  //   icon: AlertCircle,
  // },
  // {
  //   name: "דוחות",
  //   href: "/reports",
  //   icon: BarChart3,
  // },
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

export default function AppSidebar({
  className,
  isCollapsed = false,
}: AppSidebarProps) {
  const activePath = usePersistentPathname();
  const { user, logout, isAuthenticated, isLoading } = useAuth();

  const canAccessCrm = ["broker", "appraiser", "admin"].includes(user?.role || "");
  const canAccessAlertsAndReports = ["broker", "admin"].includes(user?.role || "");

  const navigation = baseNavigation
    .filter((item) => item.href !== "/crm" || canAccessCrm)
    .filter((item) => {
      if (item.href === "/alerts" || item.href === "/reports") {
        return canAccessAlertsAndReports;
      }
      return true;
    })
    .map((item) => ({ ...item }));

  if (user?.role === "admin") {
    // navigation.push({ name: "מעקב", href: "/admin/analytics", icon: LineChart });
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

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto p-3 pt-16">
        <Tooltip.Provider delayDuration={0} skipDelayDuration={0}>
          <nav className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;

              const matchState = getRouteMatchState(item.href, activePath);
              const isSelf = matchState === "self";
              const isDescendant = matchState === "descendant";

              return (
                <Tooltip.Root key={item.name}>
                  <Tooltip.Trigger asChild>
                    <Link
                      href={item.href}
                      aria-label={isCollapsed ? item.name : undefined}
                      aria-current={
                        isSelf ? "page" : isDescendant ? "true" : undefined
                      }
                      data-active-state={matchState}
                      className={cn(
                        "group relative flex items-center rounded-lg text-sm transition-colors",
                        isCollapsed
                          ? "justify-center px-2 py-3"
                          : "gap-2 px-2.5 py-2",
                        isCollapsed
                          ? isSelf || isDescendant
                            ? "bg-[var(--brand-teal)]/12 text-[var(--brand-teal)]"
                            : "text-muted-foreground hover:text-[var(--brand-teal)] hover:bg-[var(--brand-teal)]/8"
                          : isSelf || isDescendant
                          ? "bg-[var(--brand-teal)]/8 text-[var(--brand-teal)]"
                          : "text-muted-foreground hover:text-[var(--brand-teal)] hover:bg-[var(--brand-teal)]/8",
                        !isCollapsed && isSelf
                          ? "font-semibold"
                          : !isCollapsed && isDescendant
                          ? "font-medium text-[var(--brand-teal)]/80"
                          : undefined
                      )}
                    >
                      {!isCollapsed && (
                        <span
                          aria-hidden="true"
                          data-active-indicator
                          className={cn(
                            "absolute inset-y-1 rounded-full bg-[var(--brand-teal)] transition-opacity duration-200",
                            "ltr:right-1 rtl:left-1",
                            "w-1",
                            isSelf
                              ? "opacity-100"
                              : isDescendant
                              ? "opacity-60"
                              : "opacity-0"
                          )}
                        />
                      )}
                      <Icon
                        className={cn(
                          isCollapsed ? "h-8 w-8" : "h-4 w-4",
                          (isSelf || isDescendant) && "text-[var(--brand-teal)]"
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
      <div className="p-3 flex-shrink-0">
        {!isLoading && isAuthenticated ? (
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
              className="w-56 bg-background shadow-lg"
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
                {/* <DropdownMenuItem asChild>
                  <Link href="/billing" className="flex items-center">
                    <CreditCard className="ms-2 h-4 w-4" />
                    <span>חבילות ותשלומים</span>
                  </Link>
                </DropdownMenuItem> */}
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
        ) : (
          <Button
            asChild
            variant="default"
            className={cn(
              "w-full bg-[var(--brand-teal)] text-white hover:bg-[var(--brand-teal)]/90 shadow-sm",
              isCollapsed ? "px-2 py-2 h-10 rounded-full" : "px-2.5 py-2 justify-center gap-2"
            )}
          >
            <Link
              href="/auth"
              className={cn(
                "flex items-center w-full",
                isCollapsed ? "justify-center" : "justify-center gap-2"
              )}
            >
              <LogIn className="h-4 w-4" />
              {isCollapsed ? (
                <span className="sr-only">התחבר</span>
              ) : (
                <span>התחבר</span>
              )}
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}
