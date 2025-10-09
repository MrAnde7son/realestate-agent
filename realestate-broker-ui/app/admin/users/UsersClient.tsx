"use client"

import React, { useEffect, useMemo, useState } from "react"
import useSWR from "swr"
import { Plus, Search, MoreVertical, Edit, Power, RefreshCcw, Trash2, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react"
import {
  AdminUser,
  AdminUserPayload,
  listAdminUsers,
  createAdminUser,
  updateAdminUser,
  deleteAdminUser,
  setAdminUserStatus,
  resetAdminUserPassword,
} from "@/lib/api/admin-users"
import { ROLE_LABELS } from "@/lib/role-constants"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/Badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Label } from "@/components/ui/label"
import { Controller, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"

const ROLE_OPTIONS = [
  { value: "all", label: "כל התפקידים" },
  { value: "admin", label: ROLE_LABELS.admin },
  { value: "broker", label: ROLE_LABELS.broker },
  { value: "appraiser", label: ROLE_LABELS.appraiser },
  { value: "investor", label: ROLE_LABELS.investor },
  { value: "viewer", label: ROLE_LABELS.viewer },
] as const

const STATUS_OPTIONS: Array<{ value: "all" | "active" | "inactive"; label: string }> = [
  { value: "all", label: "הכל" },
  { value: "active", label: "פעילים" },
  { value: "inactive", label: "מושבתים" },
]

type SortKey = "name" | "role" | "last_login"

type FiltersState = {
  role: (typeof ROLE_OPTIONS)[number]["value"]
  status: (typeof STATUS_OPTIONS)[number]["value"]
  registrationDate: string
  ordering: string
  search: string
}

const userFormSchema = z.object({
  email: z.string().email("דוא״ל לא תקין"),
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  role: z.enum(["admin", "broker", "appraiser", "investor", "viewer"]),
  phone_number: z
    .string()
    .min(3, "טלפון קצר מדי")
    .max(30, "טלפון ארוך מדי")
    .optional()
    .or(z.literal("")),
  organization_name: z.string().max(255).optional().or(z.literal("")),
  company: z.string().max(100).optional().or(z.literal("")),
  password: z.string().min(8, "סיסמה חייבת להכיל לפחות 8 תווים").optional().or(z.literal("")),
})

type UserFormValues = z.infer<typeof userFormSchema>

type UserDialogMode = "create" | "edit"

interface UserDialogProps {
  open: boolean
  mode: UserDialogMode
  onOpenChange: (open: boolean) => void
  onSubmit: (values: UserFormValues) => Promise<void>
  loading: boolean
  user?: AdminUser | null
}

function UserDialog({ open, mode, onOpenChange, onSubmit, loading, user }: UserDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<UserFormValues>({
    resolver: zodResolver(userFormSchema),
    defaultValues: {
      email: user?.email || "",
      first_name: user?.first_name || "",
      last_name: user?.last_name || "",
      role: user?.role || "broker",
      phone_number: user?.phone_number || "",
      organization_name: user?.organization_name || "",
      company: user?.company || "",
      password: "",
    },
  })

  useEffect(() => {
    if (open) {
      reset({
        email: user?.email || "",
        first_name: user?.first_name || "",
        last_name: user?.last_name || "",
        role: user?.role || "broker",
        phone_number: user?.phone_number || "",
        organization_name: user?.organization_name || "",
        company: user?.company || "",
        password: "",
      })
    }
  }, [open, reset, user])

  const dialogTitle = mode === "create" ? "הוספת משתמש חדש" : "עריכת משתמש"

  return (
    <Dialog open={open} onOpenChange={(value) => !loading && onOpenChange(value)}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{dialogTitle}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="first_name">שם פרטי</Label>
              <Input id="first_name" placeholder="לדוגמה: יעל" {...register("first_name")} />
              {errors.first_name && (
                <p className="text-sm text-destructive">{errors.first_name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="last_name">שם משפחה</Label>
              <Input id="last_name" placeholder="לדוגמה: כהן" {...register("last_name")} />
              {errors.last_name && (
                <p className="text-sm text-destructive">{errors.last_name.message}</p>
              )}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">דוא״ל</Label>
            <Input id="email" type="email" placeholder="user@example.com" {...register("email")} />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="role">תפקיד</Label>
              <Controller
                control={control}
                name="role"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="role">
                      <SelectValue placeholder="בחר תפקיד" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">{ROLE_LABELS.admin}</SelectItem>
                      <SelectItem value="broker">{ROLE_LABELS.broker}</SelectItem>
                      <SelectItem value="appraiser">{ROLE_LABELS.appraiser}</SelectItem>
                      <SelectItem value="investor">{ROLE_LABELS.investor}</SelectItem>
                      <SelectItem value="viewer">{ROLE_LABELS.viewer}</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.role && (
                <p className="text-sm text-destructive">{errors.role.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone_number">טלפון</Label>
              <Input id="phone_number" placeholder="050-0000000" {...register("phone_number")} />
              {errors.phone_number && (
                <p className="text-sm text-destructive">{errors.phone_number.message}</p>
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="company">חברה</Label>
              <Input id="company" placeholder="שם החברה" {...register("company")} />
              {errors.company && (
                <p className="text-sm text-destructive">{errors.company.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="organization_name">ארגון</Label>
              <Input id="organization_name" placeholder="לדוגמה: Nadlaner" {...register("organization_name")} />
              {errors.organization_name && (
                <p className="text-sm text-destructive">{errors.organization_name.message}</p>
              )}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">סיסמה זמנית</Label>
            <Input
              id="password"
              type="password"
              placeholder={mode === "create" ? "סיסמה למשתמש חדש (אופציונלי)" : "הזן כדי לאפס"}
              {...register("password")}
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} disabled={loading}>
              ביטול
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "שומר..." : mode === "create" ? "הוסף משתמש" : "עדכן משתמש"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

interface SortButtonProps {
  active: boolean
  direction: "asc" | "desc" | null
  onClick: () => void
  children: React.ReactNode
}

function SortButton({ active, direction, onClick, children }: SortButtonProps) {
  const Icon = !active ? ArrowUpDown : direction === "asc" ? ArrowUp : ArrowDown
  return (
    <Button variant="ghost" className="px-2 text-xs font-medium" onClick={onClick}>
      <span className="ml-2">{children}</span>
      <Icon className="h-4 w-4" />
    </Button>
  )
}

function formatDate(value?: string | null) {
  if (!value) return "—"
  try {
    return new Date(value).toLocaleString("he-IL", {
      dateStyle: "medium",
      timeStyle: "short",
    })
  } catch (error) {
    return value
  }
}

export default function UsersClient() {
  const { toast } = useToast()
  const [page, setPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState("")
  const [filters, setFilters] = useState<FiltersState>({
    role: "all",
    status: "all",
    registrationDate: "",
    ordering: "-created_at",
    search: "",
  })
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<UserDialogMode>("create")
  const [activeUser, setActiveUser] = useState<AdminUser | null>(null)
  const [dialogLoading, setDialogLoading] = useState(false)
  const [pendingAction, setPendingAction] = useState<{ id: number; type: string } | null>(null)
  const [userToDelete, setUserToDelete] = useState<AdminUser | null>(null)

  useEffect(() => {
    const timeout = setTimeout(() => {
      setFilters((prev) => ({ ...prev, search: searchTerm.trim() }))
      setPage(1)
    }, 350)
    return () => clearTimeout(timeout)
  }, [searchTerm])

  const swrKey = useMemo(
    () => [
      "admin-users",
      page,
      filters.role,
      filters.status,
      filters.registrationDate,
      filters.ordering,
      filters.search || "",
    ],
    [filters.ordering, filters.registrationDate, filters.role, filters.search, filters.status, page]
  )

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    swrKey,
    () =>
      listAdminUsers({
        role: filters.role,
        status: filters.status,
        registrationDate: filters.registrationDate || undefined,
        ordering: filters.ordering,
        search: filters.search || undefined,
        page,
        pageSize: 10,
      }),
    {
      keepPreviousData: true,
      revalidateOnFocus: false,
    }
  )

  const users = data?.data || []
  const pagination = data?.pagination
  const loading = isLoading || isValidating

  const sortState = useMemo(() => {
    const { ordering } = filters
    if (!ordering) return { key: null as SortKey | null, direction: null as "asc" | "desc" | null }
    const desc = ordering.startsWith("-")
    const key = (desc ? ordering.slice(1) : ordering) as SortKey
    return { key, direction: desc ? "desc" : "asc" }
  }, [filters])

  const handleSort = (key: SortKey) => {
    setPage(1)
    setFilters((prev) => {
      const current = prev.ordering
      if (current === key) {
        return { ...prev, ordering: `-${key}` }
      }
      if (current === `-${key}`) {
        return { ...prev, ordering: "-created_at" }
      }
      return { ...prev, ordering: key }
    })
  }

  const openCreateDialog = () => {
    setActiveUser(null)
    setDialogMode("create")
    setDialogOpen(true)
  }

  const openEditDialog = (user: AdminUser) => {
    setActiveUser(user)
    setDialogMode("edit")
    setDialogOpen(true)
  }

  const handleDialogSubmit = async (values: UserFormValues) => {
    setDialogLoading(true)
    try {
      const payload: AdminUserPayload = {
        email: values.email,
        first_name: values.first_name?.trim() || undefined,
        last_name: values.last_name?.trim() || undefined,
        role: values.role,
        phone_number: values.phone_number?.trim() || undefined,
        organization_name: values.organization_name?.trim() || undefined,
        company: values.company?.trim() || undefined,
        password: values.password?.trim() || undefined,
      }

      if (dialogMode === "create") {
        const created = await createAdminUser(payload)
        await mutate()
        setDialogOpen(false)
        toast({
          title: "משתמש נוצר בהצלחה",
          description: created.temporary_password
            ? `סיסמה זמנית: ${created.temporary_password}`
            : "המשתמש נוסף למערכת",
        })
      } else if (activeUser) {
        await updateAdminUser(activeUser.id, payload)
        await mutate()
        setDialogOpen(false)
        toast({ title: "המשתמש עודכן" })
      }
    } catch (err) {
      toast({
        title: "שגיאה בשמירת משתמש",
        description: err instanceof Error ? err.message : "נסה שוב מאוחר יותר",
        variant: "destructive",
      })
    } finally {
      setDialogLoading(false)
    }
  }

  const handleStatusToggle = async (user: AdminUser) => {
    setPendingAction({ id: user.id, type: "status" })
    try {
      await setAdminUserStatus(user.id, !user.is_active)
      await mutate()
      toast({ title: !user.is_active ? "המשתמש הופעל" : "המשתמש הושבת" })
    } catch (err) {
      toast({
        title: "שגיאה בעדכון סטטוס",
        description: err instanceof Error ? err.message : "נסה שוב מאוחר יותר",
        variant: "destructive",
      })
    } finally {
      setPendingAction(null)
    }
  }

  const handleRoleChange = async (user: AdminUser, role: AdminUser["role"]) => {
    setPendingAction({ id: user.id, type: "role" })
    try {
      await updateAdminUser(user.id, { role })
      await mutate()
      toast({ title: "תפקיד עודכן" })
    } catch (err) {
      toast({
        title: "שגיאה בעדכון תפקיד",
        description: err instanceof Error ? err.message : "נסה שוב מאוחר יותר",
        variant: "destructive",
      })
    } finally {
      setPendingAction(null)
    }
  }

  const handleResetPassword = async (user: AdminUser) => {
    setPendingAction({ id: user.id, type: "reset" })
    try {
      const { temporaryPassword } = await resetAdminUserPassword(user.id)
      toast({
        title: "הסיסמה אופסה",
        description: temporaryPassword
          ? `סיסמה זמנית: ${temporaryPassword}`
          : "הסיסמה אופסה בהצלחה",
      })
    } catch (err) {
      toast({
        title: "שגיאה באיפוס סיסמה",
        description: err instanceof Error ? err.message : "נסה שוב מאוחר יותר",
        variant: "destructive",
      })
    } finally {
      setPendingAction(null)
    }
  }

  const confirmDeleteUser = async () => {
    if (!userToDelete) return
    setPendingAction({ id: userToDelete.id, type: "delete" })
    try {
      await deleteAdminUser(userToDelete.id)
      setUserToDelete(null)
      await mutate()
      toast({ title: "המשתמש נמחק" })
    } catch (err) {
      toast({
        title: "שגיאה במחיקת משתמש",
        description: err instanceof Error ? err.message : "נסה שוב מאוחר יותר",
        variant: "destructive",
      })
    } finally {
      setPendingAction(null)
    }
  }

  const renderRows = () => {
    if (loading && !users.length) {
      return (
        <TableBody>
          {Array.from({ length: 5 }).map((_, index) => (
            <TableRow key={index}>
              <TableCell colSpan={6}>
                <Skeleton className="h-8 w-full" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      )
    }

    if (!users.length) {
      return (
        <TableBody>
          <TableRow>
            <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
              לא נמצאו משתמשים תואמים.
            </TableCell>
          </TableRow>
        </TableBody>
      )
    }

    return (
      <TableBody>
        {users.map((user) => {
          const pending = pendingAction?.id === user.id
          return (
            <TableRow key={user.id}>
              <TableCell>
                <div className="flex flex-col text-right">
                  <span className="font-medium">{user.full_name || user.email}</span>
                  <span className="text-xs text-muted-foreground">{user.email}</span>
                </div>
              </TableCell>
              <TableCell>
                <Select
                  value={user.role}
                  onValueChange={(value) => handleRoleChange(user, value as AdminUser["role"])}
                  disabled={pending}
                >
                  <SelectTrigger className="w-[150px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">{ROLE_LABELS.admin}</SelectItem>
                    <SelectItem value="broker">{ROLE_LABELS.broker}</SelectItem>
                    <SelectItem value="appraiser">{ROLE_LABELS.appraiser}</SelectItem>
                    <SelectItem value="investor">{ROLE_LABELS.investor}</SelectItem>
                    <SelectItem value="viewer">{ROLE_LABELS.viewer}</SelectItem>
                  </SelectContent>
                </Select>
              </TableCell>
              <TableCell>
                <div className="flex flex-col text-right">
                  <span>{user.organization_name || "—"}</span>
                  <span className="text-xs text-muted-foreground">{user.company || ""}</span>
                </div>
              </TableCell>
              <TableCell>
                <Badge variant={user.is_active ? "success" : "secondary"}>
                  {user.is_active ? "פעיל" : "מושבת"}
                </Badge>
              </TableCell>
              <TableCell>{formatDate(user.last_login)}</TableCell>
              <TableCell className="text-left">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem onClick={() => openEditDialog(user)}>
                      <Edit className="ml-2 h-4 w-4" /> עריכה
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleStatusToggle(user)} disabled={pending}>
                      <Power className="ml-2 h-4 w-4" /> {user.is_active ? "השבתה" : "הפעלה"}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleResetPassword(user)} disabled={pending}>
                      <RefreshCcw className="ml-2 h-4 w-4" /> איפוס סיסמה
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setUserToDelete(user)}
                      className="text-destructive focus:text-destructive"
                    >
                      <Trash2 className="ml-2 h-4 w-4" /> מחיקה
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              className="w-64 pl-9 pr-3"
              placeholder="חיפוש לפי שם או דוא״ל"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
            />
          </div>
          <Select
            value={filters.role}
            onValueChange={(value) => {
              setFilters((prev) => ({ ...prev, role: value as FiltersState["role"] }))
              setPage(1)
            }}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="תפקיד" />
            </SelectTrigger>
            <SelectContent>
              {ROLE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-1 rounded-md border p-1">
            {STATUS_OPTIONS.map((option) => (
              <Button
                key={option.value}
                variant={filters.status === option.value ? "secondary" : "ghost"}
                size="sm"
                onClick={() => {
                  setFilters((prev) => ({ ...prev, status: option.value }))
                  setPage(1)
                }}
              >
                {option.label}
              </Button>
            ))}
          </div>
          <Input
            type="date"
            className="w-44"
            value={filters.registrationDate}
            onChange={(event) => {
              setFilters((prev) => ({ ...prev, registrationDate: event.target.value }))
              setPage(1)
            }}
          />
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="ml-2 h-4 w-4" /> הוסף משתמש
        </Button>
      </div>

      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          אירעה שגיאה בטעינת הנתונים: {error instanceof Error ? error.message : "נסה שוב מאוחר יותר"}
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-[220px] text-right">
                <SortButton
                  active={sortState.key === "name"}
                  direction={sortState.direction}
                  onClick={() => handleSort("name")}
                >
                  שם
                </SortButton>
              </TableHead>
              <TableHead className="min-w-[180px] text-right">
                <SortButton
                  active={sortState.key === "role"}
                  direction={sortState.direction}
                  onClick={() => handleSort("role")}
                >
                  תפקיד
                </SortButton>
              </TableHead>
              <TableHead className="min-w-[180px] text-right">ארגון</TableHead>
              <TableHead className="min-w-[100px] text-right">סטטוס</TableHead>
              <TableHead className="min-w-[160px] text-right">
                <SortButton
                  active={sortState.key === "last_login"}
                  direction={sortState.direction}
                  onClick={() => handleSort("last_login")}
                >
                  כניסה אחרונה
                </SortButton>
              </TableHead>
              <TableHead className="min-w-[80px] text-left">פעולות</TableHead>
            </TableRow>
          </TableHeader>
          {renderRows()}
        </Table>
      </div>

      {pagination && (
        <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
          <p className="text-sm text-muted-foreground">
            מציג {users.length} מתוך {pagination.count} משתמשים
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1 || loading}
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
            >
              הקודם
            </Button>
            <span className="text-sm">
              עמוד {pagination.page} מתוך {pagination.total_pages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= pagination.total_pages || loading}
              onClick={() => setPage((prev) => prev + 1)}
            >
              הבא
            </Button>
          </div>
        </div>
      )}

      <UserDialog
        open={dialogOpen}
        mode={dialogMode}
        onOpenChange={setDialogOpen}
        onSubmit={handleDialogSubmit}
        loading={dialogLoading}
        user={dialogMode === "edit" ? activeUser : null}
      />

      <AlertDialog open={!!userToDelete} onOpenChange={(open) => !pendingAction && setUserToDelete(open ? userToDelete : null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>מחיקת משתמש</AlertDialogTitle>
            <AlertDialogDescription>
              האם אתה בטוח שברצונך למחוק את {userToDelete?.full_name || userToDelete?.email}? פעולה זו אינה הפיכה.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={pendingAction?.type === "delete"}>
              ביטול
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteUser}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={pendingAction?.type === "delete"}
            >
              מחיקה
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
