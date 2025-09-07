import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import Link from "next/link";

type Tone = "teal" | "blue" | "green" | "amber" | "red";

const toneMap: Record<Tone, {border: string; dot: string; icon: string; value: string; hover: string}> = {
  teal:  { border: "border-[var(--brand-teal)]/30",  dot: "bg-[var(--brand-teal)]",  icon: "text-[var(--brand-teal)]",  value: "text-[var(--brand-teal)]",  hover: "hover:border-[var(--brand-teal)]/60 hover:shadow-[var(--brand-teal)]/10" },
  blue:  { border: "border-[var(--brand-blue)]/30",  dot: "bg-[var(--brand-blue)]",  icon: "text-[var(--brand-blue)]",  value: "text-[var(--brand-blue)]",  hover: "hover:border-[var(--brand-blue)]/60 hover:shadow-[var(--brand-blue)]/10" },
  green: { border: "border-[var(--brand-green)]/30", dot: "bg-[var(--brand-green)]", icon: "text-[var(--brand-green)]", value: "text-[var(--brand-green)]", hover: "hover:border-[var(--brand-green)]/60 hover:shadow-[var(--brand-green)]/10" },
  amber: { border: "border-amber-400/40",           dot: "bg-amber-400",           icon: "text-amber-500",            value: "text-amber-500",            hover: "hover:border-amber-400/60 hover:shadow-amber-400/10" },
  red:   { border: "border-red-500/30",             dot: "bg-red-500",             icon: "text-red-500",              value: "text-red-500",              hover: "hover:border-red-500/60 hover:shadow-red-500/10" },
};

interface KpiCardProps {
  title: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
  tone?: Tone;
  className?: string;
  children?: React.ReactNode;
  href?: string;
  onClick?: () => void;
  showHoverEffect?: boolean;
}

export function KpiCard({ 
  title, 
  value, 
  icon, 
  tone = "teal", 
  className, 
  children, 
  href, 
  onClick, 
  showHoverEffect = true 
}: KpiCardProps) {
  const t = toneMap[tone];
  
  const cardContent = (
    <Card
      className={cn(
        "transition-all duration-200 cursor-pointer",
        t.border,
        showHoverEffect && t.hover,
        showHoverEffect && "hover:shadow-lg hover:-translate-y-0.5",
        className
      )}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-1">
        <CardTitle className="text-sm text-muted-foreground font-medium flex items-center gap-2">
          <span className={cn("size-2 rounded-full", t.dot)} />
          {title}
        </CardTitle>
        {icon ? <div className={cn("size-5", t.icon)}>{icon}</div> : null}
      </CardHeader>
      <CardContent>
        <div className={cn("text-2xl font-semibold leading-none", t.value)}>{value}</div>
        {children ? <div className="mt-2 text-xs text-muted-foreground">{children}</div> : null}
      </CardContent>
    </Card>
  );

  if (href) {
    return (
      <Link href={href} className="block">
        {cardContent}
      </Link>
    );
  }

  if (onClick) {
    return (
      <div onClick={onClick}>
        {cardContent}
      </div>
    );
  }

  return cardContent;
}
